-- VeriScope Production PostgreSQL Schema
-- Compatible with PostgreSQL 13+ (AWS RDS, Supabase, Neon, Docker)

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('applicant', 'reviewer', 'admin')),
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    token_version INTEGER DEFAULT 1,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TEXT
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TEXT;

-- 2. Rulesets
CREATE TABLE IF NOT EXISTS rulesets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    checksum TEXT NOT NULL,
    source_note TEXT,
    effective_date TEXT,
    is_provisional BOOLEAN NOT NULL DEFAULT TRUE,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (name, version)
);

-- 3. Cases
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    case_ref TEXT NOT NULL UNIQUE,
    application_type TEXT NOT NULL,
    applicant_ref TEXT NOT NULL,
    institution_ref TEXT NOT NULL,
    applicant_user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    status TEXT NOT NULL CHECK (status IN ('received', 'processing', 'needs_review', 'clarification_requested', 'approved', 'rejected', 'processing_failed')),
    assigned_reviewer_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    triage_priority INTEGER NOT NULL DEFAULT 0,
    triage_components_json JSONB,
    rule_set_version TEXT,
    summary_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS ix_cases_applicant ON cases(applicant_user_id);
CREATE INDEX IF NOT EXISTS ix_cases_priority ON cases(triage_priority DESC);

-- 4. Documents
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    original_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    sha256 TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    uploaded_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    page_count INTEGER NOT NULL DEFAULT 0,
    processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'processed', 'failed')),
    processing_error TEXT,
    trust_label TEXT NOT NULL DEFAULT 'NOT_VERIFIED' CHECK (trust_label IN ('ISSUER_VERIFIED', 'ANOMALY_DETECTED', 'NOT_VERIFIED')),
    issuer_check_json JSONB,
    signals_json JSONB
);
CREATE INDEX IF NOT EXISTS ix_documents_case ON documents(case_id);
CREATE INDEX IF NOT EXISTS ix_documents_sha ON documents(sha256);

-- 5. Document Pages
CREATE TABLE IF NOT EXISTS pages (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    width DOUBLE PRECISION NOT NULL,
    height DOUBLE PRECISION NOT NULL,
    text_source TEXT NOT NULL,
    mean_confidence DOUBLE PRECISION,
    words_json JSONB NOT NULL,
    UNIQUE (document_id, page_number)
);

-- 6. Extracted Fields
CREATE TABLE IF NOT EXISTS extracted_fields (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    field_key TEXT NOT NULL,
    raw_value TEXT,
    normalized_value TEXT,
    confidence DOUBLE PRECISION NOT NULL,
    page_number INTEGER,
    evidence_excerpt TEXT,
    bbox_json JSONB,
    source TEXT NOT NULL CHECK (source IN ('pdf_text', 'ocr', 'visual', 'llm_suggestion')),
    corrected_value TEXT,
    corrected_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    corrected_at TIMESTAMPTZ,
    correction_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_fields_case ON extracted_fields(case_id);
CREATE INDEX IF NOT EXISTS ix_fields_doc ON extracted_fields(document_id);

-- 7. Findings
CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('completeness', 'consistency', 'compliance', 'document_signal', 'issuer_check')),
    severity TEXT NOT NULL CHECK (severity IN ('info', 'low', 'medium', 'high')),
    status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'waived')),
    trust_label TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail TEXT NOT NULL,
    evidence_refs_json JSONB NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    next_action TEXT,
    clause_citation TEXT,
    outcome TEXT NOT NULL DEFAULT 'FAIL' CHECK (outcome IN ('PASS', 'FAIL', 'REVIEW_REQUIRED', 'NOT_APPLICABLE')),
    resolution_note TEXT,
    resolved_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    is_current INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (case_id, fingerprint)
);
CREATE INDEX IF NOT EXISTS ix_findings_case ON findings(case_id);

-- 8. Decisions
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    reviewer_id TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    outcome TEXT NOT NULL CHECK (outcome IN ('approve', 'request_clarification', 'reject')),
    reason_code TEXT,
    note TEXT,
    findings_snapshot_json JSONB NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Background Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
    progress INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    heartbeat_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_jobs_heartbeat ON jobs(status, heartbeat_at);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS heartbeat_at TIMESTAMPTZ;

-- 10. Audit Events (Append-Only)
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    case_id TEXT REFERENCES cases(id) ON DELETE SET NULL,
    actor_ref TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    payload_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    seq INTEGER DEFAULT 0,
    prev_hash TEXT DEFAULT '0000000000000000000000000000000000000000000000000000000000000000',
    event_hash TEXT DEFAULT ''
);
ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS seq INTEGER DEFAULT 0;
ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS prev_hash TEXT DEFAULT '0000000000000000000000000000000000000000000000000000000000000000';
ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS event_hash TEXT DEFAULT '';
CREATE INDEX IF NOT EXISTS ix_audit_case_seq ON audit_events(case_id, seq);
CREATE INDEX IF NOT EXISTS ix_audit_case ON audit_events(case_id, created_at);

-- 11. Incorruptible Append-Only Triggers (PL/pgSQL)
CREATE OR REPLACE FUNCTION audit_immutable_guard() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_events is an immutable append-only ledger and cannot be modified or deleted.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_no_update ON audit_events;
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION audit_immutable_guard();

DROP TRIGGER IF EXISTS audit_no_delete ON audit_events;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION audit_immutable_guard();
