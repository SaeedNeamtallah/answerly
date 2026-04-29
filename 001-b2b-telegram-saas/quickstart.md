# Quickstart: Validate RAGMind B2B SaaS Telegram Support Platform

This guide describes how to validate the feature after implementation. It is not
an implementation script.

## 1. Configure Environment

From the repository root, copy `.env.example` to `.env` if needed and configure
the existing RAG providers.

Required for bot integration creation:

```powershell
BOT_TOKEN_ENCRYPTION_KEY=<generated-secret-key>
PUBLIC_WEBHOOK_BASE_URL=https://example.com
```

Use test or mocked Telegram tokens in automated tests. Real Telegram token values
must never be committed, logged, or shared.

## 2. Start The Stack

```powershell
scripts\dev\setup.bat
scripts\dev\start.bat
```

Wait for:

```text
http://127.0.0.1:8000/health
```

to return a healthy status.

## 3. Apply Migrations

Backend startup normally runs Alembic migrations. For manual validation:

```powershell
alembic -c backend/alembic/alembic.ini upgrade head
```

## 4. Validate Existing RAG Behavior

Run the existing authenticated smoke path:

```powershell
python tools/test_all.py
```

Expected:

- signup/login works
- project creation works
- document upload/process works
- `POST /projects/{project_id}/query` works
- cleanup works

## 5. Validate Company Bot Integration Flow

Using tests or API calls:

1. Create company A and company B.
2. Create at least one project for company A.
3. Create a Telegram bot integration for company A linked to company A's
   project.
4. Confirm the API response does not include the bot token.
5. Attempt to link a company A bot integration to company B's project.
6. Confirm the backend rejects the cross-company link.
7. Create a second bot integration for company A.

Expected:

- multiple bots per company work
- every bot links to exactly one project
- tokens are encrypted server-side and not returned
- cross-company project linking is denied

## 6. Validate Telegram Webhook Flow

Simulate a Telegram webhook update against:

```text
POST /telegram/webhook/{integration_id}/{webhook_secret}
```

Expected:

- integration resolves by id and secret
- Telegram customer is created or updated
- open conversation is created or reused
- customer message is saved
- bot answer is generated from the linked project only
- bot reply is saved
- Telegram send call is executed through a mock or test adapter
- no global `active_project_id` is read
- no service/admin login is used
- no alternate project is selected on failure

## 7. Validate Conversation Dashboard Flow

As company A:

1. List conversations.
2. Open a conversation.
3. View messages and internal sources.
4. Send a manual reply.
5. Escalate and resolve the conversation.
6. Block the customer.

Expected:

- company A sees only company A conversations
- manual reply is sent through the linked bot
- agent reply is stored as `sender_type=agent`
- blocked customers do not receive automated answers

As company B:

1. Attempt to access company A conversations and messages.

Expected:

- backend denies access.

## 8. Validate Platform Owner Flow

As `platform_owner`:

1. Request `/admin/companies`.
2. View one company's projects.
3. View one company's bot integrations.
4. View one company's conversations and messages.
5. View platform stats.
6. Suspend and activate a company.

Expected:

- platform owner can see cross-company data only through `/admin/*`.
- company endpoints remain owner-scoped.
- non-platform-owner users receive `403` from `/admin/*`.

## 9. Validate Customer-Safe Output

For a bot integration with `show_sources_to_customer=false`:

1. Simulate a customer question.
2. Inspect the saved bot message.
3. Inspect the Telegram reply text.

Expected:

- internal sources are stored in `conversation_messages`.
- Telegram reply text does not expose document names, similarity scores, raw
  chunks, provider details, or debug metadata.

For a bot integration with `show_sources_to_customer=true`:

1. Simulate a customer question.

Expected:

- customer-visible source output follows the approved customer-safe format.

## 10. Stop The Stack

```powershell
scripts\dev\stop.bat
```
