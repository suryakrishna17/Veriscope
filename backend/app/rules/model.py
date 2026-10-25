"""Data passed into and out of the rule engine. The engine is pure: no DB, no I/O."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):  # noqa: UP042
        pass


class RuleOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Skipped(Exception):
    """Raised when a rule or operator cannot be evaluated due to missing preconditions or data."""

    def __init__(self, reason: str = "") -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class FieldView:
    id: str
    document_id: str
    doc_type: str
    field_key: str
    value: str | None  # effective normalised value (reviewer correction wins)
    raw: str | None
    confidence: float
    page: int | None
    bbox: list[float] | None
    excerpt: str | None
    corrected: bool = False

    def ref(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "doc_type": self.doc_type,
            "field_key": self.field_key,
            "field_id": self.id,
            "page": self.page,
            "bbox": self.bbox,
            "excerpt": self.excerpt,
            "value": self.value,
        }


@dataclass(frozen=True)
class DocView:
    id: str
    doc_type: str
    original_name: str
    sha256: str
    processing_status: str
    signals: dict[str, Any] = field(default_factory=dict)
    duplicates: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CaseContext:
    case_id: str
    case_ref: str
    today: date
    docs: list[DocView]
    fields: list[FieldView]

    def docs_of(self, doc_type: str) -> list[DocView]:
        return [d for d in self.docs if d.doc_type == doc_type]

    def field(self, doc_type: str, key: str) -> FieldView | None:
        cands = [f for f in self.fields if f.doc_type == doc_type and f.field_key == key and f.value not in (None, "")]
        if not cands:
            return None
        return max(cands, key=lambda f: (f.corrected, f.confidence))


@dataclass
class RuleResult:
    rule_id: str
    rule_version: str
    category: str
    severity: str
    summary: str
    detail: str
    evidence_refs: list[dict[str, Any]]
    confidence: float
    next_action: str
    subject: str  # stable identity of *what* failed, used for idempotent fingerprints
    trust_label: str = "ANOMALY_DETECTED"
    clause_citation: str | None = None
    outcome: str = "FAIL"  # PASS | FAIL | REVIEW_REQUIRED | NOT_APPLICABLE
    is_verified: bool = True  # True if verified against official source (e.g. AICTE APH), False if illustrative


@dataclass
class RuleEvaluation:
    rule_id: str
    rule_version: str
    category: str
    severity: str
    summary: str
    outcome: str  # PASS | FAIL | REVIEW_REQUIRED | NOT_APPLICABLE
    detail: str
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    clause_citation: str | None = None
    is_verified: bool = True
    verification_status: str = "VERIFIED_OFFICIAL"
    next_action: str | None = None
    subject: str = ""
    findings: list[RuleResult] = field(default_factory=list)
    applicable_condition: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "category": self.category,
            "severity": self.severity,
            "summary": self.summary,
            "outcome": self.outcome,
            "detail": self.detail,
            "evidence_refs": self.evidence_refs,
            "confidence": self.confidence,
            "clause_citation": self.clause_citation,
            "is_verified": self.is_verified,
            "verification_status": self.verification_status,
            "next_action": self.next_action,
            "subject": self.subject,
            "applicable_condition": self.applicable_condition,
        }
