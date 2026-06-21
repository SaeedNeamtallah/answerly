# Quickstart: Bot System Prompt Feature

This feature is already fully integrated into the platform.

## To Use:
1. Log into the `frontend-next` application.
2. Navigate to the Bots section.
3. Click "Create bot" or "Edit" on an existing bot.
4. In the drawer that appears, fill out the "System Prompt / Persona" text area.
5. Save the bot.

## Validation:
To confirm it works, send a message to the bot on Telegram. The backend `AnswerService` will receive the custom system prompt associated with the bot and utilize it to instruct the LLM response.
