"""Every operator has at least one passing and one failing case."""
import unittest
from datetime import date

from app.rules.engine import RulesetError, evaluate, load_ruleset
from app.rules.model import CaseContext, DocView, FieldView

FORM, LETTER, PROOF = "APPLICATION_FORM", "INSTITUTION_AUTHORIZATION_LETTER", "ENROLMENT_OR_IDENTITY_PROOF"
RS = load_ruleset("student_support_lite.v1.yaml")

CLEAN = {
    FORM: {"applicant_name": "Ananya Rao", "institution_name": "Northstar Technical Institute", "institution_id": "1-4410023451",
           "application_date": "2026-10-05", "programme_name": "B.Tech CSE", "tuition_fee": "85000.00", "hostel_fee": "42000.00",
           "exam_fee": "6500.00", "total_amount": "133500.00", "contact_phone": "9845012345", "signature_present": "yes", "declaration_checked": "yes"},
    LETTER: {"institution_name": "Northstar Technical Institute", "institution_id": "1-4410023451", "student_name": "Ananya Rao",
             "valid_until": "2027-03-31", "seal_present": "yes"},
    PROOF: {"person_name": "Ananya Rao", "enrolment_number": "NTI-1", "institution_name": "Northstar Technical Institute"},
}


def ctx(values=None, docs=None, today=date(2026, 10, 22)):  # type: ignore[no-untyped-def]
    values = values if values is not None else CLEAN
    docs = docs if docs is not None else [DocView(f"d-{t}", t, f"{t}.pdf", "abc", "processed") for t in values]
    fields = [FieldView(f"{t}-{k}", f"d-{t}", t, k, v, v, 0.98, 1, [0, 0, 1, 1], f"{k}: {v}") for t, kv in values.items() for k, v in kv.items()]
    return CaseContext("c1", "TEST-1", today, docs, fields)


def with_change(doc_type, key, value):  # type: ignore[no-untyped-def]
    v = {t: dict(kv) for t, kv in CLEAN.items()}
    if value is None:
        v[doc_type].pop(key)
    else:
        v[doc_type][key] = value
    return v


def ids(c):  # type: ignore[no-untyped-def]
    return sorted({r.rule_id for r in evaluate(RS, c)})


class RuleTests(unittest.TestCase):
    def test_clean_case_has_no_findings(self) -> None:
        self.assertEqual(ids(ctx()), [])

    def test_cmp001_signature(self) -> None:
        self.assertIn("CMP-001", ids(ctx(with_change(FORM, "signature_present", "no"))))

    def test_cmp002_missing_doc(self) -> None:
        v = {FORM: CLEAN[FORM], LETTER: CLEAN[LETTER]}
        res = [r for r in evaluate(RS, ctx(v)) if r.rule_id == "CMP-002"]
        self.assertEqual(len(res), 1)
        self.assertIn("No source evidence", res[0].detail)

    def test_cmp003_missing_field(self) -> None:
        self.assertIn("CMP-003", ids(ctx(with_change(FORM, "institution_id", None))))

    def test_cmp004_declaration(self) -> None:
        self.assertIn("CMP-004", ids(ctx(with_change(FORM, "declaration_checked", "no"))))

    def test_fmt001_institution_id(self) -> None:
        self.assertIn("FMT-001", ids(ctx(with_change(FORM, "institution_id", "ABC123"))))

    def test_fmt002_phone(self) -> None:
        self.assertIn("FMT-002", ids(ctx(with_change(FORM, "contact_phone", "12345"))))

    def test_dat001_future_date(self) -> None:
        self.assertIn("DAT-001", ids(ctx(with_change(FORM, "application_date", "2027-01-01"))))

    def test_dat002_expired_letter(self) -> None:
        self.assertIn("DAT-002", ids(ctx(with_change(LETTER, "valid_until", "2026-06-30"))))

    def test_ari001_sum(self) -> None:
        c = ctx(with_change(FORM, "total_amount", "148500.00"))
        r = [x for x in evaluate(RS, c) if x.rule_id == "ARI-001"][0]
        self.assertIn("133,500.00", r.detail)
        self.assertEqual(len(r.evidence_refs), 4)

    def test_con001_institution(self) -> None:
        self.assertIn("CON-001", ids(ctx(with_change(LETTER, "institution_name", "Northgate Institute of Technology"))))
        self.assertNotIn("CON-001", ids(ctx(with_change(LETTER, "institution_name", "The Northstar Technical Institute"))))

    def test_con002_student(self) -> None:
        self.assertIn("CON-002", ids(ctx(with_change(PROOF, "person_name", "Rahul Verma"))))

    def test_con003_institution_id(self) -> None:
        self.assertIn("CON-003", ids(ctx(with_change(LETTER, "institution_id", "1-4410023452"))))

    def test_sig001_duplicate(self) -> None:
        docs = [DocView(f"d-{t}", t, f"{t}.pdf", "abc", "processed", {}, [{"id": "x", "doc_type": PROOF, "original_name": "p.pdf", "case_ref": "OTHER"}] if t == PROOF else [])
                for t in CLEAN]
        self.assertIn("SIG-001", ids(ctx(docs=docs)))

    def test_sig002_metadata(self) -> None:
        docs = [DocView(f"d-{t}", t, f"{t}.pdf", "abc", "processed", {"metadata": {"notes": ["edited"]}} if t == LETTER else {}) for t in CLEAN]
        self.assertIn("SIG-002", ids(ctx(docs=docs)))

    def test_sig003_ocr(self) -> None:
        docs = [DocView(f"d-{t}", t, f"{t}.pdf", "abc", "processed", {"quality": {"ocr_used": True, "min_ocr_confidence": 61.0}} if t == PROOF else {}) for t in CLEAN]
        r = [x for x in evaluate(RS, ctx(docs=docs)) if x.rule_id == "SIG-003"][0]
        self.assertIn("61%", r.detail)

    def test_sig004_seal(self) -> None:
        self.assertIn("SIG-004", ids(ctx(with_change(LETTER, "seal_present", "no"))))

    def test_signals_are_review_prompts_never_high(self) -> None:
        for rule in RS.rules:
            if rule["category"] == "document_signal":
                self.assertNotEqual(rule["severity"], "high", rule["id"])

    def test_every_finding_has_evidence_or_explanation(self) -> None:
        v = with_change(FORM, "institution_id", None)
        v.pop(PROOF)
        for r in evaluate(RS, ctx(v)):
            self.assertTrue(r.evidence_refs or "No source evidence" in r.detail, r.rule_id)

    def test_ruleset_validation(self) -> None:
        self.assertTrue(RS.is_provisional)
        self.assertEqual(len({r["id"] for r in RS.rules}), len(RS.rules))
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            Path(d, "bad.yaml").write_text("ruleset: x\nversion: 1\nrules:\n  - {id: A, category: nope, severity: high, summary: s, operator: regex}\n")
            with self.assertRaises(RulesetError):
                load_ruleset("bad.yaml", Path(d))

    def test_numeric_min_operator(self) -> None:
        from app.rules.operators import OPERATORS
        rule = {"id": "TEST-NUM", "_version": "1.0", "category": "completeness", "severity": "medium", "summary": "Area below norm"}
        op = OPERATORS["numeric_min"]
        
        # Passing case: 500 >= 300
        c_pass = ctx({FORM: {"total_amount": "500.00"}})
        res_pass = list(op(rule, {"doc_type": FORM, "field": "total_amount", "min_value": 300}, c_pass))
        self.assertEqual(len(res_pass), 0)

        # Failing case: 200 < 300
        c_fail = ctx({FORM: {"total_amount": "200.00"}})
        res_fail = list(op(rule, {"doc_type": FORM, "field": "total_amount", "min_value": 300, "unit": "sqm"}, c_fail))
        self.assertEqual(len(res_fail), 1)
        self.assertIn("below the statutory requirement", res_fail[0].detail)

    def test_land_norm_by_category_operator(self) -> None:
        from app.rules.operators import OPERATORS
        rule = {"id": "TEST-LAND", "_version": "1.0", "category": "completeness", "severity": "high", "summary": "Land norm not met"}
        op = OPERATORS["land_norm_by_category"]

        # Rural requires 7.5 acres. Test 8.0 acres -> PASS
        c_pass = ctx({FORM: {"total_land_area_acres": "8.0", "land_category": "RURAL"}})
        res_pass = list(op(rule, {"doc_type": FORM, "land_field": "total_land_area_acres", "category_field": "land_category"}, c_pass))
        self.assertEqual(len(res_pass), 0)

        # Rural requires 7.5 acres. Test 5.0 acres -> FAIL
        c_fail = ctx({FORM: {"total_land_area_acres": "5.0", "land_category": "RURAL"}})
        res_fail = list(op(rule, {"doc_type": FORM, "land_field": "total_land_area_acres", "category_field": "land_category"}, c_fail))
        self.assertEqual(len(res_fail), 1)
        self.assertIn("fails the minimum statutory requirement of 7.5 acres", res_fail[0].detail)
