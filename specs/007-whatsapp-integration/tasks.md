---
description: "Task list template for feature implementation"
---

# Tasks: WhatsApp Integration

**Input**: Design documents from `/specs/007-whatsapp-integration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Initialize `whatsapp-bridge` Node.js project (package.json, tsconfig.json).
- [x] T002 Add `@whiskeysockets/baileys` and `express` dependencies to `whatsapp-bridge`.
- [x] T003 [P] Add `whatsapp-bridge` service to `docker/docker-compose.yml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create SQLAlchemy `WhatsAppIntegration` model in `backend/database/models.py`
- [x] T005 [P] Create SQLAlchemy `WhatsAppCustomer` model in `backend/database/models.py`
- [x] T006 Update `Conversation` model to support `channel` and `whatsapp` foreign keys in `backend/database/models.py`
- [x] T007 Generate and apply Alembic migration for the new and updated models.

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Connect WhatsApp Account (Priority: P1) 🎯 MVP

**Goal**: As a company admin, I want to connect my WhatsApp account to the platform so that it can act as a customer support bot.

**Independent Test**: Can be fully tested by navigating to the integrations page, clicking "Add WhatsApp Bot", and successfully authenticating a WhatsApp account by scanning a QR code.

### Implementation for User Story 1

- [x] T008 [P] [US1] Create Baileys session manager and QR code generation endpoint in `whatsapp-bridge/src/whatsappClient.ts` and `whatsapp-bridge/src/index.ts`.
- [x] T009 [P] [US1] Create FastAPI endpoints to list, create, and delete `WhatsAppIntegration` in `backend/routes/whatsapp_integrations.py`.
- [x] T010 [US1] Register `whatsapp_integrations` router in `backend/main.py`.
- [x] T011 [P] [US1] Create frontend API clients for WhatsApp integrations in `frontend-next/src/lib/api/whatsappIntegrations.ts`.
- [x] T012 [P] [US1] Create frontend page for WhatsApp bots list in `frontend-next/src/app/(company)/whatsapp-bots/page.tsx`.
- [x] T013 [US1] Create frontend page for WhatsApp bot details and QR scanning in `frontend-next/src/app/(company)/whatsapp-bots/[botId]/page.tsx`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Automated Knowledge Base Replies (Priority: P1)

**Goal**: As a customer, I want to send a question to the company's WhatsApp number and receive an instant AI-generated answer.

**Independent Test**: Can be tested by sending a message from a personal WhatsApp account to the connected business number and verifying that a correct AI reply is received.

### Implementation for User Story 2

- [x] T014 [P] [US2] Update `whatsappClient.ts` to listen for incoming text messages (`messages.upsert`) and forward them via HTTP POST to the backend webhook endpoint.
- [x] T015 [P] [US2] Create backend webhook route in `backend/routes/whatsapp_webhook.py` to receive incoming WhatsApp messages.
- [x] T016 [US2] Update `ConversationService` and `backend/routes/whatsapp_webhook.py` to save `WhatsAppCustomer` and `ConversationMessage` in the DB.
- [x] T017 [P] [US2] Create Celery task `generate_whatsapp_reply` in `backend/tasks/whatsapp_query.py` to process the message via `QueryController.answer_query()`.
- [x] T018 [US2] Update `backend/main.py` to register the `whatsapp_webhook` router.
- [x] T019 [P] [US2] Create `whatsapp_outbox.py` Celery task to deliver pending outgoing messages.
- [x] T020 [P] [US2] Create endpoint in `whatsapp-bridge/src/index.ts` to receive outgoing messages from backend and send them via Baileys.
- [x] T021 [US2] Register outbox task in `backend/celery_app.py` scheduler.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. AI can reply to WhatsApp queries.

---

## Phase 5: User Story 3 - Human Handoff (Priority: P2)

**Goal**: As a company agent, I want to view WhatsApp conversations in the dashboard and take over from the bot when human intervention is needed.

**Independent Test**: Can be tested by having the AI escalate a conversation, then the human agent replying via the dashboard, and the customer receiving the message on WhatsApp.

### Implementation for User Story 3

- [x] T022 [P] [US3] Update `ConversationService` in `backend/services/conversation_service.py` to correctly query WhatsApp-linked conversations.
- [x] T023 [P] [US3] Update frontend conversation UI `frontend-next/src/components/conversations/` to display the channel type (WhatsApp vs Telegram).
- [x] T024 [US3] Ensure manual agent replies sent from the dashboard are routed to the WhatsApp outbox queue if the conversation channel is WhatsApp.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T025 [P] Code cleanup and refactoring in backend models and services.
- [x] T026 [P] Run quickstart.md validation to ensure the bridge runs correctly.
- [x] T027 Update `AGENTS.md` to reflect new WhatsApp routes, tasks, and frontend entrypoints.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Depends on US1 (requires an active connection to test).
- **User Story 3 (P2)**: Depends on US1 & US2 (requires conversations to view and reply to).
