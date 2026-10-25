"""Tests for issuer verifier implementations (Null, Mock, DigiLocker DPI)."""
import unittest

from app.issuer.verifier import DigiLockerIssuerVerifier, NullIssuerVerifier, build_verifier


class IssuerVerifierTests(unittest.TestCase):
    def test_null_verifier(self) -> None:
        v = NullIssuerVerifier()
        check = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "FS-1234"})
        self.assertEqual(check.label, "NOT_VERIFIED")
        self.assertIsNone(check.issuer)

    def test_digilocker_verifier_without_key_never_verifies(self) -> None:
        v = DigiLockerIssuerVerifier()
        # Even with DL-... prefix or digilocker_uri, unauthenticated checks must be NOT_VERIFIED
        check = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "DL-FIRE-2026-9912"})
        self.assertEqual(check.label, "NOT_VERIFIED")
        self.assertIn("not configured", check.reason)

        check_uri = v.verify("UNIVERSITY_AFFILIATION_ORDER", {"digilocker_uri": "in.gov.aicte/eoa/2026/1-4410023451"})
        self.assertEqual(check_uri.label, "NOT_VERIFIED")

    def test_digilocker_verifier_without_token(self) -> None:
        v = DigiLockerIssuerVerifier()
        check = v.verify("FIRE_SAFETY_CERTIFICATE", {"certificate_number": "REGULAR-123"})
        self.assertEqual(check.label, "NOT_VERIFIED")

    def test_build_verifier(self) -> None:
        self.assertIsInstance(build_verifier("digilocker"), DigiLockerIssuerVerifier)
        self.assertIsInstance(build_verifier("null"), NullIssuerVerifier)
