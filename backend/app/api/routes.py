"""HTTP API v1. Routers are thin: parse → authorise → call a service → serialise."""
from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request

from ..container import Services
from ..core.errors import ApiError, bad_request, not_found
from ..core.security import current_user, hash_password, issue_token, rate_limit, require_auth, verify_password
from ..processing.fields import DOC_TYPES
from ..services import analytics as analytics_svc
from ..services import cases as case_svc
from ..services import digilocker as digilocker_svc
from ..services import reports
from ..services.audit import compute_merkle_root, list_events, verify_audit_chain
from ..services.processing import start_processing

DUMMY_PASSWORD_HASH = hash_password("dummy-auth-timing-guard-string")

api = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def svc() -> Services:
    return current_app.extensions["veriscope"]  # type: ignore[no-any-return]


def body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if data is None:
        if request.data:
            raise bad_request("The request body must be valid JSON.")
        return {}
    if not isinstance(data, dict):
        raise bad_request("The request body must be a JSON object.")
    return data


def _int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(request.args.get(name, default))))
    except ValueError as e:
        raise bad_request(f"'{name}' must be a number.") from e


# ------------------------------------------------------------------ auth
@api.post("/auth/login")
@rate_limit("login", 10)
def login():  # type: ignore[no-untyped-def]
    b = body()
    email = str(b.get("email", "")).strip().lower()
    pw = str(b.get("password", ""))
    user = svc().db.one("SELECT * FROM users WHERE email = ?", (email,))
    hash_to_verify = user["password_hash"] if user else DUMMY_PASSWORD_HASH
    valid = verify_password(hash_to_verify, pw)
    if user is None or not valid:
        raise ApiError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    token = issue_token(user, svc().settings.secret_key, svc().settings.jwt_ttl_minutes)
    return jsonify({"access_token": token, "token_type": "bearer", "user": {k: user[k] for k in ("id", "email", "name", "role")}})


@api.get("/auth/me")
@require_auth()
def me():  # type: ignore[no-untyped-def]
    return jsonify(current_user())


# ------------------------------------------------------------------ meta
@api.get("/meta")
@require_auth()
def meta():  # type: ignore[no-untyped-def]
    s = svc()
    return jsonify({
        "application_types": [{"id": k, "label": v} for k, v in case_svc.APPLICATION_TYPES.items()],
        "doc_types": [{"id": d, "label": d.replace("_", " ").capitalize().replace("Or identity", "or identity")} for d in DOC_TYPES],
        "reason_codes": {k: sorted(v) for k, v in case_svc.REASON_CODES.items()},
        "max_upload_mb": s.settings.max_upload_mb,
        "max_pages": s.settings.max_pages,
        "ai_provider": s.llm.name,
        "issuer_verifier": s.issuer.name,
    })


@api.get("/rulesets/active")
@require_auth("reviewer", "admin")
def active_ruleset():  # type: ignore[no-untyped-def]
    app_type = request.args.get("application_type")
    rs = svc().get_ruleset(app_type)
    return jsonify({
        "name": rs.name, "version": rs.version, "checksum": rs.checksum, "is_provisional": rs.is_provisional,
        "source_note": rs.source_note, "effective_date": rs.effective_date,
        "rules": [
            {
                k: r.get(k)
                for k in ("id", "category", "severity", "summary", "operator", "next_action", "clause_citation", "applicability", "limitations", "is_verified", "verification_status")
                if k in r
            }
            for r in rs.rules
        ],
    })


# ------------------------------------------------------------------ cases
@api.post("/cases")
@require_auth("applicant", "reviewer", "admin")
def create_case():  # type: ignore[no-untyped-def]
    return jsonify(case_svc.create_case(svc(), current_user(), body())), 201


@api.get("/cases")
@require_auth()
def list_cases():  # type: ignore[no-untyped-def]
    return jsonify(case_svc.list_cases(
        svc(), current_user(), request.args.get("status"), (request.args.get("q") or "").strip()[:100] or None,
        _int("page", 1, 1, 10_000), _int("page_size", 20, 1, 100), request.args.get("sort", "priority"),
    ))


@api.get("/cases/<case_id>")
@require_auth()
def get_case(case_id: str):  # type: ignore[no-untyped-def]
    return jsonify(case_svc.case_detail(svc(), case_id, current_user()))


@api.post("/cases/<case_id>/documents")
@require_auth()
@rate_limit("upload", 30)
def upload(case_id: str):  # type: ignore[no-untyped-def]
    f = request.files.get("file")
    if f is None:
        raise bad_request("Attach a file in the 'file' field.")
    data = f.read(svc().settings.max_upload_bytes + 1)
    result = case_svc.upload_document(svc(), current_user(), case_id, (request.form.get("doc_type") or "").strip(), f.filename or "document", data)
    return jsonify(result), 201


@api.post("/cases/<case_id>/process")
@require_auth()
def process(case_id: str):  # type: ignore[no-untyped-def]
    user = current_user()
    case = case_svc.load_case(svc(), case_id, user)
    # allowed_actions does not include "process" when the case is already
    # "processing", so we no longer need a special carve-out for that state.
    if "process" not in case_svc.allowed_actions(case, user):
        raise ApiError(409 if user["role"] != "applicant" else 403, "INVALID_STATE" if user["role"] != "applicant" else "FORBIDDEN",
                       f"Checks cannot be run while the case is '{case['status']}'.")
    return jsonify(start_processing(svc(), user, case_id, force=bool(body().get("force", False)))), 202


@api.get("/jobs/<job_id>")
@require_auth()
def job(job_id: str):  # type: ignore[no-untyped-def]
    j = svc().db.one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if j is None:
        raise ApiError(404, "NOT_FOUND", "Job was not found.")
    case_svc.load_case(svc(), j["case_id"], current_user())
    return jsonify(case_svc.serialize_job(j))


@api.get("/documents/<doc_id>/file")
@require_auth()
def document_file(doc_id: str):  # type: ignore[no-untyped-def]
    d = case_svc.document_for_user(svc(), current_user(), doc_id)
    data = svc().storage.get(d["storage_key"])
    return Response(data, mimetype=d["mime_type"], headers={"Content-Disposition": f'inline; filename="{d["original_name"]}"', "Cache-Control": "private, no-store"})


@api.get("/documents/<doc_id>/pages/<int:page>/image")
@require_auth()
def page_image(doc_id: str, page: int):  # type: ignore[no-untyped-def]
    return Response(case_svc.page_image(svc(), current_user(), doc_id, page), mimetype="image/png", headers={"Cache-Control": "private, max-age=300"})


@api.patch("/fields/<field_id>")
@require_auth("reviewer", "admin")
def correct_field(field_id: str):  # type: ignore[no-untyped-def]
    return jsonify(case_svc.correct_field(svc(), current_user(), field_id, body()))


@api.patch("/findings/<finding_id>")
@require_auth("reviewer", "admin")
def update_finding(finding_id: str):  # type: ignore[no-untyped-def]
    return jsonify(case_svc.update_finding(svc(), current_user(), finding_id, body()))


@api.post("/cases/<case_id>/decisions")
@rate_limit("cases_decide", 20)
@require_auth("reviewer", "admin")
def decide(case_id: str):  # type: ignore[no-untyped-def]
    return jsonify(case_svc.decide(svc(), current_user(), case_id, body())), 201


@api.post("/cases/<case_id>/reopen")
@require_auth("admin")
def reopen(case_id: str):  # type: ignore[no-untyped-def]
    return jsonify(case_svc.reopen(svc(), current_user(), case_id, body()))


@api.get("/cases/<case_id>/audit")
@require_auth("reviewer", "admin")
def audit_log(case_id: str):  # type: ignore[no-untyped-def]
    case = case_svc.load_case(svc(), case_id, current_user())
    page, size = _int("page", 1, 1, 10_000), _int("page_size", 50, 1, 200)
    return jsonify({"items": list_events(svc().db, case["id"], size, (page - 1) * size), "page": page})


@api.get("/cases/<case_id>/audit/merkle")
@require_auth("reviewer", "admin")
def audit_merkle(case_id: str):  # type: ignore[no-untyped-def]
    case = case_svc.load_case(svc(), case_id, current_user())
    return jsonify(compute_merkle_root(svc().db, case["id"]))


@api.get("/cases/<case_id>/audit/verify")
@require_auth("reviewer", "admin")
def audit_verify(case_id: str):  # type: ignore[no-untyped-def]
    case = case_svc.load_case(svc(), case_id, current_user())
    return jsonify(verify_audit_chain(svc().db, case["id"]))


@api.get("/cases/<case_id>/report")
@require_auth()
def report(case_id: str):  # type: ignore[no-untyped-def]
    rep = reports.build_report(svc(), current_user(), case_id)
    if request.args.get("format", "json") == "pdf":
        name = f"{rep['case']['case_ref']}-report.pdf"
        return Response(reports.render_pdf(rep), mimetype="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})
    return jsonify(rep)


@api.get("/analytics")
@require_auth("reviewer", "admin")
def analytics():  # type: ignore[no-untyped-def]
    return jsonify(analytics_svc.get_analytics_summary(svc()))


# ------------------------------------------------------------------ digilocker dpi
@api.get("/integrations/digilocker/certificates")
@require_auth("reviewer", "admin")
def digilocker_certificates():  # type: ignore[no-untyped-def]
    if not svc().settings.digilocker_sandbox:
        raise not_found("DigiLocker sandbox integration is disabled")
    return jsonify(digilocker_svc.list_sandbox_certificates())


@api.post("/cases/<case_id>/digilocker/pull")
@require_auth("reviewer", "admin")
@rate_limit("digilocker_pull", 30)
def digilocker_pull(case_id: str):  # type: ignore[no-untyped-def]
    if not svc().settings.digilocker_sandbox:
        raise not_found("DigiLocker sandbox integration is disabled")
    b = body()
    doc_type = str(b.get("doc_type") or "").strip()
    cert_num = str(b.get("certificate_number") or "").strip() or None
    if not doc_type:
        raise bad_request("Provide 'doc_type' to pull from DigiLocker.")
    return jsonify(digilocker_svc.pull_document_from_digilocker(svc(), current_user(), case_id, doc_type, cert_num)), 201


# ------------------------------------------------------------------ health
health = Blueprint("health", __name__)


@health.get("/healthz")
def healthz():  # type: ignore[no-untyped-def]
    return jsonify({"status": "ok"})


@health.get("/readyz")
def readyz():  # type: ignore[no-untyped-def]
    s = svc()
    s.db.scalar("SELECT 1")
    return jsonify({"status": "ready"})
