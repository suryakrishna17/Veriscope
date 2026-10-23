"""Processing orchestration: extraction → signals → issuer check → rules → triage → summary."""
from __future__ import annotations

import hashlib
import logging
from datetime import date
from typing import TYPE_CHECKING, Any

from ..core.db import dumps, loads, new_id, utcnow
from ..core.errors import ApiError, conflict
from ..processing import signals as sig
from ..processing.fields import extract_fields
from ..processing.text import OcrUnavailable, extract
from ..rules.engine import evaluate
from ..rules.model import CaseContext, DocView, FieldView
from . import audit
from .audit import SYSTEM_ACTOR
from .cases import effective_value, load_case, transition

if TYPE_CHECKING:
    from ..container import Services

log = logging.getLogger("veriscope.processing")

TRIAGE_WEIGHTS = {"high": 30, "medium": 12, "low": 4, "info": 0}


def start_processing(svc: Services, user: dict[str, Any], case_id: str, force: bool = False) -> dict[str, Any]:
    case = load_case(svc, case_id, user)
    if case["status"] == "processing":
        raise conflict("This case is already being processed. Wait for the current run to finish.")
    n_docs = svc.db.scalar("SELECT COUNT(*) FROM documents WHERE case_id = ?", (case["id"],))
    if not n_docs:
        raise ApiError(422, "NO_DOCUMENTS", "Upload at least one document before running checks.")
    job_id = new_id()
    with svc.db.transaction():
        transition(svc, case, "processing", user, "processing requested")
        svc.db.insert("jobs", {"id": job_id, "case_id": case["id"], "kind": "process_case", "status": "queued", "progress": 0, "created_at": utcnow()})
        audit.record(svc.db, case["id"], user, "job.queued", "job", job_id, {"force": force})
    svc.jobs.submit(lambda: run_job(svc, job_id, case["id"], force))
    return {"job_id": job_id, "status": "queued"}


def _job(svc: Services, job_id: str, **changes: Any) -> None:
    svc.db.update("jobs", job_id, changes)


def run_job(svc: Services, job_id: str, case_id: str, force: bool) -> None:
    _job(svc, job_id, status="running", started_at=utcnow(), progress=5)
    try:
        docs = svc.db.all("SELECT * FROM documents WHERE case_id = ? ORDER BY uploaded_at", (case_id,))
        todo = [d for d in docs if force or d["processing_status"] in ("pending", "failed")]
        for i, d in enumerate(todo):
            process_document(svc, d)
            _job(svc, job_id, progress=5 + int(80 * (i + 1) / max(1, len(todo))))
        docs = svc.db.all("SELECT processing_status FROM documents WHERE case_id = ?", (case_id,))
        case = svc.db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
        assert case is not None
        if docs and all(d["processing_status"] == "failed" for d in docs):
            with svc.db.transaction():
                transition(svc, case, "processing_failed", SYSTEM_ACTOR, "no document could be processed")
            _job(svc, job_id, status="failed", progress=100, finished_at=utcnow(), error_code="ALL_DOCUMENTS_FAILED",
                 error_message="None of the documents could be read. Check the files and retry.")
            return
        evaluate_case(svc, case_id, SYSTEM_ACTOR)
        case = svc.db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
        assert case is not None
        with svc.db.transaction():
            transition(svc, case, "needs_review", SYSTEM_ACTOR, "automated checks complete")
        _job(svc, job_id, status="succeeded", progress=100, finished_at=utcnow())
    except Exception as e:  # keep the case recoverable
        log.exception("job_failed", extra={"ctx": {"job_id": job_id}})
        case = svc.db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
        if case and case["status"] == "processing":
            with svc.db.transaction():
                transition(svc, case, "processing_failed", SYSTEM_ACTOR, "internal processing error")
        _job(svc, job_id, status="failed", progress=100, finished_at=utcnow(), error_code="PROCESSING_ERROR",
             error_message=f"Processing stopped unexpectedly ({type(e).__name__}). Retry the run.")


def process_document(svc: Services, d: dict[str, Any]) -> None:
    svc.db.update("documents", d["id"], {"processing_status": "processing", "processing_error": None})
    try:
        data = svc.storage.get(d["storage_key"])
        pages = extract(data, d["mime_type"], svc.settings.ocr_enabled, svc.settings.ocr_lang)
        extracted = extract_fields(d["doc_type"], pages)
        if d["doc_type"] in ("APPLICATION_FORM", "INSTITUTION_AUTHORIZATION_LETTER"):
            extracted.append(sig.detect_signature(pages))
        if d["doc_type"] == "INSTITUTION_AUTHORIZATION_LETTER":
            extracted.append(sig.detect_seal(pages))
            extracted.append(sig.detect_letterhead(pages))
        signals = {"quality": sig.quality_signals(pages), "metadata": sig.metadata_signals(data, d["mime_type"])}
        issuer = svc.issuer.verify(d["doc_type"], {e.field_key: e.normalized_value for e in extracted})
    except OcrUnavailable:
        _fail_doc(svc, d, "OCR is not available on the server, so this scanned document could not be read.")
        return
    except Exception:
        log.exception("document_failed", extra={"ctx": {"document_id": d["id"]}})
        _fail_doc(svc, d, "The document could not be read. Re-upload a clearer copy or a digital PDF.")
        return

    with svc.db.transaction():
        svc.db.execute("DELETE FROM pages WHERE document_id = ?", (d["id"],))
        for p in pages:
            svc.db.insert("pages", {"id": new_id(), "document_id": d["id"], "page_number": p.page_number, "width": p.width, "height": p.height,
                                    "text_source": p.source, "mean_confidence": round(p.mean_confidence, 1), "words_json": dumps([w.as_dict() for w in p.words])})
        corrected = {r["field_key"] for r in svc.db.all("SELECT field_key FROM extracted_fields WHERE document_id = ? AND corrected_value IS NOT NULL", (d["id"],))}
        svc.db.execute("DELETE FROM extracted_fields WHERE document_id = ? AND corrected_value IS NULL", (d["id"],))
        now = utcnow()
        for e in extracted:
            if e.field_key in corrected:
                continue
            svc.db.insert("extracted_fields", {
                "id": new_id(), "case_id": d["case_id"], "document_id": d["id"], "field_key": e.field_key, "raw_value": e.raw_value,
                "normalized_value": e.normalized_value, "confidence": e.confidence, "page_number": e.page_number,
                "evidence_excerpt": e.evidence_excerpt, "bbox_json": dumps(e.bbox) if e.bbox else None, "source": e.source, "created_at": now,
            })
        svc.db.update("documents", d["id"], {"processing_status": "processed", "page_count": len(pages), "signals_json": dumps(signals),
                                              "trust_label": issuer.label, "issuer_check_json": dumps(issuer.as_dict())})
        audit.record(svc.db, d["case_id"], SYSTEM_ACTOR, "document.processed", "document", d["id"],
                     {"pages": len(pages), "fields": len(extracted), "ocr_used": signals["quality"]["ocr_used"], "issuer_check": issuer.label})


def _fail_doc(svc: Services, d: dict[str, Any], message: str) -> None:
    with svc.db.transaction():
        svc.db.update("documents", d["id"], {"processing_status": "failed", "processing_error": message})
        audit.record(svc.db, d["case_id"], SYSTEM_ACTOR, "document.failed", "document", d["id"], {"error": message})


def build_context(svc: Services, case: dict[str, Any], today: date | None = None) -> CaseContext:
    docs = svc.db.all("SELECT * FROM documents WHERE case_id = ? AND processing_status = 'processed'", (case["id"],))
    all_docs = svc.db.all("SELECT * FROM documents WHERE case_id = ?", (case["id"],))
    doc_types = {d["id"]: d["doc_type"] for d in all_docs}
    views = []
    for d in all_docs:
        dupes = svc.db.all(
            """SELECT d.id, d.doc_type, d.original_name, c.case_ref FROM documents d JOIN cases c ON c.id = d.case_id
               WHERE d.sha256 = ? AND d.id != ? AND d.uploaded_at < ? ORDER BY d.uploaded_at""",
            (d["sha256"], d["id"], d["uploaded_at"]),
        )
        views.append(DocView(d["id"], d["doc_type"], d["original_name"], d["sha256"], d["processing_status"], loads(d["signals_json"], {}), dupes))
    rows = svc.db.all("SELECT * FROM extracted_fields WHERE case_id = ? AND document_id IN (%s)" % ",".join("?" * len(docs)), (case["id"], *[d["id"] for d in docs])) if docs else []
    fields = [
        FieldView(r["id"], r["document_id"], doc_types[r["document_id"]], r["field_key"], effective_value(r), r["corrected_value"] or r["raw_value"],
                  1.0 if r["corrected_value"] else r["confidence"], r["page_number"], loads(r["bbox_json"]), r["evidence_excerpt"], bool(r["corrected_value"]))
        for r in rows
    ]
    return CaseContext(case["id"], case["case_ref"], today or date.today(), views, fields)


def _fingerprint(rule_id: str, version: str, subject: str) -> str:
    return hashlib.sha256(f"{rule_id}|{version}|{subject}".encode()).hexdigest()[:32]


def compute_triage(findings: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    comps: list[dict[str, Any]] = []
    for sev in ("high", "medium", "low"):
        n = sum(1 for f in findings if f["is_current"] and f["status"] == "open" and f["severity"] == sev)
        if n:
            comps.append({"label": f"{n} open {sev}-severity finding(s)", "points": n * TRIAGE_WEIGHTS[sev]})
    if any(f["is_current"] and f["status"] == "open" and f["rule_id"] == "SIG-001" for f in findings):
        comps.append({"label": "Duplicate-file signal", "points": 10})
    score = min(100, sum(c["points"] for c in comps))
    return score, comps


def evaluate_case(svc: Services, case_id: str, actor: dict[str, Any]) -> None:
    case = svc.db.one("SELECT * FROM cases WHERE id = ?", (case_id,))
    assert case is not None
    ctx = build_context(svc, case)
    results = evaluate(svc.ruleset, ctx)
    now = utcnow()
    with svc.db.transaction():
        existing = {f["fingerprint"]: f for f in svc.db.all("SELECT * FROM findings WHERE case_id = ?", (case_id,))}
        seen: set[str] = set()
        created = 0
        for r in results:
            fp = _fingerprint(r.rule_id, r.rule_version, r.subject)
            if fp in seen:
                continue
            seen.add(fp)
            payload = {"summary": r.summary, "detail": r.detail, "evidence_refs_json": dumps(r.evidence_refs), "confidence": r.confidence,
                       "severity": r.severity, "next_action": r.next_action, "is_current": 1, "updated_at": now}
            if fp in existing:
                svc.db.update("findings", existing[fp]["id"], payload)  # keep reviewer resolution
            else:
                created += 1
                svc.db.insert("findings", {"id": new_id(), "case_id": case_id, "fingerprint": fp, "rule_id": r.rule_id, "rule_version": r.rule_version,
                                           "category": r.category, "status": "open", "trust_label": r.trust_label, "created_at": now, **payload})
        stale = [f["id"] for fp, f in existing.items() if fp not in seen and f["is_current"]]
        for fid in stale:
            svc.db.update("findings", fid, {"is_current": 0, "updated_at": now})
        rows = svc.db.all("SELECT * FROM findings WHERE case_id = ?", (case_id,))
        score, comps = compute_triage(rows)
        current = [f for f in rows if f["is_current"]]
        summary = svc.llm.summarize(case["case_ref"], [{k: f[k] for k in ("rule_id", "severity", "status", "category", "summary", "detail")} for f in current])
        svc.db.update("cases", case_id, {"triage_priority": score, "triage_components_json": dumps(comps), "summary_json": dumps({**summary.as_dict(), "generated_at": now}),
                                         "rule_set_version": svc.ruleset.label, "updated_at": now})
        audit.record(svc.db, case_id, actor, "rules.evaluated", "case", case_id,
                     {"ruleset": svc.ruleset.label, "results": len(seen), "new_findings": created, "cleared_findings": len(stale)})
