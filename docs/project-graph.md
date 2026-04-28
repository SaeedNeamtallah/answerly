# RAGMind Project Graph

Updated: 2026-04-27

## Runtime Entry Points

- `backend/main.py`
  - Creates the FastAPI app, configures middleware, and mounts all route modules.
- `frontend/app.js`
  - Static dashboard runtime for projects, RAG chat, bot integrations, conversations, and Admin Console.
- `telegram_bot/bot.py`
  - Legacy single-bot runner. Not the production multi-company Telegram path.
- `backend/celery_app.py`
  - Celery app used by document processing and indexing tasks.

## Core RAG Flow

```mermaid
flowchart LR
  U[Dashboard User] --> R1[POST /projects/{id}/documents]
  R1 --> DC[DocumentController.upload_document]
  DC --> FS[FileService.save_upload_file]
  FS --> T1[Celery process_document_task]
  T1 --> DL[DocumentLoaderService]
  DL --> CH[ChunkingService]
  CH --> EM[EmbeddingService]
  EM --> VDB[PGVectorProvider or QdrantProvider]

  U --> R2[POST /projects/{id}/query]
  R2 --> QC[QueryController.answer_query]
  QC --> QS[QueryService.search_similar_chunks]
  QS --> VDB
  QC --> AS[AnswerService.generate_answer]
```

Security invariant: dashboard query and document routes derive `owner_id` from JWT `current_user`; request payloads never choose ownership.

## B2B Telegram SaaS Flow

```mermaid
flowchart LR
  CA[company_admin] --> BI[POST /bot-integrations]
  BI --> TV[TelegramAPIService.validate_token]
  BI --> TC[TokenCryptoService encrypt/hash]
  BI --> DB[(bot_integrations)]
  BI --> WH[Telegram setWebhook]

  TG[Telegram Update] --> WR[POST /telegram/webhook/{integration_id}/{secret}]
  WR --> W[TelegramWebhookService]
  W --> BIR[BotIntegration lookup]
  BIR --> CUST[TelegramCustomer]
  CUST --> CONV[Conversation]
  CONV --> MSG1[ConversationMessage customer]
  W --> CBQ[CustomerBotQueryService]
  CBQ --> QC[QueryController.answer_query]
  QC --> QS[QueryService]
  QC --> AS[AnswerService]
  W --> SEND[TelegramAPIService.send_message]
  SEND --> MSG2[ConversationMessage bot]
```

Security invariant: each Telegram update resolves to exactly one `BotIntegration`; that row supplies the only allowed `owner_id` and `project_id`. There is no fallback to another project.

Customer-safety invariant: sources and retrieval metadata are stored internally on `conversation_messages`; customer replies hide sources unless `show_sources_to_customer` is enabled on the integration.

## Data Model

Existing protected RAG core:

- `users`
- `projects`
- `assets`
- `chunks`
- `celery_task_executions`

B2B Telegram SaaS additions:

- `users.role`
  - `company_admin` by default
  - `platform_owner` via `PLATFORM_OWNER_USERNAME` bootstrap or future admin flows
- `bot_integrations`
  - company-owned bot/project link
  - encrypted token, token hash, webhook secret, status/readiness fields
  - API responses expose only webhook configured state; webhook URLs and webhook secrets stay server-side
- `telegram_customers`
  - external Telegram profiles scoped to one bot integration
- `conversations`
  - durable support lifecycle: `open`, `escalated`, `resolved`, `blocked`
- `conversation_messages`
  - sender types: `customer`, `bot`, `agent`, `system`, `error`
  - idempotency fields for Telegram update/message IDs
  - internal sources/retrieval metadata and expiring raw payload JSON

Schema source of truth: Alembic migrations under `backend/alembic/versions/`, including `20260427_01_add_b2b_telegram_saas.py`.

## Route Graph

Company-scoped routes:

- `backend/routes/projects.py`
- `backend/routes/documents.py`
- `backend/routes/query.py`
- `backend/routes/bot_integrations.py`
- `backend/routes/conversations.py`

Unauthenticated Telegram ingress:

- `backend/routes/telegram_webhook.py`

Platform-owner-only routes:

- `backend/routes/admin_console.py`
  - all `/admin/*` product-console routes use `require_platform_owner_access()`

Legacy/demo routes:

- `backend/routes/bot_config.py`
  - shared JSON active-project config
  - retained for compatibility, deprecated for production multi-company Telegram behavior

## Service Graph

RAG services:

- `DocumentLoaderService`
- `ChunkingService`
- `EmbeddingService`
- `QueryService`
- `AnswerService`

Telegram SaaS services:

- `TokenCryptoService`
  - Fernet encryption for stored bot tokens
  - SHA-256 token hashes for dedupe
- `TelegramAPIService`
  - token validation, webhook registration, message sending
- `BotIntegrationService`
  - owner/project validation, token handling, readiness
- `ConversationService`
  - customers, conversations, message persistence, manual replies
- `CustomerBotQueryService`
  - customer-safe wrapper around `QueryController`
- `TelegramWebhookService`
  - webhook parsing, throttling, idempotency, answer orchestration, fallback persistence

## Frontend Graph

- `frontend/index.html`
  - nav entries for projects, chat, bot integrations, conversations, Admin Console
  - templates: `bot-integrations-template`, `conversations-template`, `admin-console-template`
- `frontend/app.js`
  - `views['bot-integrations']` calls `/bot-integrations/*`
  - bot integrations view supports create, readiness test, edit, rotate token, enable/disable, delete, and conversation jump actions
  - `views.conversations` calls `/conversations/*`
  - conversations view supports status filtering, bot-local filtering, source/retrieval metadata details, assign-to-self, manual reply, escalate, resolve, and block
  - `views['admin-console']` calls `/admin/*`
  - Admin Console supports overview, company list, company detail, projects, bots, conversations, activate, suspend, and block
  - Admin Console nav is visible only when `/auth/me` returns `platform_owner`
- `frontend/style.css`
  - product list, conversation inbox, status pills, and responsive support layout

## Operational Config

Required for production bot integrations:

- `BOT_TOKEN_ENCRYPTION_KEY`
- `PUBLIC_WEBHOOK_BASE_URL`
- `PLATFORM_OWNER_USERNAME`

Webhook safety controls:

- `TELEGRAM_WEBHOOK_REQUESTS_PER_MINUTE`
- `TELEGRAM_WEBHOOK_MAX_IN_FLIGHT`
- `TELEGRAM_RAW_PAYLOAD_RETENTION_DAYS`

Legacy single-bot config:

- `TELEGRAM_BOT_TOKEN`
- `uploads/config/bot_config.json`
- `/bot/config`

Do not use legacy active-project config for production multi-company Telegram support.
