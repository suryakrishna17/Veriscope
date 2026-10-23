"""Background job runner with an explicit job table. Sync mode runs inline (tests, seeding)."""
from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

log = logging.getLogger("veriscope.jobs")


class JobRunner:
    def __init__(self, sync: bool = False, workers: int = 2) -> None:
        self.sync = sync
        self._pool = None if sync else ThreadPoolExecutor(max_workers=workers, thread_name_prefix="vs-job")
        self._futures: list[Future[None]] = []

    def submit(self, fn: Callable[[], None]) -> None:
        if self._pool is None:
            fn()
            return
        self._futures = [f for f in self._futures if not f.done()]
        self._futures.append(self._pool.submit(fn))

    def wait_all(self) -> None:
        for f in list(self._futures):
            f.result()
