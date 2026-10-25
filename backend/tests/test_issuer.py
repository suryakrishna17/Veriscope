"""Tests for issuer verifier implementations (Null, Mock, DigiLocker DPI)."""
import unittest

from app.issuer.verifier import DigiLockerIssuerVerifier, NullIssuerVerifier, build_verifier


class IssuerVerifierTests(unittest.TestCase):
    def test_null_verifier(self) -> None:
        v = NullIssuerVerifier()
        check = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "FS-1234"})
        self.assertEqual(check.label, "NOT_VERIFIED")
        self.assertIsNone(check.issuer)

    def test_digilocker_verifier_with_valid_token(self) -> None:
        v = DigiLockerIssuerVerifier()
        # Verifiable certificate number DL-...
        check = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "DL-FIRE-2026-9912"})
        self.assertEqual(check.label, "ISSUER_VERIFIED")
        self.assertIn("DigiLocker", check.issuer or "")
        self.assertTrue(check.response_id and check.response_id.startswith("DPI-"))

        # Verifiable DigiLocker URI
        check_uri = v.verify("UNIVERSITY_AFFILIATION_ORDER", {"digilocker_uri": "in.gov.aicte/eoa/2026/1-4410023451"})
        self.assertEqual(check_uri.label, "ISSUER_VERIFIED")
        self.assertIn("MeitY", check_uri.issuer or "")

    def test_digilocker_verifier_without_token(self) -> None:
        v = DigiLockerIssuerVerifier()
        check = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "REGULAR-123"})
        self.assertEqual(check.label, "NOT_VERIFIED")

    def test_build_verifier(self) -> None:
        self.assertIsInstance(build_verifier("digilocker"), DigiLockerIssuerVerifier)
        self.assertIsInstance(build_verifier("null"), NullIssuerVerifier)
