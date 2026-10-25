"""Tests for the job reaper and stale job recovery."""
from datetime import datetime, timedelta, timezone

from app.services.processing import reap_stale_jobs
from tests.helpers import AppTestCase


class TestJobReaper(AppTestCase):
    def test_stale_job_reaped_and_failed(self) -> None:
        case = self.new_case()
        case_id = case["id"]
        self.svc.db.update("cases", case_id, {"status": "processing"})

        stale_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        job_id = "job-stale-1"
        self.svc.db.insert(
            "jobs",
            {
                "id": job_id,
                "case_id": case_id,
                "kind": "process_case",
                "status": "running",
                "progress": 25,
                "created_at": stale_time,
                "started_at": stale_time,
                "heartbeat_at": stale_time,
            },
        )

        reaped = reap_stale_jobs(self.svc, timeout_seconds=120)
        self.assertIn(job_id, reaped)

        job = self.svc.db.one("SELECT * FROM jobs WHERE id = ?", (job_id,))
        self.assertIsNotNone(job)
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["error_code"], "TIMEOUT_STALE")

        case_row = self.svc.db.one("SELECT status FROM cases WHERE id = ?", (case_id,))
        self.assertEqual(case_row["status"], "processing_failed")

    def test_active_job_not_reaped(self) -> None:
        case = self.new_case()
        case_id = case["id"]
        self.svc.db.update("cases", case_id, {"status": "processing"})

        fresh_time = datetime.now(timezone.utc).isoformat()
        job_id = "job-active-1"
        self.svc.db.insert(
            "jobs",
            {
                "id": job_id,
                "case_id": case_id,
                "kind": "process_case",
                "status": "running",
                "progress": 25,
                "created_at": fresh_time,
                "started_at": fresh_time,
                "heartbeat_at": fresh_time,
            },
        )

        reaped = reap_stale_jobs(self.svc, timeout_seconds=120)
        self.assertNotIn(job_id, reaped)

        job = self.svc.db.one("SELECT status FROM jobs WHERE id = ?", (job_id,))
        self.assertEqual(job["status"], "running")
