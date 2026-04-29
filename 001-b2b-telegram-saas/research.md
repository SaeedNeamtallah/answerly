# Research: RAGMind B2B SaaS Telegram Support Platform

## Decision 1: Preserve the RAG core and call it internally

**Decision**: Customer Telegram answers will call the existing
`QueryController.answer_query(db, owner_id, project_id, query, top_k, language)`
path through a new `CustomerBotQueryService`.

**Rationale**: `QueryController` already enforces owner/project scoped retrieval
when called with the correct values, and the web route already validates project
ownership for dashboard users. Reusing the controller avoids duplicating vector
search, answer generation, fallback text, provider selection, and retrieval
configuration.

**Alternatives considered**:

- Rebuild a separate Telegram retrieval pipeline: rejected because it risks
  drifting from web query behavior and breaking owner-aware retrieval.
- Call the authenticated HTTP query route as a service account: rejected because
  the constitution forbids customer Telegram queries through service/admin login.

## Decision 2: Store product roles on users, reuse existing account status

**Decision**: Add a `role` field for `platform_owner` and `company_admin`, plus
optional company profile fields. Reuse the existing `User.status` enum
(`ACTIVE`, `BLOCKED`, `SUSPENDED`) for account status instead of adding a second
`account_status` column.

**Rationale**: Current code already enforces account status in
`get_current_db_user()` through `_enforce_account_status_policy()`. Adding a
duplicate account-status field would create contradictory state and extra
migration risk.

**Alternatives considered**:

- Add `account_status` exactly as a new column: rejected because the current
  model already has account status semantics.
- Keep platform owner as environment-derived admin role only: rejected because
  product admin access must be explicit and database-backed for SaaS views.

## Decision 3: Database-backed bot integrations are the Telegram source of truth

**Decision**: Production Telegram traffic resolves through `bot_integrations`
using `{integration_id}/{webhook_secret}` and never through global bot config.

**Rationale**: Each integration stores the owner, linked project, token secret,
webhook secret, and customer-facing behavior. This creates a stable tenant
boundary for every message.

**Alternatives considered**:

- Continue using `uploads/config/bot_config.json`: rejected because a global
  active project cannot support multiple companies safely.
- Auto-select a project when the linked project fails: rejected because it can
  leak data across project or tenant boundaries.

## Decision 4: Backend webhook for product traffic, legacy bot remains demo only

**Decision**: Add `POST /telegram/webhook/{integration_id}/{webhook_secret}` as
the product receiving path. Keep `telegram_bot/` for local/demo compatibility and
document it as deprecated for production product behavior.

**Rationale**: Webhook routing maps cleanly to database bot integrations and
lets each bot have a unique URL and secret. The existing polling bot currently
uses global config and service-account login, which is incompatible with the
SaaS model.

**Alternatives considered**:

- Expand the polling bot to multiplex all companies: rejected because secrets,
  project scoping, scaling, and routing become harder than backend webhooks.

## Decision 5: Token encryption uses an explicit application key

**Decision**: Add `TokenEncryptionService` with
`encrypt_secret(value)`, `decrypt_secret(value)`, and `hash_secret(value)`.
Require `BOT_TOKEN_ENCRYPTION_KEY` for creating or rotating bot integrations.
Use a vetted symmetric encryption library, adding a backend dependency if the
chosen library is not already present.

**Rationale**: Bot tokens must be recoverable for Telegram API calls, but cannot
be stored in plaintext. A separate hash supports uniqueness without decrypting.

**Alternatives considered**:

- Store tokens plaintext: rejected for secret-protection reasons.
- Store only a hash: rejected because sending messages and managing webhooks
  require the original token.

## Decision 6: Telegram API integration uses a small backend service

**Decision**: Add `TelegramApiService` with explicit methods for token
validation, webhook management, and sending messages. Use direct HTTP calls
through `httpx` or a minimal wrapper that redacts tokens from errors.

**Rationale**: The backend product path needs predictable API calls and strict
secret redaction. Direct HTTP calls also keep it independent from the legacy
polling bot package.

**Alternatives considered**:

- Reuse `python-telegram-bot` application objects in backend routes: rejected
  because the product path needs simple request/response service calls, not a
  polling runtime.

## Decision 7: Store internal sources but hide them from customers by default

**Decision**: Save answer sources and retrieval metadata in
`conversation_messages.answer_sources_json`, `context_used`, and
`confidence_score` when available. Customer Telegram text includes sources only
when the integration enables `show_sources_to_customer`.

**Rationale**: Companies need internal traceability, while customers should not
receive document names, similarity scores, chunks, or debug metadata by default.

**Alternatives considered**:

- Drop sources entirely for Telegram: rejected because companies need internal
  review and support context.
- Always append sources to Telegram replies: rejected because it leaks internal
  document details.

## Decision 8: Verification combines unit tests and authenticated smoke checks

**Decision**: Add focused backend tests for services/route authorization and
extend `tools/test_all.py` or add an equivalent smoke path for the full product
flow with mocked Telegram validation/sending.

**Rationale**: Tenant isolation, linked-project-only retrieval, and legacy flow
exclusion must be tested end to end.

**Alternatives considered**:

- Rely on manual testing only: rejected because the critical risks are security
  and isolation regressions.
