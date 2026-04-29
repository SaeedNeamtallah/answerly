# Research: Production Security Fixes

**Date**: 2026-04-29  
**Branch**: `002-production-security-fixes`

## R1: Startup Secret Validation — Best Practices

**Decision**: Add a `validate_production_secrets()` function in `backend/config.py`, called at module-import time when `ENVIRONMENT=production`.

**Rationale**: Pydantic `Field(default=...)` happily accepts weak values. The app should crash before accepting traffic if secrets are known-weak. This is the standard FastAPI/Django/Rails pattern: fail fast.

**Alternatives considered**:
- Pydantic custom validators — rejected because the check needs to see multiple fields and halt the process, not just raise a validation error on one field.
- Docker entrypoint script check — rejected; too easy to bypass and doesn't protect non-Docker runs.

**Key findings**:
- `AUTH_JWT_SECRET_KEY` default is `"change-me-in-env"` (line 127 of `backend/config.py`).
- `AUTH_ADMIN_PASSWORD` default is `"admin123"` (line 131).
- `BOT_TOKEN_ENCRYPTION_KEY` default is `""` (line 234).
- No `ENVIRONMENT` variable exists yet; add one with default `"development"`.

---

## R2: Transactional Outbox for Telegram — Pattern Evaluation

**Decision**: Add a `delivery_status` column to `ConversationMessage` and a `TelegramOutboxWorker` Celery task that polls `pending` bot messages.

**Rationale**: The current `telegram_webhook_service.py` flow (lines 198-218) sends the Telegram reply _before_ committing the DB transaction. If the commit fails or the process crashes after send, the message is lost from DB but delivered to the user. Telegram may re-deliver the webhook, causing a duplicate reply.

**Alternatives considered**:
- Separate outbox table — rejected for this project size; adding columns to `ConversationMessage` is simpler and avoids a new migration for a new table.
- Redis stream outbox — rejected; adds a dependency and doesn't guarantee durability.

**Key findings**:
- `ConversationMessage` already has `telegram_message_id` (line 310 of models.py), which serves as the delivery receipt.
- Idempotency is partially covered by unique index `ix_conversation_messages_update_unique` on `(bot_integration_id, telegram_update_id)`.
- The outbox pattern needs: (1) save bot reply as `pending`, (2) commit, (3) return 200 to Telegram, (4) worker picks up pending, (5) sends via API, (6) updates to `sent` with `telegram_message_id`.

---

## R3: Security Simulation Safety — Current State

**Decision**: Change `escalate_to_block` default from `True` to `False` in both the route query parameter and the service method. Add a `SECURITY_SIMULATION_DESTRUCTIVE_ENABLED` setting defaulting to `False`. Require `platform_owner` role for destructive simulation.

**Rationale**: Line 233 of `backend/routes/security.py` shows `escalate_to_block: bool = Query(default=True)` — a destructive default. Line 205 of the service confirms `escalate_to_block: bool = True`. The `require_security_center_access` dependency is necessary but not sufficient; it allows `cybersecurity_engineer` users, not just platform owners.

**Key findings**:
- `simulate_attack_with_user_control` calls `self._incident_management_service.block_user()` which performs a real DB block.
- No `SECURITY_SIMULATION_ENABLED` setting exists.
- The route auto-targets another ACTIVE user if `target_user_id` is omitted.

---

## R4: Frontend Token Storage — HttpOnly Cookie Migration

**Decision**: Implement a dual-mode auth flow. The backend `/auth/login` sets an `HttpOnly` cookie. The frontend stops using `localStorage.setItem("access_token", ...)`. Bearer token header is still accepted for API clients (Telegram bot, `test_all.py`).

**Rationale**: 45+ `innerHTML` calls found in `frontend/app.js`, many using `escapeHtml()` but the sheer count creates risk. Moving the token out of JS-accessible storage eliminates account-takeover via XSS.

**Alternatives considered**:
- CSP-only mitigation — insufficient; CSP reduces XSS but doesn't eliminate it with inline event handlers present.
- Memory-only token (JS variable) — better than `localStorage` but still XSS-accessible and lost on refresh.

**Key findings**:
- `localStorage.getItem(ACCESS_TOKEN_KEY)` is used at line 632 of `app.js`.
- Login stores token at line 383 of `login.html`.
- Backend currently returns `{"access_token": ..., "token_type": "bearer"}` from `/auth/login`.
- Need to add `Set-Cookie` header and a `GET /auth/me` that reads from cookie.

---

## R5: Runtime Config Concurrency — File Locking

**Decision**: For now, implement atomic write (write to temp file → `os.replace`) with an `fcntl`/`msvcrt` file lock. DB migration is deferred to a future feature.

**Rationale**: `backend/runtime_config.py` (lines 38-45) writes directly to the config file with no locking. `update_runtime_config` does read-modify-write without atomicity. Two concurrent requests can corrupt the file.

**Alternatives considered**:
- Move to DB table immediately — ideal but scope-heavy for this fix round; deferred.
- Redis-backed config — adds dependency; the file-based approach is used by all three processes (backend, worker, telegram bot).

---

## R6: Token Budget for RAG Context — Approach

**Decision**: Add a `CONTEXT_TOKEN_BUDGET` setting (default: 6000 tokens). In `AnswerService._build_context()`, track cumulative token count and stop adding chunks when budget is reached.

**Rationale**: `answer_service.py` line 58 sets `max_tokens=25000` but context can grow unboundedly. Parent-child strategy duplicates parent text across children. While `_build_context` deduplicates parents by `(asset_id, parent_index)`, no total limit exists.

**Key findings**:
- `_build_context` at line 82 iterates all chunks with no token cap.
- Parent deduplication exists (seen_parents set) but content size is unchecked.
- Need a simple `tiktoken` or char-based estimator (4 chars ≈ 1 token) to cap.

---

## R7: GET /config/providers Auth — Current State

**Decision**: Add `get_current_db_user` dependency to `GET /config/providers`.

**Rationale**: Line 96-97 of `backend/routes/app_config.py` shows `GET /config/providers` has no auth dependency. It exposes available LLM/embedding/vector provider names and all retrieval configuration values. While not catastrophic, it leaks internal stack choices to unauthenticated users.

---

## R8: Health Endpoint Separation — Liveness vs Readiness

**Decision**: Add a lightweight `/health/live` endpoint that returns `{"status": "alive"}` with no external dependencies checked.

**Rationale**: `/health` already serves as a fast readiness probe (skips deep checks). `/health/full` is deep diagnostics. But neither is a true liveness probe — both hit the database. Container orchestrators need a `/health/live` that answers instantly even when DB is down.

---

## R9: Structured Logging — Approach

**Decision**: Configure Python `logging` with `python-json-logger` and add a `RequestIdMiddleware` that generates/propagates `X-Request-ID`.

**Rationale**: Current logging uses plain text with f-strings. No correlation ID exists to trace a request across backend logs, Celery tasks, and Telegram webhook processing.

---

## R10: DocumentController Dual Path — Cleanup

**Decision**: Remove the inline processing implementation from `DocumentController._process_document_impl()` and make `process_document()` a thin wrapper that raises `NotImplementedError` or delegates to the Celery task path.

**Rationale**: Lines 127-305 of `document_controller.py` contain a full processing pipeline (extract → chunk → embed → vector store) that duplicates the Celery task path in `backend/tasks/file_processing.py`. The controller path lacks the safety mechanisms (old chunk preservation, parent workflow reconciliation) that the task path has.
