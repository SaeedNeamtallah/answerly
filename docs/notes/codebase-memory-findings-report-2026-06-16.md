# Codebase Memory Findings Report - 2026-06-16

Scope: current working tree at `c:\Users\saeid\github projects\ragmind discussed`.

Tools used:

- `mcp__codebase_memory.index_repository(mode="moderate", persistence=true)`: indexed project `C-Users-saeid-github-projects-ragmind-discussed` with 3,684 nodes and 10,732 edges.
- `mcp__codebase_memory.get_architecture`, `trace_path`, and `detect_changes`.
- `code-review-graph` architecture, hub, and bridge checks for repo-level hotspot context.
- Targeted source reads and one executable validator check.

## Findings

### 1. Critical: production secret validation accepts public placeholder auth secrets

Evidence:

- `.env.example:108` sets `AUTH_JWT_SECRET_KEY=change-me-to-a-strong-random-secret-at-least-32-chars`.
- `.env.example:109` sets `AUTH_ADMIN_PASSWORD=change-me-to-a-strong-password`.
- `backend/config.py:354-360` only rejects the old JWT default `change-me-in-env`, JWT secrets shorter than 32 characters, and admin password `admin123`.
- `backend/tests/test_production_security_fixes.py:17-25` only covers the old default values.
- Executable check: constructing `Settings(ENVIRONMENT="production", AUTH_JWT_SECRET_KEY="change-me-to-a-strong-random-secret-at-least-32-chars", AUTH_ADMIN_PASSWORD="change-me-to-a-strong-password", ...)` and calling `_validate_production_secrets()` printed `accepted`.

Failure mode:

If an operator copies `.env.example` into a production environment and fills the other required values, startup accepts a known public JWT signing key and known admin password placeholder. The JWT secret is 53 characters, so it passes the length check.

Impact:

An attacker who knows the example JWT signing key can forge bearer tokens for any user id or role accepted by the application. The known admin password placeholder also weakens the bootstrap account if used.

Recommendation:

- Reject the current `.env.example` placeholder values explicitly.
- Prefer blank auth values in `.env.example` or placeholders that cannot pass production validation.
- Add regression tests that pass the current sample values and assert `SystemExit`.
- Consider requiring `AUTH_ADMIN_PASSWORD_HASH` in production or enforcing a generated strong admin password path.

### 2. High: frontend production Docker build is broken by build-context mismatch

Evidence:

- `scripts/deploy/azure-deploy.ps1:229-232` builds the frontend image with `docker build -f frontend-next/Dockerfile ... -t $webImage .`, so the Docker build context is the repository root.
- `frontend-next/Dockerfile:6` now runs `COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./`, which expects those files at the context root.
- The repository root does not contain `package.json` or `pnpm-lock.yaml`; those files exist under `frontend-next/`.
- Root `.dockerignore:7-14` explicitly includes `frontend-next/package.json`, `frontend-next/pnpm-lock.yaml`, and `frontend-next/pnpm-workspace.yaml`, confirming the current build context was designed around prefixed frontend paths.

Failure mode:

Running the Azure deployment script will fail during the first frontend Docker `COPY` step because the requested package files do not exist at the repository root.

Impact:

Production frontend image publishing is blocked. Backend image build may succeed, but deployment cannot complete cleanly with the current script and Dockerfile combination.

Recommendation:

- Either restore root-context paths in `frontend-next/Dockerfile`, for example `COPY frontend-next/package.json frontend-next/pnpm-lock.yaml frontend-next/pnpm-workspace.yaml ./` and `COPY frontend-next ./`.
- Or change `scripts/deploy/azure-deploy.ps1` to build with `frontend-next` as the context, for example `docker build -f Dockerfile ... frontend-next`, and align `.dockerignore` with that context.
- Add a CI smoke step that runs the exact deployment build command without pushing.

### 3. High: `/metrics` access control trusts private peer IPs on a publicly exposed app

Evidence:

- `backend/monitoring/metrics.py:69-83` treats loopback and all RFC1918 ranges as trusted.
- `backend/monitoring/metrics.py:121-124` allows `/metrics` without a bearer token when `request.client.host` is in those ranges.
- `infra/azure/main.bicep:419-421` exposes the API Container App externally on port 8000.
- The Azure backend environment block does not provision `METRICS_AUTH_TOKEN`.

Failure mode:

For a publicly exposed API behind an ingress proxy, the immediate ASGI peer can be the platform proxy or sidecar on a private address. In that deployment shape, a public request to `/metrics` can be accepted because the app trusts the proxy's private source IP instead of requiring a monitoring credential or an explicitly private ingress.

Impact:

Unauthenticated users may be able to scrape operational metrics from the public API hostname, exposing route names, status code patterns, latency distributions, task/error counters, and other operational signals.

Recommendation:

- In production, require `METRICS_AUTH_TOKEN` or another authenticated scrape path regardless of `request.client.host`.
- If IP trust is retained, base it on explicit configured trusted proxies and intended scrape source ranges, not broad private CIDRs.
- Add tests for a private direct peer with no token and for public-ingress proxy scenarios.
- Provision the metrics token in Azure if the endpoint remains externally routable.

### 4. Medium: unmatched request paths create unbounded Prometheus label cardinality

Evidence:

- `backend/monitoring/metrics.py:100-107` labels metrics with `endpoint = getattr(route, "path", request.url.path)`.
- For unmatched routes, `route` can be absent and the raw request path is used as the `endpoint` label.
- The API app is externally exposed in `infra/azure/main.bicep:419-421`.

Failure mode:

An unauthenticated client can request many unique missing paths such as `/x/<random>`. Each unique path can create a distinct Prometheus time series for `http_requests_total` and `http_request_duration_seconds`.

Impact:

This can inflate in-process metric memory and create noisy or expensive Prometheus scrapes. It also makes dashboards less useful under scan traffic.

Recommendation:

- Collapse missing or unknown routes to a bounded label such as `__unknown__` or `404`.
- Normalize known dynamic routes only through route templates.
- Add a test that two different unknown paths produce the same endpoint label.

## Codebase-Memory Context

The codebase-memory graph identified these high-fan-in or high-blast-radius areas:

- `frontend-next/src/lib/api/client.ts::apiRequest`, called by most frontend API bindings.
- `backend/tasks/file_processing.py::_process_document`.
- `backend/tasks/telegram_query.py::_generate_bot_reply`.
- `backend/tasks/telegram_outbox.py::_deliver_pending_messages`.
- `backend/security/event_service.py::log_event`.
- `backend/runtime_config.py::get_runtime_value`.

Code-review graph warnings matched the same risk profile:

- High coupling between `routes-admin` and `security-access`.
- High coupling between `security-access` and `services-service`.
- High coupling between `backend-config` and `routes-admin`.

## Open Questions And Assumptions

- I treated the current dirty working tree as the review target. `git status --short` shows local edits across backend config, metrics, Docker, Azure, frontend API/layout, and new untracked frontend files.
- I did not run the full backend or frontend test suite.
- I did not run Docker builds because the frontend build-context issue is already statically proven by the deploy script and missing root package files.
- The `/metrics` exposure depends on how the ingress sets `request.client.host`; the broad private-CIDR trust is still unsafe for a public ingress even if one environment happens to pass the public client IP through.

## Brief Project Health Summary

The main product architecture is coherent: FastAPI routes call controllers/services, async Telegram processing is separated into Celery query and outbox tasks, and the Next.js frontend centralizes API calls through `apiRequest`. The current risk is concentrated in production hardening changes and deployment plumbing rather than core RAG flow logic. The two fixes to prioritize are rejecting example auth placeholders in production and repairing the frontend Docker build context.
