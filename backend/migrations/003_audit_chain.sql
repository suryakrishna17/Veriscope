-- Migration 003: Tamper-evident hash-chained audit trail
ALTER TABLE audit_events ADD COLUMN seq INTEGER DEFAULT 0;
ALTER TABLE audit_events ADD COLUMN prev_hash TEXT DEFAULT '0000000000000000000000000000000000000000000000000000000000000000';
ALTER TABLE audit_events ADD COLUMN event_hash TEXT DEFAULT '';
CREATE INDEX IF NOT EXISTS ix_audit_case_seq ON audit_events(case_id, seq);
