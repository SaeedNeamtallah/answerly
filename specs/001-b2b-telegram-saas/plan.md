# Implementation Plan: RAGMind B2B SaaS Telegram Support Platform

**Branch**: `001-b2b-telegram-saas` | **Date**: 2026-04-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-b2b-telegram-saas/spec.md`

## Summary

Extend the existing RAGMind application into a B2B SaaS Telegram customer-support
platform while preserving the current RAG pipeline. The implementation adds
database-backed Telegram bot integrations, durable Telegram customers and
conversations, platform-owner admin views, company-scoped conversation and bot
management, and backend webhook processing that calls the existing
`QueryController.answer_query()` path with the bot integration's `owner_id` and
linked `project_id`.

The plan intentionally keeps `users`, `projects`, `assets`, and `chunks` as the
knowledge-base core. Existing project upload/process/index/query behavior stays
in place. Legacy `bot_config.json` and `telegram_bot` behavior become local/demo
only for product traffic.

## Technical Context

**Language/Version**: Python 3.11+ backend, static browser frontend with HTML/CSS/JavaScript  
**Primary Dependencies**: FastAPI, SQLAlchemy async, Alembic, Celery, PostgreSQL/pgvector, optional Qdrant, httpx, pydantic, python-telegram-bot for legacy bot only  
**Storage**: PostgreSQL for application data, pgvector or Qdrant for vectors, uploaded files under `uploads/`  
**Testing**: Existing `tools/test_all.py` authenticated smoke test plus backend pytest-style tests under `backend/tests/`  
**Target Platform**: Dockerized local/production backend stack with static frontend served separately  
**Project Type**: Web application with FastAPI backend, static frontend, background workers, and webhook integration  
**Performance Goals**: Keep existing RAG query latency characteristics; webhook processing must avoid unbounded retries and must not block unrelated tenants  
**Constraints**: Preserve owner-scoped retrieval, do not expose bot tokens, do not route Telegram messages to fallback projects, keep existing `/projects/{project_id}/query` working  
**Scale/Scope**: First production SaaS layer for multiple companies, multiple bots per company, one linked project per bot, durable customer conversations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **RAG core preservation**: Pass. Existing upload, processing, chunking,
  embedding, vector retrieval, answer generation, and
  `POST /projects/{project_id}/query` remain in place. New Telegram customer
  query behavior calls the existing query controller internally.
- **Tenant isolation**: Pass. Company routes filter by `owner_id=current_user.id`.
  Bot integrations store `owner_id` and `project_id`; webhook retrieval uses
  only those stored values.
- **Platform-owner access**: Pass. Cross-company views are only in `/admin/*`
  routes and Admin Console UI. Non-platform-owner requests return `403`.
- **Role separation**: Pass. Dashboard users stay in `users`; Telegram customers
  use `telegram_customers` and never authenticate as users.
- **Bot integration source of truth**: Pass. Production Telegram messages resolve
  through `bot_integrations` using integration id and webhook secret. Global
  `bot_config.json`, `active_project_id`, service-account login, and project
  auto-selection are excluded from product flow.
- **Secret protection**: Pass. Tokens are validated, encrypted, hashed for
  uniqueness, redacted from logs/responses, hidden after save, and rotatable.
  Webhook secrets are generated server-side.
- **Durable conversations**: Pass. Customers, conversations, customer messages,
  bot replies, agent/system/error messages, sources, and retrieval metadata are
  persisted.
- **Customer-safe answers**: Pass. Telegram replies omit sources and debug data
  by default. Sources are stored internally and exposed to customers only when
  explicitly enabled.
- **Human handoff**: Pass. Conversation status, `needs_human`, manual reply,
  escalation, resolve, assignment, and block flows are planned.
- **Backend enforcement**: Pass. Security rules live in backend dependencies and
  services; frontend role visibility is presentation only.
- **Minimal compatibility**: Pass. The design adds new models/routes/services
  around existing controllers. It reuses existing `User.status` for account
  state instead of adding a duplicate account-status field.
- **Operational readiness**: Pass. Bot readiness checks cover token, webhook,
  linked project, usable chunks, providers, integration status, and last error.
- **Verification**: Pass. Smoke coverage includes existing RAG flow, bot creation,
  webhook processing, tenant denial, admin access, source hiding, and legacy
  exclusion.
- **Documentation**: Pass. Implementation must update `AGENTS.md`,
  `backend/ENDPOINTS.md`, `README.md` when behavior/setup changes, and
  `docs/project-graph.md` when architecture documentation exists or is added.

## Project Structure

### Documentation (this feature)

```text
specs/001-b2b-telegram-saas/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── alembic/
│   └── versions/
├── controllers/
│   ├── project_controller.py
│   ├── document_controller.py
│   └── query_controller.py
├── database/
│   ├── connection.py
│   └── models.py
├── routes/
│   ├── admin.py
│   ├── bot_integrations.py
│   ├── conversations.py
│   ├── telegram_webhook.py
│   └── bot_config.py
├── security/
│   └── auth.py
├── services/
│   ├── admin_service.py
│   ├── bot_integration_service.py
│   ├── conversation_service.py
│   ├── customer_bot_query_service.py
│   ├── telegram_api_service.py
│   ├── telegram_webhook_service.py
│   └── token_encryption_service.py
└── tests/

frontend/
├── app.js
├── index.html
└── style.css

telegram_bot/
├── bot.py
└── handlers.py

tools/
└── test_all.py
```

**Structure Decision**: Keep the current monorepo layout. Add focused backend
routes and services under existing `backend/routes` and `backend/services`
packages, add SQLAlchemy models in `backend/database/models.py`, add an Alembic
revision under `backend/alembic/versions`, extend static frontend files in
place, and keep `telegram_bot/` as legacy/demo behavior.

## Complexity Tracking

No constitution violations are planned.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research

Research output is captured in [research.md](./research.md).

Key decisions:

- Reuse the existing RAG query stack through `QueryController.answer_query()`.
- Add product role storage to `users` while reusing existing `User.status` for
  active/suspended/blocked account state.
- Use database-backed bot integrations as the only production Telegram source
  of truth.
- Use backend webhook routes for product traffic and keep `telegram_bot/` as
  legacy/demo only.
- Add token encryption with an explicit `BOT_TOKEN_ENCRYPTION_KEY` and avoid
  returning or logging secrets.

## Phase 1: Design

Design artifacts:

- Data model: [data-model.md](./data-model.md)
- API contract: [contracts/openapi.yaml](./contracts/openapi.yaml)
- Validation guide: [quickstart.md](./quickstart.md)

### Backend Design

1. Add `User.role`, `User.company_name`, and `User.company_website`. Reuse
   existing `User.status` for active/suspended/blocked account enforcement.
2. Add `BotIntegration`, `TelegramCustomer`, `Conversation`, and
   `ConversationMessage` models plus Alembic migration and indexes.
3. Add `get_platform_owner_user` and company-active helpers in
   `backend/security/auth.py`.
4. Add company-scoped `/bot-integrations` routes and service logic.
5. Add `/telegram/webhook/{integration_id}/{webhook_secret}` and service flow.
6. Add company-scoped `/conversations` routes and manual reply lifecycle.
7. Add platform-owner-only `/admin/*` routes for companies, projects, bots,
   conversations, messages, stats, suspend, and activate.
8. Mark `backend/routes/bot_config.py` and `telegram_bot/` as legacy/demo for
   production product behavior.
9. Mount new routers in `backend/main.py`.

### Frontend Design

1. Extend navigation with Dashboard, Projects/Knowledge Bases, Smart Chat,
   Telegram Bots, Conversations, AI Settings, Account Settings, and Admin
   Console only for `platform_owner`.
2. Replace the product-facing Bot Settings page with Telegram Bots list and
   create/edit workflows.
3. Add Conversations inbox and detail view with internal sources and manual
   action controls.
4. Add linked Telegram bots to project detail and a Connect Telegram Bot action.
5. Add Admin Console views for companies, company details, company projects,
   company bots, company conversations, global conversations, and stats.

### Verification Design

Add or extend backend tests and `tools/test_all.py` coverage for:

- Existing signup/login/project/upload/process/query flow.
- Company A cannot access Company B projects, bot integrations, or conversations.
- Company can create multiple bot integrations linked to owned projects.
- Bot cannot link to another company's project.
- Webhook creates customer/conversation/messages and sends a mocked Telegram
  reply.
- Bot answers only from linked project and never auto-selects another project.
- Sources are hidden by default.
- Production Telegram flow does not use global `active_project_id`,
  `bot_config.json`, or service/admin login.
- Platform owner can access cross-company data through `/admin/*`; company users
  receive `403`.

## Phase 2: Task Planning Approach

Tasks should be generated in this order:

1. Database models and Alembic migration.
2. Security role/account helpers.
3. Bot integration backend routes/services.
4. Telegram webhook backend routes/services.
5. Conversation backend routes/services.
6. Platform admin backend routes/services.
7. Legacy bot config deprecation.
8. Frontend bot, conversation, project-detail, and admin views.
9. Tests and smoke coverage.
10. Documentation updates.

`tasks.md` is intentionally not created by this planning step; generate it with
the Spec Kit task workflow after reviewing this plan.
