-- VeriScope initial schema. Portable to PostgreSQL (TEXT uuid keys, ISO-8601 UTC timestamps).
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('applicant','reviewer','admin')),
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE rulesets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    checksum TEXT NOT NULL,
    source_note TEXT,
    effective_date TEXT,
    is_provisional INTEGER NOT NULL DEFAULT 1,
    loaded_at TEXT NOT NULL,
    UNIQUE (name, version)
);

CREATE TABLE cases (
    id TEXT PRIMARY KEY,
    case_ref TEXT NOT NULL UNIQUE,
    application_type TEXT NOT NULL,
    applicant_ref TEXT NOT NULL,
    institution_ref TEXT NOT NULL,
    applicant_user_id TEXT REFERENCES users(id),
    status TEXT NOT NULL CHECK (status IN ('received','processing','needs_review','clarification_requested','approved','rejected','processing_failed')),
    assigned_reviewer_id TEXT REFERENCES users(id),
    triage_priority INTEGER NOT NULL DEFAULT 0,
    triage_components_json TEXT,
    rule_set_version TEXT,
    summary_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX ix_cases_status ON cases(status);
CREATE INDEX ix_cases_applicant ON cases(applicant_user_id);

CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    doc_type TEXT NOT NULL,
    original_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    uploaded_by TEXT REFERENCES users(id),
    page_count INTEGER NOT NULL DEFAULT 0,
    processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending','processing','processed','failed')),
    processing_error TEXT,
    trust_label TEXT NOT NULL DEFAULT 'NOT_VERIFIED' CHECK (trust_label IN ('ISSUER_VERIFIED','ANOMALY_DETECTED','NOT_VERIFIED')),
    issuer_check_json TEXT,
    signals_json TEXT
);
CREATE INDEX ix_documents_case ON documents(case_id);
CREATE INDEX ix_documents_sha ON documents(sha256);

CREATE TABLE pages (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    page_number INTEGER NOT NULL,
    width REAL NOT NULL,
    height REAL NOT NULL,
    text_source TEXT NOT NULL,
    mean_confidence REAL,
    words_json TEXT NOT NULL,
    UNIQUE (document_id, page_number)
);

CREATE TABLE extracted_fields (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    document_id TEXT NOT NULL REFERENCES documents(id),
    field_key TEXT NOT NULL,
    raw_value TEXT,
    normalized_value TEXT,
    confidence REAL NOT NULL,
    page_number INTEGER,
    evidence_excerpt TEXT,
    bbox_json TEXT,
    source TEXT NOT NULL CHECK (source IN ('pdf_text','ocr','visual','llm_suggestion')),
    corrected_value TEXT,
    corrected_by TEXT REFERENCES users(id),
    corrected_at TEXT,
    correction_reason TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX ix_fields_case ON extracted_fields(case_id);
CREATE INDEX ix_fields_doc ON extracted_fields(document_id);

CREATE TABLE findings (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    fingerprint TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('completeness','consistency','compliance','document_signal','issuer_check')),
    severity TEXT NOT NULL CHECK (severity IN ('info','low','medium','high')),
    status TEXT NOT NULL CHECK (status IN ('open','resolved','waived')),
    trust_label TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    next_action TEXT,
    resolution_note TEXT,
    resolved_by TEXT REFERENCES users(id),
    resolved_at TEXT,
    is_current INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (case_id, fingerprint)
);
CREATE INDEX ix_findings_case ON findings(case_id);

CREATE TABLE decisions (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    reviewer_id TEXT NOT NULL REFERENCES users(id),
    outcome TEXT NOT NULL CHECK (outcome IN ('approve','request_clarification','reject')),
    reason_code TEXT,
    note TEXT,
    findings_snapshot_json TEXT NOT NULL,
    decided_at TEXT NOT NULL
);

CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    kind TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed')),
    progress INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);

CREATE TABLE audit_events (
    id TEXT PRIMARY KEY,
    case_id TEXT REFERENCES cases(id),
    actor_ref TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX ix_audit_case ON audit_events(case_id, created_at);

-- Audit log is append-only.
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
