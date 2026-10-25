"""Background job runner supporting in-process thread pools and distributed Celery workers."""
from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

log = logging.getLogger("veriscope.jobs")


class JobRunner:
    def __init__(self, sync: bool = False, workers: int = 2, redis_url: str = "") -> None:
        self.sync = sync
        self.redis_url = redis_url
        self._pool = None if sync else ThreadPoolExecutor(max_workers=workers, thread_name_prefix="vs-job")
        self._futures: list[Future[None]] = []

    @property
    def is_distributed(self) -> bool:
        return bool(self.redis_url)

    def submit(self, fn: Callable[[], None]) -> None:
        if self._pool is None:
            fn()
            return
        self._futures = [f for f in self._futures if not f.done()]
        self._futures.append(self._pool.submit(fn))

    def submit_celery(self, task_fn: Any, *args: Any, **kwargs: Any) -> bool:
        """Dispatches to distributed Celery worker if configured, returns True if queued via Celery."""
        if not self.sync and self.is_distributed:
            try:
                task_fn.delay(*args, **kwargs)
                return True
            except Exception as e:
                log.warning("celery_dispatch_failed_falling_back_to_thread", extra={"error": str(e)})
        return False

    def wait_all(self) -> None:
        for f in list(self._futures):
            f.result()
