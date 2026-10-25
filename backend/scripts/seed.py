"""Seed demo users and the synthetic demo cases. Idempotent: existing cases are skipped.

Run: python -m scripts.seed   (from backend/)
"""
from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

from app.container import Services, build_services
from app.core.config import Settings
from app.core.db import new_id, utcnow
from app.core.security import hash_password
from app.services import cases as case_svc
from app.services.processing import start_processing

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DEMO_PASSWORD = "demo1234"
USERS = [
    ("applicant@demo.local", "Asha Applicant", "applicant"),
    ("reviewer@demo.local", "Ravi Reviewer", "reviewer"),
    ("admin@demo.local", "Aditi Admin", "admin"),
]


def ensure_users(svc: Services) -> dict[str, dict]:
    out = {}
    for email, name, role in USERS:
        u = svc.db.one("SELECT id, email, name, role FROM users WHERE email = ?", (email,))
        if u is None:
            u = {"id": new_id(), "email": email, "name": name, "role": role}
            password = os.environ.get("ADMIN_INITIAL_PASSWORD") or os.environ.get("DEMO_PASSWORD") or DEMO_PASSWORD
            svc.db.insert("users", {**u, "password_hash": hash_password(password), "created_at": utcnow()})
        out[role] = u
    return out


def seed(svc: Services) -> list[str]:
    is_demo_authorized = os.environ.get("SEED_DEMO", "").lower() in {"1", "true", "yes"} or os.environ.get("ALLOW_DEMO_SEED", "").lower() in {"1", "true", "yes"}
    if svc.settings.app_env not in {"dev", "test"} and not is_demo_authorized:
        raise RuntimeError("seed.py is prohibited in production environments unless explicitly authorized via SEED_DEMO=true.")
    users = ensure_users(svc)
    if not (FIXTURES / "expected_results.json").exists():
        from scripts.generate_fixtures import main as gen

        gen()
    expected = json.loads((FIXTURES / "expected_results.json").read_text())
    created = []
    for ref, spec in expected.items():
        if svc.db.one("SELECT 1 FROM cases WHERE case_ref = ?", (ref,)):
            continue
        c = case_svc.create_case(svc, users["admin"], {"case_ref": ref, "applicant_ref": spec["applicant"], "institution_ref": spec["institution"],
                                                     "applicant_user_id": users["applicant"]["id"]})
        for doc_type, fname in spec["files"].items():
            data = (FIXTURES / "cases" / ref / fname).read_bytes()
            case_svc.upload_document(svc, users["applicant"], c["id"], doc_type, fname, data)
        if spec["files"]:
            start_processing(svc, users["reviewer"], c["id"])
        created.append(ref)
    return created


def main() -> None:
    settings = replace(Settings.from_env(), sync_jobs=True)
    svc = build_services(settings)
    created = seed(svc)
    print(f"Seeded users ({', '.join(e for e, _, _ in USERS)}; password '{DEMO_PASSWORD}') and cases: {', '.join(created) or 'none (already present)'}")


if __name__ == "__main__":
    main()
