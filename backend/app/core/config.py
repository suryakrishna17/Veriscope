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
    database_url: str = ""
    redis_url: str = ""
    storage_path: Path = BACKEND_ROOT / "var" / "storage"
    max_upload_mb: int = 10
    max_pages: int = 20
    ocr_enabled: bool = True
    ocr_lang: str = "eng"
    tesseract_cmd: str = ""
    llm_provider: str = "none"  # none | mock | openai_compatible | anthropic | groq
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_s: int = 20
    groq_api_key: str = ""
    groq_ocr_enabled: bool = False
    issuer_verifier: str = "null"  # null | mock
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "https://*.vercel.app", "*")
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
        groq_key = env.get("GROQ_API_KEY", "")
        provider = env.get("LLM_PROVIDER", cls.llm_provider).lower()
        api_key = env.get("LLM_API_KEY", "") or (groq_key if provider == "groq" else "")
        model = env.get("LLM_MODEL", "")
        base_url = env.get("LLM_BASE_URL", cls.llm_base_url)
        if provider == "groq":
            if not env.get("LLM_BASE_URL"):
                base_url = "https://api.groq.com/openai/v1"
            if not model:
                model = "qwen/qwen3.8-27b"
            if not api_key:
                api_key = groq_key

        def _resolve_repo_path(raw: str | None, default: Path) -> Path:
            if not raw:
                return default
            p = Path(raw)
            if p.is_absolute():
                return p
            parts = [pt for pt in p.parts if pt not in (".", "backend")]
            return (BACKEND_ROOT / Path(*parts)).resolve()

        s = cls(
            app_env=env.get("APP_ENV", cls.app_env),
            secret_key=env.get("SECRET_KEY", cls.secret_key),
            database_path=_resolve_repo_path(env.get("DATABASE_PATH"), cls.database_path),
            database_url=env.get("DATABASE_URL", cls.database_url),
            redis_url=env.get("REDIS_URL", env.get("CELERY_BROKER_URL", cls.redis_url)),
            storage_path=_resolve_repo_path(env.get("STORAGE_PATH"), cls.storage_path),
            max_upload_mb=int(env.get("MAX_UPLOAD_MB", cls.max_upload_mb)),
            max_pages=int(env.get("MAX_PAGES", cls.max_pages)),
            ocr_enabled=_bool(env.get("OCR_ENABLED"), True),
            ocr_lang=env.get("OCR_LANG", cls.ocr_lang),
            tesseract_cmd=env.get("TESSERACT_CMD", ""),
            llm_provider=provider,
            llm_api_key=api_key,
            llm_model=model,
            llm_base_url=base_url,
            groq_api_key=groq_key or (api_key if provider == "groq" else ""),
            groq_ocr_enabled=_bool(env.get("GROQ_OCR_ENABLED"), provider == "groq" or bool(groq_key or api_key)),
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
        if s.app_env not in {"dev", "test"}:
            if s.secret_key == cls.secret_key:
                raise RuntimeError(
                    "SECRET_KEY must be changed from the default in non-dev/test environments. "
                    "Set the SECRET_KEY environment variable."
                )
            if len(s.secret_key.encode("utf-8")) < 32:
                import hashlib
                s = replace(s, secret_key=hashlib.sha256(s.secret_key.encode("utf-8")).hexdigest())
        return s
