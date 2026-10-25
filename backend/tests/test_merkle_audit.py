"""Tests for Merkle-tree cryptographic audit notarization and endpoint."""
from app.services.audit import compute_merkle_root, record
from tests.helpers import AppTestCase


class MerkleAuditTests(AppTestCase):
    def test_merkle_tree_calculation_and_endpoint(self) -> None:
        case = self.new_case()
        case_id = case["id"]

        # Empty or default case has at least case.created event
        data = compute_merkle_root(self.app.extensions["veriscope"].db, case_id)
        self.assertIsNotNone(data["merkle_root"])
        self.assertGreaterEqual(data["event_count"], 1)
        self.assertEqual(data["algorithm"], "SHA-256")
        self.assertGreaterEqual(data["tree_depth"], 1)

        # Record additional audit events and assert root updates deterministically
        user = {"id": "test_actor", "role": "reviewer"}
        record(self.app.extensions["veriscope"].db, case_id, user, "document.reviewed", "document", "doc1", {"note": "Pass 1"})
        record(self.app.extensions["veriscope"].db, case_id, user, "document.reviewed", "document", "doc2", {"note": "Pass 2"})

        updated = compute_merkle_root(self.app.extensions["veriscope"].db, case_id)
        self.assertNotEqual(data["merkle_root"], updated["merkle_root"])
        self.assertEqual(updated["event_count"], data["event_count"] + 2)

        # Test API endpoint
        res = self.client.get(f"/api/v1/cases/{case_id}/audit/merkle", headers=self.h("reviewer"))
        self.assertEqual(res.status_code, 200)
        json_body = res.get_json()
        self.assertEqual(json_body["merkle_root"], updated["merkle_root"])
