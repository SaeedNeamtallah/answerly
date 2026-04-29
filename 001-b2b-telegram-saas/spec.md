# Feature Specification: RAGMind B2B SaaS Telegram Support Platform

**Feature Branch**: `001-b2b-telegram-saas`  
**Created**: 2026-04-27  
**Status**: Draft  
**Input**: User description: `newplan.md`

## Clarifications

### Session 2026-04-27

- Q: How should duplicate Telegram webhook deliveries be handled? → A: Treat duplicate Telegram deliveries as idempotent: detect by bot integration plus Telegram message/update id, do not create duplicate messages, and return success without sending another answer.
- Q: How should the initial platform owner be created? → A: Configure a platform-owner username in an environment or seed flow; implementation promotes or creates that specific user only.
- Q: Who can a company admin assign a conversation to in v1? → A: Allow assignment only to the current company admin; keep `assigned_to_user_id` for future support-agent/team expansion.
- Q: What webhook throttling is required for v1? → A: Per bot integration, cap customer webhook handling by messages per minute plus maximum concurrent in-flight answers.
- Q: How long should raw Telegram payloads be retained? → A: Store sanitized raw Telegram payloads for 30 days, then purge or redact them.

## Constitution Alignment *(mandatory)*

- **RAG core impact**: The existing users/projects/assets/chunks RAG core,
  document upload, processing, chunking, embedding, vector retrieval, answer
  generation, and `POST /projects/{project_id}/query` remain preserved.
- **Tenant isolation**: Company data is scoped by `owner_id == current_user.id`.
  Telegram messages resolve through one bot integration, which defines the
  `owner_id` and linked `project_id` used for retrieval.
- **Platform-owner access**: Cross-company visibility is available only to
  `platform_owner` users through `/admin/*` endpoints and Admin Console views.
- **Role separation**: Dashboard users are `platform_owner` or `company_admin`.
  Telegram customers are external contacts created from Telegram update data and
  do not login to the dashboard.
- **Bot integration source of truth**: Production Telegram behavior uses
  database-backed bot integrations, not global `bot_config.json`,
  `active_project_id`, service-account login, auto-project selection, or one
  global bot.
- **Secret protection**: Telegram bot tokens are validated, encrypted, hashed for
  uniqueness, never logged, never returned after saving, hidden from the
  frontend, and rotatable. Webhook secrets are unguessable.
- **Conversation durability**: Telegram customers, conversations, customer
  messages, bot replies, agent replies, system/error messages, answer sources,
  and retrieval metadata are persisted.
- **Customer-safe answers**: Telegram replies hide internal sources, document
  names, similarity scores, raw chunks, provider details, and debug data by
  default. Sources are customer-visible only when explicitly enabled.
- **Human handoff**: Company admins can view, filter, reply to, escalate,
  resolve, assign, and block conversations where supported.
- **Backend enforcement**: Role checks, ownership checks, account status checks,
  bot/project ownership, conversation ownership, token protection, source
  visibility, and no project auto-switching are enforced server-side.
- **Verification**: Smoke or automated coverage must verify tenant isolation,
  platform-owner access, bot linking, webhook conversation creation, linked
  project-only answers, hidden sources by default, legacy bot config exclusion,
  no service-account customer queries, no project auto-switching, and existing
  RAG upload/process/query compatibility.
- **Documentation**: Implementation must update `AGENTS.md`,
  `backend/ENDPOINTS.md`, `README.md` when behavior/setup changes, and
  `docs/project-graph.md` when architecture documentation exists or is added.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Company Admin Manages Knowledge Bases (Priority: P1)

As a company admin, I can create and manage my own projects as knowledge bases,
upload documents, process/index them, and test answers from the dashboard using
the existing project query flow.

**Why this priority**: The SaaS Telegram product depends on reliable company-owned
knowledge bases before any customer bot can answer correctly.

**Independent Test**: Create a company account, create a project, upload and
process a document, query the project through the web/admin endpoint, and verify
another company cannot access that project or its documents.

**Acceptance Scenarios**:

1. **Given** a logged-in company admin, **When** they create a project and upload
   a document, **Then** the document is processed into chunks for that company
   owned project.
2. **Given** a processed company project, **When** the company admin asks a
   question through `POST /projects/{project_id}/query`, **Then** the answer uses
   only that project and remains scoped to the company's `owner_id`.
3. **Given** two company admins, **When** company B requests company A's project,
   documents, or query endpoint, **Then** the backend denies access.

---

### User Story 2 - Company Admin Connects Multiple Telegram Bots (Priority: P1)

As a company admin, I can connect multiple Telegram bots, link each bot to one of
my projects, configure customer-facing behavior, and manage each bot lifecycle.

**Why this priority**: Multi-bot, project-linked integrations are the core product
change from a demo Telegram bot to a B2B SaaS support platform.

**Independent Test**: Create two bot integrations for one company, link each to a
company-owned project, verify tokens are not returned after save, and verify a
bot cannot be linked to another company's project.

**Acceptance Scenarios**:

1. **Given** a company admin owns a project, **When** they submit a Telegram bot
   token and select that project, **Then** the system validates the token, stores
   encrypted secret data, records Telegram bot identity, generates webhook
   routing data, and returns integration metadata without the token.
2. **Given** a company admin has multiple projects, **When** they create multiple
   bot integrations, **Then** each integration links to exactly one selected
   company-owned project.
3. **Given** a project owned by another company, **When** a company admin tries
   to link a bot to it, **Then** the backend rejects the request.
4. **Given** an existing bot integration, **When** the company admin disables,
   enables, tests readiness, rotates the token, edits settings, or deletes it,
   **Then** the change applies only to that company's bot integration.

---

### User Story 3 - Telegram Customer Gets Answers From Linked Project (Priority: P1)

As a Telegram customer, I can message a company's Telegram bot and receive an
answer generated from that bot's linked project without logging into the
dashboard.

**Why this priority**: This is the primary customer-support workflow and must
prove that Telegram traffic is tenant- and project-scoped.

**Independent Test**: Simulate a Telegram webhook update for a configured bot and
verify the system creates the customer, conversation, customer message, bot
answer, and Telegram response using only the linked project.

**Acceptance Scenarios**:

1. **Given** an active bot integration linked to a processed project, **When** a
   Telegram text message arrives at its webhook URL, **Then** the system resolves
   the bot integration by integration id and webhook secret.
2. **Given** a resolved active integration, **When** the message is processed,
   **Then** the system creates or updates the Telegram customer, creates or finds
   an open conversation, stores the customer message, generates an answer using
   the linked project, stores the bot reply, sends the reply to Telegram, and
   updates conversation activity.
3. **Given** the linked project is invalid, unavailable, or not ready, **When** a
   Telegram message arrives, **Then** the system does not auto-select another
   project, records the integration error, and returns safe fallback behavior
   where appropriate.
4. **Given** `show_sources_to_customer` is false, **When** a bot replies to a
   Telegram customer, **Then** internal sources and retrieval metadata are stored
   internally but not shown to the customer.

---

### User Story 4 - Company Admin Handles Conversations (Priority: P2)

As a company admin, I can view my company's Telegram conversations, inspect
message history and internal answer metadata, reply manually, escalate, resolve,
assign, or block a customer.

**Why this priority**: Durable support workflows turn bot answers into an
operational customer-support product.

**Independent Test**: Create a conversation through a webhook simulation, list it
as the owning company, view its messages, send a manual reply, escalate and
resolve it, then verify another company cannot access it.

**Acceptance Scenarios**:

1. **Given** a company has Telegram conversations, **When** the company admin
   opens the Conversations view, **Then** only that company's conversations are
   listed with status, bot, project, customer, unread count, and last activity.
2. **Given** a company admin opens a conversation, **When** messages are shown,
   **Then** customer, bot, agent, system, and error messages are visible with
   internal sources and retrieval metadata where available.
3. **Given** a company admin sends a manual reply, **When** the reply is sent,
   **Then** the system sends it through the linked Telegram bot and stores the
   message as an agent reply.
4. **Given** a company admin blocks a customer, **When** that customer sends
   another Telegram message, **Then** the system does not answer the blocked
   customer.
5. **Given** a company admin assigns a conversation in v1, **When** the assignment
   is saved, **Then** the conversation is assigned only to that same current
   company admin.

---

### User Story 5 - Platform Owner Monitors All Companies (Priority: P2)

As the platform owner, I can use the Admin Console to view all companies,
projects, bot integrations, conversations, messages, usage, errors, and suspend
or activate company accounts.

**Why this priority**: The platform owner needs cross-company operational control
without weakening company endpoint ownership rules.

**Independent Test**: Promote or seed a platform owner, create two companies with
projects and conversations, verify the platform owner can view all data through
`/admin/*`, and verify company endpoints still show only company-owned data.

**Acceptance Scenarios**:

1. **Given** a `platform_owner` user, **When** they request `/admin/companies`,
   **Then** all company accounts are visible.
2. **Given** a company id, **When** the platform owner opens its admin detail
   views, **Then** the platform owner can see that company's projects, bot
   integrations, conversations, and messages.
3. **Given** a non-platform-owner user, **When** they request any `/admin/*`
   endpoint, **Then** the backend returns `403`.
4. **Given** a platform owner suspends a company, **When** that company attempts
   restricted product actions, **Then** active-account checks prevent those
   actions until reactivated.

---

### User Story 6 - Legacy Bot Config Remains Demo Only (Priority: P3)

As an operator, I can keep legacy Telegram bot config behavior available only for
local/demo compatibility while production Telegram behavior uses database-backed
bot integrations.

**Why this priority**: The project can preserve existing local behavior while
removing it from production customer-support flows.

**Independent Test**: Verify production webhook/customer-query paths do not read
global `active_project_id`, do not login through service/admin credentials, and
do not auto-select a project.

**Acceptance Scenarios**:

1. **Given** product Telegram traffic, **When** a customer message is processed,
   **Then** the system resolves the database bot integration and does not read
   global `bot_config.json` or `active_project_id`.
2. **Given** product Telegram traffic, **When** a customer question is answered,
   **Then** the system does not authenticate as `BOT_API_*` or `AUTH_ADMIN_*`.
3. **Given** legacy bot configuration endpoints remain available, **When** they
   are used, **Then** responses indicate the legacy behavior is deprecated or
   limited to demo/local use.

### Edge Cases

- What happens when a Telegram webhook uses an unknown integration id or invalid
  webhook secret?
- What happens when a bot integration is disabled, inactive, or in error status?
- What happens when Telegram sends a non-text update?
- What happens when the Telegram customer is blocked?
- What happens when the linked project has no processed documents or usable
  chunks?
- What happens when the LLM, embedding provider, vector provider, or Telegram API
  is unavailable?
- What prevents a company from linking a bot to another company's project?
- What prevents a Telegram message from falling back to another project?
- What prevents customer replies from exposing internal sources or debug
  metadata?
- What happens when token validation succeeds but webhook registration fails?
- What happens when manual reply delivery to Telegram fails?
- Duplicate Telegram webhook deliveries are handled idempotently by detecting
  the same bot integration plus Telegram message or update id; duplicates must
  not create duplicate messages and must not trigger another bot reply.
- How does the system handle suspended company accounts?
- How does the system protect tokens, webhook secrets, raw payloads, and stack
  traces in errors and logs?
- What happens when one bot integration exceeds its per-minute message limit or
  maximum concurrent in-flight answer limit?
- How does the system purge or redact sanitized raw Telegram payloads after 30
  days?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve the existing RAG pipeline and keep
  `POST /projects/{project_id}/query` available for authenticated web/admin
  testing.
- **FR-002**: The system MUST represent normal dashboard users as company
  accounts by default and support `company_admin` and `platform_owner` roles.
- **FR-003**: The system MUST support active and suspended company account
  statuses.
- **FR-004**: The system MUST enforce `owner_id == current_user.id` for all
  company-owned projects, documents/assets, bot integrations, customers,
  conversations, messages, settings, and usage data.
- **FR-005**: The system MUST expose cross-company visibility only through
  `/admin/*` endpoints restricted to `platform_owner` users.
- **FR-006**: The system MUST prevent non-platform-owner users from accessing
  `/admin/*` routes.
- **FR-007**: The system MUST allow a platform owner to view all companies,
  company projects, bot integrations, conversations, messages, usage, errors,
  and platform stats.
- **FR-008**: The system MUST allow a platform owner to suspend and activate
  company accounts.
- **FR-009**: The system MUST allow each company admin to create, list, view,
  update, disable, enable, test, rotate-token, and delete only their own Telegram
  bot integrations.
- **FR-010**: Each bot integration MUST belong to exactly one owner/company and
  exactly one project.
- **FR-011**: The system MUST allow a company to create multiple bot
  integrations and link multiple bot integrations to the same project.
- **FR-012**: The system MUST validate that a selected project belongs to the
  current company admin before creating or updating a bot integration.
- **FR-013**: The system MUST validate a Telegram bot token with Telegram before
  activating the integration.
- **FR-014**: The system MUST encrypt Telegram bot tokens before storage and
  store a token hash for uniqueness or deduplication.
- **FR-015**: The system MUST NOT return saved bot tokens in API responses or
  expose them in frontend views after creation.
- **FR-016**: The system MUST NOT write bot tokens, webhook secrets, internal
  credentials, stack traces, or raw sensitive payloads to logs or client-facing
  errors.
- **FR-017**: The system MUST generate unguessable webhook secrets for bot
  integrations.
- **FR-018**: The system MUST register, update, and delete Telegram webhooks as
  required by bot integration lifecycle operations.
- **FR-019**: The system MUST expose readiness/status checks for bot
  integrations covering token validity, webhook configuration, linked project
  existence, linked project ownership, usable chunks, provider readiness,
  integration status, and last error.
- **FR-020**: The production Telegram webhook MUST resolve every incoming
  customer message through `bot_integration_id` plus webhook secret.
- **FR-021**: The production Telegram webhook MUST ignore or safely handle
  inactive, disabled, or invalid bot integrations without querying another
  project.
- **FR-022**: The production Telegram webhook MUST create or update a Telegram
  customer from Telegram update data.
- **FR-023**: The production Telegram webhook MUST create or find an open
  conversation for the resolved customer and bot integration.
- **FR-024**: The system MUST persist every customer message before or during
  answer processing.
- **FR-025**: The system MUST generate customer bot answers by reusing the
  existing retrieval and answer stack with `owner_id` and linked `project_id`
  from the resolved bot integration.
- **FR-026**: The system MUST NOT use `bot_config.json`, global
  `active_project_id`, service/admin login, or first-project auto-selection for
  production customer Telegram queries.
- **FR-027**: The system MUST save every bot reply with answer sources,
  context/retrieval metadata, delivery status, and useful error information when
  available.
- **FR-028**: The system MUST send bot replies through the integration's
  Telegram bot token.
- **FR-029**: The system MUST hide internal sources and retrieval/debug metadata
  from Telegram customers by default.
- **FR-030**: The system MUST expose sources to Telegram customers only when the
  bot integration explicitly enables `show_sources_to_customer`.
- **FR-031**: The system MUST support configurable welcome, fallback, and handoff
  messages for bot integrations.
- **FR-032**: The system MUST support bot language and tone settings for
  customer-facing bot behavior.
- **FR-033**: The system MUST support human handoff settings and mark or
  escalate conversations when handoff is needed.
- **FR-034**: The system MUST allow company admins to list and filter only their
  own conversations by status, bot, project, and unread state.
- **FR-035**: The system MUST allow company admins to view only their own
  conversation message history.
- **FR-036**: The system MUST allow company admins to send manual replies through
  the linked Telegram bot and store those replies as `agent` messages.
- **FR-037**: The system MUST allow company admins to resolve, escalate, assign,
  and block customers for their own conversations where supported.
- **FR-038**: The system MUST prevent blocked Telegram customers from receiving
  automated answers.
- **FR-039**: The frontend MUST provide navigation for Dashboard,
  Projects/Knowledge Bases, Smart Chat, Telegram Bots, Conversations, AI
  Settings, Account Settings, and Admin Console only for platform owners.
- **FR-040**: The frontend MUST provide Telegram Bots list and create/edit
  workflows where users enter a token only during creation or rotation.
- **FR-041**: The frontend MUST provide a Conversations inbox, conversation
  detail view, internal source/retrieval metadata for company review, and manual
  action controls.
- **FR-042**: The frontend MUST show linked Telegram bots in project detail views
  and provide a way to connect a Telegram bot to the project.
- **FR-043**: The frontend MUST provide an Admin Console visible only to
  `platform_owner` users while relying on backend authorization for security.
- **FR-044**: Existing upload, processing, indexing, and web project query flows
  MUST continue to work after the SaaS Telegram changes.
- **FR-045**: `AGENTS.md`, `backend/ENDPOINTS.md`, `README.md` when setup or
  behavior changes, and architecture documentation MUST be updated when this
  feature is implemented.
- **FR-046**: The system MUST handle duplicate Telegram webhook deliveries
  idempotently by detecting repeated Telegram message or update identifiers per
  bot integration, returning success, and not saving duplicate messages or
  sending duplicate bot replies.
- **FR-047**: The system MUST support controlled platform-owner bootstrap through
  a configured username or seed flow that promotes or creates only that specific
  user; first-user automatic promotion and implicit `AUTH_ADMIN_USERNAME`
  promotion are not product requirements.
- **FR-048**: Conversation assignment in v1 MUST allow assignment only to the
  current company admin. `assigned_to_user_id` remains available for future
  support-agent or team-member expansion.
- **FR-049**: The production Telegram webhook MUST enforce throttling per bot
  integration using both a messages-per-minute cap and a maximum concurrent
  in-flight answer cap. Throttled requests must fail safely without querying a
  different project.
- **FR-050**: The system MAY store sanitized raw Telegram payloads for debugging,
  but it MUST purge or redact those raw payloads after 30 days. Normalized
  conversation fields and message content may remain according to conversation
  retention needs.

### Key Entities *(include if feature involves data)*

- **User**: Existing dashboard user. Gains role and account status concepts.
  `company_admin` users own company-scoped data. `platform_owner` users access
  cross-company admin views.
- **Project**: Existing company-owned knowledge base used by web/admin chat and
  linked bot integrations.
- **Asset/Document**: Existing uploaded document stored and processed into
  chunks for a project.
- **Chunk**: Existing retrievable unit of document content used by vector search
  and answer generation.
- **Bot Integration**: Database-backed Telegram bot configuration owned by one
  company and linked to one project. Holds Telegram identity, encrypted token,
  token hash, webhook secret, status, behavior settings, and last error.
- **Telegram Customer**: External Telegram user/contact scoped to a bot
  integration and company. Does not authenticate as a dashboard user.
- **Conversation**: Durable support thread for one Telegram customer, one bot
  integration, and one linked project. Tracks status, assignment, unread count,
  last activity, handoff state, and resolution.
- **Conversation Message**: Durable message event in a conversation. Sender types
  include customer, bot, agent, system, and error. Bot messages may store
  internal sources and retrieval metadata. Sanitized raw Telegram payloads may be
  stored temporarily for up to 30 days before purge or redaction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A company admin can create at least two Telegram bot integrations
  linked to company-owned projects without receiving saved bot tokens back from
  the API.
- **SC-002**: A company admin cannot create or update a bot integration linked to
  a project owned by another company.
- **SC-003**: A simulated Telegram webhook message creates or updates exactly one
  Telegram customer, one open conversation, one customer message, and one bot
  reply for the resolved bot integration.
- **SC-004**: A Telegram bot answer uses only the project linked to the resolved
  bot integration and never auto-selects another project.
- **SC-005**: Customer-facing Telegram replies hide sources and retrieval/debug
  metadata by default.
- **SC-006**: Company A cannot list, view, reply to, resolve, escalate, assign,
  or block Company B conversations.
- **SC-007**: A `platform_owner` user can view all companies, projects, bot
  integrations, conversations, and messages through `/admin/*` routes.
- **SC-008**: A non-platform-owner user receives `403` from every `/admin/*`
  endpoint.
- **SC-009**: Automated or smoke tests prove production Telegram customer queries
  do not use global `active_project_id`, `bot_config.json`, service/admin login,
  or project auto-selection.
- **SC-010**: Existing document upload, process/index, and
  `POST /projects/{project_id}/query` smoke coverage still passes.

## Assumptions

- Existing authenticated users can represent company accounts for the first
  production SaaS version.
- A full organizations/team-members model, billing/plans, WhatsApp, advanced
  analytics, and CRM integrations are out of scope for this feature but must not
  be blocked by the design.
- Support-agent/team assignment is out of scope for v1; assignment is limited to
  the current company admin.
- A platform owner is created through a configured username or seed flow that
  promotes or creates only that specific user.
- Telegram token validation and webhook registration can be mocked in automated
  smoke tests where real Telegram access is unavailable.
- The existing RAG query stack can be called internally without requiring a
  Telegram customer to login as a dashboard user.
- Legacy `telegram_bot` behavior may remain for local/demo compatibility, but
  production customer-support traffic uses backend webhooks and bot integrations.
- The first version may ignore non-text Telegram messages while handling them
  safely and without errors visible to customers.
