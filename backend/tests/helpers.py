from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from app import create_app
from app.core.config import Settings
from scripts.seed import DEMO_PASSWORD, ensure_users

try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

os.environ.setdefault("APP_ENV", "test")
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
EXPECTED = json.loads((FIXTURES / "expected_results.json").read_text())


class AppTestCase(unittest.TestCase):
    """Fresh app + database per test class; jobs run synchronously."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="vs-test-"))
        settings = Settings(app_env="test", secret_key="veriscope-test-secret-at-least-32-bytes-long", database_path=cls.tmp / "t.db", storage_path=cls.tmp / "files",
                            sync_jobs=True, frontend_dist=None, log_level="WARNING")
        cls.app = create_app(settings)
        cls.svc = cls.app.extensions["veriscope"]
        cls.users = ensure_users(cls.svc)
        cls.client = cls.app.test_client()
        cls.tokens = {role: cls.login(f"{role}@demo.local") for role in ("applicant", "reviewer", "admin")}

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def login(cls, email: str, password: str = DEMO_PASSWORD) -> str:
        r = cls.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.get_json()
        return r.get_json()["access_token"]  # type: ignore[no-any-return]

    def h(self, role: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.tokens[role]}"}

    def new_case(self, role: str = "applicant", applicant: str = "Test Applicant") -> dict[str, Any]:
        r = self.client.post("/api/v1/cases", json={"applicant_ref": applicant, "institution_ref": "Northstar Technical Institute"}, headers=self.h(role))
        self.assertEqual(r.status_code, 201, r.get_json())
        return r.get_json()  # type: ignore[no-any-return]

    def upload(self, case_id: str, path: Path, doc_type: str, role: str = "applicant", name: str | None = None):  # type: ignore[no-untyped-def]
        with path.open("rb") as fh:
            return self.client.post(f"/api/v1/cases/{case_id}/documents", data={"doc_type": doc_type, "file": (fh, name or path.name)},
                                    headers=self.h(role), content_type="multipart/form-data")

    def upload_fixture_case(self, ref: str, role: str = "applicant") -> str:
        spec = EXPECTED[ref]
        case = self.new_case(role, spec["applicant"])
        for doc_type, fname in spec["files"].items():
            r = self.upload(case["id"], FIXTURES / "cases" / ref / fname, doc_type, role)
            self.assertEqual(r.status_code, 201, r.get_json())
        return case["id"]  # type: ignore[no-any-return]

    def process(self, case_id: str, role: str = "reviewer"):  # type: ignore[no-untyped-def]
        return self.client.post(f"/api/v1/cases/{case_id}/process", json={}, headers=self.h(role))

    def detail(self, case_id: str, role: str = "reviewer") -> dict[str, Any]:
        r = self.client.get(f"/api/v1/cases/{case_id}", headers=self.h(role))
        self.assertEqual(r.status_code, 200, r.get_json())
        return r.get_json()  # type: ignore[no-any-return]
