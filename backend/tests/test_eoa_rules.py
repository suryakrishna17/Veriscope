"""Tests for AICTE Chapter II and Annexure-2 EoA rule catalogue."""
from __future__ import annotations

import re
import unittest
from datetime import date
from pathlib import Path

from app.rules.engine import CATEGORIES, SEVERITIES, Ruleset, evaluate, evaluate_ruleset, load_ruleset
from app.rules.model import CaseContext, DocView, FieldView, RuleOutcome
from app.rules.operators import OPERATORS

RULESET_FILE = "aicte_eoa_chapter2.v1.yaml"
RS = load_ruleset(RULESET_FILE)
VERDICT_WORDS = re.compile(r"\b(forged|forgery|fake|fraud|fraudulent|genuine)\b", re.I)

FORM = "EOA_APPLICATION_FORM"
AFFILIATION = "UNIVERSITY_AFFILIATION_ORDER"
FIRE = "FIRE_SAFETY_CERTIFICATE"
BUILDING = "BUILDING_SAFETY_CERTIFICATE"
LAND = "LAND_DOCUMENT_AND_USE_CERTIFICATE"
OCCUPANCY = "OCCUPANCY_CERTIFICATE"

CLEAN_VALUES: dict[str, dict[str, str]] = {
    FORM: {
        "institution_name": "Aryabhatta Institute of Technology",
        "institution_id": "1-3310045678",
        "academic_year": "2024-25",
        "principal_director_name": "Dr. Vikram Sarabhai",
        "land_category": "Urban",
        "total_built_up_area": "12500.00",
        "application_date": "2024-04-15",
        "anti_ragging_committee_constituted": "yes",
        "anti_ragging_squad_constituted": "yes",
        "icc_constituted": "yes",
        "sgrc_constituted": "yes",
        "sc_st_committee_constituted": "yes",
        "iqac_established": "yes",
        "barrier_free_environment_available": "yes",
        "mandatory_disclosure_url_active": "yes",
        "declaration_checked": "yes",
    },
    AFFILIATION: {
        "university_name": "Technical State University",
        "institution_name": "Aryabhatta Institute of Technology",
        "academic_year": "2024-25",
        "affiliation_order_number": "TSU/AFF/2024/889",
        "order_date": "2024-03-20",
    },
    FIRE: {
        "fire_authority_name": "State Fire and Rescue Services",
        "institution_name": "Aryabhatta Institute of Technology",
        "noc_number": "NOC-FS-2024-112",
        "valid_until": "2025-03-31",
        "building_coverage": "Blocks A, B, and C",
    },
    BUILDING: {
        "structural_engineer_name": "Er. K. Ramanathan",
        "license_registration_number": "SE-REG-4412",
        "valid_until": "2026-12-31",
    },
    LAND: {
        "khasra_survey_numbers": "Survey 42/1, 42/2",
        "land_area_acres": "2.5",
    },
    OCCUPANCY: {
        "occupancy_certificate_number": "MC-OC-2022-990",
    },
}


def build_ctx(
    values: dict[str, dict[str, str]] | None = None,
    docs: list[DocView] | None = None,
    today: date = date(2024, 4, 20),
) -> CaseContext:
    effective_values = values if values is not None else CLEAN_VALUES
    if docs is None:
        doc_list = [DocView(f"doc-{dt}", dt, f"{dt.lower()}.pdf", f"sha256-{dt}", "processed") for dt in effective_values]
    else:
        doc_list = docs

    field_list: list[FieldView] = []
    for dt, kv in effective_values.items():
        for key, val in kv.items():
            field_list.append(
                FieldView(
                    id=f"{dt}-{key}",
                    document_id=f"doc-{dt}",
                    doc_type=dt,
                    field_key=key,
                    value=val,
                    raw=val,
                    confidence=0.98,
                    page=1,
                    bbox=[0.1, 0.1, 0.9, 0.9],
                    excerpt=f"{key}: {val}",
                )
            )

    return CaseContext("case-eoa-001", "EOA-DEMO-2024", today, doc_list, field_list)


def with_val(doc_type: str, key: str, value: str | None) -> dict[str, dict[str, str]]:
    v = {dt: dict(pairs) for dt, pairs in CLEAN_VALUES.items()}
    if value is None:
        v[doc_type].pop(key, None)
    else:
        v[doc_type][key] = value
    return v


def finding_ids(ctx: CaseContext) -> list[str]:
    return sorted({r.rule_id for r in evaluate(RS, ctx)})


class EoaRulesetMetadataTests(unittest.TestCase):
    """Verifies ruleset structure, unique identifiers, and regulatory metadata."""

    def test_ruleset_loads_and_has_required_header(self) -> None:
        self.assertEqual(RS.name, "aicte_eoa_chapter2")
        self.assertEqual(RS.version, "1.0.0")
        self.assertTrue(RS.is_provisional)
        self.assertTrue(RS.checksum)
        self.assertIn("Approval Process Handbook", RS.source_note)
        self.assertEqual(RS.effective_date, "2024-04-01")

    def test_rule_ids_unique_and_count(self) -> None:
        ids = [r["id"] for r in RS.rules]
        self.assertEqual(len(ids), len(set(ids)), "Rule IDs must be strictly unique")
        self.assertGreaterEqual(len(ids), 20, "Catalogue should contain comprehensive Chapter II/Annexure 2 coverage")

    def test_rule_fields_and_schema_validity(self) -> None:
        for r in RS.rules:
            rid = r["id"]
            self.assertTrue(rid.startswith("EOA-"), f"Rule {rid} must use EOA- prefix")
            self.assertIn(r["category"], CATEGORIES, f"Rule {rid} has invalid category {r['category']}")
            self.assertIn(r["severity"], SEVERITIES, f"Rule {rid} has invalid severity {r['severity']}")
            self.assertIn(r["operator"], OPERATORS, f"Rule {rid} operator must be registered")
            self.assertIn("clause_citation", r, f"Rule {rid} must provide clause_citation")
            self.assertIn("AICTE APH 2024-27", r["clause_citation"], f"Rule {rid} citation must cite APH 2024-27")
            self.assertIn("applicability", r, f"Rule {rid} must specify applicability")
            self.assertIn("limitations", r, f"Rule {rid} must specify limitations")
            self.assertIn("next_action", r, f"Rule {rid} must specify reviewer next_action")

    def test_trust_language_guardrails(self) -> None:
        yaml_path = Path(__file__).resolve().parents[1] / "app" / "rules" / "rulesets" / RULESET_FILE
        content = yaml_path.read_text(encoding="utf-8")
        offenders = [m.group(0) for m in VERDICT_WORDS.finditer(content)]
        self.assertEqual(offenders, [], f"Found forbidden verdict words in {RULESET_FILE}: {offenders}")


class EoaRuleEvaluationTests(unittest.TestCase):
    """Verifies pass, fail, and boundary paths for rules in the catalogue."""

    def test_clean_case_produces_no_findings(self) -> None:
        ctx = build_ctx()
        self.assertEqual(finding_ids(ctx), [])

    def test_findings_payload_structure_and_citations(self) -> None:
        """Verifies that rules specify clause citations and emitted findings have valid evidence refs and details."""
        # Rule schema provides clause citation
        rule = [r for r in RS.rules if r["id"] == "EOA-FMT-001"][0]
        self.assertIn("AICTE APH 2024-27", rule.get("clause_citation", ""))

        # Evaluated finding provides evidence refs and remediation action
        ctx = build_ctx(with_val(FORM, "institution_id", "INVALID-ID"))
        results = evaluate(RS, ctx)
        self.assertGreaterEqual(len(results), 1)
        r = [res for res in results if res.rule_id == "EOA-FMT-001"][0]
        self.assertEqual(r.severity, "medium")
        self.assertTrue(len(r.evidence_refs) > 0)
        self.assertIn("institution_id", r.evidence_refs[0]["field_key"])
        self.assertTrue(len(r.next_action) > 0)
        self.assertTrue(len(r.detail) > 0)

    def test_eoa_cmp001_missing_core_dossier_docs(self) -> None:
        docs = [DocView(f"doc-{dt}", dt, f"{dt.lower()}.pdf", "hash", "processed") for dt in [FORM, AFFILIATION, BUILDING, LAND, OCCUPANCY]]
        ctx = build_ctx(docs=docs)
        self.assertIn("EOA-CMP-001", finding_ids(ctx))

    def test_eoa_cmp002_missing_land_occupancy_docs(self) -> None:
        docs = [DocView(f"doc-{dt}", dt, f"{dt.lower()}.pdf", "hash", "processed") for dt in [FORM, AFFILIATION, FIRE, BUILDING, LAND]]
        ctx = build_ctx(docs=docs)
        self.assertIn("EOA-CMP-002", finding_ids(ctx))

    def test_eoa_cmp003_missing_form_fields(self) -> None:
        ctx = build_ctx(with_val(FORM, "total_built_up_area", None))
        self.assertIn("EOA-CMP-003", finding_ids(ctx))

    def test_eoa_cmp004_missing_affiliation_details(self) -> None:
        ctx = build_ctx(with_val(AFFILIATION, "affiliation_order_number", None))
        self.assertIn("EOA-CMP-004", finding_ids(ctx))

    def test_eoa_cmp005_missing_fire_safety_details(self) -> None:
        ctx = build_ctx(with_val(FIRE, "noc_number", None))
        self.assertIn("EOA-CMP-005", finding_ids(ctx))

    def test_eoa_cmp006_missing_building_safety_details(self) -> None:
        ctx = build_ctx(with_val(BUILDING, "license_registration_number", None))
        self.assertIn("EOA-CMP-006", finding_ids(ctx))

    def test_eoa_fmt001_invalid_institution_id_format(self) -> None:
        ctx = build_ctx(with_val(FORM, "institution_id", "INVALID-ID-999"))
        self.assertIn("EOA-FMT-001", finding_ids(ctx))

    def test_eoa_fmt002_invalid_academic_session_format(self) -> None:
        ctx = build_ctx(with_val(FORM, "academic_year", "2024/2025"))
        self.assertIn("EOA-FMT-002", finding_ids(ctx))

    def test_eoa_dat001_future_submission_date(self) -> None:
        ctx = build_ctx(with_val(FORM, "application_date", "2025-01-01"), today=date(2024, 4, 20))
        self.assertIn("EOA-DAT-001", finding_ids(ctx))

    def test_eoa_dat002_expired_fire_safety_certificate(self) -> None:
        # Fire safety certificate expired on 2024-03-31, but application was submitted 2024-04-15
        ctx = build_ctx(with_val(FIRE, "valid_until", "2024-03-31"))
        self.assertIn("EOA-DAT-002", finding_ids(ctx))

    def test_eoa_dat002_date_boundary_equal_dates_pass(self) -> None:
        """Boundary test: application_date == valid_until is valid (certificate not expired)."""
        ctx = build_ctx(with_val(FIRE, "valid_until", "2024-04-15"))
        self.assertNotIn("EOA-DAT-002", finding_ids(ctx))

    def test_eoa_dat003_expired_building_safety_certificate(self) -> None:
        ctx = build_ctx(with_val(BUILDING, "valid_until", "2024-01-01"))
        self.assertIn("EOA-DAT-003", finding_ids(ctx))

    def test_eoa_dat003_date_boundary_equal_dates_pass(self) -> None:
        """Boundary test: application_date == valid_until is valid (stability certificate valid through day of filing)."""
        ctx = build_ctx(with_val(BUILDING, "valid_until", "2024-04-15"))
        self.assertNotIn("EOA-DAT-003", finding_ids(ctx))

    def test_eoa_com001_anti_ragging_committee_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "anti_ragging_committee_constituted", "no"))
        self.assertIn("EOA-COM-001", finding_ids(ctx))

    def test_eoa_com002_anti_ragging_squad_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "anti_ragging_squad_constituted", "no"))
        self.assertIn("EOA-COM-002", finding_ids(ctx))

    def test_eoa_com003_icc_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "icc_constituted", "no"))
        self.assertIn("EOA-COM-003", finding_ids(ctx))

    def test_eoa_com004_sgrc_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "sgrc_constituted", "no"))
        self.assertIn("EOA-COM-004", finding_ids(ctx))

    def test_eoa_com005_sc_st_committee_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "sc_st_committee_constituted", "no"))
        self.assertIn("EOA-COM-005", finding_ids(ctx))

    def test_eoa_com006_iqac_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "iqac_established", "no"))
        self.assertIn("EOA-COM-006", finding_ids(ctx))

    def test_eoa_inf001_barrier_free_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "barrier_free_environment_available", "no"))
        self.assertIn("EOA-INF-001", finding_ids(ctx))

    def test_eoa_inf002_mandatory_disclosure_missing(self) -> None:
        ctx = build_ctx(with_val(FORM, "mandatory_disclosure_url_active", "no"))
        self.assertIn("EOA-INF-002", finding_ids(ctx))

    def test_eoa_inf003_declaration_unticked(self) -> None:
        ctx = build_ctx(with_val(FORM, "declaration_checked", "no"))
        self.assertIn("EOA-INF-003", finding_ids(ctx))

    def test_eoa_con001_institution_name_mismatch(self) -> None:
        ctx = build_ctx(with_val(AFFILIATION, "institution_name", "Aryabhatta College of Technology"))
        self.assertIn("EOA-CON-001", finding_ids(ctx))

    def test_eoa_con001_name_similarity_threshold_boundary_pass(self) -> None:
        """Boundary test: 'Aryabhatta Institute of Tech' yields similarity 90.3 >= 88 and passes."""
        ctx = build_ctx(with_val(AFFILIATION, "institution_name", "Aryabhatta Institute of Tech"))
        self.assertNotIn("EOA-CON-001", finding_ids(ctx))

    def test_eoa_con001_name_similarity_threshold_boundary_fail(self) -> None:
        """Boundary test: 'Aryabhatta College of Technology' yields similarity 78.8 < 88 and triggers EOA-CON-001."""
        ctx = build_ctx(with_val(AFFILIATION, "institution_name", "Aryabhatta College of Technology"))
        self.assertIn("EOA-CON-001", finding_ids(ctx))

    def test_eoa_con002_academic_session_mismatch(self) -> None:
        ctx = build_ctx(with_val(AFFILIATION, "academic_year", "2023-24"))
        self.assertIn("EOA-CON-002", finding_ids(ctx))

    def test_eoa_sig001_duplicate_hash(self) -> None:
        docs = [
            DocView(f"doc-{dt}", dt, f"{dt.lower()}.pdf", "sha123", "processed", duplicates=[{"case_ref": "CASE-OLD-99"}] if dt == FIRE else [])
            for dt in CLEAN_VALUES
        ]
        ctx = build_ctx(docs=docs)
        self.assertIn("EOA-SIG-001", finding_ids(ctx))

    def test_eoa_sig002_low_ocr_confidence(self) -> None:
        docs = [
            DocView(
                f"doc-{dt}",
                dt,
                f"{dt.lower()}.pdf",
                "sha123",
                "processed",
                signals={"quality": {"ocr_used": True, "min_ocr_confidence": 64.0}} if dt == FIRE else {},
            )
            for dt in CLEAN_VALUES
        ]
        ctx = build_ctx(docs=docs)
        self.assertIn("EOA-SIG-002", finding_ids(ctx))



class EoaFoundationTests(unittest.TestCase):
    """Tests for Step 3A: AICTE EoA Ruleset Foundation, outcomes, configurability, and source verification."""

    def test_evaluate_ruleset_returns_pass_on_clean_context(self) -> None:
        """When clean documents and values are provided, all 24 rules evaluate to PASS."""
        ctx = build_ctx()
        evaluations = evaluate_ruleset(RS, ctx)
        self.assertEqual(len(evaluations), 25)

        for ev in evaluations:
            self.assertEqual(ev.outcome, RuleOutcome.PASS.value, f"Rule {ev.rule_id} did not pass: {ev.detail}")
            self.assertEqual(len(ev.findings), 0)
            self.assertTrue(ev.rule_id.startswith("EOA-"))
            self.assertTrue(ev.clause_citation)
            self.assertTrue(ev.is_verified)
            self.assertEqual(ev.verification_status, "VERIFIED_OFFICIAL")

    def test_evaluate_ruleset_distinguishes_fail_and_review_required(self) -> None:
        """Strict non-compliance yields FAIL, while conditions requiring human inspection yield REVIEW_REQUIRED."""
        # 1. Strict deterministic non-compliance: invalid permanent ID format
        ctx_fail = build_ctx(with_val(FORM, "institution_id", "INVALID-ID-XYZ"))
        evals_fail = {ev.rule_id: ev for ev in evaluate_ruleset(RS, ctx_fail)}
        self.assertEqual(evals_fail["EOA-FMT-001"].outcome, RuleOutcome.FAIL.value)
        self.assertEqual(len(evals_fail["EOA-FMT-001"].findings), 1)

        # 2. Strict non-compliance: application date in the future
        ctx_future = build_ctx(with_val(FORM, "application_date", "2025-12-31"))
        evals_future = {ev.rule_id: ev for ev in evaluate_ruleset(RS, ctx_future)}
        self.assertEqual(evals_future["EOA-DAT-001"].outcome, RuleOutcome.FAIL.value)

        # 3. Human inspection required: fire safety validity date (may have pending renewal challan)
        ctx_fire_exp = build_ctx(with_val(FIRE, "valid_until", "2024-01-01"))
        evals_fire = {ev.rule_id: ev for ev in evaluate_ruleset(RS, ctx_fire_exp)}
        self.assertEqual(evals_fire["EOA-DAT-002"].outcome, RuleOutcome.REVIEW_REQUIRED.value)
        self.assertIn("refer to the human reviewer", evals_fire["EOA-DAT-002"].next_action or "")

        # 4. Human inspection required: structural stability certificate validity
        ctx_bld_exp = build_ctx(with_val(BUILDING, "valid_until", "2024-01-01"))
        evals_bld = {ev.rule_id: ev for ev in evaluate_ruleset(RS, ctx_bld_exp)}
        self.assertEqual(evals_bld["EOA-DAT-003"].outcome, RuleOutcome.REVIEW_REQUIRED.value)

        # 5. Human inspection required: barrier-free environment self-disclosure
        ctx_ramp = build_ctx(with_val(FORM, "barrier_free_environment_available", "no"))
        evals_ramp = {ev.rule_id: ev for ev in evaluate_ruleset(RS, ctx_ramp)}
        self.assertEqual(evals_ramp["EOA-INF-001"].outcome, RuleOutcome.REVIEW_REQUIRED.value)

        # 6. Document signals always yield REVIEW_REQUIRED
        docs_dupe = [
            DocView(f"doc-{dt}", dt, f"{dt.lower()}.pdf", "sha123", "processed", duplicates=[{"case_ref": "CASE-OLD-99"}] if dt == FIRE else [])
            for dt in CLEAN_VALUES
        ]
        evals_dupe = {ev.rule_id: ev for ev in evaluate_ruleset(RS, build_ctx(docs=docs_dupe))}
        self.assertEqual(evals_dupe["EOA-SIG-001"].outcome, RuleOutcome.REVIEW_REQUIRED.value)

    def test_evaluate_ruleset_supports_not_applicable(self) -> None:
        """Disabled rules or rules with unmet applicability conditions evaluate to NOT_APPLICABLE."""
        # Create a mock rule with an unmet condition
        test_rule = {
            "id": "EOA-TEST-001",
            "category": "compliance",
            "severity": "medium",
            "summary": "Expansion land requirement for new campuses",
            "description": "Applies only to expansion dossiers",
            "operator": "required_fields",
            "params": {"doc_type": "NON_EXISTENT_DOC", "fields": ["dummy_field"]},
            "condition": {"doc_present": "NON_EXISTENT_DOC"},
            "applicable_condition": "Applicable when NON_EXISTENT_DOC is submitted",
            "is_verified": False,
            "verification_status": "ILLUSTRATIVE",
        }
        custom_rs = Ruleset(
            name="custom_test",
            version="1.0.0",
            checksum="abc",
            is_provisional=True,
            source_note="Test ruleset",
            effective_date=None,
            rules=[test_rule],
        )
        ctx = build_ctx()
        evals = evaluate_ruleset(custom_rs, ctx)
        self.assertEqual(len(evals), 1)
        self.assertEqual(evals[0].outcome, RuleOutcome.NOT_APPLICABLE.value)
        self.assertIn("not in dossier", evals[0].detail)

        # Disabled rule evaluates to NOT_APPLICABLE
        test_rule_disabled = {**test_rule, "enabled": False}
        custom_rs_disabled = Ruleset(
            name="custom_disabled",
            version="1.0.0",
            checksum="def",
            is_provisional=True,
            source_note="Test ruleset",
            effective_date=None,
            rules=[test_rule_disabled],
        )
        evals_disabled = evaluate_ruleset(custom_rs_disabled, ctx)
        self.assertEqual(evals_disabled[0].outcome, RuleOutcome.NOT_APPLICABLE.value)
        self.assertIn("disabled", evals_disabled[0].detail)

    def test_verified_official_vs_illustrative_ruleset_distinction(self) -> None:
        """Ruleset loader cleanly distinguishes verified official AICTE rules from illustrative prototypes."""
        self.assertTrue(RS.is_provisional)
        self.assertEqual(len(RS.verified_rules), 25)
        self.assertEqual(len(RS.illustrative_rules), 0)

        for r in RS.verified_rules:
            self.assertTrue(r["is_verified"])
            self.assertEqual(r["verification_status"], "VERIFIED_OFFICIAL")
            self.assertTrue(r["clause_citation"])
            self.assertIn("AICTE", r["clause_citation"])

        # Load prototype student support ruleset to verify illustrative tagging
        ssl_rs = load_ruleset("student_support_lite.v1.yaml")
        self.assertEqual(len(ssl_rs.illustrative_rules), len(ssl_rs.rules))
        for r in ssl_rs.rules:
            self.assertFalse(r.get("is_verified", True))
            self.assertEqual(r.get("verification_status"), "ILLUSTRATIVE")

    def test_ruleset_helper_methods_and_grouping(self) -> None:
        """Ruleset methods allow convenient access by ID and grouping by category."""
        r_cmp = RS.get_rule("EOA-CMP-001")
        self.assertIsNotNone(r_cmp)
        self.assertEqual(r_cmp["category"], "completeness")  # type: ignore[index]

        r_none = RS.get_rule("NON-EXISTENT-ID")
        self.assertIsNone(r_none)

        by_cat = RS.rules_by_category
        self.assertIn("completeness", by_cat)
        self.assertIn("compliance", by_cat)
        self.assertIn("consistency", by_cat)
        self.assertIn("document_signal", by_cat)
        self.assertEqual(sum(len(v) for v in by_cat.values()), 25)

    def test_eoa_sig_003_hidden_text_detection(self) -> None:
        """EOA-SIG-003 triggers high-severity REVIEW_REQUIRED when hidden_text_detected is true."""
        clean_ctx = build_ctx()
        evals_clean = evaluate_ruleset(RS, clean_ctx)
        sig003_clean = next(e for e in evals_clean if e.rule_id == "EOA-SIG-003")
        self.assertEqual(sig003_clean.outcome, RuleOutcome.PASS.value)

        # Context with hidden text signal
        doc_hidden = DocView(
            id="doc-hidden",
            doc_type="EOA_APPLICATION_FORM",
            original_name="app_form.pdf",
            sha256="abc",
            processing_status="processed",
            signals={"quality": {"hidden_text_detected": True, "hidden_word_count": 3}},
        )
        hidden_ctx = build_ctx()
        hidden_ctx.docs = [doc_hidden]
        evals_hidden = evaluate_ruleset(RS, hidden_ctx)
        sig003_flagged = next(e for e in evals_hidden if e.rule_id == "EOA-SIG-003")
        self.assertEqual(sig003_flagged.outcome, RuleOutcome.REVIEW_REQUIRED.value)
        self.assertEqual(sig003_flagged.severity, "high")
        self.assertIn("hidden or zero-contrast", sig003_flagged.detail)

    def test_backward_compatibility_evaluate_findings_only(self) -> None:
        """Calling evaluate() returns findings for non-passing rules while returning empty list on clean context."""
        ctx_clean = build_ctx()
        self.assertEqual(evaluate(RS, ctx_clean), [])

        ctx_mismatch = build_ctx(with_val(AFFILIATION, "academic_year", "2023-24"))
        findings = evaluate(RS, ctx_mismatch)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "EOA-CON-002")
        self.assertEqual(findings[0].outcome, RuleOutcome.FAIL.value)
        self.assertTrue(findings[0].clause_citation)
        self.assertTrue(findings[0].is_verified)
