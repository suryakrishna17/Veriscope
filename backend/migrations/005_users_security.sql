-- 005_users_security.sql: Token revocation, account lockout, and credential lifecycle
ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TEXT;
