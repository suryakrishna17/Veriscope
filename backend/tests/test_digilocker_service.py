"""Integration tests for the DigiLocker DPI service and certificate pull endpoint."""

from tests.helpers import AppTestCase


class DigiLockerIntegrationTests(AppTestCase):
    def test_digilocker_disabled_by_default(self) -> None:
        self.svc.settings = type(self.svc.settings)(**{**self.svc.settings.__dict__, "digilocker_sandbox": False})
        r = self.client.get("/api/v1/integrations/digilocker/certificates", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 404)

        case = self.new_case()
        r = self.client.post(
            f"/api/v1/cases/{case['id']}/digilocker/pull",
            json={"doc_type": "FIRE_SAFETY_CERTIFICATE"},
            headers=self.h("reviewer"),
        )
        self.assertEqual(r.status_code, 404)

    def test_list_sandbox_certificates_when_enabled(self) -> None:
        self.svc.settings = type(self.svc.settings)(**{**self.svc.settings.__dict__, "digilocker_sandbox": True})
        # Applicant cannot call integration endpoint (403)
        r_applicant = self.client.get("/api/v1/integrations/digilocker/certificates", headers=self.h("applicant"))
        self.assertEqual(r_applicant.status_code, 403)

        # Reviewer can call integration endpoint
        r = self.client.get("/api/v1/integrations/digilocker/certificates", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200)
        certs = r.get_json()
        self.assertGreaterEqual(len(certs), 3)
        doc_types = {c["doc_type"] for c in certs}
        self.assertIn("FIRE_SAFETY_CERTIFICATE", doc_types)
        self.assertIn("UNIVERSITY_AFFILIATION_ORDER", doc_types)

    def test_pull_document_is_marked_not_verified(self) -> None:
        self.svc.settings = type(self.svc.settings)(**{**self.svc.settings.__dict__, "digilocker_sandbox": True})
        case = self.new_case()
        case_id = case["id"]

        # Applicant cannot pull
        r_applicant = self.client.post(
            f"/api/v1/cases/{case_id}/digilocker/pull",
            json={"doc_type": "FIRE_SAFETY_CERTIFICATE"},
            headers=self.h("applicant"),
        )
        self.assertEqual(r_applicant.status_code, 403)

        # Reviewer pull succeeds but is strictly NOT_VERIFIED and simulated
        r = self.client.post(
            f"/api/v1/cases/{case_id}/digilocker/pull",
            json={"doc_type": "FIRE_SAFETY_CERTIFICATE"},
            headers=self.h("reviewer"),
        )
        self.assertEqual(r.status_code, 201)
        doc = r.get_json()
        self.assertEqual(doc["doc_type"], "FIRE_SAFETY_CERTIFICATE")
        self.assertEqual(doc["trust_label"], "NOT_VERIFIED")
        self.assertTrue(doc.get("simulated", False))
        self.assertIn("Delhi Fire Service", doc["issuer"])
        self.assertEqual(doc["version"], 1)

        # Resubmit another version via DigiLocker to test sequential versioning
        r2 = self.client.post(
            f"/api/v1/cases/{case_id}/digilocker/pull",
            json={"doc_type": "FIRE_SAFETY_CERTIFICATE"},
            headers=self.h("reviewer"),
        )
        self.assertEqual(r2.status_code, 201)
        doc2 = r2.get_json()
        self.assertEqual(doc2["version"], 2)
        self.assertEqual(doc2["trust_label"], "NOT_VERIFIED")
