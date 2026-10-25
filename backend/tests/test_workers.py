"""Tests for background JobRunner and Celery worker dispatch architecture."""
import unittest

from app.services.jobs import JobRunner


class WorkerArchitectureTests(unittest.TestCase):
    def test_in_process_job_runner(self) -> None:
        executed = []
        runner = JobRunner(sync=True)
        self.assertFalse(runner.is_distributed)

        runner.submit(lambda: executed.append("done"))
        self.assertEqual(executed, ["done"])

    def test_distributed_runner_flag(self) -> None:
        runner_local = JobRunner(redis_url="")
        self.assertFalse(runner_local.is_distributed)

        runner_redis = JobRunner(redis_url="redis://localhost:6379/0")
        self.assertTrue(runner_redis.is_distributed)

    def test_celery_dispatch_fallback(self) -> None:
        runner = JobRunner(sync=False, redis_url="redis://localhost:6379/0")
        # When Celery worker is unreachable or mock task fails, returns False gracefully
        dispatched = runner.submit_celery(lambda: None)
        self.assertFalse(dispatched)
