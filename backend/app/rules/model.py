"""Data passed into and out of the rule engine. The engine is pure: no DB, no I/O."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


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
