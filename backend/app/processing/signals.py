"""Document signals: signatures, letterheads, stamps, quality and metadata checks.

Every detector is heuristic and best-effort. Extracted signals carry a confidence and are
presented to the reviewer as clues, not proofs.
"""
from __future__ import annotations

import io
import logging
import re
from datetime import datetime, timezone
from typing import Any

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore[assignment]

import numpy as np
from PIL import Image

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore[assignment]

from .fields import Extracted, bbox_of, group_lines
from .text import PageText

UTC = getattr(datetime, "UTC", timezone.utc)

log = logging.getLogger("veriscope.signals")

EDITOR_HINTS = re.compile(r"photoshop|gimp|canva|pdf ?editor|ilovepdf|smallpdf|sejda|foxit phantom|nitro", re.I)


def _gray(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"))


def _crop(arr: np.ndarray, box: tuple[float, float, float, float]) -> np.ndarray:
    h, w = arr.shape
    x0, y0, x1, y1 = (max(0.0, min(1.0, v)) for v in box)
    return arr[int(y0 * h) : int(y1 * h), int(x0 * w) : int(x1 * w)]


def detect_signature(pages: list[PageText]) -> Extracted:
    """Ink in the region to the right of the last 'Signature' label on the document."""
    best: tuple[PageText, Any] | None = None
    for page in pages:
        for line in group_lines(page.words):
            for w in line:
                if w.t.lower().startswith("signature"):
                    best = (page, w)
    if best is None:
        return Extracted("signature_present", "no", "no", 0.55, None, "No 'Signature' label found on the document.", None, "visual")
    if best[0].image is None:
        return Extracted("signature_present", "no", "no", 0.5, None, "Page image was not available; signature presence could not be checked visually.", None, "visual")
    page, label = best
    arr = _gray(page.image).copy()
    h, w = arr.shape
    # mask every recognised word so printed text is not mistaken for ink
    for word in page.words:
        arr[int(word.y0 * h) : int(word.y1 * h) + 1, int(word.x0 * w) : int(word.x1 * w) + 1] = 255
    region = (label.x1 + 0.01, label.y0 - 0.06, min(label.x1 + 0.42, 0.98), label.y1 + 0.004)
    crop = _crop(arr, region)
    ink = float((crop < 110).mean()) if crop.size else 0.0
    present = ink > 0.012
    conf = round(min(0.95, 0.6 + abs(ink - 0.012) * 12), 3)
    bbox = [round(v, 5) for v in (max(0.0, region[0]), max(0.0, region[1]), region[2], region[3])]
    val = "yes" if present else "no"
    return Extracted("signature_present", val, val, conf, page.page_number, f"Ink coverage beside the signature label: {ink:.1%}", bbox, "visual")


def detect_seal(pages: list[PageText]) -> Extracted:
    if cv2 is None:
        return Extracted("seal_present", "no", "no", 0.5, None, "Visual stamp analysis is not available.", None, "visual")
    for page in pages:
        if page.image is None:
            continue
        gray = _gray(page.image)
        h, w = gray.shape
        _, th = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            (cx, cy), r = cv2.minEnclosingCircle(c)
            if not (0.035 * w <= r <= 0.14 * w):
                continue
            perim = cv2.arcLength(c, True)
            if perim == 0:
                continue
            circularity = 4 * np.pi * cv2.contourArea(c) / (perim * perim)
            if circularity > 0.75:
                bbox = [round((cx - r) / w, 5), round((cy - r) / h, 5), round((cx + r) / w, 5), round((cy + r) / h, 5)]
                return Extracted("seal_present", "yes", "yes", round(min(0.95, circularity), 3), page.page_number, "Circular stamp-like mark found.", bbox, "visual")
    return Extracted("seal_present", "no", "no", 0.6, None, "No circular stamp-like mark found.", None, "visual")


def detect_letterhead(pages: list[PageText]) -> Extracted:
    if not pages or not pages[0].words:
        return Extracted("letterhead_present", "no", "no", 0.5, None, "No text found on the first page.", None, "visual")
    page = pages[0]
    heights = sorted(w.y1 - w.y0 for w in page.words)
    median = heights[len(heights) // 2]
    top = [w for w in page.words if w.y1 < 0.14 and (w.y1 - w.y0) > median * 1.35]
    if top:
        return Extracted("letterhead_present", "yes", "yes", 0.8, 1, " ".join(w.t for w in top)[:120], bbox_of(top), "visual")
    return Extracted("letterhead_present", "no", "no", 0.65, None, "No large heading in the top band of page 1.", None, "visual")


def quality_signals(pages: list[PageText]) -> dict[str, Any]:
    out: dict[str, Any] = {"pages": []}
    for p in pages:
        info: dict[str, Any] = {"page": p.page_number, "source": p.source}
        if p.image is not None:
            gray = _gray(p.image)
            if cv2 is not None:
                info["blur_variance"] = round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1)
            else:
                info["blur_variance"] = 100.0
            info["pixels"] = [p.image.width, p.image.height]
        if p.source == "ocr":
            info["ocr_mean_confidence"] = round(p.mean_confidence, 1)
            info["ocr_word_count"] = len(p.words)
        out["pages"].append(info)
    ocr_pages = [x for x in out["pages"] if x["source"] == "ocr"]
    out["ocr_used"] = bool(ocr_pages)
    out["min_ocr_confidence"] = min((x["ocr_mean_confidence"] for x in ocr_pages), default=None)
    out["low_resolution"] = any(min(x.get("pixels", [9999, 9999])) < 1000 for x in ocr_pages)
    out["blurry"] = any(x.get("blur_variance", 9999) < 60 for x in ocr_pages)
    return out


def _pdf_date(value: Any) -> datetime | None:
    if not value:
        return None
    s = str(value)
    m = re.match(r"D?:?(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?", s)
    if not m:
        return None
    parts = [int(p) if p else d for p, d in zip(m.groups(), (0, 1, 1, 0, 0, 0))]  # noqa: B905
    try:
        return datetime(*parts, tzinfo=UTC)  # type: ignore[misc]
    except ValueError:
        log.debug("pdf_date_parse_failed", extra={"ctx": {"raw": s[:30]}})
        return None


def metadata_signals(data: bytes, mime: str) -> dict[str, Any]:
    out: dict[str, Any] = {"notes": []}
    if mime == "application/pdf":
        if PdfReader is None:
            return out
        try:
            reader = PdfReader(io.BytesIO(data))
            meta = reader.metadata or {}
            producer = str(meta.get("/Producer", "") or "")
            creator = str(meta.get("/Creator", "") or "")
            created, modified = _pdf_date(meta.get("/CreationDate")), _pdf_date(meta.get("/ModDate"))
            out.update(producer=producer[:120], creator=creator[:120], created=created.isoformat() if created else None, modified=modified.isoformat() if modified else None)
            out["incremental_saves"] = max(0, data.count(b"%%EOF") - 1)
            if created and modified:
                gap = (modified - created).days
                out["modification_gap_days"] = gap
                if gap < 0:
                    out["notes"].append("Modification date is earlier than creation date.")
                elif gap > 30:
                    out["notes"].append(f"File was modified {gap} days after it was created.")
            if out["incremental_saves"]:
                out["notes"].append(f"PDF contains {out['incremental_saves']} incremental update(s) after first save.")
            if EDITOR_HINTS.search(producer + " " + creator):
                out["notes"].append(f"Producer/creator names an editing tool ({(producer or creator)[:60]}).")
        except Exception:
            return out
    else:
        with Image.open(io.BytesIO(data)) as im:
            software = str(im.getexif().get(305, "") or "")
        out["software"] = software[:120]
        if EDITOR_HINTS.search(software):
            out["notes"].append(f"Image metadata names an editing tool ({software[:60]}).")
    return out
