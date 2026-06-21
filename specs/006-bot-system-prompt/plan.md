# Implementation Plan: Bot System Prompt Configuration

**Branch**: `006-bot-system-prompt` | **Date**: 2026-06-19 | **Spec**: [spec.md](file:///c:/Users/saeid/github projects/ragmind discussed/specs/006-bot-system-prompt/spec.md)
**Input**: Feature specification from `/specs/006-bot-system-prompt/spec.md`

## Summary

The requested feature is to allow users to customize a system prompt for each bot during creation and edit it later in the frontend, rather than relying on a single global prompt.

**Discovery**: Extensive research indicates this feature **is already fully implemented** in the current repository:
- The database schema `bot_integrations` has a `system_prompt` text field.
- The backend API accepts, validates, and saves `system_prompt` correctly.
- The `CustomerBotQueryService` passes this `system_prompt` directly to the `AnswerService`, successfully overriding the default prompt.
- The frontend `BotFormDrawer.tsx` already contains a "System Prompt / Persona" field that works for bot creation and editing.

Therefore, this "implementation" plan is merely validating and verifying the existing codebase configuration, ensuring tests pass and it is ready for deployment.

## Technical Context

**Language/Version**: Python 3.11, TypeScript (Next.js)
**Primary Dependencies**: FastAPI, Next.js, SQLAlchemy, pgvector
**Storage**: PostgreSQL
**Testing**: pytest, Playwright (UI)
**Project Type**: Web Application (Backend API + Frontend App)
**Constraints**: System prompt is limited to 4000 characters by the backend validator.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No Constitution Violations. No new code is being added.

## Project Structure

### Documentation (this feature)

```text
specs/006-bot-system-prompt/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

No new source code files are needed. The existing structure handling this is:
```text
backend/
├── src/
│   ├── models.py (BotIntegration.system_prompt)
│   ├── routes/bot_integrations.py (API endpoints)
│   ├── services/bot_integration_service.py (Business logic)
│   ├── services/customer_bot_query_service.py (Uses prompt in LLM query)
│   └── alembic/versions/2bf0e9a9148a_add_system_prompt_to_bot_integrations.py (DB Migration)
frontend-next/
├── src/
│   ├── components/bots/BotFormDrawer.tsx (UI Field)
│   └── lib/types/bot.ts (Types)
```

**Structure Decision**: Use existing architecture. No modifications required.
