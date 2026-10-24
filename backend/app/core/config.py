"""Environment-driven settings. All configuration enters the app through here."""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = "dev"
    secret_key: str = "dev-only-change-me"
    database_path: Path = BACKEND_ROOT / "var" / "veriscope.db"
    storage_path: Path = BACKEND_ROOT / "var" / "storage"
    max_upload_mb: int = 10
    max_pages: int = 20
    ocr_enabled: bool = True
    ocr_lang: str = "eng"
    tesseract_cmd: str = ""
    llm_provider: str = "none"  # none | mock | openai_compatible | anthropic
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_s: int = 20
    issuer_verifier: str = "null"  # null | mock
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    log_level: str = "INFO"
    sync_jobs: bool = False
    jwt_ttl_minutes: int = 480
    ruleset_file: str = "student_support_lite.v1.yaml"
    frontend_dist: Path | None = BACKEND_ROOT.parent / "frontend" / "dist"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @classmethod
    def from_env(cls, **overrides: object) -> Settings:
        env = os.environ
        s = cls(
            app_env=env.get("APP_ENV", cls.app_env),
            secret_key=env.get("SECRET_KEY", cls.secret_key),
            database_path=Path(env.get("DATABASE_PATH", str(cls.database_path))),
            storage_path=Path(env.get("STORAGE_PATH", str(cls.storage_path))),
            max_upload_mb=int(env.get("MAX_UPLOAD_MB", cls.max_upload_mb)),
            max_pages=int(env.get("MAX_PAGES", cls.max_pages)),
            ocr_enabled=_bool(env.get("OCR_ENABLED"), True),
            ocr_lang=env.get("OCR_LANG", cls.ocr_lang),
            tesseract_cmd=env.get("TESSERACT_CMD", ""),
            llm_provider=env.get("LLM_PROVIDER", cls.llm_provider).lower(),
            llm_api_key=env.get("LLM_API_KEY", ""),
            llm_model=env.get("LLM_MODEL", ""),
            llm_base_url=env.get("LLM_BASE_URL", cls.llm_base_url),
            issuer_verifier=env.get("ISSUER_VERIFIER", cls.issuer_verifier).lower(),
            cors_origins=tuple(
                o.strip() for o in env.get("CORS_ORIGINS", ",".join(cls.cors_origins)).split(",") if o.strip()
            ),
            log_level=env.get("LOG_LEVEL", cls.log_level),
            sync_jobs=_bool(env.get("SYNC_JOBS"), False),
            jwt_ttl_minutes=int(env.get("JWT_TTL_MINUTES", cls.jwt_ttl_minutes)),
            frontend_dist=Path(env["FRONTEND_DIST"]) if env.get("FRONTEND_DIST") else cls.frontend_dist,
        )
        if overrides:
            s = replace(s, **overrides)  # type: ignore[arg-type]
        if s.app_env not in {"dev", "test"} and s.secret_key == cls.secret_key:
            raise RuntimeError(
                "SECRET_KEY must be changed from the default in non-dev/test environments. "
                "Set the SECRET_KEY environment variable."
            )
        return s
