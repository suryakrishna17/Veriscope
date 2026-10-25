"""Integration tests for the DigiLocker DPI service and certificate pull endpoint."""
from tests.helpers import AppTestCase


class DigiLockerIntegrationTests(AppTestCase):
    def test_list_sandbox_certificates(self) -> None:
        r = self.client.get("/api/v1/integrations/digilocker/certificates", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200)
        certs = r.get_json()
        self.assertGreaterEqual(len(certs), 3)
        doc_types = {c["doc_type"] for c in certs}
        self.assertIn("FIRE_SAFETY_CERTIFICATE", doc_types)
        self.assertIn("UNIVERSITY_AFFILIATION_ORDER", doc_types)

    def test_pull_document_from_digilocker(self) -> None:
        case = self.new_case()
        case_id = case["id"]

        r = self.client.post(
            f"/api/v1/cases/{case_id}/digilocker/pull",
            json={"doc_type": "FIRE_SAFETY_CERTIFICATE"},
            headers=self.h("applicant"),
        )
        self.assertEqual(r.status_code, 201)
        doc = r.get_json()
        self.assertEqual(doc["doc_type"], "FIRE_SAFETY_CERTIFICATE")
        self.assertEqual(doc["trust_label"], "ISSUER_VERIFIED")
        self.assertIn("Delhi Fire Service", doc["issuer"])
        self.assertEqual(doc["version"], 1)

        # Resubmit another version via DigiLocker to test sequential versioning
        r2 = self.client.post(
            f"/api/v1/cases/{case_id}/digilocker/pull",
            json={"doc_type": "FIRE_SAFETY_CERTIFICATE"},
            headers=self.h("applicant"),
        )
        self.assertEqual(r2.status_code, 201)
        doc2 = r2.get_json()
        self.assertEqual(doc2["version"], 2)
