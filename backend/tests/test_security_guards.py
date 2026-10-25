"""Test deployment security guards: secret key enforcement, seed environment restrictions, and proxy fix."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Stub optional heavyweight extraction libraries if not installed in local environment
for mod_name in ("pdfplumber", "pypdfium2", "pytesseract", "pypdf", "pypdf.errors", "cv2"):
    if mod_name not in sys.modules:
        m = MagicMock()
        if mod_name == "pypdf.errors":
            m.PdfReadError = Exception
        sys.modules[mod_name] = m

from app import create_app  # noqa: E402
from app.core.config import Settings  # noqa: E402
from scripts.seed import seed  # noqa: E402


class TestSecurityGuards(unittest.TestCase):
    def test_prod_rejects_default_secret_key(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "prod", "SECRET_KEY": "dev-only-change-me"}, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                Settings.from_env()
            self.assertIn("SECRET_KEY must be changed", str(ctx.exception))

    def test_prod_rejects_short_secret_key(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "prod", "SECRET_KEY": "short-secret-under-32-chars"}, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                Settings.from_env()
            self.assertIn("at least 32 bytes", str(ctx.exception))

    def test_prod_accepts_strong_32byte_secret_key(self) -> None:
        valid_key = "a" * 32
        with patch.dict(os.environ, {"APP_ENV": "prod", "SECRET_KEY": valid_key}, clear=False):
            s = Settings.from_env()
            self.assertEqual(s.secret_key, valid_key)

    def test_seed_prohibited_in_production(self) -> None:
        mock_svc = MagicMock()
        mock_svc.settings.app_env = "prod"
        with self.assertRaises(RuntimeError) as ctx:
            seed(mock_svc)
        self.assertIn("prohibited in production", str(ctx.exception))

    def test_proxy_fix_installed_in_production(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            valid_key = "b" * 32
            s = Settings(app_env="prod", secret_key=valid_key, database_path=tmp / "test.db", storage_path=tmp / "files")
            app = create_app(s)
            self.assertEqual(app.wsgi_app.__class__.__name__, "ProxyFix")
            self.assertEqual(app.wsgi_app.x_for, 1)
            self.assertEqual(app.wsgi_app.x_proto, 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
