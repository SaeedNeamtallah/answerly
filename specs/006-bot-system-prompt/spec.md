# Feature Specification: Bot System Prompt Configuration

**Feature Branch**: `006-bot-system-prompt`  
**Created**: 2026-06-19
**Status**: Draft  
**Input**: User description: "انا عايز اخصص سيتم برومبت لكل بوت مش كل البوتات يبقي ليها سستم برومبت واحد وضيف الجزء بتاعها في الفرونت بحيث اثناء انشاء البوت نقدر نضيف السيتم برومبت وفي الواجهه ممكن يبقي في اوبشن التعديل بعد الانشاء استخدم speckit للاضافة الفيتشر دي +specify plan task implement test all in local and consider after testing i will rebuild the images and push to azure so consider this new integration will be deployed in future in vm in azure"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set System Prompt During Bot Creation (Priority: P1)

As a bot creator, I want to specify a custom system prompt when creating a new bot, so that the bot behaves according to my specific instructions.

**Why this priority**: Core value of the feature, allows bots to be customized from the start.

**Independent Test**: Can be fully tested by creating a bot through the UI, supplying a custom system prompt, and verifying the bot uses it in subsequent queries.

**Acceptance Scenarios**:

1. **Given** I am on the bot creation page, **When** I fill in the bot details and enter a custom system prompt, **Then** the bot is created successfully with the provided system prompt.
2. **Given** I am on the bot creation page, **When** I leave the system prompt empty, **Then** the bot is created with a default system prompt.

---

### User Story 2 - Edit System Prompt After Creation (Priority: P2)

As a bot owner, I want to edit the system prompt of an existing bot, so that I can refine its behavior over time.

**Why this priority**: Allows for iterative improvement of bot behavior.

**Independent Test**: Can be tested by navigating to an existing bot's settings, updating the system prompt, and verifying the bot behavior changes accordingly.

**Acceptance Scenarios**:

1. **Given** I am viewing an existing bot's settings, **When** I update the system prompt and save, **Then** the changes are persisted and new queries use the updated prompt.

### Edge Cases

- What happens when a user inputs a very large system prompt? (Need character limits)
- How does the system handle special characters or formatting in the system prompt?
- Does changing the system prompt affect currently ongoing bot conversations or only new ones?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to input a system prompt string during bot creation.
- **FR-002**: System MUST store the system prompt associated with each specific bot entity.
- **FR-003**: System MUST provide an interface to edit the system prompt of an existing bot.
- **FR-004**: System MUST use the bot-specific system prompt when generating answers instead of a global default prompt.
- **FR-005**: System MUST fallback to a reasonable default prompt if the bot's system prompt is empty or not set.
- **FR-006**: System MUST enforce a maximum character limit on the system prompt to prevent abuse.

### Key Entities

- **BotIntegration / TelegramBot**: The entity representing a bot, which needs a new attribute for `system_prompt`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully save a custom system prompt during bot creation without errors.
- **SC-002**: The backend successfully uses the bot's custom prompt when sending requests to the LLM provider.
- **SC-003**: Changes to a bot's system prompt take effect immediately for new queries.

## Assumptions

- We are targeting the BotIntegration / Telegram webhook multi-company SaaS bots described in `AGENTS.md`.
- We assume the database requires an Alembic migration to add a `system_prompt` column to the `bot_integrations` table.
- A standard character limit of e.g. 2000-4000 characters is acceptable.
