"""Celery application and configuration for distributed background document processing."""
from __future__ import annotations

import os

try:
    from celery import Celery
except ImportError:
    Celery = None  # type: ignore[assignment]


def make_celery() -> Celery | None:
    if Celery is None:
        return None
    broker = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    backend = os.getenv("CELERY_RESULT_BACKEND", broker)
    app = Celery("veriscope", broker=broker, backend=backend)
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5-minute timeout per dossier
    )
    return app


celery_app = make_celery()
