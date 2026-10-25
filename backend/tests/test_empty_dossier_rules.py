"""Regression test suite for P0 rules engine behavior.

Verifies that empty and incomplete dossiers cannot produce false PASS outcomes
when mandatory statutory documents, fields, or committee self-disclosures are missing.
"""
import unittest
from datetime import date

from app.rules.engine import evaluate, evaluate_ruleset, load_ruleset
from app.rules.model import CaseContext, RuleOutcome
from tests.test_eoa_rules import (
    FIRE,
    build_ctx,
)

RS = load_ruleset("aicte_eoa_chapter2.v1.yaml")
TODAY = date(2024, 4, 20)


class EmptyDossierRegressionTests(unittest.TestCase):
    """P0 Regression tests verifying absence of false passes."""

    def test_entirely_empty_application_does_not_false_pass_rules(self) -> None:
        """An empty dossier (no documents, no fields) must flag failures and must NOT falsely pass."""
        empty_ctx = CaseContext("c-empty", "CASE-EMPTY", TODAY, docs=[], fields=[])
        evaluations = evaluate_ruleset(RS, empty_ctx)
        outcomes = {e.rule_id: e.outcome for e in evaluations}

        # Must evaluate all 24 rules
        self.assertEqual(len(evaluations), 25)

        # Mandatory document completeness rules must FAIL
        self.assertEqual(outcomes["EOA-CMP-001"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-CMP-003"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-CMP-004"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-CMP-005"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-CMP-006"], RuleOutcome.FAIL.value)

        # Mandatory statutory committee self-disclosures must FAIL
        self.assertEqual(outcomes["EOA-COM-001"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-COM-002"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-COM-003"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-COM-004"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-COM-005"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-COM-006"], RuleOutcome.FAIL.value)

        # Mandatory infrastructure and undertaking self-disclosures must flag FAIL or REVIEW_REQUIRED
        self.assertIn(outcomes["EOA-INF-001"], (RuleOutcome.FAIL.value, RuleOutcome.REVIEW_REQUIRED.value))
        self.assertEqual(outcomes["EOA-INF-002"], RuleOutcome.FAIL.value)
        self.assertEqual(outcomes["EOA-INF-003"], RuleOutcome.FAIL.value)

        # Land & occupancy missing for EoA review is flagged
        self.assertIn(outcomes["EOA-CMP-002"], (RuleOutcome.FAIL.value, RuleOutcome.REVIEW_REQUIRED.value))

        # Overall non-pass count must be at least 15 (cannot pass 22 rules)
        non_pass_count = sum(1 for o in outcomes.values() if o != RuleOutcome.PASS.value)
        self.assertGreaterEqual(non_pass_count, 15)

    def test_missing_single_document_fails_its_mandatory_fields(self) -> None:
        """Uploading an application form but omitting the fire certificate must fail fire safety rules."""
        clean = build_ctx()
        # Remove the fire safety document and its extracted fields
        docs_no_fire = [d for d in clean.docs if d.doc_type != FIRE]
        fields_no_fire = [f for f in clean.fields if f.doc_type != FIRE]
        ctx_no_fire = CaseContext("c-no-fire", "CASE-NO-FIRE", TODAY, docs_no_fire, fields_no_fire)

        evaluations = evaluate_ruleset(RS, ctx_no_fire)
        outcomes = {e.rule_id: e.outcome for e in evaluations}

        # Core dossier is missing Fire Safety Certificate
        self.assertEqual(outcomes["EOA-CMP-001"], RuleOutcome.FAIL.value)
        # Specific fire safety required fields rule must FAIL, not PASS
        self.assertEqual(outcomes["EOA-CMP-005"], RuleOutcome.FAIL.value)

    def test_missing_mandatory_field_on_uploaded_document_fails(self) -> None:
        """When a document is uploaded but lacks a required statutory field, it fails."""
        clean = build_ctx()
        fields_no_id = [f for f in clean.fields if f.field_key != "institution_id"]
        ctx_no_id = CaseContext("c-no-id", "CASE-NO-ID", TODAY, clean.docs, fields_no_id)

        evaluations = evaluate_ruleset(RS, ctx_no_id)
        outcomes = {e.rule_id: e.outcome for e in evaluations}

        self.assertEqual(outcomes["EOA-CMP-003"], RuleOutcome.FAIL.value)

    def test_complete_clean_dossier_passes_all_rules(self) -> None:
        """A complete dossier with all 6 statutory documents and valid fields passes with 0 findings."""
        clean = build_ctx()
        findings = evaluate(RS, clean)
        self.assertEqual(findings, [])

        evaluations = evaluate_ruleset(RS, clean)
        for ev in evaluations:
            self.assertEqual(ev.outcome, RuleOutcome.PASS.value, f"Rule {ev.rule_id} did not pass: {ev.detail}")
