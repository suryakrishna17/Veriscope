"""Page text extraction. Native PDF text first; OCR fallback for image-only pages and images.

Every word carries a bounding box as fractions of the page (0..1) so the UI can highlight it
regardless of render resolution, and a confidence (100 for native PDF text).
"""
from __future__ import annotations

import base64
import io
import logging
import os
import re
from dataclasses import dataclass, field

try:
    import pdfplumber
except ImportError:
    pdfplumber = None
try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None
try:
    import pytesseract
except ImportError:
    pytesseract = None
import numpy as np
import requests
from PIL import Image, ImageOps

log = logging.getLogger("veriscope.text")

MAX_RENDER_PIXELS = 12_000_000
OCR_SCALE = 300 / 72  # render PDFs at 300 dpi for OCR
MIN_NATIVE_CHARS = 25


@dataclass
class Word:
    t: str
    x0: float
    y0: float
    x1: float
    y1: float
    c: float = 100.0
    source: str = "ocr"  # pdf_text | ocr | llm_suggestion

    def as_dict(self) -> dict[str, float | str]:
        return {"t": self.t, "x0": round(self.x0, 5), "y0": round(self.y0, 5), "x1": round(self.x1, 5), "y1": round(self.y1, 5), "c": round(self.c, 1)}


@dataclass
class PageText:
    page_number: int
    width: float
    height: float
    source: str  # pdf_text | ocr
    words: list[Word] = field(default_factory=list)
    image: Image.Image | None = None  # rendered page, used for visual signals
    hidden_words: list[Word] = field(default_factory=list)

    @property
    def mean_confidence(self) -> float:
        if not self.words:
            return 0.0
        return sum(w.c for w in self.words) / len(self.words)

    @property
    def text(self) -> str:
        return " ".join(w.t for w in self.words)


class OcrUnavailable(RuntimeError):
    pass


def render_pdf_page(data: bytes, page_index: int, scale: float) -> Image.Image:
    if pdfium is None:
        raise OcrUnavailable("pypdfium2 is not installed.")
    pdf = pdfium.PdfDocument(data)
    try:
        page = pdf[page_index]
        # Close the page handle in its own finally so it is released even if
        # render() or to_pil() raises an exception.
        try:
            pw, ph = page.get_size()
            target_pixels = (pw * scale) * (ph * scale)
            if target_pixels > MAX_RENDER_PIXELS:
                scale = (MAX_RENDER_PIXELS / max(1.0, pw * ph)) ** 0.5
            img = page.render(scale=scale).to_pil().convert("RGB")
        finally:
            page.close()
        return img
    finally:
        pdf.close()


def groq_ocr_image(img: Image.Image) -> list[Word] | None:
    """Invokes Groq Vision OCR as an emergency fallback when enabled with explicit third-party consent."""
    groq_enabled = os.environ.get("GROQ_OCR_ENABLED", "").lower() in {"1", "true", "yes"}
    consent = os.environ.get("OCR_THIRD_PARTY_CONSENT", "").lower() in {"1", "true", "yes"}
    if not (groq_enabled and consent):
        return None

    api_key = os.environ.get("GROQ_API_KEY") or (os.environ.get("LLM_API_KEY") if os.environ.get("LLM_PROVIDER") == "groq" else "")
    if not api_key:
        return None
    try:
        log.info("groq_vision_ocr_dispatch", extra={"model": "qwen/qwen3.8-27b"})
        max_dim = 1600
        w, h = img.size
        scale = min(1.0, max_dim / max(w, h))
        if scale < 1.0:
            resample = getattr(Image, "Resampling", Image).LANCZOS
            thumb = img.resize((int(w * scale), int(h * scale)), resample)
        else:
            thumb = img
        buf = io.BytesIO()
        thumb.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        prompt = (
            "You are an OCR engine. Extract all readable text from this document image exactly as it appears. "
            "Preserve line breaks. Output ONLY the extracted text, with no introductory or concluding remarks."
        )
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "qwen/qwen3.8-27b",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                        ],
                    }
                ],
                "temperature": 0,
                "max_tokens": 1500,
            },
            timeout=18,
        )
        if r.status_code != 200:
            log.warning("groq_ocr_http_failed", extra={"status": r.status_code, "text": r.text[:100]})
            return None
        raw_text = r.json()["choices"][0]["message"]["content"]
        # Strip reasoning blocks (e.g. <think>...</think>) before parsing
        cleaned_text = re.sub(r"(?i)<think>[\s\S]*?</think>", "", raw_text).strip()
        lines = [line.strip() for line in cleaned_text.split("\n") if line.strip()]
        if not lines:
            return []
        words: list[Word] = []
        for line in lines:
            line_words = line.split()
            for w_txt in line_words:
                # LLM OCR suggestions carry no synthetic pixel bbox and capped confidence <= 0.60
                words.append(Word(w_txt, 0.0, 0.0, 0.0, 0.0, 60.0, source="llm_suggestion"))
        return words
    except Exception as e:
        log.warning("groq_ocr_failed", extra={"error": str(e)})
        return None


def ocr_image(img: Image.Image, lang: str) -> list[Word]:
    if pytesseract is None:
        groq_words = groq_ocr_image(img)
        if groq_words is not None:
            return groq_words
        raise OcrUnavailable("pytesseract is not installed.")
    gray = ImageOps.grayscale(img)
    try:
        data = pytesseract.image_to_data(gray, lang=lang, output_type=pytesseract.Output.DICT, config="--psm 4", timeout=60)
        w, h = gray.size
        words: list[Word] = []
        for i, txt in enumerate(data["text"]):
            txt = (txt or "").strip()
            conf = float(data["conf"][i])
            if not txt or conf < 0:
                continue
            left, top, bw, bh = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            words.append(Word(txt, left / w, top / h, (left + bw) / w, (top + bh) / h, conf))
        return words
    except (pytesseract.TesseractNotFoundError, RuntimeError) as e:
        groq_words = groq_ocr_image(img)
        if groq_words is not None:
            return groq_words

        raise OcrUnavailable(str(e)) from e


def extract_pdf(data: bytes, ocr_enabled: bool, lang: str) -> list[PageText]:
    if pdfplumber is None:
        raise OcrUnavailable("pdfplumber is not installed.")
    pages: list[PageText] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for idx, page in enumerate(pdf.pages):
            pw, ph = float(page.width), float(page.height)
            try:
                raw = page.extract_words(
                    keep_blank_chars=False,
                    use_text_flow=False,
                    extra_attrs=["size", "non_stroking_color", "rendering_mode"],
                )
            except Exception:
                try:
                    raw = page.extract_words(keep_blank_chars=False, use_text_flow=False, extra_attrs=["size", "non_stroking_color"])
                except Exception:
                    raw = page.extract_words(keep_blank_chars=False, use_text_flow=False, extra_attrs=["size"])

            # Render page to check visual contrast against background pixels
            scale = 1.5
            img = render_pdf_page(data, idx, scale)
            gray_arr = np.asarray(img.convert("L"))
            iw, ih = img.width, img.height

            words: list[Word] = []
            hidden_words: list[Word] = []
            for r in raw:
                txt = str(r["text"]).strip()
                if not txt:
                    continue
                w_obj = Word(txt, r["x0"] / pw, r["top"] / ph, r["x1"] / pw, r["bottom"] / ph, 100.0)
                size = float(r.get("size") or 12.0)
                render_mode = r.get("rendering_mode")

                out_of_bounds = r["x1"] < 0 or r["x0"] > pw or r["bottom"] < 0 or r["top"] > ph
                # Mode 3 = invisible text (render neither fill nor stroke per PDF spec ISO 32000)
                if size <= 1.0 or out_of_bounds or render_mode in (3, "3"):
                    hidden_words.append(w_obj)
                    continue

                # Inspect rendered image crop to determine true visual contrast
                cx0 = max(0, min(iw - 1, int((r["x0"] / pw) * iw)))
                cx1 = max(0, min(iw, int((r["x1"] / pw) * iw)))
                cy0 = max(0, min(ih - 1, int((r["top"] / ph) * ih)))
                cy1 = max(0, min(ih, int((r["bottom"] / ph) * ih)))

                if cx1 <= cx0 or cy1 <= cy0:
                    hidden_words.append(w_obj)
                    continue

                crop = gray_arr[cy0:cy1, cx0:cx1]
                contrast = int(np.ptp(crop)) if crop.size > 0 else 0

                # If rendered contrast is low (< 35 grey levels), text is hidden against background
                # (covers white-on-white, near-white grey, and black text masked by white shapes).
                # If contrast >= 35, text is visually readable (e.g. white headings on dark banners).
                if contrast < 35:
                    hidden_words.append(w_obj)
                else:
                    words.append(w_obj)

            native_chars = sum(len(w.t) for w in words)
            if native_chars >= MIN_NATIVE_CHARS:
                pages.append(PageText(idx + 1, pw, ph, "pdf_text", words, img, hidden_words))
            elif ocr_enabled:
                ocr_img = render_pdf_page(data, idx, OCR_SCALE)
                pages.append(PageText(idx + 1, pw, ph, "ocr", ocr_image(ocr_img, lang), ocr_img, hidden_words))
            else:
                pages.append(PageText(idx + 1, pw, ph, "pdf_text", words, img, hidden_words))
    return pages


def extract_image(data: bytes, ocr_enabled: bool, lang: str) -> list[PageText]:
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img).convert("RGB")
    words = ocr_image(img, lang) if ocr_enabled else []
    return [PageText(1, float(img.width), float(img.height), "ocr", words, img)]


def extract(data: bytes, mime: str, ocr_enabled: bool, lang: str) -> list[PageText]:
    if mime == "application/pdf":
        return extract_pdf(data, ocr_enabled, lang)
    return extract_image(data, ocr_enabled, lang)
