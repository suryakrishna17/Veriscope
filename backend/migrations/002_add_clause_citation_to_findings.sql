-- Migration 002: Add clause_citation and outcome columns to findings table.
-- Required for Step 3B (AICTE EoA backend integration).
-- These columns persist the statutory citation and 4-valued outcome alongside each finding.
ALTER TABLE findings ADD COLUMN clause_citation TEXT;
ALTER TABLE findings ADD COLUMN outcome TEXT NOT NULL DEFAULT 'FAIL';
