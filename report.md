# Project Review Report

Date: 2026-05-01

Scope: repository-wide review of backend routes/services/tasks/providers, frontend API/auth flows, runtime scripts, Docker config, and dependency audit results.

## Findings

### High - Fresh document processing can complete without pgvector embeddings

Evidence:
- `backend/tasks/file_processing.py:281-320` flushes new `Chunk` rows, then calls `vector_db.add_vectors(...)` before the worker session commits those rows.
- `backend/providers/vectordb/pgvector_provider.py:255-264` opens a separate session and runs `UPDATE chunks SET embedding=... WHERE id = ...`.

Impact: with the default `pgvector` provider, the separate update transaction cannot see the uncommitted chunk rows. Upload processing can mark an asset `completed` while the new chunks keep `embedding = NULL`, so project queries and bot readiness find no usable context.

Suggested fix: either store embeddings on the same `AsyncSession`/transaction that created the chunks, or commit chunks before the pgvector update and verify update row counts. Add a regression test that processes a document with pgvector and asserts all created chunks have non-null embeddings.

### High - Alembic unknown-revision recovery can silently stamp production databases

Evidence:
- `backend/database/connection.py:67-95` catches unknown Alembic revision errors, deletes `alembic_version`, stamps the current head, and retries without checking `settings.environment`.

Impact: this is documented as a local/dev recovery behavior, but the code runs in every environment. In production, a bad Alembic stamp could be treated as success while missing migrations are skipped, leaving schema drift hidden until runtime failures or data corruption.

Suggested fix: gate this path to `ENVIRONMENT != production` or behind an explicit one-shot recovery flag. Production should fail closed and require an operator migration/stamp decision.

### High - Client-supplied `X-Forwarded-For` is trusted for rate limiting and login abuse controls

Evidence:
- `backend/security/middleware.py:121-144`
- `backend/routes/auth.py:140-142`
- `backend/security/auth.py:209-211`
- `docker/docker-compose.yml:157-158` exposes the backend as `8000:8000`.

Impact: direct clients can spoof `X-Forwarded-For` to rotate the apparent IP address. That weakens unauthenticated endpoint throttling and login brute-force controls. This matters more because the backend port is exposed on all interfaces in compose.

Suggested fix: only honor forwarded headers from a configured trusted proxy list, otherwise use `request.client.host`. Prefer binding local compose ports to `127.0.0.1` unless deliberately deploying behind a real proxy.

### High - Telegram outbox messages can be stuck forever in `sending`

Evidence:
- `backend/tasks/telegram_outbox.py:48-56` only selects `delivery_status == "pending"`.
- `backend/tasks/telegram_outbox.py:90-94` commits `delivery_status = "sending"` before the external Telegram API call.

Impact: if the worker crashes or is killed after the claim commit, the message remains `sending` and will never be selected again. Customer replies can be permanently lost from the delivery loop.

Suggested fix: add a lease timestamp/claim owner and requeue stale `sending` rows, or select both `pending` and expired `sending` messages. Add a test for recovering a stale claimed message.

### High - Dependency audits report known vulnerabilities

Evidence:
- `uvx pip-audit --path .venv\Lib\site-packages` reported:
  - `fastapi 0.109.0` / `PYSEC-2024-38`, fixed in `0.109.1`
  - `python-dotenv 1.0.0` / `CVE-2026-28684`, fixed in `1.2.2`
  - `python-multipart 0.0.6` / multiple advisories, fixed by `0.0.26`
  - `starlette 0.35.1` / `CVE-2024-47874` and `CVE-2025-54121`, fixed by `0.47.2`
- `pnpm audit --prod --audit-level moderate` reported `postcss <8.5.10` through `next -> postcss@8.4.31`.
- Direct requirement lines include `backend/requirements.txt:2`, `backend/requirements.txt:4`, and `backend/requirements.txt:39`.

Impact: request parsing, framework, env parsing, and CSS serialization dependencies include known security issues.

Suggested fix: upgrade FastAPI/Starlette together, bump `python-multipart` and `python-dotenv`, and resolve the Next/PostCSS tree with a Next upgrade or a pnpm override if compatible.

### Medium - Legacy frontend defaults to a public API host instead of localhost

Evidence:
- `frontend/app.js:7`
- `frontend/login.html:79`
- `frontend/signup.html:113`
- `frontend/index.html:897`
- AGENTS says legacy frontend autodiscovery should default to `http://localhost:8000`.

Impact: users opening the legacy frontend can send login/signup/API traffic to `http://52.188.226.80:8000` unless autodiscovery finds another backend first. This contradicts repo docs and can leak credentials/tokens to the wrong host.

Suggested fix: change hardcoded defaults/placeholders to `http://localhost:8000`, then keep query-string and localStorage overrides for remote deployments.

### Medium - `/stats/` exposes global tenant counts to every authenticated user

Evidence:
- `backend/routes/stats.py:20-33` depends on `get_current_db_user` but counts all `Project`, `Asset`, and `Chunk` rows.

Impact: any company user can see global platform counts. That violates the AGENTS rule that company SaaS routes should filter by `owner_id == current_user.id`, unless this endpoint is intentionally platform-owner-only.

Suggested fix: either scope counts through `Project.owner_id == current_user.id`, or require `require_platform_owner_access()` and treat it as an admin metric endpoint.

### Medium - Invalid settings can fall back to insecure defaults

Evidence:
- `backend/config.py:127-132` defines demo defaults for JWT/admin credentials.
- `backend/config.py:324-339` catches settings load errors and retries with default settings.

Impact: a malformed `.env` can make the app start with fallback settings instead of failing. If `ENVIRONMENT=production` was only in the bad `.env`, production secret validation is also bypassed.

Suggested fix: fail startup on settings parsing errors, or only allow fallback defaults under an explicit local/dev flag.

### Medium - Local runtime surfaces bind beyond localhost

Evidence:
- `docker/docker-compose.yml:157-158` publishes backend as `8000:8000`.
- `docker/backend.Dockerfile:37` runs uvicorn on `0.0.0.0`.
- `scripts/dev/start.bat:160-162` starts `python -m http.server` without `--bind 127.0.0.1`.

Impact: local backend and frontend can be reachable from the LAN. With signup/login enabled and default local credentials in several services, accidental exposure increases attack surface.

Suggested fix: use `127.0.0.1:8000:8000` for local compose and start the static frontend with `--bind 127.0.0.1`. Keep wider binding only for an explicit deployment profile.

### Medium - Bot fallback messages cannot be cleared through update APIs

Evidence:
- `backend/routes/bot_integrations.py:39-47` models `fallback_message` as optional.
- `backend/routes/bot_integrations.py:169-178` passes `payload.fallback_message` to the service.
- `backend/services/bot_integration_service.py:202` and `backend/services/bot_integration_service.py:217-218` only update when the value is not `None`.
- Legacy frontend sends `fallback_message: ... || null` at `frontend/app.js:3512` and `frontend/app.js:4072`.

Impact: clients cannot remove an existing fallback message. Sending JSON `null` is indistinguishable from omitting the field, so the old value stays.

Suggested fix: use `payload.model_fields_set` in the route, or pass a sentinel to the service so explicit `null` clears the value.

### Medium - Next bot form wires hidden settings but does not render controls

Evidence:
- `frontend-next/src/components/bots/BotFormDrawer.tsx:18-24` includes `show_sources_to_customer` and `human_handoff_enabled`.
- `frontend-next/src/components/bots/BotFormDrawer.tsx:83-116` renders only name, token, project, and fallback message.
- Create/update pages pass those hidden values at `frontend-next/src/app/(company)/telegram-bots/page.tsx:35-44` and `frontend-next/src/app/(company)/telegram-bots/[botId]/page.tsx:51-59`.

Impact: Next.js users cannot configure source visibility or human handoff, despite backend support and frontend payload wiring.

Suggested fix: add explicit controls for both settings in the bot drawer and preserve existing values on edit.

### Low - Extra tracked dev script contradicts AGENTS script guidance

Evidence:
- `scripts/dev/tempCodeRunnerFile.bat` is tracked and duplicates `newstart.bat` behavior.
- AGENTS says only `setup.bat`, `start.bat`, `stop.bat`, plus the explicit `newstart.bat` exception should exist under `scripts/dev/`.

Impact: future agents/users can pick the wrong script and drift behavior from the supported launch path.

Suggested fix: remove `scripts/dev/tempCodeRunnerFile.bat` from the repo.

### Low - Project graph documentation path is out of sync

Evidence:
- AGENTS references `docs/project-graph.md`.
- The tracked file is root `project-graph.md`, and `.gitignore:124` ignores that path for new generated output.

Impact: future agents following AGENTS will look in the wrong location or regenerate an ignored root artifact.

Suggested fix: move the tracked graph to `docs/project-graph.md` or update AGENTS to point to the root file.

### Low - Deprecation warnings remain in backend tests

Evidence:
- `python -m pytest backend/tests` reports:
  - SQLAlchemy `declarative_base()` deprecation in `backend/database/models.py:17`
  - Pydantic class-based config deprecations in `backend/routes/documents.py:110` and `backend/routes/projects.py:50`

Impact: not breaking today, but these will become upgrade friction for future SQLAlchemy/Pydantic versions.

Suggested fix: switch to `sqlalchemy.orm.declarative_base()` and Pydantic `ConfigDict`.

## Validation Run

- `.venv\Scripts\python.exe -m pytest backend/tests`: 72 passed, 3 warnings.
- `pnpm typecheck` in `frontend-next`: passed.
- `pnpm lint` in `frontend-next`: passed.
- `python -m pip check`: passed.
- `.venv\Scripts\python.exe -m pip check`: passed.
- `pnpm audit --prod --audit-level moderate`: failed with 1 moderate PostCSS advisory.
- `uvx pip-audit -r backend/requirements.txt`: could not build the isolated audit environment because `pg_config` was missing for `psycopg2-binary`.
- `uvx pip-audit --path .venv\Lib\site-packages`: completed and found 8 vulnerabilities across 4 packages.
