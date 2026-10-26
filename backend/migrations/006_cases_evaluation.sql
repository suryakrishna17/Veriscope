-- Migration 006: Add last_evaluated_at to cases table
ALTER TABLE cases ADD COLUMN last_evaluated_at TEXT;
