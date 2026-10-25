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
