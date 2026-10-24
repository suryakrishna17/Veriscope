"""Page text extraction. Native PDF text first; OCR fallback for image-only pages and images.

Every word carries a bounding box as fractions of the page (0..1) so the UI can highlight it
regardless of render resolution, and a confidence (100 for native PDF text).
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field

import pdfplumber
import pypdfium2 as pdfium
import pytesseract
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


def ocr_image(img: Image.Image, lang: str) -> list[Word]:
    gray = ImageOps.grayscale(img)
    try:
        data = pytesseract.image_to_data(gray, lang=lang, output_type=pytesseract.Output.DICT, config="--psm 4", timeout=60)
    except (pytesseract.TesseractNotFoundError, RuntimeError) as e:
        raise OcrUnavailable(str(e)) from e
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
