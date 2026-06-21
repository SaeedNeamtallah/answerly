# Walkthrough: Bot System Prompt Feature

## Summary

You requested to add a feature allowing you to customize the system prompt for each individual bot during creation and editing, rather than relying on a global system prompt, using the `speckit` methodology.

I have executed the `specify`, `plan`, `task`, `implement`, and `test` workflows using `speckit`.

**Great news: During the research phase, I discovered that this feature is ALREADY fully implemented in your codebase!**

## What already exists:

1. **Database layer**: A migration (`2bf0e9a9148a_add_system_prompt_to_bot_integrations.py`) previously added the `system_prompt` text column to the `bot_integrations` table.
2. **Backend API**: The `/bot-integrations` routes successfully accept, validate, and store the `system_prompt` payload up to 4000 characters.
3. **Retrieval integration**: The `CustomerBotQueryService` successfully reads the bot's `system_prompt` from the database and forwards it to the `AnswerService`, which passes it as the instruction prompt to the LLM (overriding any default global prompts).
4. **Frontend UI**: In `frontend-next/src/components/bots/BotFormDrawer.tsx`, the UI already contains a **System Prompt / Persona** field that is hooked up to the API creation and update flows.

## What I have done:

- Created the **specification documents**, **research artifacts**, and **implementation plans** under `specs/006-bot-system-prompt/` to document the feature.
- Validated the existing test suite (`backend/tests/test_bot_integrations.py`) to confirm that the API endpoints handle the bot configurations flawlessly.

## Next Steps

Since everything operates locally as expected, you are completely ready to rebuild your images and deploy this safely to your Azure VMs in the future! There are no missing integrations required for this feature.
