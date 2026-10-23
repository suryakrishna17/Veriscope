"""Versioned rulebook loader and evaluator."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .model import CaseContext, RuleResult
from .operators import OPERATORS

log = logging.getLogger("veriscope.rules")
RULESET_DIR = Path(__file__).resolve().parent / "rulesets"
CATEGORIES = {"completeness", "consistency", "compliance", "document_signal", "issuer_check"}
SEVERITIES = {"info", "low", "medium", "high"}


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
        rules.append({**r, "_version": str(r.get("version", doc["version"]))})
    return Ruleset(
        name=doc["ruleset"],
        version=str(doc["version"]),
        checksum=hashlib.sha256(raw).hexdigest(),
        is_provisional=bool(doc.get("is_provisional", True)),
        source_note=str(doc.get("source_note", "")),
        effective_date=str(doc["effective_date"]) if doc.get("effective_date") else None,
        rules=rules,
    )


def evaluate(ruleset: Ruleset, ctx: CaseContext) -> list[RuleResult]:
    results: list[RuleResult] = []
    for rule in ruleset.rules:
        if rule.get("enabled", True) is False:
            continue
        try:
            results.extend(OPERATORS[rule["operator"]](rule, rule.get("params", {}), ctx))
        except Exception:  # a broken rule must not take the case down; surface it instead
            log.exception("rule_failed", extra={"ctx": {"rule_id": rule["id"], "case": ctx.case_ref}})
            results.append(
                RuleResult(rule["id"], rule["_version"], rule["category"], "info", "Rule could not be evaluated",
                           "This check raised an internal error and was skipped. The result is unknown; review manually.",
                           [], 0.0, "Review this check manually.", "error")
            )
    return results
