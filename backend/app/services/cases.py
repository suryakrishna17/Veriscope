"""Case lifecycle: creation, access control, uploads, corrections, findings and decisions."""
from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from PIL import Image

from ..core.db import dumps, loads, new_id, utcnow
from ..core.errors import ApiError, bad_request, conflict, not_found
from ..processing.fields import DOC_TYPES
from ..processing.normalize import FIELDS, normalize
from ..processing.text import render_pdf_page
from ..processing.validation import validate_upload
from . import audit

if TYPE_CHECKING:
    from ..container import Services

UTC = getattr(datetime, "UTC", timezone.utc)

APPLICATION_TYPES = {
    "STUDENT_SUPPORT_LITE": "Student support application (prototype)",
    "AICTE_EOA": "AICTE Extension of Approval (Existing Institutions)",
}

TRANSITIONS: dict[str, set[str]] = {
    "received": {"processing"},
    "processing": {"needs_review", "processing_failed"},
    "processing_failed": {"processing"},
    "needs_review": {"processing", "clarification_requested", "approved", "rejected"},
    "clarification_requested": {"processing", "approved", "rejected"},
    "approved": {"needs_review"},
    "rejected": {"needs_review"},
}
UPLOAD_STATES = {"received", "needs_review", "clarification_requested", "processing_failed"}
REVIEW_STATES = {"needs_review", "clarification_requested"}
REASON_CODES = {
    "approve": {"ALL_CHECKS_SATISFIED", "FINDINGS_RESOLVED", "FINDINGS_WAIVED_WITH_JUSTIFICATION"},
    "request_clarification": {"MISSING_DOCUMENT", "UNCLEAR_SCAN", "DATA_MISMATCH", "SIGNATURE_REQUIRED", "OTHER"},
    "reject": {"INELIGIBLE", "INCONSISTENT_INFORMATION", "EXPIRED_AUTHORIZATION", "NO_RESPONSE_TO_CLARIFICATION", "OTHER"},
}
SEV_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


# ---------------------------------------------------------------- helpers
def transition(svc: Services, case: dict[str, Any], new_status: str, actor: dict[str, Any], reason: str = "") -> None:
    if new_status not in TRANSITIONS.get(case["status"], set()):
        raise conflict(f"A case that is '{case['status']}' cannot move to '{new_status}'.", current=case["status"], requested=new_status)
    svc.db.update("cases", case["id"], {"status": new_status, "updated_at": utcnow()})
    audit.record(svc.db, case["id"], actor, "case.status_changed", "case", case["id"], {"from": case["status"], "to": new_status, "reason": reason})
    case["status"] = new_status


def load_case(svc: Services, case_id: str, user: dict[str, Any]) -> dict[str, Any]:
    case = svc.db.one("SELECT * FROM cases WHERE id = ? OR case_ref = ?", (case_id, case_id))
    if case is None:
        raise not_found("Case")
    if user["role"] == "applicant" and case["applicant_user_id"] != user["id"]:
        raise not_found("Case")
    return case


def _next_case_ref(svc: Services) -> str:
    n = svc.db.scalar("SELECT COUNT(*) FROM cases") or 0
    return f"APP-2026-{n + 1:04d}"


def effective_value(f: dict[str, Any]) -> str | None:
    if f.get("corrected_value") not in (None, ""):
        return normalize(f["field_key"], f["corrected_value"])
    return f.get("normalized_value")


def serialize_document(d: dict[str, Any], pages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "id": d["id"],
        "doc_type": d["doc_type"],
        "original_name": d["original_name"],
        "mime_type": d["mime_type"],
        "size_bytes": d["size_bytes"],
        "sha256": d["sha256"],
        "page_count": d["page_count"],
        "uploaded_at": d["uploaded_at"],
        "processing_status": d["processing_status"],
        "trust_label": d["trust_label"],
        "signals": loads(d.get("signals_json")),
        "issuer_check": loads(d.get("issuer_check_json")),
        "processing_error": d.get("processing_error"),
        "version": d.get("version", 1),
        "pages": [
            {
                "page_number": p["page_number"],
                "width": p["width"],
                "height": p["height"],
                "text_source": p["text_source"],
                "mean_confidence": p["mean_confidence"],
                "image_url": f"/api/v1/documents/{d['id']}/pages/{p['page_number']}/image",
            }
            for p in (pages or [])
        ],
    }


def serialize_field(f: dict[str, Any], doc_type: str) -> dict[str, Any]:
    return {
        "id": f["id"],
        "document_id": f["document_id"],
        "doc_type": doc_type,
        "field_key": f["field_key"],
        "label": FIELDS[f["field_key"]].label if f["field_key"] in FIELDS else f["field_key"],
        "raw_value": f["raw_value"],
        "normalized_value": f["normalized_value"],
        "effective_value": effective_value(f),
        "confidence": f["confidence"],
        "page_number": f["page_number"],
        "evidence_excerpt": f["evidence_excerpt"],
        "bbox": loads(f["bbox_json"]),
        "source": f["source"],
        "corrected_value": f["corrected_value"],
        "corrected_by": f.get("corrected_by_name") or f["corrected_by"],
        "corrected_at": f["corrected_at"],
        "correction_reason": f["correction_reason"],
    }


def serialize_finding(f: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f["id"],
        "rule_id": f["rule_id"],
        "rule_version": f["rule_version"],
        "category": f["category"],
        "severity": f["severity"],
        "status": f["status"],
        "trust_label": f["trust_label"],
        "summary": f["summary"],
        "detail": f["detail"],
        "evidence_refs": loads(f["evidence_refs_json"], []),
        "confidence": f["confidence"],
        "next_action": f["next_action"],
        "clause_citation": f.get("clause_citation"),
        "outcome": f.get("outcome", "FAIL"),
        "resolution_note": f["resolution_note"],
        "resolved_by": f.get("resolved_by_name") or f["resolved_by"],
        "resolved_at": f["resolved_at"],
        "created_at": f["created_at"],
    }


def _open_counts(svc: Services, case_id: str) -> dict[str, int]:
    rows = svc.db.all("SELECT severity, COUNT(*) n FROM findings WHERE case_id = ? AND is_current = 1 AND status = 'open' GROUP BY severity", (case_id,))
    counts = {s: 0 for s in SEV_ORDER}
    for r in rows:
        counts[r["severity"]] = r["n"]
    return counts


def serialize_case_summary(svc: Services, c: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": c["id"],
        "case_ref": c["case_ref"],
        "application_type": c["application_type"],
        "application_type_label": APPLICATION_TYPES.get(c["application_type"], c["application_type"]),
        "applicant_ref": c["applicant_ref"],
        "institution_ref": c["institution_ref"],
        "status": c["status"],
        "triage_priority": c["triage_priority"],
        "triage_components": loads(c["triage_components_json"], []),
        "open_findings": _open_counts(svc, c["id"]),
        "document_count": svc.db.scalar("SELECT COUNT(*) FROM documents WHERE case_id = ?", (c["id"],)),
        "created_at": c["created_at"],
        "updated_at": c["updated_at"],
    }


def allowed_actions(c: dict[str, Any], user: dict[str, Any]) -> list[str]:
    acts: list[str] = []
    status = c["status"]
    if status in UPLOAD_STATES:
        if user["role"] != "applicant" or status != "needs_review":
            acts.append("upload")
    if user["role"] in {"reviewer", "admin"}:
        if status in {"received", "needs_review", "clarification_requested", "processing_failed"}:
            acts.append("process")
        if status in REVIEW_STATES:
            acts += ["correct_field", "resolve_finding", "approve", "request_clarification", "reject"]
        if status in {"approved", "rejected"} and user["role"] == "admin":
            acts.append("reopen")
    elif user["role"] == "applicant" and status in {"received", "clarification_requested"}:
        acts.append("process")
    return acts


def case_detail(svc: Services, case_id: str, user: dict[str, Any]) -> dict[str, Any]:
    c = load_case(svc, case_id, user)
    docs = svc.db.all("SELECT * FROM documents WHERE case_id = ? ORDER BY uploaded_at", (c["id"],))
    v_counts: dict[str, int] = {}
    for d in docs:
        dt = d["doc_type"]
        v_counts[dt] = v_counts.get(dt, 0) + 1
        d["version"] = v_counts[dt]
    pages = svc.db.all("SELECT document_id, page_number, width, height, text_source, mean_confidence FROM pages WHERE document_id IN (SELECT id FROM documents WHERE case_id = ?) ORDER BY page_number", (c["id"],))
    doc_types = {d["id"]: d["doc_type"] for d in docs}
    is_reviewer = user["role"] in {"reviewer", "admin"}
    out = serialize_case_summary(svc, c)
    out["rule_set_version"] = c["rule_set_version"]
    out["documents"] = [serialize_document(d, [p for p in pages if p["document_id"] == d["id"]]) for d in docs]
    fields = svc.db.all(
        "SELECT f.*, u.name AS corrected_by_name FROM extracted_fields f LEFT JOIN users u ON u.id = f.corrected_by WHERE f.case_id = ? ORDER BY f.created_at",
        (c["id"],),
    )
    out["fields"] = [serialize_field(f, doc_types.get(f["document_id"], "")) for f in fields] if is_reviewer else []
    findings = svc.db.all(
        "SELECT f.*, u.name AS resolved_by_name FROM findings f LEFT JOIN users u ON u.id = f.resolved_by WHERE f.case_id = ? AND f.is_current = 1",
        (c["id"],),
    )
    findings.sort(key=lambda f: (f["status"] != "open", SEV_ORDER[f["severity"]], f["rule_id"]))
    out["findings"] = [serialize_finding(f) for f in findings] if is_reviewer else []
    decisions = svc.db.all(
        "SELECT d.*, u.name AS reviewer_name FROM decisions d JOIN users u ON u.id = d.reviewer_id WHERE d.case_id = ? ORDER BY decided_at DESC",
        (c["id"],),
    )
    out["decisions"] = [
        {"id": d["id"], "outcome": d["outcome"], "reason_code": d["reason_code"], "note": d["note"], "reviewer": d["reviewer_name"], "decided_at": d["decided_at"]}
        for d in decisions
    ]
    rs = svc.get_ruleset(c.get("application_type"))
    out["ruleset"] = {"name": rs.name, "version": rs.version, "is_provisional": rs.is_provisional}
    sum_data = loads(c["summary_json"]) if c.get("summary_json") else None
    out["summary"] = sum_data if is_reviewer else None
    eval_sum = sum_data.get("evaluation_summary") if sum_data else None
    if eval_sum is None and c["status"] not in {"received", "processing"} and docs:
        try:
            from ..rules.engine import evaluate_ruleset
            from .processing import build_context
            ctx = build_context(svc, c)
            evals = evaluate_ruleset(rs, ctx)
            eval_sum = {
                "total": len(evals),
                "pass": sum(1 for ev in evals if ev.outcome == "PASS"),
                "fail": sum(1 for ev in evals if ev.outcome == "FAIL"),
                "review_required": sum(1 for ev in evals if ev.outcome == "REVIEW_REQUIRED"),
                "not_applicable": sum(1 for ev in evals if ev.outcome == "NOT_APPLICABLE"),
                "ruleset_name": rs.name,
                "ruleset_version": rs.version,
            }
        except Exception:
            eval_sum = None
    out["evaluation_summary"] = eval_sum
    out["audit"] = audit.list_events(svc.db, c["id"], limit=100) if is_reviewer else []
    out["allowed_actions"] = allowed_actions(c, user)
    job = svc.db.one("SELECT * FROM jobs WHERE case_id = ? ORDER BY created_at DESC LIMIT 1", (c["id"],))
    out["latest_job"] = serialize_job(job) if job else None
    return out


def serialize_job(j: dict[str, Any]) -> dict[str, Any]:
    return {k: j[k] for k in ("id", "case_id", "kind", "status", "progress", "error_code", "error_message", "created_at", "started_at", "finished_at")}


# ---------------------------------------------------------------- commands
def create_case(svc: Services, user: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    app_type = (body.get("application_type") or "AICTE_EOA").strip()
    if app_type not in APPLICATION_TYPES:
        raise bad_request("Unknown application type.", allowed=list(APPLICATION_TYPES))
    applicant_ref = str(body.get("applicant_ref") or "").strip()
    institution_ref = str(body.get("institution_ref") or "").strip()
    errors = {}
    if not 2 <= len(applicant_ref) <= 120:
        errors["applicant_ref"] = "Enter the applicant's name or reference (2–120 characters)."
    if not 2 <= len(institution_ref) <= 160:
        errors["institution_ref"] = "Enter the institution name or code (2–160 characters)."
    if errors:
        raise ApiError(400, "INVALID_REQUEST", "Some details need fixing.", {"fields": errors})
    case_ref = str(body.get("case_ref") or "").strip() if user["role"] == "admin" else ""
    if case_ref and not re.fullmatch(r"[A-Z0-9-]{4,32}", case_ref):
        raise bad_request("Case reference must be 4–32 characters of A–Z, 0–9 or '-'.")
    applicant_user_id = body.get("applicant_user_id") if user["role"] == "admin" and body.get("applicant_user_id") else (user["id"] if user["role"] == "applicant" else None)
    if applicant_user_id and not svc.db.one("SELECT 1 FROM users WHERE id = ?", (applicant_user_id,)):
        raise bad_request("The specified applicant_user_id does not exist.")
    now = utcnow()
    with svc.db.transaction():
        row = {
            "id": new_id(),
            "case_ref": case_ref or _next_case_ref(svc),
            "application_type": app_type,
            "applicant_ref": applicant_ref,
            "institution_ref": institution_ref,
            "applicant_user_id": body.get("applicant_user_id") if user["role"] == "admin" and body.get("applicant_user_id") else (user["id"] if user["role"] == "applicant" else None),
            "status": "received",
            "triage_priority": 0,
            "triage_components_json": dumps([]),
            "rule_set_version": svc.get_ruleset(app_type).label,
            "created_at": now,
            "updated_at": now,
        }
        if svc.db.one("SELECT 1 FROM cases WHERE case_ref = ?", (row["case_ref"],)):
            raise conflict("A case with this reference already exists.")
        svc.db.insert("cases", row)
        audit.record(svc.db, row["id"], user, "case.created", "case", row["id"], {"case_ref": row["case_ref"], "application_type": app_type})
    return {"id": row["id"], "case_ref": row["case_ref"], "status": row["status"]}


def list_cases(svc: Services, user: dict[str, Any], status: str | None, q: str | None, page: int, page_size: int, sort: str) -> dict[str, Any]:
    where, params = ["1=1"], []
    if user["role"] == "applicant":
        where.append("applicant_user_id = ?")
        params.append(user["id"])
    if status:
        statuses = [s for s in status.split(",") if s in TRANSITIONS]
        if statuses:
            where.append(f"status IN ({','.join('?' * len(statuses))})")
            params += statuses
    if q:
        safe_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append("(case_ref LIKE ? ESCAPE '\\' OR applicant_ref LIKE ? ESCAPE '\\' OR institution_ref LIKE ? ESCAPE '\\')")
        params += [f"%{safe_q}%"] * 3
    order = {"priority": "triage_priority DESC, updated_at DESC", "updated": "updated_at DESC", "created": "created_at DESC"}.get(sort, "triage_priority DESC, updated_at DESC")
    total = svc.db.scalar(f"SELECT COUNT(*) FROM cases WHERE {' AND '.join(where)}", tuple(params))
    rows = svc.db.all(f"SELECT * FROM cases WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ? OFFSET ?", (*params, page_size, (page - 1) * page_size))
    return {"items": [serialize_case_summary(svc, r) for r in rows], "total": total, "page": page, "page_size": page_size}


def upload_document(svc: Services, user: dict[str, Any], case_id: str, doc_type: str, filename: str, data: bytes) -> dict[str, Any]:
    case = load_case(svc, case_id, user)
    if doc_type not in DOC_TYPES:
        raise bad_request("Choose a document type.", allowed=list(DOC_TYPES))
    if case["status"] not in UPLOAD_STATES:
        raise conflict(f"Documents cannot be added while the case is '{case['status']}'.")
    if user["role"] == "applicant" and case["status"] == "needs_review":
        raise conflict("Applicants cannot upload documents while the case is under review. Await clarification request or reviewer feedback.")
    vf = validate_upload(data, filename, svc.settings.max_upload_bytes, svc.settings.max_pages)
    doc_id = new_id()
    key = f"cases/{case['id']}/{doc_id}/original{vf.safe_name[vf.safe_name.rfind('.'):]}"
    svc.storage.put(key, vf.data)
    dupes = svc.db.all(
        "SELECT d.id, d.doc_type, d.original_name, c.case_ref FROM documents d JOIN cases c ON c.id = d.case_id WHERE d.sha256 = ?",
        (vf.sha256,),
    )
    try:
        with svc.db.transaction():
            svc.db.insert(
                "documents",
                {
                    "id": doc_id, "case_id": case["id"], "doc_type": doc_type, "original_name": vf.safe_name,
                    "mime_type": vf.mime_type, "size_bytes": len(vf.data), "sha256": vf.sha256, "storage_key": key,
                    "uploaded_at": utcnow(), "uploaded_by": user["id"], "page_count": vf.page_count,
                    "processing_status": "pending", "trust_label": "NOT_VERIFIED",
                },
            )
            svc.db.update("cases", case["id"], {"updated_at": utcnow()})
            audit.record(svc.db, case["id"], user, "document.uploaded", "document", doc_id,
                         {"doc_type": doc_type, "sha256": vf.sha256, "size_bytes": len(vf.data), "pages": vf.page_count, "duplicate_of": [d["id"] for d in dupes]})
    except Exception:
        try:
            svc.storage.delete(key)
        except Exception:
            pass
        raise
    return {"document_id": doc_id, "processing_status": "pending", "sha256": vf.sha256, "duplicate": bool(dupes)}


def document_for_user(svc: Services, user: dict[str, Any], doc_id: str) -> dict[str, Any]:
    d = svc.db.one("SELECT * FROM documents WHERE id = ?", (doc_id,))
    if d is None:
        raise not_found("Document")
    load_case(svc, d["case_id"], user)
    return d


def page_image(svc: Services, user: dict[str, Any], doc_id: str, page_number: int) -> bytes:
    d = document_for_user(svc, user, doc_id)
    if not 1 <= page_number <= max(1, d["page_count"]):
        raise not_found("Page")
    key = f"cases/{d['case_id']}/{d['id']}/page-{page_number}.png"
    if svc.storage.exists(key):
        return svc.storage.get(key)
    data = svc.storage.get(d["storage_key"])
    if d["mime_type"] == "application/pdf":
        img = render_pdf_page(data, page_number - 1, 1.6)
    else:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((1400, 1800))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    svc.storage.put(key, buf.getvalue())
    return buf.getvalue()


def correct_field(svc: Services, user: dict[str, Any], field_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from .processing import evaluate_case

    f = svc.db.one("SELECT * FROM extracted_fields WHERE id = ?", (field_id,))
    if f is None:
        raise not_found("Field")
    case = load_case(svc, f["case_id"], user)
    if case["status"] not in REVIEW_STATES:
        raise conflict("Fields can only be corrected while the case is under review.")
    value = str(body.get("value") or "").strip()
    reason = str(body.get("reason") or "").strip()
    if not value:
        raise ApiError(400, "INVALID_REQUEST", "Enter the corrected value.", {"fields": {"value": "Required"}})
    if len(reason) < 3:
        raise ApiError(400, "INVALID_REQUEST", "Say why you corrected this value.", {"fields": {"reason": "At least 3 characters"}})
    if normalize(f["field_key"], value) is None:
        raise ApiError(422, "INVALID_VALUE", f"'{value}' is not a valid {FIELDS[f['field_key']].label.lower() if f['field_key'] in FIELDS else 'value'}.")
    with svc.db.transaction():
        svc.db.update("extracted_fields", f["id"], {"corrected_value": value[:300], "corrected_by": user["id"], "corrected_at": utcnow(), "correction_reason": reason[:500]})
        event_id = audit.record(svc.db, case["id"], user, "field.corrected", "field", f["id"],
                                {"field_key": f["field_key"], "original": f["raw_value"], "previous_correction": f["corrected_value"], "new": value, "reason": reason})
    evaluate_case(svc, case["id"], user)
    updated = svc.db.one("SELECT * FROM extracted_fields WHERE id = ?", (field_id,)) or f
    doc_type = svc.db.scalar("SELECT doc_type FROM documents WHERE id = ?", (f["document_id"],))
    return {"field": serialize_field(updated, doc_type), "audit_event_id": event_id}


def update_finding(svc: Services, user: dict[str, Any], finding_id: str, body: dict[str, Any]) -> dict[str, Any]:
    f = svc.db.one("SELECT * FROM findings WHERE id = ?", (finding_id,))
    if f is None or not f["is_current"]:
        raise not_found("Finding")
    case = load_case(svc, f["case_id"], user)
    if case["status"] not in REVIEW_STATES:
        raise conflict("Findings can only be changed while the case is under review.")
    status = body.get("status")
    note = str(body.get("note") or body.get("resolution_note") or "").strip()
    if status not in {"open", "resolved", "waived"}:
        raise bad_request("Status must be open, resolved or waived.")
    if status != "open" and len(note) < 5:
        raise ApiError(400, "INVALID_REQUEST", "Add a note of at least 5 characters explaining your decision.", {"fields": {"note": "Required"}})
    if status == "waived" and f["severity"] == "high" and len(note) < 20:
        raise ApiError(
            400,
            "INVALID_REQUEST",
            "A detailed justification of at least 20 characters is required to waive a high-severity finding.",
            {"fields": {"note": "At least 20 characters required"}},
        )
    with svc.db.transaction():
        changes = {"status": status, "updated_at": utcnow(), "resolution_note": note[:1000] if status != "open" else None,
                   "resolved_by": user["id"] if status != "open" else None, "resolved_at": utcnow() if status != "open" else None}
        svc.db.update("findings", f["id"], changes)
        audit.record(svc.db, case["id"], user, f"finding.{status}", "finding", f["id"], {"rule_id": f["rule_id"], "from": f["status"], "note": note})
        _refresh_triage(svc, case["id"])
    row = svc.db.one("SELECT f.*, u.name AS resolved_by_name FROM findings f LEFT JOIN users u ON u.id = f.resolved_by WHERE f.id = ?", (f["id"],))
    return serialize_finding(row or f)


def decide(svc: Services, user: dict[str, Any], case_id: str, body: dict[str, Any]) -> dict[str, Any]:
    case = load_case(svc, case_id, user)
    outcome = body.get("outcome")
    reason = body.get("reason_code")
    note = str(body.get("note") or "").strip()[:2000]
    if outcome not in REASON_CODES:
        raise bad_request("Outcome must be approve, request_clarification or reject.")
    if reason not in REASON_CODES[outcome]:
        raise ApiError(400, "INVALID_REQUEST", "Choose a reason for this decision.", {"fields": {"reason_code": sorted(REASON_CODES[outcome])}})
    if outcome in {"reject", "request_clarification"} and len(note) < 5:
        raise ApiError(400, "INVALID_REQUEST", "Add a note the applicant can act on (at least 5 characters).", {"fields": {"note": "Required"}})
    if case["status"] not in REVIEW_STATES:
        raise conflict(f"A decision cannot be recorded while the case is '{case['status']}'.")
    findings = svc.db.all("SELECT id, rule_id, severity, status FROM findings WHERE case_id = ? AND is_current = 1", (case["id"],))
    if outcome == "approve":
        unprocessed = svc.db.all(
            "SELECT id, original_name, processing_status FROM documents WHERE case_id = ? AND processing_status IN ('pending', 'processing')",
            (case["id"],),
        )
        if unprocessed:
            raise conflict("All documents must be completely processed before approving.", unprocessed_documents=[d["original_name"] for d in unprocessed])

        latest_doc_time = svc.db.scalar("SELECT MAX(uploaded_at) FROM documents WHERE case_id = ?", (case["id"],))
        latest_eval_time = case.get("last_evaluated_at") or svc.db.scalar(
            "SELECT MAX(created_at) FROM audit_events WHERE case_id = ? AND action = 'rules.evaluated'", (case["id"],)
        ) or svc.db.scalar("SELECT MAX(created_at) FROM findings WHERE case_id = ?", (case["id"],))
        if latest_doc_time and latest_eval_time and str(latest_doc_time) > str(latest_eval_time):
            raise conflict("Documents were added or updated after rules were last evaluated. Run evaluation before deciding.")

        blocking = [f["rule_id"] for f in findings if f["status"] == "open" and f["severity"] == "high"]
        if blocking:
            raise conflict("Resolve or waive every high-severity finding before approving.", open_high_findings=blocking)
    new_status = {"approve": "approved", "reject": "rejected", "request_clarification": "clarification_requested"}[outcome]
    with svc.db.transaction():
        did = new_id()
        svc.db.insert("decisions", {"id": did, "case_id": case["id"], "reviewer_id": user["id"], "outcome": outcome, "reason_code": reason,
                                    "note": note, "findings_snapshot_json": dumps(findings), "decided_at": utcnow()})
        audit.record(svc.db, case["id"], user, f"decision.{outcome}", "decision", did, {"reason_code": reason, "note": note, "open_findings": [f["rule_id"] for f in findings if f["status"] == "open"]})
        transition(svc, case, new_status, user, reason)
    return {"decision_id": did, "outcome": outcome, "status": new_status}


def reopen(svc: Services, user: dict[str, Any], case_id: str, body: dict[str, Any]) -> dict[str, Any]:
    case = load_case(svc, case_id, user)
    note = str(body.get("note") or "").strip()
    if len(note) < 5:
        raise ApiError(400, "INVALID_REQUEST", "Explain why the case is being reopened.", {"fields": {"note": "Required"}})
    with svc.db.transaction():
        transition(svc, case, "needs_review", user, f"reopened: {note[:200]}")
    return {"status": "needs_review"}


def _refresh_triage(svc: Services, case_id: str) -> None:
    from .processing import compute_triage

    rows = svc.db.all("SELECT * FROM findings WHERE case_id = ? AND is_current = 1", (case_id,))
    score, comps = compute_triage(rows)
    svc.db.update("cases", case_id, {"triage_priority": score, "triage_components_json": dumps(comps), "updated_at": utcnow()})
