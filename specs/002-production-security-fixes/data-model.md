# Data Model Changes: Production Security Fixes

**Date**: 2026-04-29  
**Branch**: `002-production-security-fixes`

## New Columns

### `conversation_messages.delivery_status`

| Attribute       | Value                                              |
|-----------------|----------------------------------------------------|
| Table           | `conversation_messages`                            |
| Column          | `delivery_status`                                  |
| Type            | `String(16)`, nullable=False                       |
| Default         | `"none"`                                           |
| Server default  | `"none"`                                           |
| Index           | `ix_conversation_messages_delivery_status`         |
| Allowed values  | `none`, `pending`, `sent`, `failed`                |

**Purpose**: Enables the Transactional Outbox pattern. Bot reply messages are saved with `delivery_status = "pending"` before the DB commit. A Celery worker polls for `pending` messages and delivers them via the Telegram API, then updates the status to `sent` (with `telegram_message_id`) or `failed`.

**State transitions**:
- `none` → initial state for customer/agent/error messages that don't need outbox delivery
- `pending` → bot message saved, not yet delivered to Telegram
- `sent` → successfully delivered; `telegram_message_id` is populated
- `failed` → delivery attempted and failed after retries

### `conversation_messages.delivery_attempts`

| Attribute       | Value                                  |
|-----------------|----------------------------------------|
| Table           | `conversation_messages`                |
| Column          | `delivery_attempts`                    |
| Type            | `Integer`, nullable=False              |
| Default         | `0`                                    |
| Server default  | `"0"`                                  |

**Purpose**: Tracks how many times the outbox worker has attempted delivery. Used for retry backoff and dead-letter decisions.

---

## New Settings (backend/config.py)

| Setting                                  | Type   | Default           | Purpose                                      |
|------------------------------------------|--------|-------------------|----------------------------------------------|
| `ENVIRONMENT`                            | str    | `"development"`   | Controls fail-fast secret validation         |
| `CONTEXT_TOKEN_BUDGET`                   | int    | `6000`            | Max estimated tokens for RAG context         |
| `SECURITY_SIMULATION_DESTRUCTIVE_ENABLED`| bool   | `False`           | Gate for destructive simulation actions       |
| `TELEGRAM_OUTBOX_POLL_INTERVAL_SECONDS`  | int    | `2`               | Outbox worker polling frequency              |
| `TELEGRAM_OUTBOX_MAX_DELIVERY_ATTEMPTS`  | int    | `3`               | Max retries before marking message `failed`  |

---

## Unchanged Entities (for reference)

The following entities are **not modified** but are involved in the changes:

- **User** — referenced by simulation safety checks (role enforcement)
- **BotIntegration** — token decryption for outbox delivery
- **Conversation** — status updates happen before commit in outbox flow
- **Chunk** — parent_content deduplication is a retrieval-time optimization, no schema change needed
- **CeleryTaskExecution** — outbox worker is a new Celery beat task, tracked here

---

## Alembic Migration Notes

1. Add `delivery_status` and `delivery_attempts` columns to `conversation_messages` via new revision.
2. Backfill: all existing messages get `delivery_status = "none"`, `delivery_attempts = 0`.
3. Add index `ix_conversation_messages_delivery_status` on `(delivery_status)` filtered to `pending`.
