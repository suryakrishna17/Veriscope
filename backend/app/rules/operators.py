"""Rule operators. Each takes (rule, params, ctx) and yields zero or more failures.

Operators fail closed: missing required preconditions raise Skipped, which the engine
marks as NOT_APPLICABLE rather than a silent false pass.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from typing import Any

from ..processing.normalize import FIELDS, similarity
from .model import CaseContext, FieldView, RuleResult, Skipped

Rule = dict[str, Any]
Op = Callable[[Rule, dict[str, Any], CaseContext], Iterator[RuleResult]]
OPERATORS: dict[str, Op] = {}

NO_EVIDENCE = "No source evidence: the value was not found in the uploaded documents."


def operator(name: str) -> Callable[[Op], Op]:
    def deco(fn: Op) -> Op:
        OPERATORS[name] = fn
        return fn

    return deco


def _label(key: str) -> str:
    return FIELDS[key].label if key in FIELDS else key.replace("_", " ")


def _doc_label(doc_type: str) -> str:
    return doc_type.replace("_", " ").lower()


def _parse_decimal(val: Any) -> Decimal:
    """Parse numeric values with optional units and commas (e.g. '3,200 sq.m', '₹ 5,00,000', '1.5 acres')."""
    if val is None:
        raise ValueError("Missing numeric value")
    s = str(val).strip().replace(",", "")
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if not m:
        raise ValueError(f"Cannot parse numeric value from '{val}'")
    return Decimal(m.group(0))


def _result(
    rule: Rule,
    detail: str,
    refs: list[dict[str, Any]],
    confidence: float,
    subject: str,
    summary: str | None = None,
    outcome: str | None = None,
) -> RuleResult:
    rule_outcome = outcome or rule.get("outcome_on_fail") or ("REVIEW_REQUIRED" if rule.get("review_required") or rule.get("category") == "document_signal" else "FAIL")
    return RuleResult(
        rule_id=rule["id"],
        rule_version=rule["_version"],
        category=rule["category"],
        severity=rule["severity"],
        summary=summary or rule["summary"],
        detail=detail,
        evidence_refs=refs,
        confidence=round(max(0.0, min(1.0, confidence)), 3),
        next_action=rule.get("next_action", "Review the evidence and decide."),
        subject=subject,
        clause_citation=rule.get("clause_citation"),
        outcome=rule_outcome,
        is_verified=bool(rule.get("is_verified", True)),
    )


def _doc_ref(ctx: CaseContext, doc_type: str) -> list[dict[str, Any]]:
    return [{"document_id": d.id, "doc_type": d.doc_type, "page": None, "excerpt": d.original_name} for d in ctx.docs_of(doc_type)]


@operator("required_doc_types")
def required_doc_types(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    present = {d.doc_type for d in ctx.docs}
    missing = [t for t in p["doc_types"] if t not in present]
    if missing:
        names = ", ".join(_doc_label(t) for t in missing)
        yield _result(rule, f"Missing: {names}. {NO_EVIDENCE}", [], 1.0, "|".join(missing))


@operator("required_fields")
def required_fields(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    names = ", ".join(_label(k) for k in p["fields"])
    if not ctx.docs_of(p["doc_type"]):
        yield _result(
            rule,
            f"Required document {_doc_label(p['doc_type'])} was not uploaded; mandatory fields ({names}) cannot be verified. {NO_EVIDENCE}",
            [],
            1.0,
            "|".join(p["fields"]),
        )
        return
    missing = [k for k in p["fields"] if ctx.field(p["doc_type"], k) is None]
    if missing:
        missing_names = ", ".join(_label(k) for k in missing)
        yield _result(
            rule,
            f"Not found on the {_doc_label(p['doc_type'])}: {missing_names}. {NO_EVIDENCE} OCR may also have missed it; check the page.",
            _doc_ref(ctx, p["doc_type"]),
            0.8,
            "|".join(missing),
        )


@operator("field_equals")
def field_equals(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    if not ctx.docs_of(p["doc_type"]):
        yield _result(
            rule,
            f"Required document {_doc_label(p['doc_type'])} was not uploaded; {_label(p['field'])} cannot be confirmed. {NO_EVIDENCE}",
            [],
            1.0,
            p["field"],
        )
        return
    f = ctx.field(p["doc_type"], p["field"])
    if f is None:
        yield _result(rule, f"{_label(p['field'])} could not be determined. {NO_EVIDENCE}", _doc_ref(ctx, p["doc_type"]), 0.6, p["field"])
    elif f.value != p["expected"]:
        detail = p.get("detail", "{label} is '{value}', expected '{expected}'.").format(label=_label(p["field"]), value=f.value, expected=p["expected"], excerpt=f.excerpt or "")
        yield _result(rule, detail, [f.ref()], f.confidence, p["field"])


@operator("regex")
def regex(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    pattern = re.compile(p["pattern"])
    bad: list[FieldView] = []
    checked = False
    for doc_type in p["doc_types"]:
        for key in p["fields"]:
            f = ctx.field(doc_type, key)
            if f is not None and f.value:
                checked = True
                if not pattern.fullmatch(f.value):
                    bad.append(f)
    if not checked:
        raise Skipped(f"No fields present to validate format pattern '{p['pattern']}'.")
    if bad:
        detail = "; ".join(f"{_label(f.field_key)} '{f.value}' on the {_doc_label(f.doc_type)} does not match the expected format" for f in bad)
        yield _result(rule, detail + ".", [f.ref() for f in bad], min(f.confidence for f in bad), "|".join(sorted(f"{f.doc_type}.{f.field_key}" for f in bad)))


@operator("date_not_future")
def date_not_future(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    f = ctx.field(p["doc_type"], p["field"])
    if not (f and f.value):
        raise Skipped(f"Date field '{_label(p['field'])}' on {_doc_label(p['doc_type'])} was not present.")
    if date.fromisoformat(f.value) > ctx.today:
        yield _result(rule, f"{_label(f.field_key)} {f.value} is later than today ({ctx.today.isoformat()}).", [f.ref()], f.confidence, f.field_key)


@operator("date_order")
def date_order(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    a = ctx.field(p["earlier"]["doc_type"], p["earlier"]["field"])
    b = ctx.field(p["later"]["doc_type"], p["later"]["field"])
    if not (a and b and a.value and b.value):
        raise Skipped("Date fields not both present for sequence comparison.")
    if date.fromisoformat(a.value) > date.fromisoformat(b.value):
        detail = f"{_label(b.field_key)} on the {_doc_label(b.doc_type)} is {b.value}, before the {_label(a.field_key).lower()} {a.value}."
        yield _result(rule, detail, [b.ref(), a.ref()], min(a.confidence, b.confidence), f"{a.field_key}<{b.field_key}")


@operator("arithmetic_sum")
def arithmetic_sum(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    parts = [ctx.field(p["doc_type"], k) for k in p["parts"]]
    total = ctx.field(p["doc_type"], p["total"])
    if not ctx.docs_of(p["doc_type"]):
        raise Skipped(f"Document '{_doc_label(p['doc_type'])}' was not uploaded.")
    if total is None or total.value is None:
        raise Skipped(f"Total field '{_label(p['total'])}' missing.")
    if any(x is None or x.value is None for x in parts):
        raise Skipped(f"One or more component fields missing for arithmetic sum in '{p['doc_type']}'.")
    try:
        s = sum((_parse_decimal(x.value) for x in parts if x and x.value is not None), Decimal("0"))
        t = _parse_decimal(total.value)
    except Exception as exc:
        raise Skipped(f"Failed to parse numeric amounts for arithmetic sum: {exc}") from exc
    if abs(s - t) > Decimal(str(p.get("tolerance", "0.01"))):
        detail = f"Components add up to {s:,.2f} but {_label(total.field_key).lower()} is {t:,.2f} (difference {t - s:,.2f})."
        refs = [total.ref()] + [x.ref() for x in parts if x]
        yield _result(rule, detail, refs, min([total.confidence] + [x.confidence for x in parts if x]), p["total"])


@operator("cross_doc_match")
def cross_doc_match(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    found = [f for ref in p["refs"] if (f := ctx.field(ref["doc_type"], ref["field"])) is not None and f.value]
    if len(found) < 2:
        raise Skipped("Fewer than 2 referenced documents present for cross-document match.")
    anchor = found[0]
    kind = p.get("kind", "name")
    worst: tuple[float, FieldView] | None = None
    for other in found[1:]:
        score = similarity(kind, anchor.value or "", other.value or "")
        if worst is None or score < worst[0]:
            worst = (score, other)
    if worst and worst[0] < p.get("threshold", 90):
        score, other = worst
        detail = (
            f"'{anchor.value}' ({_doc_label(anchor.doc_type)}) vs '{other.value}' ({_doc_label(other.doc_type)}): "
            f"similarity {score:.0f}/100, threshold {p.get('threshold', 90)}."
        )
        yield _result(rule, detail, [f.ref() for f in found], min(f.confidence for f in found), "|".join(sorted(f"{f.doc_type}.{f.field_key}" for f in found)))


@operator("duplicate_hash")
def duplicate_hash(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    for d in ctx.docs:
        if not d.duplicates:
            continue
        where = "; ".join(
            f"{x.get('original_name', 'document')} as {_doc_label(x.get('doc_type', ''))} in case {x.get('case_ref', 'unknown')}"
            for x in d.duplicates[:3]
        )
        detail = f"'{d.original_name}' has the same SHA-256 as: {where}. Identical files can be legitimate; confirm the intended document was submitted."
        refs = [{"document_id": d.id, "doc_type": d.doc_type, "page": 1, "excerpt": f"sha256 {d.sha256[:16]}…"}]
        yield _result(rule, detail, refs, 1.0, d.id)


@operator("metadata_notes")
def metadata_notes(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    for d in ctx.docs:
        notes = (d.signals.get("metadata") or {}).get("notes") or []
        if notes:
            refs = [{"document_id": d.id, "doc_type": d.doc_type, "page": None, "excerpt": "File metadata"}]
            yield _result(rule, f"'{d.original_name}': " + " ".join(notes), refs, 0.7, d.id)


@operator("scan_quality")
def scan_quality(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    for d in ctx.docs:
        q = d.signals.get("quality") or {}
        reasons = []
        mc = q.get("min_ocr_confidence")
        if mc is not None and mc < p.get("min_confidence", 80):
            reasons.append(f"mean OCR confidence {mc:.0f}% (below {p.get('min_confidence', 80)}%)")
        if q.get("blurry"):
            reasons.append("page looks blurred")
        if q.get("low_resolution"):
            reasons.append("scan resolution is low")
        if q.get("ocr_used") and not reasons and p.get("flag_any_ocr", True):
            reasons.append("text was read by OCR from an image, so values may contain recognition errors")
        if reasons:
            refs = [{"document_id": d.id, "doc_type": d.doc_type, "page": 1, "excerpt": "Scanned page"}]
            yield _result(rule, f"'{d.original_name}': " + "; ".join(reasons) + ".", refs, 0.9, d.id)


@operator("numeric_min")
def numeric_min(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    if not ctx.docs_of(p["doc_type"]):
        raise Skipped(f"Document '{_doc_label(p['doc_type'])}' was not uploaded.")
    f = ctx.field(p["doc_type"], p["field"])
    if f is None or f.value is None:
        raise Skipped(f"Field '{_label(p['field'])}' was not found on '{_doc_label(p['doc_type'])}'.")
    try:
        val = _parse_decimal(f.value)
        min_val = _parse_decimal(p["min_value"])
        if val < min_val:
            unit = p.get("unit", "")
            detail = f"{_label(f.field_key)} is {val}{' ' + unit if unit else ''}, which is below the statutory requirement of {min_val}{' ' + unit if unit else ''}."
            yield _result(rule, detail, [f.ref()], f.confidence, f.field_key)
    except Exception as exc:
        raise Skipped(f"Cannot evaluate minimum on '{f.value}': {exc}") from exc


@operator("land_norm_by_category")
def land_norm_by_category(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    """Evaluates land acreage against AICTE APH 2024-27 Appendix 4 Table 4.1 norms."""
    doc_type = p.get("doc_type", "EOA_APPLICATION_FORM")
    if not ctx.docs_of(doc_type):
        raise Skipped(f"Document '{_doc_label(doc_type)}' was not uploaded.")
    land_field = ctx.field(doc_type, p.get("land_field", "total_land_area_acres"))
    cat_field = ctx.field(doc_type, p.get("category_field", "land_category"))
    if land_field is None or land_field.value is None:
        raise Skipped("Land area field was not found on application form.")
    if cat_field is None or cat_field.value is None:
        raise Skipped("Land category field was not found on application form.")
    norms: dict[str, Decimal] = {
        "MEGA_METRO": Decimal("1.5"),
        "METRO": Decimal("1.5"),
        "URBAN": Decimal("2.5"),
        "RURAL": Decimal("7.5"),
        "HILLY": Decimal("1.5"),
    }
    cat = str(cat_field.value).strip().upper().replace(" ", "_")
    required = norms.get(cat, Decimal("2.5"))
    try:
        actual = _parse_decimal(land_field.value)
        if actual < required:
            detail = (
                f"Land area is {actual} acres for category '{cat}', which fails the minimum statutory requirement of "
                f"{required} acres under AICTE APH Chapter II & Appendix 4 Table 4.1."
            )
            yield _result(rule, detail, [land_field.ref(), cat_field.ref()], min(land_field.confidence, cat_field.confidence), "land_norm")
    except Exception as exc:
        raise Skipped(f"Cannot parse land area '{land_field.value}': {exc}") from exc


@operator("built_up_area_norm")
def built_up_area_norm(rule: Rule, p: dict[str, Any], ctx: CaseContext) -> Iterator[RuleResult]:
    """Evaluates institutional built-up area and FSR norms under AICTE APH Appendix 4 Table 4.2."""
    doc_type = p.get("doc_type", "EOA_APPLICATION_FORM")
    if not ctx.docs_of(doc_type):
        raise Skipped(f"Document '{_doc_label(doc_type)}' was not uploaded.")
    area_field = ctx.field(doc_type, p.get("area_field", "total_built_up_area"))
    intake_field = ctx.field(doc_type, p.get("intake_field", "approved_intake"))
    if area_field is None or area_field.value is None:
        raise Skipped("Built-up area field was not found on application form.")
    norm_per_seat = _parse_decimal(p.get("norm_sqm_per_seat", "9.5"))
    base_min = _parse_decimal(p.get("min_base_area_sqm", "4000.0"))
    try:
        actual_area = _parse_decimal(area_field.value)
        intake_val = _parse_decimal(intake_field.value) if intake_field and intake_field.value else Decimal("0")
        required_area = max(base_min, intake_val * norm_per_seat)
        if actual_area < required_area:
            detail = (
                f"Total built-up area is {actual_area:,.1f} sq.m., which is below the statutory requirement of "
                f"{required_area:,.1f} sq.m. (based on base norm {base_min:,.0f} sq.m. and {norm_per_seat} sq.m./student) "
                f"under AICTE APH Chapter II & Appendix 4 Table 4.2."
            )
            refs = [area_field.ref()]
            if intake_field:
                refs.append(intake_field.ref())
            yield _result(rule, detail, refs, area_field.confidence, "built_up_area_norm")
    except Exception as exc:
        raise Skipped(f"Cannot parse built up area '{area_field.value}': {exc}") from exc
