# Telegram Bot Incident Report: customerservices

Date: 2026-06-15

## Scope

Investigated the production Telegram integration for `@Saeedaiforservicesaibot` / `customerservices`.

## Exact Problem

Telegram was still registered to an old ngrok webhook URL:

`https://f931-84-233-167-217.ngrok-free.app/telegram/webhook/40/<redacted>`

That public URL no longer routed to the local backend. Telegram reported:

`Wrong response from the webhook: 404 Not Found`

This prevented incoming Telegram updates from reaching `POST /telegram/webhook/{integration_id}/{webhook_secret}`, so no customer messages were inserted into the database and the outbox had nothing to send.

## Evidence Before Fix

- Docker was running.
- Backend liveness was available locally at `http://localhost:8000/health/live`.
- Full backend health was healthy: database, broker, result backend, Celery worker, shared config, vector store, LLM provider, embedding provider, and pgvector.
- Bot integration existed:
  - integration id: `40`
  - Telegram username: `Saeedaiforservicesaibot`
  - Telegram bot id: `8947225451`
  - owner: `saeedneama`
  - linked project id: `160`
  - linked project: `saeed neamtallah`
  - status: `active`
- Linked project had indexed content:
  - chunks: `13`
  - embedded chunks: `13`
- Telegram `getMe` matched the stored bot id and username.
- Telegram `getWebhookInfo` showed:
  - pending updates: `4`
  - last error: `Wrong response from the webhook: 404 Not Found`
- Database had no conversation messages for integration `40`.
- Celery Telegram outbox was polling successfully but repeatedly claimed `0` pending messages.

## Fix Applied

1. Started a new ngrok tunnel to the backend:

   `https://77a3-197-60-142-198.ngrok-free.app -> http://localhost:8000`

2. Verified the new tunnel reaches the backend with a non-browser request:

   `GET /health/live -> {"status":"alive"}`

3. Re-registered Telegram webhook for integration `40` to:

   `https://77a3-197-60-142-198.ngrok-free.app/telegram/webhook/40/<redacted>`

4. Updated the `bot_integrations.webhook_url` row for integration `40`.

5. Updated local `.env`:

   `PUBLIC_WEBHOOK_BASE_URL=https://77a3-197-60-142-198.ngrok-free.app`

## Verification After Fix

Telegram `getWebhookInfo` now shows:

- URL: `https://77a3-197-60-142-198.ngrok-free.app/telegram/webhook/40/<redacted>`
- pending updates: `0`
- last error: `null`

Database/outbox after Telegram retried the queued updates:

- total messages: `8`
- customer messages: `4`
- bot messages: `4`
- pending: `0`
- sending: `0`
- sent: `4`
- failed: `0`

## Residual Risk

This is a working local development fix, but it depends on the current ngrok process staying alive. If ngrok stops or the machine restarts, the free ngrok URL can change and Telegram will break again until `PUBLIC_WEBHOOK_BASE_URL`, `bot_integrations.webhook_url`, and Telegram `setWebhook` are updated.

For a durable production fix, use a stable HTTPS backend URL or a reserved ngrok domain.
