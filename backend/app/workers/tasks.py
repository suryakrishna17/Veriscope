"""Distributed asynchronous task definitions for Celery worker."""
from __future__ import annotations

import logging

from .celery_app import celery_app

log = logging.getLogger("veriscope.tasks")


def get_task_decorator():  # type: ignore[no-untyped-def]
    if celery_app is not None:
        return celery_app.task(bind=True, name="veriscope.process_case")
    return lambda fn: fn


@get_task_decorator()
def process_case_task(self=None, job_id: str = "", case_id: str = "", force: bool = False):  # type: ignore[no-untyped-def]
    """Asynchronous worker task that executes multi-tier OCR and statutory rule evaluation."""
    from .. import create_app
    from ..services.processing import run_job

    app = create_app()
    with app.app_context():
        svc = app.extensions["veriscope"]
        log.info("Starting distributed celery processing", extra={"job_id": job_id, "case_id": case_id})
        run_job(svc, job_id, case_id, force)
    return {"job_id": job_id, "case_id": case_id, "status": "completed"}
