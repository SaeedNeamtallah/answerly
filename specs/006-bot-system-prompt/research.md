# Research: Bot System Prompt Configuration

**Feature**: 006-bot-system-prompt

## Findings

1. **Database Schema**: The `bot_integrations` table already contains a `system_prompt` column of type `Text` (added via Alembic migration `2bf0e9a9148a_add_system_prompt_to_bot_integrations.py` on 2026-06-17).
2. **Backend API**: The endpoints in `backend/routes/bot_integrations.py` (`POST /bot-integrations` and `PUT /bot-integrations/{id}`) already parse, validate (max 4000 chars), and save the `system_prompt` payload field via `BotIntegrationService`.
3. **LLM Integration**: `CustomerBotQueryService.generate_bot_reply` correctly reads the bot's `system_prompt` and passes it as `custom_system_prompt` to `QueryController`, which then passes it to `AnswerService._build_system_prompt`. This successfully overrides the global default system prompt.
4. **Frontend UI**: The Next.js frontend already has the form field `System Prompt / Persona` in the `BotFormDrawer.tsx` component which is used for both Creating and Editing bots. The schema validates the field and properly maps it to `system_prompt` in `BotIntegrationCreatePayload` and `BotIntegrationUpdatePayload` inside `frontend-next/src/lib/types/bot.ts`.

## Decision

The requested feature **is already 100% implemented** in the `ragmind discussed` codebase. 

No further code modifications are required. The implementation plan will document this and we will conclude the process gracefully.
