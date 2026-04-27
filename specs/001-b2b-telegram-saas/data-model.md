# Data Model: RAGMind B2B SaaS Telegram Support Platform

## Existing Entities

### User

Existing dashboard account used for authentication.

Planned additions:

- `role`: string, required, default `company_admin`
  - Allowed values: `platform_owner`, `company_admin`
- `company_name`: string, nullable
- `company_website`: string, nullable

Existing fields reused:

- `status`: existing account state enum with `ACTIVE`, `BLOCKED`, and
  `SUSPENDED`

Relationships:

- One user owns many projects.
- One company user owns many bot integrations.
- One company user owns many Telegram customers.
- One company user owns many conversations and conversation messages.

Rules:

- Company endpoints filter by `owner_id == current_user.id`.
- Platform-owner cross-company access uses `/admin/*` only.
- Suspended or blocked users cannot perform company product actions.

### Project

Existing company-owned knowledge base.

Relationships:

- Belongs to one user through `owner_id`.
- Has many assets/documents and chunks.
- Has many bot integrations.

Rules:

- A bot integration links to exactly one project.
- A project may have multiple bot integrations.
- Telegram retrieval uses only the project linked to the receiving bot
  integration.

### Asset and Chunk

Existing document and retrievable text chunk models.

Rules:

- Upload, processing, chunking, embedding, indexing, vector retrieval, and web
  project query behavior remain preserved.
- New Telegram query behavior does not introduce JSON fallback vector search or
  alternate retrieval paths.

## New Entities

### BotIntegration

Database-backed Telegram bot configuration and product source of truth.

Fields:

- `id`: integer primary key
- `owner_id`: foreign key to `users.id`, required, cascade delete
- `project_id`: foreign key to `projects.id`, required, cascade delete
- `platform`: string, required, default `telegram`
- `name`: string, nullable
- `telegram_bot_id`: big integer, unique, nullable until validation completes
- `telegram_bot_username`: string, nullable
- `telegram_bot_display_name`: string, nullable
- `bot_token_encrypted`: text, required
- `bot_token_hash`: string, required, unique
- `webhook_secret`: string, required, unique
- `status`: string, required, default `active`
- `last_error`: text, nullable
- `welcome_message`: text, nullable
- `fallback_message`: text, nullable
- `handoff_message`: text, nullable
- `language`: string, default `ar`
- `tone`: string, default `professional`
- `show_sources_to_customer`: boolean, default false
- `human_handoff_enabled`: boolean, default true
- `collect_contact_enabled`: boolean, default false
- `created_by_user_id`: foreign key to `users.id`, nullable
- `created_at`: timestamp
- `updated_at`: timestamp

Statuses:

- `active`
- `disabled`
- `error`

Indexes:

- `owner_id`
- `project_id`
- `status`
- unique `telegram_bot_id`
- unique `bot_token_hash`
- unique `webhook_secret`

Rules:

- The linked project must belong to the owner.
- Tokens are encrypted and never returned after save.
- Readiness checks validate token, webhook, project ownership, project content,
  providers, status, and last error.

### TelegramCustomer

External Telegram contact scoped to one bot integration.

Fields:

- `id`: integer primary key
- `owner_id`: foreign key to `users.id`, required, cascade delete
- `bot_integration_id`: foreign key to `bot_integrations.id`, required,
  cascade delete
- `telegram_user_id`: big integer, nullable
- `chat_id`: big integer, required
- `username`: string, nullable
- `first_name`: string, nullable
- `last_name`: string, nullable
- `language_code`: string, nullable
- `is_blocked`: boolean, default false
- `first_seen_at`: timestamp
- `last_seen_at`: timestamp

Indexes and constraints:

- `owner_id`
- unique `(bot_integration_id, chat_id)`

Rules:

- Telegram customers do not authenticate as dashboard users.
- Blocked customers do not receive automated answers.

### Conversation

Durable support thread between one Telegram customer and one bot integration.

Fields:

- `id`: integer primary key
- `owner_id`: foreign key to `users.id`, required, cascade delete
- `bot_integration_id`: foreign key to `bot_integrations.id`, required,
  cascade delete
- `project_id`: foreign key to `projects.id`, required, cascade delete
- `customer_id`: foreign key to `telegram_customers.id`, required, cascade
  delete
- `platform`: string, required, default `telegram`
- `status`: string, required, default `open`
- `assigned_to_user_id`: foreign key to `users.id`, nullable
- `last_message_text`: text, nullable
- `last_message_at`: timestamp, nullable
- `unread_count`: integer, default 0
- `needs_human`: boolean, default false
- `resolved_at`: timestamp, nullable
- `created_at`: timestamp
- `updated_at`: timestamp

Statuses:

- `open`
- `escalated`
- `resolved`
- `blocked`

Indexes:

- `(owner_id, status)`
- `bot_integration_id`
- `project_id`
- `last_message_at`

Rules:

- Company admins access only conversations where `owner_id == current_user.id`.
- Platform owners access cross-company conversations only through `/admin/*`.
- Manual replies use the linked bot integration token.

### ConversationMessage

Durable message event in a conversation.

Fields:

- `id`: integer primary key
- `owner_id`: foreign key to `users.id`, required, cascade delete
- `conversation_id`: foreign key to `conversations.id`, required, cascade delete
- `sender_type`: string, required
- `sender_user_id`: foreign key to `users.id`, nullable
- `telegram_message_id`: big integer, nullable
- `content`: text, required
- `answer_sources_json`: JSONB, nullable
- `context_used`: integer, nullable
- `confidence_score`: float, nullable
- `raw_payload_json`: JSONB, nullable
- `status`: string, default `sent`
- `error_message`: text, nullable
- `created_at`: timestamp

Sender types:

- `customer`
- `bot`
- `agent`
- `system`
- `error`

Indexes:

- `owner_id`
- `(conversation_id, created_at)`

Rules:

- Internal sources and retrieval metadata are stored here for company/admin
  review.
- Customer-facing Telegram replies include sources only when the integration
  enables source display.

## State Transitions

### BotIntegration

```text
active -> disabled
disabled -> active
active -> error
error -> active
error -> disabled
```

### Conversation

```text
open -> escalated
open -> resolved
open -> blocked
escalated -> resolved
escalated -> blocked
resolved -> open
```

## Ownership Rules

- `BotIntegration.owner_id`, `TelegramCustomer.owner_id`,
  `Conversation.owner_id`, and `ConversationMessage.owner_id` must match the
  company user that owns the linked project.
- Telegram webhook processing derives ownership only from the resolved
  `BotIntegration`.
- No request payload may override the owner for company data.
