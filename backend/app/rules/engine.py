"""Versioned rulebook loader and evaluator."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .model import CaseContext, RuleEvaluation, RuleOutcome, RuleResult
from .operators import OPERATORS

log = logging.getLogger("veriscope.rules")
RULESET_DIR = Path(__file__).resolve().parent / "rulesets"
CATEGORIES = {"completeness", "consistency", "compliance", "document_signal", "issuer_check"}
SEVERITIES = {"info", "low", "medium", "high"}

APPLICATION_RULESETS: dict[str, str] = {
    "STUDENT_SUPPORT_LITE": "student_support_lite.v1.yaml",
    "AICTE_EOA": "aicte_eoa_chapter2.v1.yaml",
}


class RulesetError(ValueError):
    pass


@dataclass(frozen=True)
class Ruleset:
    name: str
    version: str
    checksum: str
    is_provisional: bool
    source_note: str
    effective_date: str | None
    rules: list[dict[str, Any]]

    @property
    def label(self) -> str:
        return f"{self.name}@{self.version}"

    def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        """Find a rule by its unique identifier."""
        for r in self.rules:
            if r["id"] == rule_id:
                return r
        return None

    @property
    def verified_rules(self) -> list[dict[str, Any]]:
        """Rules verified against official regulatory provisions (e.g., AICTE APH)."""
        return [r for r in self.rules if r.get("is_verified", True)]

    @property
    def illustrative_rules(self) -> list[dict[str, Any]]:
        """Illustrative or prototype rules not yet verified against statutory sources."""
        return [r for r in self.rules if not r.get("is_verified", True)]

    @property
    def rules_by_category(self) -> dict[str, list[dict[str, Any]]]:
        """Rules grouped by their statutory inspection category."""
        grouped: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
        for r in self.rules:
            grouped[r["category"]].append(r)
        return grouped


def load_ruleset(filename: str, directory: Path = RULESET_DIR) -> Ruleset:
    raw = (directory / filename).read_bytes()
    doc = yaml.safe_load(raw)
    for k in ("ruleset", "version", "rules"):
        if k not in doc:
            raise RulesetError(f"ruleset missing '{k}'")
    seen: set[str] = set()
    rules = []
    for r in doc["rules"]:
        for k in ("id", "category", "severity", "summary", "operator"):
            if k not in r:
                raise RulesetError(f"rule {r.get('id', '?')} missing '{k}'")
        if r["id"] in seen:
            raise RulesetError(f"duplicate rule id {r['id']}")
        if r["category"] not in CATEGORIES or r["severity"] not in SEVERITIES:
            raise RulesetError(f"rule {r['id']} has invalid category/severity")
        if r["operator"] not in OPERATORS:
            raise RulesetError(f"rule {r['id']} uses unknown operator {r['operator']}")
        seen.add(r["id"])
        rules.append({
            **r,
            "_version": str(r.get("version", doc["version"])),
            "is_verified": bool(r.get("is_verified", doc.get("is_verified", True))),
            "verification_status": str(r.get("verification_status", doc.get("verification_status", "VERIFIED_OFFICIAL"))),
        })
    return Ruleset(
        name=doc["ruleset"],
        version=str(doc["version"]),
        checksum=hashlib.sha256(raw).hexdigest(),
        is_provisional=bool(doc.get("is_provisional", True)),
        source_note=str(doc.get("source_note", "")),
        effective_date=str(doc["effective_date"]) if doc.get("effective_date") else None,
        rules=rules,
    )


def check_rule_applicability(rule: dict[str, Any], ctx: CaseContext) -> tuple[bool, str]:
    """Determine whether a rule is applicable to the current dossier context."""
    if rule.get("enabled", True) is False:
        return False, "Rule is disabled in ruleset configuration."

    condition = rule.get("condition")
    if condition:
        if isinstance(condition, dict):
            if "doc_present" in condition:
                req_doc = condition["doc_present"]
                if not ctx.docs_of(req_doc):
                    return False, f"Rule not applicable: Document '{req_doc}' is not in dossier."
            if "field_equals" in condition:
                fe = condition["field_equals"]
                f = ctx.field(fe["doc_type"], fe["field"])
                if f is None or f.value != fe["value"]:
                    return False, f"Rule not applicable: Condition '{fe['field']} == {fe['value']}' not met."
        elif isinstance(condition, str) and condition.lower() in ("false", "disabled", "skip"):
            return False, f"Rule not applicable: {condition}."

    return True, "Rule is applicable."


def evaluate_ruleset(ruleset: Ruleset, ctx: CaseContext) -> list[RuleEvaluation]:
    """Evaluate every rule in the ruleset, returning a consistent result structure (PASS, FAIL, REVIEW_REQUIRED, NOT_APPLICABLE)."""
    evaluations: list[RuleEvaluation] = []
    for rule in ruleset.rules:
        rule_id = rule["id"]
        version = rule.get("_version", ruleset.version)
        category = rule["category"]
        severity = rule["severity"]
        summary = rule["summary"]
        citation = rule.get("clause_citation")
        is_verified = bool(rule.get("is_verified", True))
        ver_status = str(rule.get("verification_status", "VERIFIED_OFFICIAL" if is_verified else "ILLUSTRATIVE"))
        app_cond = str(rule.get("applicable_condition") or rule.get("applicability") or "")
        next_action = rule.get("next_action")

        # 1. Applicability check
        applicable, reason = check_rule_applicability(rule, ctx)
        if not applicable:
            evaluations.append(
                RuleEvaluation(
                    rule_id=rule_id,
                    rule_version=version,
                    category=category,
                    severity=severity,
                    summary=summary,
                    outcome=RuleOutcome.NOT_APPLICABLE.value,
                    detail=reason,
                    evidence_refs=[],
                    confidence=1.0,
                    clause_citation=citation,
                    is_verified=is_verified,
                    verification_status=ver_status,
                    next_action=next_action,
                    applicable_condition=app_cond,
                )
            )
            continue

        # 2. Evaluation logic via operator
        try:
            op_fn = OPERATORS[rule["operator"]]
            failures = list(op_fn(rule, rule.get("params", {}), ctx))
        except Exception:
            log.exception("rule_failed", extra={"ctx": {"rule_id": rule_id, "case": ctx.case_ref}})
            err_finding = RuleResult(
                rule_id=rule_id,
                rule_version=version,
                category=category,
                severity="info",
                summary="Rule could not be evaluated",
                detail="This check raised an internal error and was skipped. The result is unknown; review manually.",
                evidence_refs=[],
                confidence=0.0,
                next_action="Review this check manually.",
                subject="error",
                trust_label="ANOMALY_DETECTED",
                clause_citation=citation,
                outcome=RuleOutcome.REVIEW_REQUIRED.value,
                is_verified=is_verified,
            )
            evaluations.append(
                RuleEvaluation(
                    rule_id=rule_id,
                    rule_version=version,
                    category=category,
                    severity="info",
                    summary=summary,
                    outcome=RuleOutcome.REVIEW_REQUIRED.value,
                    detail="Rule evaluation encountered an unexpected error; human review required.",
                    evidence_refs=[],
                    confidence=0.0,
                    clause_citation=citation,
                    is_verified=is_verified,
                    verification_status=ver_status,
                    next_action="Review this check manually.",
                    findings=[err_finding],
                    applicable_condition=app_cond,
                )
            )
            continue

        # 3. Determine outcome (PASS vs FAIL vs REVIEW_REQUIRED)
        if not failures:
            evaluations.append(
                RuleEvaluation(
                    rule_id=rule_id,
                    rule_version=version,
                    category=category,
                    severity=severity,
                    summary=summary,
                    outcome=RuleOutcome.PASS.value,
                    detail=f"Requirement satisfied: {summary}.",
                    evidence_refs=[],
                    confidence=1.0,
                    clause_citation=citation,
                    is_verified=is_verified,
                    verification_status=ver_status,
                    next_action=None,
                    applicable_condition=app_cond,
                )
            )
        else:
            configured_fail_outcome = rule.get("outcome_on_fail")
            if configured_fail_outcome in (RuleOutcome.FAIL.value, RuleOutcome.REVIEW_REQUIRED.value):
                outcome = configured_fail_outcome
            elif rule.get("review_required") or category == "document_signal":
                outcome = RuleOutcome.REVIEW_REQUIRED.value
            else:
                outcome = RuleOutcome.FAIL.value

            for f in failures:
                f.outcome = outcome
                if f.clause_citation is None:
                    f.clause_citation = citation
                f.is_verified = is_verified

            combined_detail = "; ".join(f.detail for f in failures)
            all_refs: list[dict[str, Any]] = []
            for f in failures:
                all_refs.extend(f.evidence_refs)
            min_conf = min((f.confidence for f in failures), default=1.0)

            evaluations.append(
                RuleEvaluation(
                    rule_id=rule_id,
                    rule_version=version,
                    category=category,
                    severity=severity,
                    summary=summary,
                    outcome=outcome,
                    detail=combined_detail,
                    evidence_refs=all_refs,
                    confidence=min_conf,
                    clause_citation=citation,
                    is_verified=is_verified,
                    verification_status=ver_status,
                    next_action=next_action,
                    findings=failures,
                    applicable_condition=app_cond,
                )
            )

    return evaluations


def evaluate(ruleset: Ruleset, ctx: CaseContext) -> list[RuleResult]:
    """Evaluate ruleset and return active findings for non-passing rules (FAIL and REVIEW_REQUIRED)."""
    evaluations = evaluate_ruleset(ruleset, ctx)
    results: list[RuleResult] = []
    for ev in evaluations:
        if ev.outcome in (RuleOutcome.FAIL.value, RuleOutcome.REVIEW_REQUIRED.value):
            results.extend(ev.findings)
    return results
