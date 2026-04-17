-- RAGMind Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table for JWT authentication
CREATE TABLE IF NOT EXISTS users (
	id SERIAL PRIMARY KEY,
	username VARCHAR(150) NOT NULL UNIQUE,
	hashed_password VARCHAR(255) NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ragmind TO ragmind;
