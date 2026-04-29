# Implementation Plan: Production Security Fixes

**Branch**: `002-production-security-fixes` | **Date**: 2026-04-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-production-security-fixes/spec.md`

## Summary

This plan addresses 11 production blockers and high-priority issues identified in the security review. The fixes span five critical areas: (1) startup secret validation to prevent weak defaults in production, (2) Transactional Outbox pattern for Telegram replies to eliminate split-brain scenarios, (3) safety controls on the security simulation endpoint, (4) HttpOnly cookie-based auth to protect tokens from XSS, and (5) runtime config concurrency safety. Secondary improvements include RAG token budgeting, provider config auth, health endpoint separation, structured logging, and document controller cleanup.

## Technical Context

**Language/Version**: Python 3.11, JavaScript (vanilla)
**Primary Dependencies**: FastAPI, SQLAlchemy (async), Celery, Pydantic v2, python-jose, httpx, python-json-logger (new)
**Storage**: PostgreSQL 15 via asyncpg, pgvector, RabbitMQ (broker), Redis (result backend)
**Testing**: pytest (backend), `tools/test_all.py` smoke tests
**Target Platform**: Linux containers (Docker Compose), Windows local dev
**Project Type**: Web service (backend API) + static frontend + Telegram bot integrations
**Performance Goals**: Maintain current response times; outbox delivery adds ≤ 2s latency to Telegram replies
**Constraints**: No new external dependencies except `python-json-logger`; changes must be backward-compatible with existing API clients
**Scale/Scope**: Single-node deployment; < 100 concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is in template form (not customized). No specific gates to enforce. Proceeding with general best practices:

- [x] Changes follow existing layered architecture (routes → controllers → services → providers)
- [x] Alembic is used for schema changes (no raw DDL)
- [x] No new external services added (outbox uses existing Celery)
- [x] Backward-compatible API changes (cookie auth is additive)

## Project Structure

### Documentation (this feature)

```text
specs/002-production-security-fixes/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research decisions
├── data-model.md        # Phase 1 data model changes
├── quickstart.md        # Phase 1 verification guide
├── contracts/
│   └── api-changes.md   # Phase 1 API contract changes
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
backend/
├── config.py                           # Secret validation, new settings
├── logging_config.py                   # NEW: structured JSON logging setup
├── runtime_config.py                   # Atomic write + file locking
├── routes/
│   ├── auth.py                         # Cookie Set-Cookie, logout endpoint
│   ├── security.py                     # Simulation safety defaults
│   ├── app_config.py                   # Auth on GET /config/providers
│   └── health.py                       # New /health/live endpoint
├── security/
│   └── auth.py                         # Cookie token extraction
├── services/
│   ├── telegram_webhook_service.py     # Outbox: save pending, no inline send
│   ├── security_dashboard_service.py   # Destructive gate enforcement
│   └── answer_service.py              # Token budget in _build_context
├── tasks/
│   └── telegram_outbox.py             # NEW: outbox delivery worker
├── controllers/
│   └── document_controller.py         # Remove inline processing path
├── database/
│   └── models.py                      # delivery_status, delivery_attempts columns
└── alembic/
    └── versions/
        └── xxxx_add_delivery_status.py # NEW: migration

frontend/
├── login.html                         # Remove localStorage token storage
└── app.js                            # Cookie-based auth, remove token from localStorage
```

**Structure Decision**: All changes fit within the existing layered architecture. No new top-level directories needed. One new file (`logging_config.py`) and one new Celery task module (`telegram_outbox.py`) are the only structural additions.

## Complexity Tracking

No constitution violations to justify.
