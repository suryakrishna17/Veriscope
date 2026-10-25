"""Tests for hardened approval gates, waiver requirements, and applicant upload restrictions."""
import io

from tests.helpers import AppTestCase


class TestHardenedGates(AppTestCase):
    def test_approve_blocked_if_unprocessed_documents_exist(self) -> None:
        case = self.new_case()
        case_id = case["id"]
        # Transition case to needs_review
        self.svc.db.update("cases", case_id, {"status": "needs_review"})

        # Insert an unprocessed document directly into DB
        self.svc.db.insert(
            "documents",
            {
                "id": "doc-unproc",
                "case_id": case_id,
                "doc_type": "APPLICATION_FORM",
                "original_name": "app.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1024,
                "sha256": "abcdef123456",
                "storage_key": "dummy",
                "uploaded_at": "2026-10-25T10:00:00Z",
                "uploaded_by": self.users["applicant"]["id"],
                "page_count": 1,
                "processing_status": "pending",
                "trust_label": "NOT_VERIFIED",
            },
        )

        r = self.client.post(
            f"/api/v1/cases/{case_id}/decisions",
            json={"outcome": "approve", "reason_code": "ALL_CHECKS_SATISFIED", "note": "All good"},
            headers=self.h("reviewer"),
        )
        self.assertEqual(r.status_code, 409)
        self.assertIn("completely processed", r.get_json()["error"]["message"])

    def test_waive_high_finding_requires_at_least_20_chars(self) -> None:
        case = self.new_case()
        case_id = case["id"]
        self.svc.db.update("cases", case_id, {"status": "needs_review"})

        # Insert a high severity finding
        finding_id = "f-high-1"
        self.svc.db.insert(
            "findings",
            {
                "id": finding_id,
                "case_id": case_id,
                "rule_id": "CMP-001",
                "rule_version": "1.0",
                "category": "completeness",
                "severity": "high",
                "status": "open",
                "trust_label": "ANOMALY_DETECTED",
                "summary": "High finding",
                "detail": "Test high finding",
                "evidence_refs_json": "[]",
                "confidence": 1.0,
                "next_action": "Check",
                "is_current": 1,
                "fingerprint": "fp-high-1",
                "created_at": "2026-10-25T10:00:00Z",
                "updated_at": "2026-10-25T10:00:00Z",
            },
        )

        # Short note (< 20 chars) fails
        r_short = self.client.patch(
            f"/api/v1/findings/{finding_id}",
            json={"status": "waived", "note": "Too short"},
            headers=self.h("reviewer"),
        )
        self.assertEqual(r_short.status_code, 400)
        self.assertIn("20 characters", r_short.get_json()["error"]["message"])

        # Sufficient note (>= 20 chars) succeeds
        r_long = self.client.patch(
            f"/api/v1/findings/{finding_id}",
            json={"status": "waived", "note": "Approved exception under statutory waiver reference 104-B."},
            headers=self.h("reviewer"),
        )
        self.assertEqual(r_long.status_code, 200)
        self.assertEqual(r_long.get_json()["status"], "waived")

    def test_applicant_cannot_upload_during_needs_review(self) -> None:
        case = self.new_case()
        case_id = case["id"]
        self.svc.db.update("cases", case_id, {"status": "needs_review"})

        pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 600 800]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000108 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        r = self.client.post(
            f"/api/v1/cases/{case_id}/documents",
            data={"doc_type": "APPLICATION_FORM", "file": (io.BytesIO(pdf_bytes), "doc.pdf")},
            content_type="multipart/form-data",
            headers=self.h("applicant"),
        )
        self.assertEqual(r.status_code, 409)
        self.assertIn("under review", r.get_json()["error"]["message"])
