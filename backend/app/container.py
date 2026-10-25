"""Dependency container: one place that wires settings to concrete adapters."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ai.adapter import LLMAdapter, build_llm
from .core.config import Settings
from .core.db import Database
from .core.security import RateLimiter
from .issuer.verifier import IssuerVerifier, build_verifier
from .rules.engine import APPLICATION_RULESETS, Ruleset, load_ruleset
from .services.jobs import JobRunner
from .storage.local import LocalStorage, StorageBackend


@dataclass
class Services:
    settings: Settings
    db: Database
    storage: StorageBackend
    ruleset: Ruleset
    llm: LLMAdapter
    issuer: IssuerVerifier
    jobs: JobRunner
    rate_limiter: RateLimiter
    _ruleset_cache: dict[str, Ruleset] = field(default_factory=dict)

    def get_ruleset(self, app_type: str | None = None) -> Ruleset:
        if not app_type or app_type not in APPLICATION_RULESETS:
            return self.ruleset
        filename = APPLICATION_RULESETS[app_type]
        if filename not in self._ruleset_cache:
            self._ruleset_cache[filename] = load_ruleset(filename)
        return self._ruleset_cache[filename]


def build_services(settings: Settings) -> Services:
    if settings.tesseract_cmd:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    db = Database(settings.database_url or settings.database_path)
    db.migrate()
    default_ruleset = load_ruleset(settings.ruleset_file)
    return Services(
        settings=settings,
        db=db,
        storage=LocalStorage(settings.storage_path),
        ruleset=default_ruleset,
        llm=build_llm(settings.llm_provider, settings.llm_base_url, settings.llm_api_key, settings.llm_model, settings.llm_timeout_s),
        issuer=build_verifier(settings.issuer_verifier),
        jobs=JobRunner(sync=settings.sync_jobs, redis_url=settings.redis_url),
        rate_limiter=RateLimiter(),
        _ruleset_cache={settings.ruleset_file: default_ruleset},
    )
