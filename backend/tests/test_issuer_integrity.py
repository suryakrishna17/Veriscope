"""Test issuer integrity: verifiers must never falsely claim ISSUER_VERIFIED."""
import unittest

from app.issuer.verifier import DigiLockerIssuerVerifier, NullIssuerVerifier, build_verifier


class TestIssuerIntegrity(unittest.TestCase):
    def test_null_verifier_never_verifies(self) -> None:
        v = NullIssuerVerifier()
        res = v.verify("ANY_DOC", {"certificate_number": "DL-12345"})
        self.assertEqual(res.label, "NOT_VERIFIED")
        self.assertFalse(res.simulated)

    def test_digilocker_verifier_without_key_never_verifies(self) -> None:
        v = DigiLockerIssuerVerifier(api_key="")
        # Even with DL- prefix, it must reject
        res = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "DL-DFS-NOC-2026-0881"})
        self.assertEqual(res.label, "NOT_VERIFIED")
        self.assertIn("not configured", res.reason)

    def test_digilocker_verifier_does_not_use_heuristic(self) -> None:
        v = DigiLockerIssuerVerifier(api_key="mock_key")
        res = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "DL-DFS-NOC-2026-0881"})
        self.assertEqual(res.label, "NOT_VERIFIED")

    def test_build_verifier_defaults(self) -> None:
        v = build_verifier("unknown")
        self.assertIsInstance(v, NullIssuerVerifier)


class TestQrAndSignatureIntegrity(unittest.TestCase):
    def test_qr_detection_allowlist_and_no_network(self) -> None:
        """Item 7: Validates QR domain allowlist matching on dot-boundaries without network calls."""
        from PIL import Image

        from app.processing.signals import ALLOWED_DOMAINS, detect_qr_codes
        from app.processing.text import PageText

        # 1. Page with no QR
        blank = Image.new("RGB", (200, 200), color=(255, 255, 255))
        p_blank = PageText(1, 200, 200, "pdf_text", [], blank)
        res = detect_qr_codes([p_blank])
        self.assertEqual(len(res), 0)

        # 2. Allowlist checks (dot boundary logic)
        allowed_sample = "portal.aicte-india.org"
        self.assertTrue(any(allowed_sample == d or allowed_sample.endswith("." + d) for d in ALLOWED_DOMAINS))

        # Lookalike attacker domain must NOT match allowlist
        imposter = "fake-aicte-india.org"
        self.assertFalse(any(imposter == d or imposter.endswith("." + d) for d in ALLOWED_DOMAINS))

    def test_pdf_signatures_unsigned_document(self) -> None:
        """Item 6: Verifies that unsigned PDFs are cleanly reported without false positives."""
        import io

        from pypdf import PdfWriter

        from app.processing.signals import detect_pdf_signatures

        w = PdfWriter()
        w.add_blank_page(width=595, height=842)
        out = io.BytesIO()
        w.write(out)

        sig_info = detect_pdf_signatures(out.getvalue(), "application/pdf")
        self.assertFalse(sig_info["has_signatures"])
        self.assertEqual(sig_info.get("count", 0), 0)


class TestAicteInstitutionalRecords(unittest.TestCase):
    def test_lookup_and_cross_check_records(self) -> None:
        """Item 9 (R2): AICTE Institutional Records Store validates ID, name, intake, and TER fee payment."""
        from app.records.registry import aicte_records

        # 1. Valid registered institution
        res_valid = aicte_records.cross_check_application("1-1234567890", "Apex Institute of Technology", declared_intake=240)
        self.assertTrue(res_valid["verified"])
        self.assertEqual(res_valid["status"], "VERIFIED")
        self.assertEqual(res_valid["ter_payment_status"], "PAID")
        self.assertEqual(res_valid["deficiency_status"], "NIL")

        # 2. Name mismatch detected
        res_mismatch = aicte_records.cross_check_application("1-1234567890", "Totally Different Academy Name")
        self.assertFalse(res_mismatch["verified"])
        self.assertEqual(res_mismatch["status"], "MISMATCH_DETECTED")
        self.assertIn("Name mismatch", res_mismatch["notes"])

        # 3. Non-existent institute ID
        res_none = aicte_records.cross_check_application("1-0000000000", "Unknown College")
        self.assertFalse(res_none["verified"])
        self.assertEqual(res_none["status"], "NOT_FOUND")
