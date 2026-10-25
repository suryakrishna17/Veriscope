"""Page text extraction. Native PDF text first; OCR fallback for image-only pages and images.

Every word carries a bounding box as fractions of the page (0..1) so the UI can highlight it
regardless of render resolution, and a confidence (100 for native PDF text).
"""
from __future__ import annotations

import base64
import io
import logging
import os
from dataclasses import dataclass, field

import pdfplumber
import pypdfium2 as pdfium
import pytesseract
import requests
from PIL import Image, ImageOps

log = logging.getLogger("veriscope.text")

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
    pdf = pdfium.PdfDocument(data)
    try:
        page = pdf[page_index]
        # Close the page handle in its own finally so it is released even if
        # render() or to_pil() raises an exception.
        try:
            img = page.render(scale=scale).to_pil().convert("RGB")
        finally:
            page.close()
        return img
    finally:
        pdf.close()


def groq_ocr_image(img: Image.Image) -> list[Word] | None:
    api_key = os.environ.get("GROQ_API_KEY") or (os.environ.get("LLM_API_KEY") if os.environ.get("LLM_PROVIDER") == "groq" else "")
    if not api_key:
        return None
    try:
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
        text = r.json()["choices"][0]["message"]["content"]
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return []
        words: list[Word] = []
        num_lines = len(lines)
        for line_idx, line in enumerate(lines):
            line_words = line.split()
            if not line_words:
                continue
            y0 = (line_idx + 0.1) / num_lines
            y1 = (line_idx + 0.9) / num_lines
            num_words = len(line_words)
            for word_idx, w_txt in enumerate(line_words):
                x0 = word_idx / num_words
                x1 = (word_idx + 0.9) / num_words
                words.append(Word(w_txt, x0, y0, x1, y1, 95.0))
        return words
    except Exception as e:
        log.warning("groq_ocr_failed", extra={"error": str(e)})
        return None


def ocr_image(img: Image.Image, lang: str) -> list[Word]:
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
    pages: list[PageText] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for idx, page in enumerate(pdf.pages):
            pw, ph = float(page.width), float(page.height)
            raw = page.extract_words(keep_blank_chars=False, use_text_flow=False, extra_attrs=["size"])
            words = [Word(str(r["text"]), r["x0"] / pw, r["top"] / ph, r["x1"] / pw, r["bottom"] / ph, 100.0) for r in raw]
            img = render_pdf_page(data, idx, OCR_SCALE if ocr_enabled else 2.0)
            if sum(len(w.t) for w in words) >= MIN_NATIVE_CHARS:
                pages.append(PageText(idx + 1, pw, ph, "pdf_text", words, img))
            elif ocr_enabled:
                pages.append(PageText(idx + 1, pw, ph, "ocr", ocr_image(img, lang), img))
            else:
                pages.append(PageText(idx + 1, pw, ph, "pdf_text", words, img))
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
