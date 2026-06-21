# Implementation Plan: WhatsApp Integration

**Branch**: `007-whatsapp-integration` | **Date**: 2026-06-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-whatsapp-integration/spec.md`

## Summary

Integrate WhatsApp as a customer support channel using the `Baileys` Node.js library. The integration will mirror the existing Telegram integration architecture: supporting individual system prompts, user/conversation modeling, and handling via Celery tasks. Since Baileys is Node.js-based and the backend is Python, a new lightweight Node.js microservice will be added to the Docker compose stack to bridge Baileys and FastAPI.

## Technical Context

**Language/Version**: Python 3.11 (Backend), Node.js 20+ (Baileys Bridge), TypeScript (Frontend)  
**Primary Dependencies**: FastAPI, Celery, SQLAlchemy (Backend), `@whiskeysockets/baileys` (Node.js), Next.js (Frontend)  
**Storage**: PostgreSQL (for Integration/User/Conversation state)  
**Testing**: pytest (Backend), Playwright (Frontend)  
**Target Platform**: Linux Server (Docker / Azure)  
**Project Type**: web-service + frontend + node-service  
**Performance Goals**: <2s webhook processing, durable session management for Baileys  
**Constraints**: Baileys sessions must be stored persistently (e.g., in Postgres or mounted volume) to survive restarts.  
**Scale/Scope**: Supports multiple WhatsApp numbers (one per integration), integrated into unified conversation dashboard.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Does not introduce unnecessary complexity (Node.js microservice is required for Baileys).
- [x] Follows existing patterns (mirrors Telegram integration).

## Project Structure

### Documentation (this feature)

```text
specs/007-whatsapp-integration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/ (whatsapp_integration.py, whatsapp_customer.py)
│   ├── services/ (whatsapp_webhook_service.py)
│   ├── routes/ (whatsapp_integrations.py, whatsapp_webhook.py)
│   └── tasks/ (whatsapp_query.py, whatsapp_outbox.py)
├── tests/

frontend-next/
├── src/
│   ├── app/(company)/whatsapp-bots/
│   ├── components/whatsapp/
│   └── lib/api/whatsappIntegrations.ts

whatsapp-bridge/ (NEW)
├── package.json
├── src/
│   ├── index.ts
│   └── whatsappClient.ts
└── Dockerfile

docker/
├── docker-compose.yml (updated with whatsapp-bridge)
```

**Structure Decision**: Added a `whatsapp-bridge` directory for the Node.js Baileys microservice. The rest follows the existing `backend` and `frontend-next` structure.
