تمام. دي **النسخة النهائية الكاملة** الجاهزة تتحط كـ `tasks.md` أو تديها للـ coding agent. عدلتها بحيث:

* **مفيش frontend changes في الراوند ده**.
* أضفت task صريح لمشكلة **Document Processing duplicate path** وخليت المسار الرسمي هو **Celery only**.
* أضفت Secret hygiene task.
* قوّيت Telegram outbox عشان مايبعتش duplicate.
* ضفت Final Verification Phase يتأكد إن المشروع شغال قبل ما يقول Done.
* خليت التعليمات very specific عشان موديل رخيص يقدر ينفذ بدون اجتهاد كتير.

اعتمدت على `task.md` اللي رفعته وعلى خريطة المشروع/الكود الحالي اللي فيها إن backend عنده Celery document tasks وroutes/controllers/services/providers، وإن frontend tasks كانت موجودة في النسخة الأصلية لكنها مؤجلة الآن.  

انسخ ده كما هو:

````md
# Tasks: Production Security Fixes — Backend-Only Round

**Input**: Design documents from `/specs/002-production-security-fixes/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-changes.md`

---

## Critical Scope Rules

This implementation round is **backend-only**.

### Do NOT modify frontend files in this round

Do not edit:

- `frontend/app.js`
- `frontend/login.html`
- `frontend/signup.html`
- any frontend CSS files
- any frontend auth/token/localStorage behavior

Frontend auth hardening is postponed to the next round.

### Postponed tasks

Move these tasks to a future frontend-auth round:

- Cookie token extraction in auth dependencies
- Login `Set-Cookie`
- Logout endpoint
- Removing localStorage token usage
- Updating frontend requests to cookie-based auth
- Frontend monolith refactor
- Frontend CSS refactor

### Current round focuses only on

1. Secret hygiene guardrails
2. Production secret validation
3. Telegram transactional outbox for automatic webhook bot replies
4. Safe security simulation defaults
5. Atomic runtime config writes
6. Provider config GET auth
7. Lightweight liveness endpoint
8. RAG answer context token budget
9. Enforcing Celery-only document processing
10. Verification that Docker/API/Celery still work

---

## Format

`[ID] [P?] [Story] Description`

- `[P]`: Can run in parallel, different files/no direct dependency
- `[Story]`: US1–US5 maps to spec user stories
- Do not mark tasks parallel if they touch the same file

---

# Phase 0: Safety Guardrails Before Coding

## T000 — Secret hygiene guardrail

- [X] T000 [US1] Remove real secrets from repo tracking and protect future commits

### Purpose

The repo/bundle contains real-looking secrets in `.env`. This task prevents accidental secret commits and ensures only placeholder examples are committed.

### Read first

- `.gitignore`
- `.env`
- `.env.example`
- `.github/workflows/secret-scan.yml` if it exists

### Modify

- `.gitignore`
- `.env.example`
- `.github/workflows/secret-scan.yml` if missing
- Do **not** commit real `.env` values

### Search commands

```bash
rg -n "AIza|sk-or-|gsk_|csk-|TELEGRAM_BOT_TOKEN|BOT_TOKEN_ENCRYPTION_KEY|AUTH_JWT_SECRET_KEY|COHERE_API_KEY|VOYAGE_API_KEY|OPENROUTER_API_KEY|GROQ_API_KEY|CEREBRAS_API_KEY" .
git status --short
git ls-files .env
````

### Implement

1. Ensure `.env` is listed in `.gitignore`.

2. If `.env` is tracked, stop tracking it:

   ```bash
   git rm --cached .env
   ```

3. Do not delete the local developer `.env`; only ensure it is untracked.

4. Ensure `.env.example` contains placeholders only.

5. Add or verify secret scanning:

   * prefer GitHub Action with `gitleaks`, or
   * `detect-secrets` baseline.

6. Add a short README note:

   * "Never commit `.env`. Use `.env.example` as a template."

### Do not touch

* Application runtime code
* Docker Compose credentials in this task
* Real local `.env` values

### Done when

```bash
git ls-files .env
```

returns nothing.

And:

```bash
rg -n "AIza|sk-or-|gsk_|csk-|TELEGRAM_BOT_TOKEN=.*[0-9]+:" .env.example
```

does not show real secrets.

### Important manual action

The developer must rotate any real exposed API keys manually from provider dashboards. The coding agent must not print or copy secrets.

---

# Phase 1: Setup Settings

## T001 — Add new backend settings

* [X] T001 [US1] Add new settings to `backend/config.py`

### Read first

* `backend/config.py`
* `specs/002-production-security-fixes/data-model.md`

### Modify

* `backend/config.py`

### Search anchors

```bash
rg -n "auth_jwt_secret_key|bot_token_encryption_key|class Settings|model_config" backend/config.py
```

### Implement

Add these fields inside `class Settings`, before `model_config`:

```python
environment: str = Field(default="development", alias="ENVIRONMENT")
context_token_budget: int = Field(default=6000, alias="CONTEXT_TOKEN_BUDGET")
security_simulation_destructive_enabled: bool = Field(
    default=False,
    alias="SECURITY_SIMULATION_DESTRUCTIVE_ENABLED",
)
telegram_outbox_poll_interval_seconds: int = Field(
    default=2,
    alias="TELEGRAM_OUTBOX_POLL_INTERVAL_SECONDS",
)
telegram_outbox_max_delivery_attempts: int = Field(
    default=3,
    alias="TELEGRAM_OUTBOX_MAX_DELIVERY_ATTEMPTS",
)
```

### Do not touch

* Existing settings
* `model_config`
* global `settings = Settings()` instantiation

### Done when

```bash
python -c "from backend.config import settings; print(settings.environment, settings.context_token_budget)"
```

prints:

```text
development 6000
```

---

## T002 — Add production secret validation

* [X] T002 [US1] Add startup secret validation function to `backend/config.py`

### Read first

* `backend/config.py`

### Modify

* `backend/config.py`

### Search anchors

```bash
rg -n "settings = Settings|Global settings instance|class Settings" backend/config.py
```

### Implement

Add this function after `class Settings`, before global `settings = Settings()`:

```python
def _validate_production_secrets(s: Settings) -> None:
    if s.environment.lower() != "production":
        return

    reasons: list[str] = []

    jwt_secret = (s.auth_jwt_secret_key or "").strip()
    if jwt_secret == "change-me-in-env" or len(jwt_secret) < 32:
        reasons.append("AUTH_JWT_SECRET_KEY must be a strong non-default value in production")

    admin_password = (s.auth_admin_password or "").strip()
    if admin_password == "admin123":
        reasons.append("AUTH_ADMIN_PASSWORD must not use the default demo password in production")

    bot_key = (s.bot_token_encryption_key or "").strip()
    if not bot_key:
        reasons.append("BOT_TOKEN_ENCRYPTION_KEY is required in production")

    if reasons:
        raise SystemExit("FATAL production configuration error: " + "; ".join(reasons))
```

Then call it immediately after settings creation:

```python
settings = Settings()
_validate_production_secrets(settings)
```

### Do not touch

* Individual setting field definitions, except T001 additions

### Done when

This crashes:

```powershell
$env:ENVIRONMENT="production"
$env:AUTH_JWT_SECRET_KEY="change-me-in-env"
python -c "from backend.config import settings"
```

This does not crash:

```powershell
$env:ENVIRONMENT="development"
python -c "from backend.config import settings; print(settings.environment)"
```

---

## T006 — Document ENVIRONMENT in `.env.example`

* [X] T006 [US1] Update `.env.example` with `ENVIRONMENT`

### Read first

* `.env.example`

### Modify

* `.env.example`

### Search anchors

```bash
rg -n "AUTH_JWT_SECRET_KEY|Security Configuration|API Configuration" .env.example
```

### Implement

Near the top or under API/Security config, add:

```env
# ========================================
# Environment
# ========================================
# Set to "production" to enforce strict secret validation.
ENVIRONMENT=development
```

Also add placeholders for new settings:

```env
CONTEXT_TOKEN_BUDGET=6000
SECURITY_SIMULATION_DESTRUCTIVE_ENABLED=false
TELEGRAM_OUTBOX_POLL_INTERVAL_SECONDS=2
TELEGRAM_OUTBOX_MAX_DELIVERY_ATTEMPTS=3
```

### Do not touch

* Real `.env`

### Done when

```powershell
Select-String "ENVIRONMENT" .env.example
```

finds the new setting.

---

# Phase 2: Telegram Outbox Database Foundation

## T003 — Add delivery columns to ConversationMessage model

* [X] T003 [US2] Add `delivery_status` and `delivery_attempts` to `ConversationMessage`

### Read first

* `backend/database/models.py`
* `specs/002-production-security-fixes/data-model.md`

### Modify

* `backend/database/models.py`

### Search anchors

```bash
rg -n "class ConversationMessage|raw_payload_expires_at|telegram_message_id" backend/database/models.py
```

### Implement

Inside `ConversationMessage`, after `raw_payload_expires_at`, add:

```python
delivery_status = Column(
    String(16),
    nullable=False,
    default="none",
    server_default="none",
    index=True,
)
delivery_attempts = Column(
    Integer,
    nullable=False,
    default=0,
    server_default="0",
)
```

### Delivery status convention

Use these values by convention:

```text
none     = message does not require Telegram delivery
pending  = outbox message waiting to be sent
sending  = worker has claimed this message
sent     = Telegram delivery succeeded
failed   = max attempts reached or permanent failure
```

### Do not touch

* Existing relationships
* Existing indexes
* Existing table args

### Done when

```bash
python -c "from backend.database.models import ConversationMessage; print(ConversationMessage.delivery_status)"
```

works.

---

## T004 — Create Alembic migration for delivery columns

* [X] T004 [US2] Create migration `backend/alembic/versions/20260429_01_add_delivery_status.py`

### Read first

* Latest migration in `backend/alembic/versions/`
* T003 output

### Modify

* New file: `backend/alembic/versions/20260429_01_add_delivery_status.py`

### Search anchors

```bash
ls backend/alembic/versions
rg -n "revision =|down_revision =" backend/alembic/versions
```

### Implement

Create a migration like:

```python
"""add delivery status to conversation messages

Revision ID: 20260429_01
Revises: <LATEST_CURRENT_HEAD>
Create Date: 2026-04-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_01"
down_revision = "<LATEST_CURRENT_HEAD>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column("delivery_status", sa.String(length=16), nullable=False, server_default="none"),
    )
    op.add_column(
        "conversation_messages",
        sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_conversation_messages_delivery_status",
        "conversation_messages",
        ["delivery_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_delivery_status", table_name="conversation_messages")
    op.drop_column("conversation_messages", "delivery_attempts")
    op.drop_column("conversation_messages", "delivery_status")
```

Replace `<LATEST_CURRENT_HEAD>` with the current Alembic head.

### Do not touch

* Existing migration files

### Done when

```bash
docker exec ragmind-backend alembic -c backend/alembic/alembic.ini upgrade head
```

succeeds.

### Depends on

* T003

---

## T008 — Update ConversationService.save_message

* [X] T008 [US2] Update `save_message()` to accept delivery status

### Read first

* `backend/services/conversation_service.py`

### Modify

* `backend/services/conversation_service.py`

### Search anchors

```bash
rg -n "async def save_message|ConversationMessage\\(" backend/services/conversation_service.py
```

### Implement

1. Add parameter to `save_message()`:

```python
delivery_status: str = "none",
```

2. Pass it into the `ConversationMessage(...)` constructor:

```python
delivery_status=delivery_status,
```

3. Do not commit inside this method unless it already commits today. Preserve existing transaction behavior.

### Do not touch

* Other service methods
* Manual reply behavior

### Done when

```bash
rg -n "delivery_status" backend/services/conversation_service.py
```

shows parameter + model assignment.

### Depends on

* T003

---

# Phase 3: Telegram Transactional Outbox

## T007 — Change webhook success path to save pending reply instead of inline send

* [X] T007 [US2] Modify success path in `backend/services/telegram_webhook_service.py`

### Purpose

Automatic webhook bot replies must be saved durably before Telegram delivery. The webhook success path should queue the bot reply in DB with `delivery_status="pending"` and return quickly.

### Read first

* `backend/services/telegram_webhook_service.py`
* `backend/services/conversation_service.py`

### Modify

* `backend/services/telegram_webhook_service.py`

### Search anchors

```bash
rg -n "telegram_result = await self.telegram_api.send_message|await self.conversation_service.save_message|sender_type=\"bot\"" backend/services/telegram_webhook_service.py
```

### Implement

In the normal successful customer webhook flow:

1. Remove inline call to:

```python
self.telegram_api.send_message(...)
```

from the success path.

2. Save the bot answer message using `conversation_service.save_message(...)` with:

```python
sender_type="bot"
delivery_status="pending"
telegram_message_id=None
```

3. Commit the DB transaction after saving the pending bot message.
4. Return the existing success shape, for example:

```python
{"ok": True, "conversation_id": conversation.id}
```

Keep exact existing response fields if currently different.

### Do not touch

* Message parsing
* Token validation
* Throttling
* Telegram update idempotency
* Customer inbound message saving
* `_handle_failure()` in this task

### Done when

```bash
rg -n "send_message" backend/services/telegram_webhook_service.py
```

does not show Telegram send in the normal success path.

### Depends on

* T003
* T004
* T008

---

## T007B — Convert webhook fallback/error replies to outbox too

* [X] T007B [US2] Convert `_handle_failure()` fallback reply to outbox

### Problem

`_handle_failure()` must not send Telegram inline. Fallback bot replies should also be saved as pending outbox messages.

### Read first

* `backend/services/telegram_webhook_service.py`
* `backend/services/conversation_service.py`

### Modify

* `backend/services/telegram_webhook_service.py`

### Search anchors

```bash
rg -n "_handle_failure|telegram_api.send_message|sender_type=\"error\"|sender_type=\"bot\"" backend/services/telegram_webhook_service.py
```

### Implement

Inside `_handle_failure()`:

1. Remove inline call to:

```python
self.telegram_api.send_message(...)
```

2. Save internal error message with:

```python
sender_type="error"
delivery_status="none"
```

3. Save customer-visible fallback message with:

```python
sender_type="bot"
text=fallback
delivery_status="pending"
telegram_message_id=None
```

4. Commit once after saving both messages.
5. Preserve current return shape, for example:

```python
{"ok": True, "conversation_id": conversation.id, "fallback": True}
```

### Do not touch

* Integration status logic
* `last_error`
* human handoff logic
* throttling/idempotency

### Done when

```bash
rg -n "_handle_failure|send_message|delivery_status=\"pending\"" backend/services/telegram_webhook_service.py
```

shows no inline Telegram send inside `_handle_failure()`.

### Depends on

* T008

---

## T009 — Create robust outbox worker

* [X] T009 [US2] Create `backend/tasks/telegram_outbox.py`

### Purpose

A Celery task must deliver pending Telegram outbox messages asynchronously and safely.

### Read first

* `backend/tasks/maintenance.py`
* `backend/tasks/data_indexing.py`
* `backend/celery_app.py`
* `backend/database/connection.py`
* `backend/database/models.py`
* `backend/services/telegram_api_service.py`
* `backend/services/token_crypto_service.py`

### Modify

* New file: `backend/tasks/telegram_outbox.py`

### Search anchors

```bash
rg -n "clean_celery_executions_table|asyncio.run|get_setup_utils" backend/tasks backend/celery_app.py
rg -n "class ConversationMessage|class BotIntegration|class TelegramCustomer" backend/database/models.py
rg -n "def send_message|async def send_message" backend/services/telegram_api_service.py
rg -n "decrypt_token" backend/services/token_crypto_service.py
```

### Implement

Create Celery task:

```python
@celery_app.task(
    bind=True,
    name="backend.tasks.telegram_outbox.deliver_pending_messages",
    queue="default",
)
def deliver_pending_messages(self):
    return asyncio.run(_deliver_pending_messages())
```

Implementation details:

1. Follow existing task setup pattern from `maintenance.py` or other async task files.
2. Open DB session using existing project utility pattern.
3. Select up to 50 messages where:

   * `ConversationMessage.delivery_status == "pending"`
   * `ConversationMessage.delivery_attempts < settings.telegram_outbox_max_delivery_attempts`
4. Order by:

   * `ConversationMessage.created_at.asc()`
5. For each message:

   * Claim it before external API call:

     * set `delivery_status="sending"`
     * increment `delivery_attempts += 1`
     * commit
   * Load `BotIntegration` using `message.bot_integration_id`
   * Load `TelegramCustomer` using `message.telegram_customer_id`
   * Decrypt `BotIntegration.token_encrypted`
   * Get chat id from `TelegramCustomer.chat_id`
   * Send via `TelegramAPIService.send_message(token, chat_id, message.text)`
6. On success:

   * set `delivery_status="sent"`
   * set `telegram_message_id=str(result.get("message_id"))`
   * commit
7. On failure:

   * if `delivery_attempts >= max`:

     * set `delivery_status="failed"`
   * else:

     * set `delivery_status="pending"`
   * commit
8. Invalid rows should not crash the batch:

   * missing integration
   * missing customer
   * missing chat id
   * missing encrypted token
   * empty text
     Mark such rows as `failed`.

Return summary:

```python
{
    "status": "success",
    "claimed": claimed_count,
    "sent": sent_count,
    "failed": failed_count,
    "retried": retried_count,
}
```

### Important duplicate-delivery rule

The worker must mark a row as `sending` and commit before calling Telegram. This reduces duplicate sends if multiple workers run.

### Do not touch

* `backend/services/telegram_api_service.py`
* `backend/services/token_crypto_service.py`
* webhook parsing/idempotency
* frontend files

### Done when

```bash
python -c "from backend.tasks.telegram_outbox import deliver_pending_messages; print(deliver_pending_messages.name)"
rg -n "delivery_status.*sending|telegram_outbox_max_delivery_attempts|send_message" backend/tasks/telegram_outbox.py
```

both work.

### Depends on

* T003
* T008

---

## T010 — Register Telegram outbox task in Celery

* [X] T010 [US2] Register outbox task in `backend/celery_app.py`

### Read first

* `backend/celery_app.py`

### Modify

* `backend/celery_app.py`

### Search anchors

```bash
rg -n "include=|task_routes|beat_schedule|clean_celery_executions_table" backend/celery_app.py
```

### Implement

1. Add to Celery include list:

```python
"backend.tasks.telegram_outbox"
```

2. Add to `task_routes`:

```python
"backend.tasks.telegram_outbox.deliver_pending_messages": {"queue": "default"}
```

3. Add to beat schedule:

```python
"deliver-pending-telegram-messages": {
    "task": "backend.tasks.telegram_outbox.deliver_pending_messages",
    "schedule": settings.telegram_outbox_poll_interval_seconds,
    "args": (),
}
```

### Do not touch

* Existing task routes
* Existing beat entries

### Done when

```bash
python -c "from backend.celery_app import celery_app; print(celery_app.conf.beat_schedule)"
```

shows `deliver-pending-telegram-messages`.

### Depends on

* T009

---

# Phase 4: Enforce Celery-Only Document Processing

## T010A — Enforce Celery-only document processing path

* [X] T010A [US2] Disable/deprecate direct controller document processing

### Purpose

The project currently has two possible document-processing paths:

1. Official async Celery path:

   * `backend/routes/documents.py`
   * `backend/tasks/file_processing.py::process_document_task`
   * `backend/tasks/process_workflow.py::process_and_index_workflow`

2. Legacy/direct controller path:

   * `backend/controllers/document_controller.py::process_document`
   * `backend/controllers/document_controller.py::_process_document_impl`

The official path must be Celery only. No API route should process documents inline through `DocumentController.process_document()`.

### Read first

* `backend/routes/documents.py`
* `backend/controllers/document_controller.py`
* `backend/tasks/file_processing.py`
* `backend/tasks/process_workflow.py`
* `AGENTS.md`

### Search commands

```bash
rg -n "process_document\\(|_process_document_impl|process_document_task|process_and_index_workflow" backend
rg -n "document_controller\\.process_document|_process_document_impl" backend/routes backend/controllers backend/tasks
```

### Modify

* `backend/controllers/document_controller.py`
* `backend/routes/documents.py` only if needed
* `AGENTS.md`

### Implement

1. Confirm `backend/routes/documents.py` uses only Celery dispatch:

   * `process_document_task.delay(...)`
   * `process_and_index_workflow.apply_async(...)`

2. Confirm no route calls:

```python
document_controller.process_document(...)
```

3. In `backend/controllers/document_controller.py`, make `process_document()` a deprecated guard method:

```python
async def process_document(self, *args, **kwargs):
    raise RuntimeError(
        "Direct document processing is disabled. Use Celery process_document_task instead."
    )
```

4. Rename `_process_document_impl` to `_deprecated_process_document_impl`, or delete it if no references exist.

Before deleting, run:

```bash
rg -n "_process_document_impl|process_document\\(" backend tests
```

5. If deleting breaks tests/imports, keep the function but make it private-deprecated and unreachable from routes.
6. Update `AGENTS.md`:

   * Document processing must go through Celery tasks only.
   * Route mapping:

     * `/documents/{asset_id}/process` -> `process_document_task`
     * `/documents/{asset_id}/process-and-index` -> `process_and_index_workflow`

### Do not touch

* `backend/tasks/file_processing.py` internals
* `backend/tasks/process_workflow.py` internals
* vector cleanup logic
* task ownership tracking
* frontend files

### Done when

```bash
rg -n "document_controller\\.process_document" backend/routes
```

returns zero matches.

And:

```bash
rg -n "_process_document_impl" backend/routes backend/tasks
```

returns zero matches.

And:

```bash
rg -n "process_document_task.delay|process_and_index_workflow.apply_async" backend/routes/documents.py
```

shows Celery dispatch still exists.

---

# Phase 5: Safe Security Simulation

## T011 — Make security simulation non-destructive by default

* [X] T011 [US3] Change simulation defaults in `backend/routes/security.py`

### Read first

* `backend/routes/security.py`
* `backend/security/auth.py`
* `backend/config.py`

### Modify

* `backend/routes/security.py`

### Search anchors

```bash
rg -n "simulate_security_attack|escalate_to_block|require_security_center_access|ROLE_PLATFORM_OWNER|get_product_role_for_user" backend/routes/security.py backend/security/auth.py
```

### Implement

1. Change:

```python
escalate_to_block: bool = Query(default=True)
```

to:

```python
escalate_to_block: bool = Query(default=False)
```

2. Add imports if missing:

```python
from backend.config import settings
from backend.security.auth import get_product_role_for_user, ROLE_PLATFORM_OWNER
```

3. After resolving target user id, add:

```python
if escalate_to_block:
    if not settings.security_simulation_destructive_enabled:
        raise HTTPException(
            status_code=403,
            detail="Destructive simulation disabled by configuration",
        )
    if get_product_role_for_user(current_user) != ROLE_PLATFORM_OWNER:
        raise HTTPException(
            status_code=403,
            detail="Only platform owners can run destructive simulations",
        )
```

### Do not touch

* Other security routes
* SSE stream endpoint
* `_resolve_simulation_target_user_id`

### Done when

```bash
rg -n "escalate_to_block.*default=False|security_simulation_destructive_enabled|ROLE_PLATFORM_OWNER" backend/routes/security.py
```

finds all expected code.

---

# Phase 6: Runtime Config Safety

## T016 — Make runtime config writes atomic and locked

* [X] T016 [US5] Harden `backend/runtime_config.py` writes

### Read first

* `backend/runtime_config.py`
* `backend/shared_config_paths.py`
* any existing tests for runtime config

### Modify

* `backend/runtime_config.py`

### Search anchors

```bash
rg -n "save_runtime_config|update_runtime_config|json.dump|open\\(\"w\"|config_path.open" backend/runtime_config.py backend
```

### Implement

Add helper functions:

```python
def _lock_file_path(config_path: Path) -> Path:
    return config_path.with_suffix(config_path.suffix + ".lock")
```

Add atomic write helper:

```python
def _atomic_write_json(config_path: Path, data: dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = config_path.with_suffix(config_path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp_path, config_path)
```

Add file lock if project has a dependency already. If no dependency exists, use a simple cross-platform lock strategy only if already present in project utilities. Do not add heavy new dependency without checking requirements.

Update `save_runtime_config()` to use atomic write.

Update `update_runtime_config()` to:

1. load current config
2. merge updates
3. atomic save

### Failure rule

If atomic write or locking fails:

* log exception
* raise `RuntimeError("Runtime config write failed")`
* do **not** fall back to direct unsafe write

### Do not touch

* Config schema
* Provider config behavior
* frontend files

### Done when

```bash
rg -n "_atomic_write_json|os.replace|Runtime config write failed" backend/runtime_config.py
```

finds the implementation.

---

# Phase 7: Provider Config GET Auth

## T017 — Require auth for `GET /config/providers`

* [X] T017 [US5] Protect provider config read endpoint

### Read first

* `backend/routes/app_config.py`
* `backend/security/auth.py`

### Modify

* `backend/routes/app_config.py`

### Search anchors

```bash
rg -n "get_providers|update_providers|get_current_db_user|@router.get|@router.post" backend/routes/app_config.py
```

### Implement

1. Add `current_user` dependency to `get_providers()`:

```python
current_user: User = Depends(get_current_db_user)
```

2. Ensure `get_current_db_user` and `User` are imported if not already.
3. Do not change response format.
4. Keep `POST /config/providers` auth behavior unchanged.

### Do not touch

* runtime config update logic
* provider registry logic
* frontend files

### Done when

```bash
rg -n "def get_providers|get_current_db_user" backend/routes/app_config.py
```

shows auth dependency on GET.

---

# Phase 8: Liveness Endpoint

## T018 — Add lightweight `/health/live`

* [X] T018 [US5] Add live health endpoint

### Read first

* `backend/routes/health.py`

### Modify

* `backend/routes/health.py`

### Search anchors

```bash
rg -n "health_check|health_check_full|@router.get" backend/routes/health.py
```

### Implement

Add:

```python
@router.get("/live")
async def health_live():
    return {"status": "alive"}
```

### Purpose

* `/health/live`: process is running
* `/health`: current readiness behavior
* `/health/full`: expensive/deep diagnostics

### Do not touch

* Existing `/health`
* Existing `/health/full`

### Done when

```bash
curl http://localhost:8000/health/live
```

returns:

```json
{"status":"alive"}
```

---

# Phase 9: RAG Context Token Budget

## T019 — Add answer context token budget

* [X] T019 [US5] Limit answer context in `backend/services/answer_service.py`

### Read first

* `backend/services/answer_service.py`
* `backend/config.py`

### Modify

* `backend/services/answer_service.py`

### Search anchors

```bash
rg -n "_build_context|_build_prompt|context|sources|generate_answer" backend/services/answer_service.py
rg -n "context_token_budget" backend/config.py
```

### Implement

Inside `_build_context()` or equivalent context assembly function:

1. Import settings if not already:

```python
from backend.config import settings
```

2. Estimate tokens roughly:

```python
def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
```

3. Track cumulative token count.
4. If one chunk is larger than budget and no context has been added yet:

   * truncate to `settings.context_token_budget * 4` characters
   * append truncated content
   * break
5. If adding another chunk would exceed budget and context already has content:

   * break
6. Preserve source extraction behavior.
7. Avoid duplicate parent content if obvious duplicate text exists.

### Pseudocode

```python
budget = max(500, settings.context_token_budget)
token_count = 0
context_parts = []

for chunk in chunks:
    content = extract_content(chunk)
    estimated = _estimate_tokens(content)

    if estimated > budget and not context_parts:
        context_parts.append(content[: budget * 4])
        break

    if token_count + estimated > budget:
        break

    context_parts.append(content)
    token_count += estimated
```

### Do not touch

* LLM provider implementations
* embedding service
* vector DB search
* frontend files

### Done when

```bash
rg -n "context_token_budget|_estimate_tokens" backend/services/answer_service.py
```

finds the implementation.

---

# Phase 10: Documentation Updates

## T020 — Update `AGENTS.md`

* [X] T020 [US5] Update agent map and current rules

### Read first

* `AGENTS.md`

### Modify

* `AGENTS.md`

### Implement

Update the following sections:

1. Settings/config:

   * add `ENVIRONMENT`
   * add `CONTEXT_TOKEN_BUDGET`
   * add `SECURITY_SIMULATION_DESTRUCTIVE_ENABLED`
   * add Telegram outbox settings

2. Background tasks:

   * add `backend/tasks/telegram_outbox.py`
   * add `deliver_pending_messages()`

3. Document processing rule:

   * state clearly:

     * "Document processing must go through Celery tasks only."
   * add route mapping:

     * `/documents/{asset_id}/process` -> `process_document_task`
     * `/documents/{asset_id}/process-and-index` -> `process_and_index_workflow`

4. Telegram flow:

   * webhook saves bot replies as `delivery_status="pending"`
   * Celery outbox worker sends replies asynchronously
   * manual replies are out of scope for this round

5. Security simulation:

   * non-destructive by default
   * destructive mode requires config flag + platform owner

6. Frontend:

   * add note:

     * "Frontend auth/localStorage changes are postponed to next round. Do not modify frontend files in this round."

### Do not add

* Cookie-auth claims
* Logout endpoint docs
* Frontend migration docs

### Done when

```bash
rg -n "telegram_outbox|Celery tasks only|SECURITY_SIMULATION_DESTRUCTIVE_ENABLED|frontend.*postponed" AGENTS.md
```

finds the new documentation.

---

## T021 — Update README security notes

* [X] T021 [US5] Update README with current backend-only security round

### Read first

* `README.md`

### Modify

* `README.md`

### Implement

Add a short section:

```md
## Security / Production Configuration Notes

- Never commit `.env`; use `.env.example` as a template.
- Set `ENVIRONMENT=production` to enforce strict secret validation.
- `AUTH_JWT_SECRET_KEY` must be a strong non-default value in production.
- `BOT_TOKEN_ENCRYPTION_KEY` is required in production.
- Security simulation is non-destructive by default.
- Destructive simulation requires `SECURITY_SIMULATION_DESTRUCTIVE_ENABLED=true` and platform-owner role.
- Telegram webhook bot replies are delivered through a database-backed Celery outbox.
- Document processing must go through Celery tasks only.
- Current round keeps existing frontend Bearer-token behavior unchanged.
- Cookie-based frontend auth is planned for a later round.
```

### Do not claim

* frontend localStorage was removed
* cookie auth is already active
* logout endpoint exists

### Done when

```bash
rg -n "ENVIRONMENT=production|Celery outbox|frontend Bearer-token" README.md
```

finds the new notes.

---

# Phase 11: Tests

## T022 — Add/Update focused regression tests

* [X] T022 [US5] Add backend tests for the modified behavior

### Read first

* `tests/`
* `backend/tests/` if exists
* `pyproject.toml` or test config

### Modify

* Add tests in existing test structure
* Prefer not to create a new test framework

### Required tests

Add tests for:

1. Production secret validation:

   * production + weak JWT secret raises `SystemExit`
   * development + weak JWT secret does not raise

2. Security simulation:

   * default simulation does not block users
   * `escalate_to_block=true` fails when config flag is false
   * `escalate_to_block=true` fails for non-platform-owner
   * destructive simulation only allowed for platform owner + config enabled

3. App config:

   * `GET /config/providers` without auth returns 401/403
   * with auth succeeds

4. Health:

   * `GET /health/live` returns `{"status": "alive"}`

5. Runtime config:

   * save writes valid JSON
   * update preserves existing keys
   * failed atomic write does not silently fall back to unsafe direct write

6. Telegram outbox:

   * webhook success path creates bot message with `delivery_status="pending"`
   * `_handle_failure()` creates fallback bot message with `delivery_status="pending"`
   * outbox worker changes pending -> sent on success
   * outbox worker changes pending -> failed after max attempts
   * invalid rows do not crash the whole batch

7. Document processing:

   * route queues `process_document_task`
   * route does not call `DocumentController.process_document`
   * direct `DocumentController.process_document()` raises RuntimeError

8. Existing Bearer token auth:

   * login still returns `access_token`
   * `Authorization: Bearer <token>` still works for protected endpoint

### Do not add frontend tests in this round

No browser/localStorage/cookie tests.

### Done when

```bash
pytest -q
```

passes locally or any failing tests are documented with exact failure reason.

---

# Phase 12: Final Verification — Must Run Before Done

## T023 — Full project verification checklist

* [X] T023 [US5] Run full verification commands before final response

### Purpose

Before reporting completion, verify the project still starts, migrations run, Celery loads, and core API flows still work. Do not just rely on static grep.

### Required static checks

Run:

```bash
git status --short
rg -n "frontend/app.js|frontend/login.html|frontend/signup.html" <changed-files-list-if-available>
rg -n "document_controller\\.process_document" backend/routes
rg -n "process_document_task.delay|process_and_index_workflow.apply_async" backend/routes/documents.py
rg -n "telegram_api.send_message" backend/services/telegram_webhook_service.py
rg -n "delivery_status=\"pending\"|delivery_status.*pending" backend/services/telegram_webhook_service.py
rg -n "backend.tasks.telegram_outbox" backend/celery_app.py
rg -n "SECURITY_SIMULATION_DESTRUCTIVE_ENABLED|CONTEXT_TOKEN_BUDGET|TELEGRAM_OUTBOX" .env.example backend/config.py
```

Expected:

* no frontend files changed
* document routes dispatch to Celery
* webhook service no longer sends Telegram inline in automatic success/fallback paths
* pending outbox messages are created
* Celery app includes telegram outbox task

### Required import checks

Run:

```bash
python -c "from backend.config import settings; print(settings.environment, settings.context_token_budget)"
python -c "from backend.database.models import ConversationMessage; print(ConversationMessage.delivery_status)"
python -c "from backend.tasks.telegram_outbox import deliver_pending_messages; print(deliver_pending_messages.name)"
python -c "from backend.celery_app import celery_app; print('deliver-pending-telegram-messages' in celery_app.conf.beat_schedule)"
```

Expected:

* no import errors
* settings load
* model column exists
* task imports
* beat schedule exists

### Required database migration check

If Docker stack is available:

```bash
docker compose -f docker/docker-compose.yml up -d postgres redis rabbitmq
docker compose -f docker/docker-compose.yml up -d backend worker scheduler
docker exec ragmind-backend alembic -c backend/alembic/alembic.ini upgrade head
```

If service names differ, inspect:

```bash
docker compose -f docker/docker-compose.yml ps
```

### Required health checks

After backend starts:

```bash
curl -s http://localhost:8000/health/live
curl -s http://localhost:8000/health
curl -s http://localhost:8000/health/full
```

Expected:

* `/health/live` returns `{"status":"alive"}`
* `/health` does not crash
* `/health/full` does not crash; if unhealthy, report exact dependency that is unhealthy

### Required test run

Run:

```bash
pytest -q
```

If the full test suite is too slow or existing unrelated tests fail, run focused tests and report both:

```bash
pytest -q tests
pytest -q backend/tests
```

Do not hide failures. Report exact failing test names and reasons.

### Required smoke flow

If `tools/test_all.py` exists and is current:

```bash
python tools/test_all.py
```

If it requires environment variables, run with local backend URL:

```bash
set RAGMIND_BASE_URL=http://localhost:8000
python tools/test_all.py
```

On PowerShell:

```powershell
$env:RAGMIND_BASE_URL="http://localhost:8000"
python tools/test_all.py
```

### Required Docker/Celery verification

Run:

```bash
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs --tail=100 backend
docker compose -f docker/docker-compose.yml logs --tail=100 worker
docker compose -f docker/docker-compose.yml logs --tail=100 scheduler
```

Expected:

* backend container running
* worker container running
* scheduler/beat container running if configured
* no repeated crash loops
* no import error for `backend.tasks.telegram_outbox`

### Required manual API checks

Use a real test user or existing dev credentials.

1. Login still returns Bearer token:

```bash
curl -s -X POST http://localhost:8000/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"<USER>\",\"password\":\"<PASSWORD>\"}"
```

2. Authenticated provider config GET works:

```bash
curl -s http://localhost:8000/config/providers ^
  -H "Authorization: Bearer <TOKEN>"
```

3. Unauthenticated provider config GET fails:

```bash
curl -i http://localhost:8000/config/providers
```

Expected:

* with token: success
* without token: 401 or 403

4. Existing Bearer-token frontend flow must remain compatible:

   * no frontend files changed
   * API still accepts `Authorization: Bearer <token>`

### Required final report format

When done, report:

```text
Files changed:
- ...

Verification run:
- command: result
- command: result

Known failures:
- None
or
- exact failure and why it is unrelated/needs follow-up

Frontend files changed:
- No

Document processing:
- Routes use Celery only: Yes/No
- Direct controller processing disabled: Yes/No

Telegram outbox:
- Success path queues pending message: Yes/No
- Failure fallback queues pending message: Yes/No
- Celery task registered: Yes/No

Production readiness:
- Secrets guardrails added: Yes/No
- Runtime config atomic writes: Yes/No
- Security simulation safe by default: Yes/No
```

### Completion rule

Do not say "done" unless:

* imports pass
* migration passes or migration failure is clearly reported
* tests run or exact blocker is reported
* Docker/backend health is checked or exact blocker is reported
* no frontend files were changed
* document processing remains Celery-only

---

# Final Out-of-Scope List

The following are intentionally not implemented in this round:

1. Frontend token/localStorage migration
2. Cookie-based auth
3. Logout endpoint
4. Next.js migration
5. Frontend monolith refactor
6. CSS refactor
7. Manual human-agent Telegram reply outbox migration
8. Full provider abstraction rewrite
9. Kubernetes/production deployment rewrite
10. Database move for runtime config; this round only hardens JSON writes

---

# Fast Command Pack

Use these commands to navigate quickly:

```bash
# Secrets
rg -n "AIza|sk-or-|gsk_|csk-|TELEGRAM_BOT_TOKEN|BOT_TOKEN_ENCRYPTION_KEY|AUTH_JWT_SECRET_KEY|COHERE_API_KEY|VOYAGE_API_KEY|OPENROUTER_API_KEY|GROQ_API_KEY|CEREBRAS_API_KEY" .

# Settings
rg -n "class Settings|ENVIRONMENT|CONTEXT_TOKEN_BUDGET|SECURITY_SIMULATION_DESTRUCTIVE_ENABLED|TELEGRAM_OUTBOX" backend/config.py .env.example

# Telegram
rg -n "telegram_api.send_message|save_message|delivery_status|ConversationMessage" backend/services backend/tasks backend/database/models.py

# Celery
rg -n "include=|task_routes|beat_schedule|process_document_task|process_and_index_workflow|telegram_outbox" backend/celery_app.py backend/tasks backend/routes

# Document processing duplicate path
rg -n "process_document\\(|_process_document_impl|document_controller\\.process_document|process_document_task|process_and_index_workflow" backend

# Security simulation
rg -n "simulate_security_attack|escalate_to_block|security_simulation_destructive_enabled|ROLE_PLATFORM_OWNER" backend/routes/security.py backend/security/auth.py

# Runtime config
rg -n "save_runtime_config|update_runtime_config|json.dump|os.replace|atomic" backend/runtime_config.py

# Provider config auth
rg -n "get_providers|update_providers|get_current_db_user" backend/routes/app_config.py

# Health
rg -n "health_live|health_check|health_check_full" backend/routes/health.py

# RAG context
rg -n "_build_context|context_token_budget|_estimate_tokens|_build_prompt" backend/services/answer_service.py
```

```

الخلاصة: دي النسخة اللي تديها للـ agent. أهم حاجة في آخرها إن هو **لازم يشغّل verification commands قبل ما يقول done**، ويتأكد إن:

- المشروع بيقوم.
- migrations شغالة.
- Celery task registered.
- document processing بقى Celery-only.
- Telegram outbox موجود.
- frontend ما اتلمسش.
- Bearer auth القديم لسه شغال.
```
