---
description: "Task list for RAGMind B2B SaaS Telegram support platform"
---

# Tasks: RAGMind B2B SaaS Telegram Support Platform

**Input**: Design documents from `/specs/001-b2b-telegram-saas/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`

**Tests**: Required for every touched constitutional gate: RAG compatibility,
tenant isolation, platform-owner access, bot integration ownership, webhook
behavior, secret protection, source visibility, no service-account customer
queries, and no project auto-switching.

**Organization**: Tasks are grouped by user story so each story can be
implemented and tested independently after the foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no
  dependency on another open task.
- **[Story]**: User story from `spec.md` such as `US1`.
- Every task includes exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared config and dependency surface for the feature.

- [X] T001 Add the chosen symmetric encryption dependency for bot-token storage to `backend/requirements.txt`
- [X] T002 Add `BOT_TOKEN_ENCRYPTION_KEY` and `PUBLIC_WEBHOOK_BASE_URL` placeholders and comments to `.env.example`
- [X] T003 Add settings for `BOT_TOKEN_ENCRYPTION_KEY` and `PUBLIC_WEBHOOK_BASE_URL` to `backend/config.py`
- [X] T004 [P] Create empty service modules `backend/services/token_encryption_service.py`, `backend/services/telegram_api_service.py`, `backend/services/bot_integration_service.py`, `backend/services/conversation_service.py`, `backend/services/customer_bot_query_service.py`, `backend/services/telegram_webhook_service.py`, and `backend/services/admin_service.py`
- [X] T005 [P] Create empty route modules `backend/routes/bot_integrations.py`, `backend/routes/telegram_webhook.py`, `backend/routes/conversations.py`, and `backend/routes/admin.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add schema and security primitives required by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Add `role`, `company_name`, and `company_website` fields plus SaaS relationships to `User` in `backend/database/models.py`
- [X] T007 Add `BotIntegration`, `TelegramCustomer`, `Conversation`, and `ConversationMessage` SQLAlchemy models and indexes to `backend/database/models.py`
- [X] T008 Add Alembic migration `backend/alembic/versions/20260427_01_add_saas_telegram_support.py` for user role/company fields, new tables, foreign keys, uniqueness constraints, and indexes
- [X] T009 Add `ROLE_PLATFORM_OWNER`, `ROLE_COMPANY_ADMIN`, `get_platform_owner_user`, and active-company helper dependencies to `backend/security/auth.py`
- [X] T010 Update `/auth/me` and auth response models in `backend/routes/auth.py` to return product `role`, `company_name`, `company_website`, and existing `status`
- [X] T011 Add model and migration regression tests for SaaS fields and table/index metadata in `backend/tests/test_saas_models.py`
- [X] T012 Add auth-helper regression tests for platform-owner access and active-company denial in `backend/tests/test_saas_auth.py`
- [X] T013 Mount the new routers in `backend/main.py` with no behavioral logic beyond registration

**Checkpoint**: Database schema, account role model, and auth dependencies are ready.

---

## Phase 3: User Story 1 - Company Admin Manages Knowledge Bases (Priority: P1)

**Goal**: Company admins continue to create projects, upload/process documents,
and query owned knowledge bases while cross-company access is denied.

**Independent Test**: Create two companies; verify company A can upload/process/query
its own project and company B cannot access company A's project, documents, or query.

### Tests for User Story 1

- [X] T014 [P] [US1] Add company project/document/query ownership tests to `backend/tests/test_company_project_scope.py`
- [X] T015 [P] [US1] Extend `tools/test_all.py` to assert existing upload/process/index/query smoke coverage still passes with `company_admin` role data

### Implementation for User Story 1

- [X] T016 [US1] Ensure project routes continue passing `owner_id=current_user.id` and use active-company dependencies where needed in `backend/routes/projects.py`
- [X] T017 [US1] Ensure document routes continue passing `owner_id=current_user.id` and use active-company dependencies where needed in `backend/routes/documents.py`
- [X] T018 [US1] Ensure query routes preserve `_ensure_query_scope()` and owner-scoped `QueryController.answer_query()` calls in `backend/routes/query.py`
- [X] T019 [US1] Update frontend account role display for `platform_owner` and `company_admin` in `frontend/app.js`

**Checkpoint**: Existing RAG knowledge-base workflow still works and remains tenant-scoped.

---

## Phase 4: User Story 2 - Company Admin Connects Multiple Telegram Bots (Priority: P1)

**Goal**: Company admins can create and manage multiple database-backed Telegram
bot integrations linked only to owned projects, with protected tokens.

**Independent Test**: Create two integrations for one company, verify tokens are
not returned, and verify linking to another company's project is rejected.

### Tests for User Story 2

- [X] T020 [P] [US2] Add token encryption/hash/redaction tests to `backend/tests/test_token_encryption_service.py`
- [X] T021 [P] [US2] Add Telegram API service mock tests for token validation, webhook setup, webhook deletion, send message, and token redaction to `backend/tests/test_telegram_api_service.py`
- [X] T022 [P] [US2] Add bot integration ownership and no-token-response tests to `backend/tests/test_bot_integrations.py`
- [X] T023 [US2] Extend `tools/test_all.py` with mocked bot integration creation and cross-company project-link denial checks

### Implementation for User Story 2

- [X] T024 [US2] Implement `TokenEncryptionService.encrypt_secret()`, `decrypt_secret()`, and `hash_secret()` in `backend/services/token_encryption_service.py`
- [X] T025 [US2] Implement `TelegramApiService.validate_token_and_get_me()`, `set_webhook()`, `delete_webhook()`, and `send_message()` with token-safe errors in `backend/services/telegram_api_service.py`
- [X] T026 [US2] Implement project ownership validation, token validation, token encryption/hash storage, webhook secret generation, webhook registration, lifecycle updates, and readiness checks in `backend/services/bot_integration_service.py`
- [X] T027 [US2] Implement request/response schemas and company-scoped `/bot-integrations` CRUD, test, enable, disable, rotate-token, and readiness endpoints in `backend/routes/bot_integrations.py`
- [X] T028 [US2] Ensure `backend/routes/bot_integrations.py` never serializes `bot_token_encrypted`, `bot_token_hash`, or raw tokens in responses
- [X] T029 [US2] Add frontend API helpers for `/bot-integrations` endpoints in `frontend/app.js`
- [X] T030 [US2] Replace product-facing Bot Settings UI with Telegram Bots list, actions, and create/edit form in `frontend/index.html`
- [X] T031 [US2] Implement Telegram Bots rendering, create/edit, test, enable/disable, rotate token, delete, and view conversations behavior in `frontend/app.js`
- [X] T032 [US2] Add Telegram Bots page styling using existing design patterns in `frontend/style.css`

**Checkpoint**: Company-owned bot integrations work without exposing tokens.

---

## Phase 5: User Story 3 - Telegram Customer Gets Answers From Linked Project (Priority: P1)

**Goal**: Telegram webhook messages create customers/conversations/messages and
answer only from the bot integration's linked project.

**Independent Test**: Simulate a webhook update and verify customer, conversation,
customer message, bot answer, and mocked Telegram reply are stored for the resolved integration only.

### Tests for User Story 3

- [X] T033 [P] [US3] Add customer bot query service tests for linked-project-only retrieval and source hiding to `backend/tests/test_customer_bot_query_service.py`
- [X] T034 [P] [US3] Add Telegram webhook service tests for invalid secret, disabled integration, non-text update, blocked customer, and no project auto-switch to `backend/tests/test_telegram_webhook_service.py`
- [X] T035 [US3] Extend `tools/test_all.py` with simulated Telegram webhook message, customer creation, conversation creation, customer message save, bot reply save, mocked send, no `active_project_id`, and no service/admin login assertions

### Implementation for User Story 3

- [X] T036 [US3] Implement `ConversationService` helpers for find/create customer, find/create open conversation, save messages, update activity, and block checks in `backend/services/conversation_service.py`
- [X] T037 [US3] Implement `CustomerBotQueryService.answer_customer_message()` using `QueryController.answer_query()` with `integration.owner_id` and `integration.project_id` in `backend/services/customer_bot_query_service.py`
- [X] T038 [US3] Implement source-hiding/customer-safe answer formatting in `backend/services/customer_bot_query_service.py`
- [X] T039 [US3] Implement Telegram update parsing, integration lookup by id/secret, inactive handling, blocked customer handling, error recording, answer generation, message persistence, and Telegram send flow in `backend/services/telegram_webhook_service.py`
- [X] T040 [US3] Implement unauthenticated `POST /telegram/webhook/{integration_id}/{webhook_secret}` route in `backend/routes/telegram_webhook.py`
- [X] T041 [US3] Ensure webhook errors update `BotIntegration.last_error` without leaking secrets or stack traces in `backend/services/telegram_webhook_service.py`

**Checkpoint**: Telegram customer messages are durable, tenant-scoped, and answered only from the linked project.

---

## Phase 6: User Story 4 - Company Admin Handles Conversations (Priority: P2)

**Goal**: Company admins can list, inspect, reply to, escalate, resolve, assign,
and block only their own conversations.

**Independent Test**: Use a webhook-created conversation; company A can manage it,
company B cannot, and manual replies are sent through the linked bot.

### Tests for User Story 4

- [X] T042 [P] [US4] Add conversation route ownership, filtering, and message access tests to `backend/tests/test_conversations.py`
- [X] T043 [P] [US4] Add manual reply, resolve, escalate, assign, and block-customer service tests to `backend/tests/test_conversation_service.py`

### Implementation for User Story 4

- [X] T044 [US4] Extend `ConversationService` with list/get messages, manual reply, resolve, escalate, assign, and block-customer operations in `backend/services/conversation_service.py`
- [X] T045 [US4] Implement company-scoped `/conversations` routes in `backend/routes/conversations.py`
- [X] T046 [US4] Add frontend API helpers for `/conversations` endpoints in `frontend/app.js`
- [X] T047 [US4] Add Conversations navigation item, inbox container, filters, and detail container to `frontend/index.html`
- [X] T048 [US4] Implement Conversations inbox filtering, detail rendering, source metadata display, manual reply, resolve, escalate, assign, and block actions in `frontend/app.js`
- [X] T049 [US4] Add Conversations inbox/detail styling using existing layout patterns in `frontend/style.css`

**Checkpoint**: Company conversation management works and remains owner-scoped.

---

## Phase 7: User Story 5 - Platform Owner Monitors All Companies (Priority: P2)

**Goal**: Platform owners can monitor all companies and related resources through
explicit `/admin/*` routes and Admin Console UI.

**Independent Test**: Platform owner sees all companies/projects/bots/conversations;
company users receive `403` from `/admin/*`.

### Tests for User Story 5

- [X] T050 [P] [US5] Add platform-owner `/admin/*` access and non-owner `403` tests to `backend/tests/test_platform_admin.py`
- [X] T051 [P] [US5] Add admin stats and suspend/activate tests using existing `User.status` to `backend/tests/test_admin_service.py`
- [X] T052 [US5] Extend `tools/test_all.py` with platform-owner can view all companies and company user cannot access `/admin/*` checks

### Implementation for User Story 5

- [X] T053 [US5] Implement company/project/bot/conversation/message aggregation, stats, suspend, and activate operations in `backend/services/admin_service.py`
- [X] T054 [US5] Implement `/admin/companies`, `/admin/companies/{company_id}`, company projects, company bot integrations, company conversations, conversation messages, stats, suspend, and activate routes in `backend/routes/admin.py`
- [X] T055 [US5] Ensure every route in `backend/routes/admin.py` depends on `get_platform_owner_user`
- [X] T056 [US5] Add frontend role helpers for `platform_owner` and Admin Console visibility in `frontend/app.js`
- [X] T057 [US5] Add Admin Console navigation and containers for companies, company detail, projects, bots, conversations, messages, stats, suspend, and activate actions to `frontend/index.html`
- [X] T058 [US5] Implement Admin Console data loading and actions in `frontend/app.js`
- [X] T059 [US5] Add Admin Console styling using existing dashboard patterns in `frontend/style.css`

**Checkpoint**: Cross-company access exists only through platform-owner admin flows.

---

## Phase 8: User Story 6 - Legacy Bot Config Remains Demo Only (Priority: P3)

**Goal**: Legacy bot config remains available only for local/demo compatibility
and production customer-support traffic uses backend webhooks.

**Independent Test**: Production webhook/customer-query paths do not read
`active_project_id`, do not use service/admin login, and do not auto-select a project.

### Tests for User Story 6

- [X] T060 [P] [US6] Add legacy exclusion regression tests for product services to `backend/tests/test_legacy_bot_exclusion.py`
- [X] T061 [P] [US6] Add static regression assertions that product webhook/query services do not call `BOT_API_USERNAME`, `AUTH_ADMIN_USERNAME`, or `active_project_id` paths in `backend/tests/test_legacy_bot_exclusion.py`

### Implementation for User Story 6

- [X] T062 [US6] Mark `backend/routes/bot_config.py` responses as legacy/deprecated without changing production bot integration behavior
- [X] T063 [US6] Add comments or runtime messaging in `telegram_bot/handlers.py` documenting that polling bot behavior is local/demo only
- [X] T064 [US6] Add comments or startup messaging in `telegram_bot/bot.py` documenting that production Telegram receiving uses backend webhooks
- [X] T065 [US6] Remove product UI dependency on `/bot/config` and `active_project_id` from `frontend/app.js`
- [X] T066 [US6] Remove or relabel legacy Bot Settings product-facing copy in `frontend/index.html`

**Checkpoint**: Legacy Telegram flow is not part of production customer-support behavior.

---

## Phase 9: Polish & Cross-Cutting Verification

**Purpose**: Final verification, documentation, and consistency updates.

- [X] T067 [P] Update route inventory for new admin, bot integration, webhook, and conversation endpoints in `backend/ENDPOINTS.md`
- [X] T068 [P] Update code graph, ownership rules, new services/routes/models, and legacy Telegram behavior in `AGENTS.md`
- [X] T069 [P] Update setup/behavior notes for SaaS Telegram bot integrations, env vars, and legacy bot status in `README.md`
- [X] T070 [P] Create or update architecture graph for SaaS bot integration, webhook, conversation, admin, and RAG query flow in `docs/project-graph.md`
- [X] T071 [P] Update OpenAPI planning contract if implementation path names or response fields differ in `specs/001-b2b-telegram-saas/contracts/openapi.yaml`
- [X] T072 Run backend regression tests for the feature with `python -m unittest discover backend/tests`
- [X] T073 Run authenticated smoke coverage with `python tools/test_all.py`
- [X] T074 Run quickstart validation steps from `specs/001-b2b-telegram-saas/quickstart.md`
- [X] T075 Run targeted search to confirm production Telegram flow excludes global config and service login: `rg -n "active_project_id|bot_config|BOT_API_USERNAME|AUTH_ADMIN_USERNAME" backend telegram_bot frontend`
- [X] T076 Review API responses and logs to confirm bot tokens, webhook secrets, stack traces, and raw sensitive payloads are not exposed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: no dependencies.
- **Phase 2 Foundational**: depends on Phase 1; blocks all user stories.
- **US1, US2, US3**: start after Phase 2. US3 depends on US2 bot integration model/service behavior.
- **US4**: depends on US3 conversation/customer/message creation.
- **US5**: depends on Phase 2 and benefits from US2/US4 data paths for complete admin views.
- **US6**: depends on US2/US3 production flow existing.
- **Phase 9 Polish**: depends on all selected user stories.

### User Story Dependencies

- **US1**: independent after foundation; validates existing RAG compatibility.
- **US2**: independent after foundation except shared schema/security.
- **US3**: requires US2 bot integration and token services.
- **US4**: requires US3 conversation persistence.
- **US5**: requires foundation and can be built after backend entities exist.
- **US6**: requires production webhook/bot integration flow to deprecate legacy safely.

### Within Each User Story

- Tests or smoke checks for touched constitutional gates must be included.
- Tests should be written before implementation when practical.
- Models and migrations precede services.
- Services precede routes.
- Backend behavior precedes frontend integration.
- Story checkpoint must pass before moving to the next dependent story.

---

## Parallel Opportunities

- T004 and T005 can run in parallel with T001-T003 after dependency choices are known.
- T011 and T012 can run in parallel because they use separate test files.
- US2 test tasks T020-T022 can run in parallel.
- US3 test tasks T033-T034 can run in parallel.
- US4 test tasks T042-T043 can run in parallel.
- US5 test tasks T050-T051 can run in parallel.
- Documentation tasks T067-T071 can run in parallel after implementation paths stabilize.

## Parallel Example: US2

```text
Task: T020 Add token encryption/hash/redaction tests to backend/tests/test_token_encryption_service.py
Task: T021 Add Telegram API service mock tests to backend/tests/test_telegram_api_service.py
Task: T022 Add bot integration ownership and no-token-response tests to backend/tests/test_bot_integrations.py
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to prove existing RAG project flow still works.
3. Complete US2 and US3 to deliver the core customer-facing Telegram product.
4. Stop and validate bot creation plus webhook answer flow before adding broader UI/admin polish.

### Incremental Delivery

1. Foundation: schema, auth role helpers, config.
2. Company knowledge-base compatibility.
3. Bot integration management.
4. Telegram webhook and customer answer path.
5. Conversation operations.
6. Platform owner monitoring.
7. Legacy deprecation, frontend completion, docs, and smoke tests.

## Notes

- The current repo uses `frontend/style.css`, not `frontend/styles.css`.
- The plan intentionally reuses existing `User.status` instead of adding a
  duplicate `account_status` column.
- Do not rewrite upload, processing, chunking, embedding, vector retrieval, or
  answer generation.
- Do not use global `active_project_id`, `bot_config.json`, `BOT_API_USERNAME`,
  or `AUTH_ADMIN_USERNAME` for production customer Telegram queries.
