# Data Model: Bot System Prompt

## Entities

### `BotIntegration`
- `id`: Integer (Primary Key)
- `owner_id`: Integer (Foreign Key -> User.id)
- `project_id`: Integer (Foreign Key -> Project.id)
- `name`: String(120)
- `telegram_bot_id`: String(64)
- `system_prompt`: Text (Nullable, max length 4000 characters) - *This is the field enabling custom bot prompts.*

No new tables or fields required.
