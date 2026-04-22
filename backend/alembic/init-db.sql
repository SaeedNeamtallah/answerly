-- RAGMind Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table for JWT authentication
CREATE TABLE IF NOT EXISTS users (
	id SERIAL PRIMARY KEY,
	username VARCHAR(150) NOT NULL UNIQUE,
	hashed_password VARCHAR(255) NOT NULL,
	status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
	status_reason VARCHAR(255) NULL,
	status_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	suspended_until TIMESTAMPTZ NULL,
	status_changed_by VARCHAR(64) NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_status ON users(status);
CREATE INDEX IF NOT EXISTS ix_users_suspended_until ON users(suspended_until);
CREATE INDEX IF NOT EXISTS ix_users_status_changed_by ON users(status_changed_by);

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ragmind TO ragmind;
