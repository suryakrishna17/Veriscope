"""Tests for fail-closed rules behavior, Skipped handling, and severity preservation."""
import unittest
from datetime import date
from unittest.mock import patch

from app.rules.engine import evaluate_ruleset, load_ruleset
from app.rules.model import CaseContext, RuleOutcome, Skipped
from app.rules.operators import _parse_decimal


class TestRulesFailClosed(unittest.TestCase):
    def test_parse_decimal_units_and_commas(self) -> None:
        self.assertEqual(_parse_decimal("3,200 sq.m"), 3200)
        self.assertEqual(_parse_decimal("₹ 5,00,000.50"), 500000.50)
        self.assertEqual(_parse_decimal("1.5 acres"), 1.5)
        self.assertEqual(_parse_decimal("-42.0"), -42.0)
        with self.assertRaises(ValueError):
            _parse_decimal("no digits here")

    def test_unexpected_operator_error_preserves_severity(self) -> None:
        rs = load_ruleset("student_support_lite.v1.yaml")
        # Find a high severity rule
        high_rule = next(r for r in rs.rules if r["severity"] == "high")
        
        ctx = CaseContext("c1", "TEST-ERR", date(2026, 10, 22), [], [])
        with patch.dict("app.rules.operators.OPERATORS", {high_rule["operator"]: lambda r, p, c: (_ for _ in ()).throw(RuntimeError("Unexpected boom"))}):
            evals = evaluate_ruleset(rs, ctx)
            high_eval = next(e for e in evals if e.rule_id == high_rule["id"])
            self.assertEqual(high_eval.severity, "high")
            self.assertEqual(high_eval.outcome, RuleOutcome.REVIEW_REQUIRED.value)
            self.assertEqual(high_eval.findings[0].severity, "high")

    def test_skipped_operator_yields_not_applicable(self) -> None:
        rs = load_ruleset("student_support_lite.v1.yaml")
        rule = rs.rules[0]
        ctx = CaseContext("c1", "TEST-SKIP", date(2026, 10, 22), [], [])
        with patch.dict("app.rules.operators.OPERATORS", {rule["operator"]: lambda r, p, c: (_ for _ in ()).throw(Skipped("Test precondition missing"))}):
            evals = evaluate_ruleset(rs, ctx)
            target_eval = next(e for e in evals if e.rule_id == rule["id"])
            self.assertEqual(target_eval.outcome, RuleOutcome.NOT_APPLICABLE.value)
            self.assertIn("Not evaluated: Test precondition missing", target_eval.detail)
