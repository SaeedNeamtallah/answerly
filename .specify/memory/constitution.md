<!--
Sync Impact Report
Version change: 0.0.0 -> 1.0.0
Modified principles:
- Placeholder template -> RAGMind production SaaS constitution
Added sections:
- Core Principles
- Product Scope
- Development Workflow
- Governance
Removed sections:
- Placeholder principle and section tokens from the generated template
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
- ⚠ .specify/templates/commands/*.md not present in this repository
Runtime guidance reviewed:
- ✅ README.md reviewed; no setup or implemented behavior changed by this constitution
- ✅ AGENTS.md reviewed; no code-graph change occurred during constitution update
- ⚠ docs/project-graph.md not present; no architecture doc update possible
- ✅ backend/ENDPOINTS.md reviewed; no endpoint implementation changed
Follow-up TODOs:
- None
-->
# RAGMind Constitution

## Core Principles

### I. Preserve the Existing RAG Core
The existing RAG pipeline is a protected core. Implementations MUST NOT rewrite
document upload, document storage, processing, text extraction, chunking,
embedding generation, vector storage, vector retrieval, answer generation, or the
existing web/admin project query endpoint unless an approved future spec targets
that behavior directly.

The canonical knowledge-base model remains `users`, `projects`,
`assets/documents`, and `chunks`. A project represents a company-owned knowledge
base. `POST /projects/{project_id}/query` MUST remain available for web/admin
testing. Customer-facing Telegram flows MUST reuse the existing retrieval and
answer stack internally while preserving `owner_id` and `project_id` scoping.

Rationale: product expansion must not destabilize the already-working RAG system
or bypass its ownership-aware retrieval behavior.

### II. Tenant Isolation Is Mandatory
Company isolation is a non-negotiable security requirement. `company_admin`
users MUST access only data where `owner_id == current_user.id`.

This applies to projects, documents/assets, chunks/retrieval, bot integrations,
Telegram customers, conversations, conversation messages, settings, and usage
data. A company MUST NOT see or query another company's data.

Telegram customer messages MUST resolve to exactly one bot integration, and that
bot integration MUST define the `owner_id` and `project_id` used for retrieval.
No Telegram message may query a project that is not linked to the receiving bot
integration. Fallback to another project is forbidden.

Rationale: the SaaS product is multi-tenant, so every data path must preserve
tenant boundaries.

### III. Platform Owner Access Must Be Explicit
Cross-company access MUST exist only through explicit platform-owner-only flows:
the `platform_owner` role, `/admin/*` backend routes, and Admin Console frontend
views.

Normal company endpoints MUST NOT be reused to bypass ownership. Admin access
MUST be checked server-side. If `current_user.role` is not `platform_owner`,
`/admin/*` endpoints MUST return `403`.

Rationale: platform oversight is valid only when it is deliberate, auditable, and
separate from company workflows.

### IV. Roles Must Stay Clear
The product has exactly three stable role categories:

- `platform_owner`: owns the platform and may view all companies, projects,
  bots, conversations, messages, usage, and errors through admin-only routes.
- `company_admin`: represents a company account and may manage only its own
  projects, documents, bots, customers, conversations, and settings.
- `telegram_customer`: represents an external Telegram user, does not login to
  the dashboard, is created automatically from Telegram update data, and
  interacts only through a company's Telegram bot.

Dashboard users and Telegram customers MUST NOT be conflated. Telegram
customers are not normal authenticated users.

Rationale: clear role boundaries prevent accidental privilege escalation and
keep customer data modeling separate from dashboard authentication.

### V. Bot Integrations Are the Source of Truth
Production Telegram behavior MUST use database-backed bot integrations.

Production product behavior MUST NOT depend on `bot_config.json`,
`active_project_id`, `BOT_API_USERNAME/BOT_API_PASSWORD` service login,
`AUTH_ADMIN_USERNAME/AUTH_ADMIN_PASSWORD` service login, auto-selecting the
first accessible project, or one global bot serving all companies.

Every production Telegram message MUST follow this flow:

`Telegram update -> bot integration -> owner/company -> linked project ->
customer -> conversation -> message -> RAG answer -> saved bot reply ->
Telegram response`.

Each bot integration MUST belong to exactly one owner/company and exactly one
project. A company may have multiple bot integrations. A project may have
multiple linked bot integrations.

Rationale: bot integrations are the durable tenant, project, and secret boundary
for customer-support traffic.

### VI. Secrets Must Be Protected
Telegram bot tokens are secrets. Bot tokens MUST be accepted only from company
admins who own the linked project, validated with Telegram before activation,
encrypted before storage, excluded from API responses after saving, excluded
from logs, hidden from the frontend after creation, and rotatable.

A token hash may be stored for uniqueness and deduplication. Webhook secrets
MUST be unguessable. Error messages MUST NOT leak tokens, secrets, internal
credentials, stack traces, or raw sensitive payloads.

Rationale: bot tokens grant control over customer-facing channels and must be
handled as production credentials.

### VII. Conversations Must Be Durable
Every customer-support interaction MUST be stored. The system MUST persist the
Telegram customer profile, conversation, customer messages, bot replies, manual
agent replies, system messages, useful error messages, internal sources used for
answers, and context/retrieval metadata when available.

Conversation records MUST support at least `open`, `escalated`, `resolved`, and
`blocked`. Message sender types MUST support at least `customer`, `bot`,
`agent`, `system`, and `error`.

No Telegram customer-support flow may be stateless.

Rationale: durable conversations are required for company dashboards, human
handoff, auditability, and platform monitoring.

### VIII. Customer-Facing Answers Must Be Safe
Telegram customers MUST receive clean, customer-safe answers. By default,
Telegram replies MUST NOT expose internal document names, similarity scores, raw
chunks, debug metadata, provider details, stack traces, or internal source
payloads.

Sources and retrieval metadata may be stored internally for company/admin review.
Sources may be shown to customers only when `show_sources_to_customer` is
explicitly enabled.

If the system cannot answer safely or confidently, it MUST use the configured
fallback or handoff behavior.

Rationale: customer-facing responses must avoid leaking internal knowledge-base
or infrastructure details.

### IX. Human Handoff Must Be Supported
The product MUST support human support workflows. The company dashboard MUST
support, or leave explicit product space for, viewing conversations, filtering by
status, identifying conversations that need human help, manual reply,
escalation, resolve, block customer, and assignment when supported.

If `human_handoff_enabled` is true and the bot cannot answer, the conversation
MUST be eligible to set `needs_human=true` or move to an escalated state.

Rationale: a support product cannot rely exclusively on automation when customer
questions require human judgment.

### X. Product Behavior Must Be Backend-Enforced
Frontend visibility is not security. Backend routes and services MUST enforce
role checks, ownership checks, account status checks, bot/project ownership
checks, conversation ownership checks, token protection, source visibility rules,
cross-company denial, and the ban on project auto-switching.

The frontend may hide or show UI by role, but the backend remains authoritative.

Rationale: client-side controls are easy to bypass; security rules belong in the
server-side product boundary.

### XI. Minimal Change, Maximum Compatibility
Implementations MUST prefer minimal changes that preserve the existing
architecture. For the first production-ready SaaS implementation, existing users
may represent company accounts, a full organizations/team model is not required,
`platform_owner` and `company_admin` roles belong on users, and only the minimum
new product tables required for bots and conversations may be introduced.

Existing controllers and services MUST NOT be rewritten unless necessary.
New services and routes MUST be introduced around the existing RAG core.

The design MUST NOT block future organizations, organization members, support
agents, billing/plans, WhatsApp, advanced analytics, or CRM integrations.

Rationale: the first production SaaS layer must ship without creating migration
debt or breaking the current app.

### XII. Operational Readiness Is Required
Bot integrations MUST expose readiness/status checks. Readiness MUST evaluate
token validity, webhook configuration, linked project existence, linked project
ownership, processed documents or usable chunks, LLM provider readiness,
embedding/vector retrieval readiness, integration status, and last error when
available.

Production flows MUST fail safely. If a bot integration cannot answer because of
configuration or project problems, the system MUST NOT use another project, MUST
save `last_error`, may mark `status=error`, and may return a safe fallback
response.

Rationale: misconfigured bots must not leak data, silently route to unrelated
knowledge bases, or fail without useful operator diagnostics.

### XIII. Testing and Verification Are Required
Any implementation MUST include tests or smoke coverage for critical flows:
existing document upload/process/query, company project creation, multiple bot
integrations per company, denial of bots linked to another company's project,
Telegram webhook customer/conversation/message creation, linked-project-only bot
answers, hidden customer sources by default, company conversation isolation,
platform-owner `/admin/*` access, no production use of global `active_project_id`,
no customer Telegram query through service/admin login, and no project
auto-switching.

No task is complete until core security and isolation behavior is verified.

Rationale: tenant isolation and RAG compatibility are too important to rely on
manual inspection alone.

### XIV. Documentation Must Stay Current
Any structural change MUST update the relevant project documentation. At
minimum, update `AGENTS.md`, `backend/ENDPOINTS.md`, `README.md` when setup or
behavior changes, and `docs/project-graph.md` when architecture changes.

`AGENTS.md` MUST remain concise and code-grounded. It MUST reflect new routes,
services, ownership rules, bot integration flow, admin flow, and deprecated
legacy Telegram behavior when those changes are implemented.

Rationale: stale docs increase agent token cost and raise the chance of unsafe
future changes.

## Product Scope

RAGMind is a production B2B SaaS Telegram customer-support platform built on the
existing RAG knowledge-base system. Feature specs and plans may define concrete
API contracts, database schemas, UI fields, migrations, and rollout details, but
they MUST comply with the principles above.

Detailed schemas and endpoint lists belong in feature specs, implementation
plans, endpoint docs, and migration files unless they express a stable product
rule that belongs in this constitution.

## Development Workflow

Every new spec, plan, and task list MUST explicitly check compliance with this
constitution before implementation begins. If a requested change violates tenant
isolation, secret protection, role separation, RAG core preservation, durable
conversation storage, or backend-enforced product behavior, the agent MUST stop
and ask for clarification.

Plans MUST identify how the work preserves the existing RAG core, enforces
ownership, handles platform-owner access, protects bot secrets, stores
conversations, verifies critical flows, and updates documentation. Task lists
MUST include the corresponding implementation, verification, and documentation
work before marking a feature complete.

## Governance

This constitution takes priority over individual feature prompts when there is a
conflict. Feature specs contain product requirements. Plans contain
implementation strategy. Tasks contain implementation steps. The constitution
contains stable non-negotiable principles.

Amendments MUST be made by updating `.specify/memory/constitution.md`, including
a Sync Impact Report, and checking dependent Spec Kit templates for consistency.
Amendments that remove or redefine core security, role, tenant-isolation, or RAG
preservation guarantees require a MAJOR version bump. New principles or
materially expanded guidance require a MINOR version bump. Clarifications,
wording fixes, and non-semantic refinements require a PATCH version bump.

Compliance review is mandatory for every spec, plan, task list, and
implementation review. A feature MUST NOT be considered complete when it violates
this constitution or lacks verification for the critical security and isolation
flows it touches.

**Version**: 1.0.0 | **Ratified**: 2026-04-27 | **Last Amended**: 2026-04-27
