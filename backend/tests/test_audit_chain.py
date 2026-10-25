"""Tests for hash-chained tamper-evident audit trail."""
from tests.helpers import AppTestCase


class TestAuditChain(AppTestCase):
    def test_audit_events_are_hash_chained(self) -> None:
        case = self.new_case()
        case_id = case["id"]

        r = self.client.get(f"/api/v1/cases/{case_id}/audit/verify", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data["valid"])
        self.assertGreaterEqual(data["event_count"], 1)

    def test_tampering_breaks_hash_chain(self) -> None:
        case = self.new_case()
        case_id = case["id"]

        # Directly tamper with an event's payload in the DB
        # Note: In SQLite, triggers might restrict updates, so we test trigger protection as well
        try:
            self.svc.db.execute(
                "UPDATE audit_events SET payload_json = '{\"tampered\": true}' WHERE case_id = ?",
                (case_id,),
            )
            # If trigger allowed it (or in environments where trigger is bypassed), verify detects it:
            r = self.client.get(f"/api/v1/cases/{case_id}/audit/verify", headers=self.h("reviewer"))
            self.assertEqual(r.status_code, 200)
            self.assertFalse(r.get_json()["valid"])
        except Exception as e:
            # If trigger prevented update, that proves the database layer is append-only
            self.assertIn("append-only", str(e))
