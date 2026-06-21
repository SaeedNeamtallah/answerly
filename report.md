# RAGMind Failure Audit Report

Date: 2026-06-20  
Branch/worktree: dirty local checkout with WhatsApp integration in progress  
Scope: code-review graph context, repo docs, backend/frontend validation, Docker logs, live API checks, and Chrome browser automation through Python Playwright.

## Executive Summary

The application is running locally, but it is not in a healthy release state.

The highest-impact failures are:

1. Backend tests cannot collect because `backend.routes.auth_mfa` is missing while security regression tests still import it.
2. Frontend validation is failing: `pnpm lint` has 14 errors and `pnpm typecheck` cannot resolve `qrcode`.
3. Browser runtime calls are trying to reach `http://backend:8000/conversations`, which only resolves inside Docker, not in a user's browser.
4. WhatsApp session persistence is wired to the wrong path. Compose mounts `/app/sessions`, but the bridge writes under `/uploads/whatsapp_sessions`.
5. WhatsApp integration status is split between DB and bridge memory. The DB remains `pending` while the bridge reports `qr_ready`.
6. Security Center is reachable as a route for a company-admin smoke user and then repeatedly fires forbidden security requests and SSE retries.
7. The outbox schedulers poll every 2 seconds even when idle, creating noisy logs and avoidable load.

## Evidence Collected

- `code-review-graph` incremental refresh completed.
- Graph risk: 18 changed files, 26 changed symbols/classes, 26 test gaps, overall risk score `0.40`.
- Architecture warnings: high coupling between `backend-config` and `routes-admin`; large `ui-admin` frontend community.
- Live containers were up: backend, frontend, worker, scheduler, WhatsApp bridge, Postgres, Redis, Qdrant, Prometheus, Grafana, nginx.
- Backend health: `GET http://127.0.0.1:8000/health/live` returned `200`.
- Frontend login: `GET http://127.0.0.1:3001/login` returned `200`.
- Browser automation used installed Chrome via Python Playwright. A Chrome DevTools MCP tool was not available in this session.

## Critical Findings

### 1. Backend Test Suite Is Broken At Collection

Evidence:

- `.venv\Scripts\python.exe -m pytest -q backend/tests` fails during collection.
- Error: `ImportError: cannot import name 'auth_mfa' from 'backend.routes'`.
- `backend/tests/test_security_regressions.py:16` imports `auth_mfa`.
- `backend/tests/test_security_regressions.py:194-198` patches and calls `auth_mfa.verify_mfa(...)`.
- `backend/routes/auth_mfa.py` is absent.
- `backend/main.py:186-187` registers only `auth` and `auth_oauth`, not an MFA route.

Impact:

No backend regression suite can run until collection is fixed. This blocks reliable security, auth, and WhatsApp validation.

Best fix:

Decide whether MFA was intentionally removed or accidentally deleted.

- If MFA should remain: restore `backend/routes/auth_mfa.py`, register it in `backend/main.py`, and make tests match the current MFA API.
- If MFA was intentionally removed: delete or rewrite the stale MFA route tests and update `AGENTS.md` because it still describes MFA-enforced privileged access.

### 2. Frontend Build Readiness Is Broken

Evidence:

- `pnpm lint` fails with 14 errors and 48 warnings.
- Representative lint failures:
  - `frontend-next/src/app/(admin)/admin/settings/page.tsx:40`: synchronous `setState` in effect.
  - `frontend-next/src/app/(admin)/admin/settings/page.tsx:59`: `any`.
  - `frontend-next/src/app/(company)/knowledge-bases/page.tsx:45`: unescaped apostrophe.
  - `frontend-next/src/app/(company)/security/page.tsx:22,29`: `any`.
  - `frontend-next/src/app/(company)/whatsapp-bots/[botId]/page.tsx:57`: synchronous `setState` in effect.
  - `frontend-next/src/components/security/EventsFeed.tsx:53`: `let` should be `const`.
  - `frontend-next/src/components/security/IncidentDetailsDrawer.tsx:52,70`: `any`.
  - `frontend-next/src/lib/api/security.ts:19,46`, `frontend-next/src/lib/api/incidents.ts:46`, `frontend-next/src/lib/types/security.ts:11`: `any`.
- `pnpm typecheck` fails:
  - `src/app/(company)/whatsapp-bots/[botId]/page.tsx(28,20): Cannot find module 'qrcode' or its corresponding type declarations.`
- `frontend-next/package.json` declares `qrcode` and `@types/qrcode`, but local `frontend-next/node_modules/qrcode` and `frontend-next/node_modules/@types/qrcode` are missing.

Impact:

The frontend cannot be treated as build-clean. The WhatsApp detail page is currently typecheck-blocking in the local install.

Best fix:

Run a clean install from `frontend-next` and commit/update the lockfile if needed:

```powershell
cd frontend-next
pnpm install
pnpm typecheck
pnpm lint
```

Then fix the actual lint errors rather than suppressing them. For the QR effect, prefer deriving QR data with React Query/select or a guarded async effect that does not synchronously clear state inside the effect body.

### 3. Browser Runtime Uses Docker-Internal Backend Host

Evidence:

- Chrome automation with a fresh valid company-admin token loaded protected pages.
- Browser console/network repeatedly showed:
  - `http://backend:8000/conversations`
  - `net::ERR_NAME_NOT_RESOLVED`
- Affected routes included `/dashboard`, `/conversations`, `/onboarding`, and navigation between company pages.
- `frontend-next/next.config.ts:7-15` rewrites `/api/*` to `process.env.BACKEND_URL || http://localhost:8000`.
- `docker/docker-compose.yml:46-54` sets `NEXT_PUBLIC_API_BASE_URL=/api` and `BACKEND_URL=http://backend:8000`.
- `frontend-next/src/components/security/EventsFeed.tsx:61` and `:121` manually build URLs from `NEXT_PUBLIC_API_BASE_URL`.

Impact:

Some frontend requests are leaking an internal Docker hostname into browser-side fetches. Browser clients cannot resolve `backend`, so key pages hang, produce console errors, and can fail `networkidle` waits.

Best fix:

Keep browser-facing API URLs relative (`/api`) and keep Docker-internal hostnames only in server-side rewrites.

- Audit all direct `fetch(...)` calls and route them through `apiRequest` or a helper that normalizes `/api`.
- Never expose `http://backend:8000` through `NEXT_PUBLIC_*`.
- For SSE/export paths in `EventsFeed`, use `/api/security/events/stream` and `/api/security/events/export`, or a shared `getBrowserApiBaseUrl()` that returns `/api` in browser builds.
- Rebuild the frontend image after changing env/build args because `NEXT_PUBLIC_*` is baked into client bundles.

### 4. WhatsApp Session Persistence Is Pointed At The Wrong Path

Evidence:

- `docker/docker-compose.yml:296` mounts `../uploads/whatsapp_sessions:/app/sessions`.
- `whatsapp-bridge/src/whatsappClient.ts:15` uses:
  - `path.join(__dirname, '../../uploads/whatsapp_sessions')`
- In the container, compiled `__dirname` is `/app/dist`, so the code resolves to `/uploads/whatsapp_sessions`, not `/app/sessions`.
- Container inspection showed `/app/sessions` exists but the session directories are under `/uploads/whatsapp_sessions`.

Impact:

Baileys auth state is not using the mounted persistent volume. Sessions may not survive container rebuilds/restarts as intended, violating `specs/007-whatsapp-integration/spec.md` FR-002.

Best fix:

Make the session directory explicit and environment-driven:

```ts
const sessionsDir = process.env.WHATSAPP_SESSION_DIR || "/app/sessions";
```

Set `WHATSAPP_SESSION_DIR=/app/sessions` in compose and production infrastructure. Add a bridge health/debug endpoint or startup log showing the resolved session path.

### 5. WhatsApp DB Status Does Not Track Bridge Status

Evidence:

- Created a smoke project and WhatsApp integration under an isolated audit user.
- `POST /whatsapp-integrations/{id}/connect` returned `200`.
- `GET /whatsapp-integrations/{id}/session-status` later returned `{"status":"qr_ready","qr":"..."}`.
- `GET /whatsapp-integrations/{id}` still returned `"status":"pending"`.
- `backend/services/whatsapp_integration_service.py:48` initializes `status="pending"`.
- `backend/routes/whatsapp_integrations.py:214-229` reads status from the bridge but does not persist it.
- `whatsapp-bridge/src/whatsappClient.ts:53-74` updates only in-memory bridge status.

Impact:

The UI and backend API can disagree about integration truth. Lists and dashboards that read the DB can show stale status even when the bridge has a QR ready or is connected/disconnected.

Best fix:

Introduce a backend status update contract from the bridge to FastAPI:

- On QR ready: persist `status="qr_ready"` or `status="connecting"` plus optional `last_qr_at`.
- On open: persist `status="connected"`.
- On close/logged out: persist `status="disconnected"` and `last_error`.
- Keep QR payload out of the DB unless there is a short-lived encrypted cache requirement.

### 6. WhatsApp Bridge Reconnect Loop Can Run Forever For Unpaired Sessions

Evidence:

- `docker logs ragmind-whatsapp-bridge` repeatedly shows `Error: QR refs attempts ended`.
- The same old session reconnects continuously:
  - `Connection closed for session 2398ff62-f930-441e-8f96-849aa46a7999. Reconnecting: true`
- `whatsapp-bridge/src/whatsappClient.ts:68-72` deletes the in-memory session and reconnects after 5 seconds whenever `shouldReconnect` is true.

Impact:

An abandoned QR flow can create endless reconnect churn and noisy logs. At scale this can become resource waste and makes real bridge failures harder to spot.

Best fix:

Add session lifecycle limits:

- Track QR attempt count and last activity time.
- Stop reconnecting after a configurable expiry window, e.g. 5-10 minutes unpaired.
- Persist a backend `last_error`/`disconnected` status when QR expires.
- Require the user to click "Connect WhatsApp" again to restart a fresh QR session.

### 7. Security Center Is Not Properly Gated In The Company Workspace

Evidence:

- A fresh company-admin smoke user could navigate directly to `/security`.
- The page rendered `Security Center`.
- It repeatedly requested:
  - `/api/security/stats` -> `403`
  - `/api/security/events?limit=30` -> `403`
  - `/api/security/events/stream` -> `403`
- Console repeatedly logged SSE disconnected errors.
- `frontend-next/src/lib/auth/permissions.ts` says `canAccessSecurityCenter()` is only platform owner, admin, or security engineer.
- `frontend-next/src/components/layout/Sidebar.tsx` hides the nav item for company admins, but direct route access still renders the page.

Impact:

Users without access see a broken page instead of a clear forbidden state. The SSE retry loop keeps hammering forbidden endpoints.

Best fix:

Apply a route-level guard to `/security`, not just sidebar hiding. If the user lacks security-center access, redirect to `/forbidden` before mounting `OverviewStats`, `EventsFeed`, or `IncidentsTab`.

Also stop SSE retry loops on `401`/`403`; retries should only happen for transient network or `5xx` failures.

### 8. Outbox Schedulers Are Too Aggressive By Default

Evidence:

- Worker logs show Telegram and WhatsApp outbox tasks firing every 2 seconds while claiming zero messages.
- `backend/celery_app.py:164-171` schedules both outbox tasks from settings.
- `backend/config.py:327-353` default outbox poll intervals are 2 seconds.

Impact:

This is acceptable for a short local demo, but it creates noisy logs and unnecessary DB/Celery traffic in production, especially as worker count grows.

Best fix:

Raise production defaults or split local/demo defaults from production:

- Local/demo: 2 seconds.
- Production: 10-30 seconds, or event-driven enqueue for immediate delivery plus slower recovery sweep for stale `sending` rows.

## Medium Findings

### 9. Host Tooling Was Broken Until Node Path Was Repaired

Evidence:

- Initial `pnpm lint` and `pnpm typecheck` failed because `node.exe` was not on PATH.
- Workaround used `.venv\Lib\site-packages\playwright\driver\node.exe` on PATH.

Impact:

Developer validation commands in `AGENTS.md` can fail misleadingly on this machine.

Best fix:

Install Node.js normally or update local dev scripts to check and report missing Node clearly. Do not rely on Playwright's private driver Node for normal development.

### 10. `python` Alias Is Broken On Host

Evidence:

- `python tools/frontend_backend_binding_audit.py` failed with Microsoft Store alias error.
- `.venv\Scripts\python.exe tools\frontend_backend_binding_audit.py` passed.

Impact:

Docs that say `python ...` may fail on this Windows machine unless the venv Python is used.

Best fix:

Use `.venv\Scripts\python.exe` in Windows validation docs/scripts, or ensure Python launcher/PATH is configured.

### 11. Security Types Are Duplicated And Drifting

Evidence:

- `frontend-next/src/lib/api/security.ts` defines local `SecurityEvent`/`SecurityStats`.
- `frontend-next/src/lib/types/security.ts` defines similar but different `SecurityEvent`/`SecurityStats`.
- Lint errors exist in both files for `Record<string, any>`.

Impact:

Security UI, API clients, and incident components can silently diverge on field shape.

Best fix:

Keep canonical security types in `src/lib/types/security.ts`; API files should import them. Replace `any` metadata with `Record<string, unknown>` or a narrower discriminated metadata type.

## Browser Audit Notes

Chrome automation with a fresh company-admin account confirmed:

- `/knowledge-bases`, `/telegram-bots`, `/whatsapp-bots`, `/smart-chat`, `/account`, and `/security` render top-level routes.
- Admin routes redirect to `/forbidden` for company-admin users, as expected.
- Mobile spot checks rendered `/knowledge-bases`, `/telegram-bots`, `/whatsapp-bots`, and `/security`; `/dashboard` timed out waiting for `networkidle` due to unresolved `http://backend:8000/conversations`.
- The audit clicked safe navigation/menu controls. It intentionally skipped destructive or state-changing actions such as delete, upload, send, connect, save, rotate, reset, logout, and create in the general browser pass.

Because the app had no existing projects/bots/conversations for the fresh user, deep detail pages were only exercised through an isolated smoke WhatsApp integration created for this audit.

## Validation Results

- Backend health: passed.
- Frontend login HTTP availability: passed.
- Docker containers: running.
- Code-review graph refresh: passed.
- `detect_changes`: risk `0.40`, 26 test gaps.
- Backend pytest: failed at collection due missing `auth_mfa`.
- Frontend binding audit: passed with static-page warnings.
- Frontend lint: failed with 14 errors.
- Frontend typecheck: failed because `qrcode` package/types are missing from local install.
- Chrome browser audit: found unresolved `http://backend:8000` requests, security route forbidden loops, and stale-token redirect when using old `auth.json`.
- WhatsApp smoke API: project create passed, integration create passed, connect passed, session status reached `qr_ready`, DB integration status remained `pending`. The temporary smoke integration and project were deleted after validation.

## Recommended Fix Order

1. Restore or remove MFA route/test expectations so backend tests collect.
2. Fix frontend dependency install and typecheck failure for `qrcode`.
3. Fix browser API base leakage: no browser request should target `http://backend:8000`.
4. Add route-level guard for `/security` and stop SSE retry on 403.
5. Fix WhatsApp session persistence path to use `/app/sessions`.
6. Add bridge-to-backend status synchronization for WhatsApp integrations.
7. Add QR expiry/reconnect limits in the WhatsApp bridge.
8. Raise production outbox polling intervals or make outbox delivery event-driven plus recovery sweep.
9. Clean lint errors and reduce duplicated security types.
10. Add tests for WhatsApp create/connect/status/outbox and frontend route guards.

## Tests To Add

- Backend:
  - WhatsApp integration create/list/get/update/delete tenant scoping.
  - WhatsApp connect route handles bridge success/failure.
  - Bridge status callback updates DB status.
  - WhatsApp webhook idempotency by message ID.
  - WhatsApp outbox stale `sending` recovery and bridge failure backoff.
  - Security route permissions for company admin vs security engineer/platform owner.

- Frontend:
  - `/security` redirects or forbidden-renders before mounting queries for unauthorized users.
  - Browser API base is `/api`, never `http://backend:8000`.
  - WhatsApp detail page renders QR status without typecheck or lint failures.
  - Mobile smoke for dashboard/conversations once API base is fixed.

- Bridge:
  - Resolved session path uses `WHATSAPP_SESSION_DIR`.
  - QR expiry stops reconnect loop.
  - `/api/sessions/:id/status` returns stable states.
  - Send endpoint rejects disconnected sessions with a typed error.
