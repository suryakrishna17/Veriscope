"""Tests for AICTE Chapter II and Annexure-2 EoA rule catalogue."""
from __future__ import annotations

import re
import unittest
from datetime import date
from pathlib import Path

from app.rules.engine import CATEGORIES, SEVERITIES, evaluate, load_ruleset
from app.rules.model import CaseContext, DocView, FieldView
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
        doc_list = [DocView(f"doc-{dt}", dt, f"{dt.lower()}.pdf", "abc123sha", "processed") for dt in effective_values]
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
    """Verifies pass and fail paths for each automated rule in the catalogue."""

    def test_clean_case_produces_no_findings(self) -> None:
        ctx = build_ctx()
        self.assertEqual(finding_ids(ctx), [])

    def test_eoa_cmp001_missing_core_dossier_docs(self) -> None:
        # Remove Fire Safety Certificate from available documents
        docs = [DocView(f"doc-{dt}", dt, f"{dt.lower()}.pdf", "hash", "processed") for dt in [FORM, AFFILIATION, BUILDING, LAND, OCCUPANCY]]
        ctx = build_ctx(docs=docs)
        self.assertIn("EOA-CMP-001", finding_ids(ctx))

    def test_eoa_cmp002_missing_land_occupancy_docs(self) -> None:
        # Remove Occupancy Certificate
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

    def test_eoa_dat003_expired_building_safety_certificate(self) -> None:
        ctx = build_ctx(with_val(BUILDING, "valid_until", "2024-01-01"))
        self.assertIn("EOA-DAT-003", finding_ids(ctx))

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
        ctx = build_ctx(with_val(AFFILIATION, "institution_name", "Other Regional Engineering College"))
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
