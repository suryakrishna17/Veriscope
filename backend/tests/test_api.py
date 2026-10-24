"""API integration tests: workflow, state machine, authorisation, guardrails, audit."""
from app.core.db import new_id
from tests.helpers import EXPECTED, FIXTURES, AppTestCase

FORM, LETTER, PROOF = "APPLICATION_FORM", "INSTITUTION_AUTHORIZATION_LETTER", "ENROLMENT_OR_IDENTITY_PROOF"


class AuthTests(AppTestCase):
    def test_login_failure(self) -> None:
        r = self.client.post("/api/v1/auth/login", json={"email": "reviewer@demo.local", "password": "nope"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()["error"]["code"], "INVALID_CREDENTIALS")
        self.assertTrue(r.get_json()["error"]["correlation_id"])

    def test_requires_token(self) -> None:
        self.assertEqual(self.client.get("/api/v1/cases").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/cases", headers={"Authorization": "Bearer junk"}).status_code, 401)

    def test_me_and_security_headers(self) -> None:
        r = self.client.get("/api/v1/auth/me", headers=self.h("reviewer"))
        self.assertEqual(r.get_json()["role"], "reviewer")
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", r.headers["Content-Security-Policy"])
        self.assertTrue(r.headers["X-Request-ID"])

    def test_health(self) -> None:
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        self.assertEqual(self.client.get("/readyz").get_json()["status"], "ready")


class UploadValidationTests(AppTestCase):
    def setUp(self) -> None:
        self.case = self.new_case()

    def _err(self, path, status, code):  # type: ignore[no-untyped-def]
        r = self.upload(self.case["id"], path, FORM)
        self.assertEqual(r.status_code, status, r.get_json())
        self.assertEqual(r.get_json()["error"]["code"], code)

    def test_rejects_bad_files(self) -> None:
        self._err(FIXTURES / "invalid" / "encrypted.pdf", 422, "DOC_ENCRYPTED")
        self._err(FIXTURES / "invalid" / "corrupt.png", 422, "DOC_CORRUPT")
        self._err(FIXTURES / "invalid" / "not_really.pdf", 415, "UNSUPPORTED_FILE")
        self._err(FIXTURES / "invalid" / "truncated.pdf", 422, "DOC_CORRUPT")

    def test_rejects_unknown_doc_type(self) -> None:
        r = self.upload(self.case["id"], FIXTURES / "cases" / "SIH-DEMO-013" / "application_form.pdf", "PASSPORT")
        self.assertEqual(r.status_code, 400)

    def test_filename_is_sanitised(self) -> None:
        r = self.upload(self.case["id"], FIXTURES / "cases" / "SIH-DEMO-013" / "application_form.pdf", FORM, name="../../etc/<script>x.pdf")
        self.assertEqual(r.status_code, 201)
        doc = self.detail(self.case["id"])["documents"][0]
        self.assertNotIn("/", doc["original_name"])
        self.assertNotIn("<", doc["original_name"])

    def test_empty_case_cannot_be_processed(self) -> None:
        c = self.new_case()
        r = self.process(c["id"])
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.get_json()["error"]["code"], "NO_DOCUMENTS")


class FixtureCaseTests(AppTestCase):
    """Seeded fixtures produce exactly the expected findings and fields."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.ids = {}
        for ref in ("SIH-DEMO-013", "SIH-DEMO-014", "SIH-DEMO-015"):
            t = cls()
            cid = t.upload_fixture_case(ref)
            r = t.process(cid)
            assert r.status_code == 202, r.get_json()
            cls.ids[ref] = cid

    def test_expected_findings(self) -> None:
        for ref, cid in self.ids.items():
            d = self.detail(cid)
            self.assertEqual(d["status"], "needs_review")
            got = sorted({f["rule_id"] for f in d["findings"]})
            self.assertEqual(got, sorted(EXPECTED[ref]["expected_rules"]), ref)

    def test_expected_fields(self) -> None:
        for ref, cid in self.ids.items():
            fields = self.detail(cid)["fields"]
            for doc_type, kv in EXPECTED[ref].get("expected_fields", {}).items():
                for key, val in kv.items():
                    match = [f for f in fields if f["doc_type"] == doc_type and f["field_key"] == key]
                    self.assertTrue(match, f"{ref} {doc_type}.{key} missing")
                    self.assertEqual(match[0]["effective_value"], val, f"{ref} {doc_type}.{key}")

    def test_findings_have_rule_version_and_evidence(self) -> None:
        for cid in self.ids.values():
            for f in self.detail(cid)["findings"]:
                self.assertTrue(f["rule_id"] and f["rule_version"] and f["severity"])
                self.assertTrue(f["evidence_refs"] or "No source evidence" in f["detail"])
                self.assertEqual(f["trust_label"], "ANOMALY_DETECTED")

    def test_documents_never_claim_issuer_verification_without_issuer(self) -> None:
        for cid in self.ids.values():
            for doc in self.detail(cid)["documents"]:
                self.assertEqual(doc["trust_label"], "NOT_VERIFIED")
                if doc.get("issuer_check"):
                    self.assertIsNone(doc["issuer_check"]["response_id"])

    def test_triage_is_explained(self) -> None:
        d = self.detail(self.ids["SIH-DEMO-014"])
        self.assertGreater(d["triage_priority"], 0)
        self.assertEqual(d["triage_priority"], min(100, sum(c["points"] for c in d["triage_components"])))

    def test_page_image_and_file(self) -> None:
        doc = self.detail(self.ids["SIH-DEMO-015"])["documents"][2]
        r = self.client.get(f"/api/v1/documents/{doc['id']}/pages/1/image", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(self.client.get(f"/api/v1/documents/{doc['id']}/pages/9/image", headers=self.h("reviewer")).status_code, 404)

    def test_report_json_and_pdf(self) -> None:
        cid = self.ids["SIH-DEMO-014"]
        rep = self.client.get(f"/api/v1/cases/{cid}/report", headers=self.h("reviewer")).get_json()
        self.assertIn("is issuer-verified unless", rep["verification_caveat"])
        self.assertTrue(rep["ruleset"]["is_provisional"])
        self.assertEqual(len(rep["documents"]), 3)
        pdf = self.client.get(f"/api/v1/cases/{cid}/report?format=pdf", headers=self.h("reviewer"))
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.data.startswith(b"%PDF"))

    def test_reprocessing_is_idempotent(self) -> None:
        cid = self.ids["SIH-DEMO-013"]
        before = {f["id"] for f in self.detail(cid)["findings"]}
        self.assertEqual(self.client.post(f"/api/v1/cases/{cid}/process", json={"force": True}, headers=self.h("reviewer")).status_code, 202)
        after = {f["id"] for f in self.detail(cid)["findings"]}
        self.assertEqual(before, after)


class ReviewWorkflowTests(AppTestCase):
    def setUp(self) -> None:
        self.cid = self.upload_fixture_case("SIH-DEMO-014")
        self.process(self.cid)

    def _finding(self, rule_id):  # type: ignore[no-untyped-def]
        return next(f for f in self.detail(self.cid)["findings"] if f["rule_id"] == rule_id)

    def test_cannot_approve_with_open_high_findings(self) -> None:
        r = self.client.post(f"/api/v1/cases/{self.cid}/decisions", json={"outcome": "approve", "reason_code": "FINDINGS_RESOLVED"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 409)
        self.assertIn("CMP-001", r.get_json()["error"]["details"]["open_high_findings"])

    def test_field_correction_preserves_original_and_reevaluates(self) -> None:
        d = self.detail(self.cid)
        total = next(f for f in d["fields"] if f["field_key"] == "total_amount")
        r = self.client.patch(f"/api/v1/fields/{total['id']}", json={"value": "1,33,500", "reason": "Applicant confirmed typo"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200, r.get_json())
        f = r.get_json()["field"]
        self.assertEqual(f["raw_value"], "Rs. 1,48,500.00")
        self.assertEqual(f["effective_value"], "133500.00")
        self.assertTrue(r.get_json()["audit_event_id"])
        self.assertNotIn("ARI-001", {x["rule_id"] for x in self.detail(self.cid)["findings"]})
        # reprocessing keeps the correction
        self.client.post(f"/api/v1/cases/{self.cid}/process", json={"force": True}, headers=self.h("reviewer"))
        f2 = next(x for x in self.detail(self.cid)["fields"] if x["field_key"] == "total_amount")
        self.assertEqual(f2["effective_value"], "133500.00")

    def test_invalid_correction_rejected(self) -> None:
        d = self.detail(self.cid)
        date_field = next(f for f in d["fields"] if f["field_key"] == "application_date")
        r = self.client.patch(f"/api/v1/fields/{date_field['id']}", json={"value": "not a date", "reason": "typo"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 422)

    def test_full_resolution_then_approve(self) -> None:
        for f in self.detail(self.cid)["findings"]:
            if f["severity"] == "high":
                bad = self.client.patch(f"/api/v1/findings/{f['id']}", json={"status": "waived"}, headers=self.h("reviewer"))
                self.assertEqual(bad.status_code, 400)  # note required
                ok = self.client.patch(f"/api/v1/findings/{f['id']}", json={"status": "waived", "note": "Checked with institution by phone"}, headers=self.h("reviewer"))
                self.assertEqual(ok.status_code, 200)
        r = self.client.post(f"/api/v1/cases/{self.cid}/decisions", json={"outcome": "approve", "reason_code": "FINDINGS_WAIVED_WITH_JUSTIFICATION"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 201, r.get_json())
        self.assertEqual(self.detail(self.cid)["status"], "approved")
        # terminal: further decisions and corrections are refused
        r2 = self.client.post(f"/api/v1/cases/{self.cid}/decisions", json={"outcome": "reject", "reason_code": "OTHER", "note": "changed mind"}, headers=self.h("reviewer"))
        self.assertEqual(r2.status_code, 409)
        # only an admin may reopen
        self.assertEqual(self.client.post(f"/api/v1/cases/{self.cid}/reopen", json={"note": "audit request"}, headers=self.h("reviewer")).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/cases/{self.cid}/reopen", json={"note": "audit request"}, headers=self.h("admin")).status_code, 200)

    def test_clarification_then_resubmit(self) -> None:
        r = self.client.post(f"/api/v1/cases/{self.cid}/decisions", json={"outcome": "request_clarification", "reason_code": "SIGNATURE_REQUIRED", "note": "Upload a signed form"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.detail(self.cid, "applicant")["status"], "clarification_requested")
        up = self.upload(self.cid, FIXTURES / "cases" / "SIH-DEMO-013" / "application_form.pdf", FORM)
        self.assertEqual(up.status_code, 201)
        self.assertEqual(self.process(self.cid, "applicant").status_code, 202)
        self.assertEqual(self.detail(self.cid)["status"], "needs_review")

    def test_reject_requires_reason_and_note(self) -> None:
        r = self.client.post(f"/api/v1/cases/{self.cid}/decisions", json={"outcome": "reject"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f"/api/v1/cases/{self.cid}/decisions", json={"outcome": "reject", "reason_code": "INCONSISTENT_INFORMATION"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 400)

    def test_audit_trail_is_complete_and_append_only(self) -> None:
        f = self._finding("SIG-002")
        self.client.patch(f"/api/v1/findings/{f['id']}", json={"status": "resolved", "note": "Original letter received"}, headers=self.h("reviewer"))
        actions = [e["action"] for e in self.client.get(f"/api/v1/cases/{self.cid}/audit", headers=self.h("reviewer")).get_json()["items"]]
        for a in ("case.created", "document.uploaded", "job.queued", "document.processed", "rules.evaluated", "finding.resolved"):
            self.assertIn(a, actions)
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.svc.db.execute("UPDATE audit_events SET action = 'x'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.svc.db.execute("DELETE FROM audit_events")


class AuthorisationTests(AppTestCase):
    def test_applicant_isolation_and_role_limits(self) -> None:
        from app.core.db import utcnow
        from app.core.security import hash_password
        self.svc.db.insert("users", {"id": new_id(), "email": "other@demo.local", "name": "Other", "role": "applicant", "password_hash": hash_password("pw123456"), "created_at": utcnow()})
        other = self.login("other@demo.local", "pw123456")
        cid = self.upload_fixture_case("SIH-DEMO-013")
        oh = {"Authorization": f"Bearer {other}"}
        self.assertEqual(self.client.get(f"/api/v1/cases/{cid}", headers=oh).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/cases", headers=oh).get_json()["total"], 0)
        self.process(cid)
        # applicants see status but not reviewer-only data, and cannot decide or correct
        d = self.detail(cid, "applicant")
        self.assertEqual(d["findings"], [])
        self.assertEqual(d["fields"], [])
        r = self.client.post(f"/api/v1/cases/{cid}/decisions", json={"outcome": "approve", "reason_code": "ALL_CHECKS_SATISFIED"}, headers=self.h("applicant"))
        self.assertEqual(r.status_code, 403)
        fid = self.detail(cid)["fields"][0]["id"]
        self.assertEqual(self.client.patch(f"/api/v1/fields/{fid}", json={"value": "x", "reason": "xyz"}, headers=self.h("applicant")).status_code, 403)

    def test_invalid_transition_returns_409(self) -> None:
        c = self.new_case()
        r = self.client.post(f"/api/v1/cases/{c['id']}/decisions", json={"outcome": "approve", "reason_code": "ALL_CHECKS_SATISFIED"}, headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.get_json()["error"]["code"], "INVALID_STATE")

    def test_queue_filters_and_pagination(self) -> None:
        for i in range(3):
            self.new_case(applicant=f"Queue Person {i}")
        r = self.client.get("/api/v1/cases?status=received&q=Queue&page_size=2", headers=self.h("reviewer")).get_json()
        self.assertEqual(r["total"], 3)
        self.assertEqual(len(r["items"]), 2)
