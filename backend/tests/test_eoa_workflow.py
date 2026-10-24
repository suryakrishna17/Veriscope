from __future__ import annotations

from datetime import date

from app.core.db import new_id, utcnow
from app.processing.fields import DOC_TYPES
from app.processing.normalize import normalize
from app.rules.engine import evaluate, evaluate_ruleset
from app.rules.model import CaseContext, RuleOutcome
from tests.helpers import AppTestCase


class EoaWorkflowIntegrationTests(AppTestCase):
    """Step 3B verification test suite for AICTE EoA backend review integration."""

    def test_eoa_ruleset_selection_and_metadata(self) -> None:
        """Confirms application_type: 'AICTE_EOA' selects aicte_eoa_chapter2@1.0.0 and exposes APH source note."""
        r = self.client.post(
            "/api/v1/cases",
            json={"application_type": "AICTE_EOA", "applicant_ref": "Principal Sharma", "institution_ref": "Delhi Tech Campus"},
            headers=self.h("reviewer"),
        )
        self.assertEqual(r.status_code, 201, r.get_json())
        cid = r.get_json()["id"]

        detail = self.detail(cid)
        self.assertEqual(detail["application_type"], "AICTE_EOA")
        self.assertEqual(detail["ruleset"]["name"], "aicte_eoa_chapter2")
        self.assertTrue(detail["rule_set_version"].startswith("aicte_eoa_chapter2@1.0.0"))

        meta_r = self.client.get("/api/v1/rulesets/active?application_type=AICTE_EOA", headers=self.h("reviewer"))
        self.assertEqual(meta_r.status_code, 200)
        meta = meta_r.get_json()
        self.assertEqual(meta["name"], "aicte_eoa_chapter2")
        self.assertEqual(meta["version"], "1.0.0")
        self.assertIn("Approval Process Handbook", meta["source_note"])
        self.assertEqual(len(meta["rules"]), 24)
        for rule in meta["rules"]:
            self.assertIsNotNone(rule.get("clause_citation"), f"Rule {rule['id']} missing statutory citation")

    def test_non_eoa_ruleset_regression_safety(self) -> None:
        """Confirms default or STUDENT_SUPPORT_LITE cases continue to select student_support_lite@1.0.0."""
        case = self.new_case("applicant", "Student Applicant")
        cid = case["id"]
        detail = self.detail(cid)
        self.assertEqual(detail["application_type"], "STUDENT_SUPPORT_LITE")
        self.assertEqual(detail["ruleset"]["name"], "student_support_lite")
        self.assertEqual(detail["rule_set_version"], "student_support_lite@1.0.0")

        # Active ruleset without param or with STUDENT_SUPPORT_LITE yields student support
        r1 = self.client.get("/api/v1/rulesets/active", headers=self.h("reviewer"))
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.get_json()["name"], "student_support_lite")

        r2 = self.client.get("/api/v1/rulesets/active?application_type=STUDENT_SUPPORT_LITE", headers=self.h("reviewer"))
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["name"], "student_support_lite")

    def test_eoa_doc_types_and_meta_endpoint(self) -> None:
        """Verifies /api/v1/meta lists all 6 EoA document types and both application types."""
        r = self.client.get("/api/v1/meta", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200)
        data = r.get_json()

        # Application types check
        app_types = {t["id"] for t in data["application_types"]}
        self.assertIn("STUDENT_SUPPORT_LITE", app_types)
        self.assertIn("AICTE_EOA", app_types)

        # 6 EoA doc types check
        doc_type_ids = {d["id"] for d in data["doc_types"]}
        expected_eoa_docs = {
            "EOA_APPLICATION_FORM",
            "UNIVERSITY_AFFILIATION_ORDER",
            "FIRE_SAFETY_CERTIFICATE",
            "BUILDING_SAFETY_CERTIFICATE",
            "LAND_DOCUMENT_AND_USE_CERTIFICATE",
            "OCCUPANCY_CERTIFICATE",
        }
        for expected in expected_eoa_docs:
            self.assertIn(expected, doc_type_ids)
            self.assertIn(expected, DOC_TYPES)

    def test_eoa_normalization_and_boolean_checkboxes(self) -> None:
        """Validates normalization of [X], ☑, yes, true across all 7 committee checkboxes and institutional fields."""
        self.assertEqual(normalize("anti_ragging_committee_constituted", "[X]"), "yes")
        self.assertEqual(normalize("anti_ragging_squad_constituted", "☑"), "yes")
        self.assertEqual(normalize("icc_constituted", "true"), "yes")
        self.assertEqual(normalize("sgrc_constituted", "Yes"), "yes")
        self.assertEqual(normalize("sc_st_committee_constituted", "1"), "yes")
        self.assertEqual(normalize("iqac_established", "[ ]"), "no")
        self.assertEqual(normalize("barrier_free_environment_available", "false"), "no")
        self.assertEqual(normalize("mandatory_disclosure_url_active", "0"), "no")

        # ID and cycle formatting
        self.assertEqual(normalize("institution_id", "  1-1234567890  "), "1-1234567890")
        self.assertEqual(normalize("academic_year", "  2024-25  "), "2024-25")

    def test_eoa_pipeline_evaluation_and_finding_persistence(self) -> None:
        """Ingests mock EoA application form, executes evaluation, and verifies findings contain statutory clause citations in DB."""
        r = self.client.post(
            "/api/v1/cases",
            json={"application_type": "AICTE_EOA", "applicant_ref": "Director Sharma", "institution_ref": "Apex Institute of Tech"},
            headers=self.h("reviewer"),
        )
        cid = r.get_json()["id"]

        # Insert a mock uploaded EOA_APPLICATION_FORM document
        now = utcnow()
        doc_id = new_id()
        self.svc.db.insert("documents", {
            "id": doc_id,
            "case_id": cid,
            "doc_type": "EOA_APPLICATION_FORM",
            "original_name": "eoa_application.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1024,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "storage_key": "mock_key",
            "uploaded_at": now,
            "page_count": 1,
            "processing_status": "processed",
            "trust_label": "NOT_VERIFIED",
        })

        # Insert extracted fields for the document
        fields = [
            ("institution_name", "Apex Institute of Technology", "apex institute of technology"),
            ("institution_id", "1-9876543210", "1-9876543210"),
            ("academic_year", "2024-25", "2024-25"),
            ("application_date", "2024-05-10", "2024-05-10"),
            ("principal_director_name", "Dr. S. K. Gupta", "dr s k gupta"),
            ("land_category", "Rural", "rural"),
            ("total_built_up_area", "15000", "15000"),
            ("declaration_checked", "yes", "yes"),
            ("anti_ragging_committee_constituted", "yes", "yes"),
            ("anti_ragging_squad_constituted", "yes", "yes"),
            ("icc_constituted", "yes", "yes"),
            ("sgrc_constituted", "yes", "yes"),
            ("sc_st_committee_constituted", "yes", "yes"),
            ("iqac_established", "yes", "yes"),
            ("barrier_free_environment_available", "yes", "yes"),
            ("mandatory_disclosure_url_active", "yes", "yes"),
        ]
        for key, raw, norm in fields:
            self.svc.db.insert("extracted_fields", {
                "id": new_id(),
                "case_id": cid,
                "document_id": doc_id,
                "field_key": key,
                "raw_value": raw,
                "normalized_value": norm,
                "confidence": 0.98,
                "page_number": 1,
                "source": "pdf_text",
                "created_at": now,
            })

        # Process / evaluate case
        res = self.process(cid)
        self.assertEqual(res.status_code, 202)

        # Verify DB findings contain clause_citation and outcome
        findings = self.svc.db.all("SELECT * FROM findings WHERE case_id = ?", (cid,))
        self.assertTrue(len(findings) > 0)
        for f in findings:
            self.assertIsNotNone(f["clause_citation"], f"Finding {f['rule_id']} missing clause_citation")
            self.assertIn("APH 2024-27", f["clause_citation"])
            self.assertIn(f["outcome"], ("FAIL", "REVIEW_REQUIRED"))

        # Check detail API serialization includes citations
        detail = self.detail(cid)
        api_findings = detail["findings"]
        self.assertTrue(len(api_findings) > 0)
        for af in api_findings:
            self.assertIsNotNone(af.get("clause_citation"))
            self.assertIsNotNone(af.get("outcome"))

    def test_reprocessing_idempotency_and_resolution_preservation(self) -> None:
        """Reprocesses a case twice and verifies finding count is unchanged and reviewer waiver notes are preserved."""
        r = self.client.post(
            "/api/v1/cases",
            json={"application_type": "AICTE_EOA", "applicant_ref": "Admin Sharma", "institution_ref": "City College of Engg"},
            headers=self.h("reviewer"),
        )
        cid = r.get_json()["id"]

        # Add a minimal document so that processing can run
        now = utcnow()
        doc_id = new_id()
        self.svc.db.insert("documents", {
            "id": doc_id,
            "case_id": cid,
            "doc_type": "EOA_APPLICATION_FORM",
            "original_name": "app.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 100,
            "sha256": "abc123def456",
            "storage_key": "mock_key_2",
            "uploaded_at": now,
            "page_count": 1,
            "processing_status": "processed",
            "trust_label": "NOT_VERIFIED",
        })

        # First evaluation
        self.process(cid)
        d1 = self.detail(cid)
        count_1 = len(d1["findings"])
        self.assertTrue(count_1 > 0)

        # Waive the first finding as reviewer
        target_f = d1["findings"][0]
        fid = target_f["id"]
        res_note = "Waiver granted per AICTE Standing Appellate Committee (SAC) order dated 15-Jun-2024"
        waive_r = self.client.patch(
            f"/api/v1/findings/{fid}",
            json={"status": "waived", "resolution_note": res_note},
            headers=self.h("reviewer"),
        )
        self.assertEqual(waive_r.status_code, 200)

        # Re-evaluate
        self.process(cid)
        d2 = self.detail(cid)
        count_2 = len(d2["findings"])
        self.assertEqual(count_1, count_2, "Finding count changed after reprocessing")

        # Verify the waived finding preserved its status and note
        waived_f = next(f for f in d2["findings"] if f["id"] == fid)
        self.assertEqual(waived_f["status"], "waived")
        self.assertEqual(waived_f["resolution_note"], res_note)

    def test_missing_input_safety_deterministic_engine(self) -> None:
        """Evaluates empty CaseContext and confirms graceful FAIL findings with NO_EVIDENCE without server crash."""
        ruleset = self.svc.get_ruleset("AICTE_EOA")
        empty_ctx = CaseContext(case_id="empty-1", case_ref="VS-EMPTY", today=date(2024, 6, 1), docs=[], fields=[])

        evaluations = evaluate_ruleset(ruleset, empty_ctx)
        self.assertEqual(len(evaluations), 24)

        # Verify that outcomes are properly assigned
        outcomes = {e.rule_id: e.outcome for e in evaluations}
        # Mandatory document check EOA-CMP-001 must FAIL on empty context
        self.assertEqual(outcomes["EOA-CMP-001"], RuleOutcome.FAIL.value)

        # Direct evaluate() must return active findings without crashing
        findings = evaluate(ruleset, empty_ctx)
        self.assertTrue(len(findings) > 0)
        for f in findings:
            self.assertIn(f.outcome, (RuleOutcome.FAIL.value, RuleOutcome.REVIEW_REQUIRED.value))
