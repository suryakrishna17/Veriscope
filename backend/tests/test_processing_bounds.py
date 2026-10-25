"""Tests for upload bounds, page size limits, and hidden text detection."""
import io
import unittest

from reportlab.lib.colors import white
from reportlab.pdfgen import canvas

from app.core.errors import ApiError
from app.processing.signals import quality_signals
from app.processing.text import extract_pdf
from app.processing.validation import validate_upload


class TestProcessingBounds(unittest.TestCase):
    def test_pdf_page_too_large_rejected(self) -> None:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(4000, 4000))
        c.drawString(100, 100, "Huge page")
        c.save()
        data = buf.getvalue()

        with self.assertRaises(ApiError) as ctx:
            validate_upload(data, "huge.pdf", max_bytes=10_000_000, max_pages=10)
        self.assertEqual(ctx.exception.code, "PAGE_SIZE_UNSUPPORTED")
        self.assertEqual(ctx.exception.status, 422)

    def test_pdf_page_too_small_rejected(self) -> None:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(20, 20))
        c.drawString(5, 5, "Tiny")
        c.save()
        data = buf.getvalue()

        with self.assertRaises(ApiError) as ctx:
            validate_upload(data, "tiny.pdf", max_bytes=10_000_000, max_pages=10)
        self.assertEqual(ctx.exception.code, "PAGE_SIZE_UNSUPPORTED")
        self.assertEqual(ctx.exception.status, 422)

    def test_hidden_text_detected_and_separated(self) -> None:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(600, 800))
        c.drawString(100, 700, "Visible text line one with sufficient length to meet native threshold")
        c.setFillColor(white)
        c.drawString(100, 600, "SecretPromptInjectionTextHere")
        c.save()
        data = buf.getvalue()

        pages = extract_pdf(data, ocr_enabled=False, lang="eng")
        self.assertEqual(len(pages), 1)
        page = pages[0]
        # Visible text should contain line one
        self.assertIn("Visible", page.text)
        # Hidden text must NOT be in standard page.text
        self.assertNotIn("SecretPromptInjectionTextHere", page.text)
        self.assertGreaterEqual(len(page.hidden_words), 1)

        sig = quality_signals(pages)
        self.assertTrue(sig["hidden_text_detected"])
        self.assertGreaterEqual(sig["hidden_word_count"], 1)
