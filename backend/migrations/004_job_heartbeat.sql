-- Migration 004: Job heartbeat tracking for stale recovery
ALTER TABLE jobs ADD COLUMN heartbeat_at TEXT;
CREATE INDEX IF NOT EXISTS ix_jobs_heartbeat ON jobs(status, heartbeat_at);
