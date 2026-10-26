-- Migration 005: Add security columns to users table
ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TEXT;
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;
