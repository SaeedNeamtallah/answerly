# Validation Evidence

This file records commands, browser checks, and backend-binding checks for each upgraded block.

## Setup Evidence

- Dependency install completed after `pnpm store prune` recovered disk space.
- Added runtime dependencies: `@tanstack/react-table`, `recharts`.
- Added test dependency: `@playwright/test`.
- Added shadcn components: `chart`, `checkbox`, `drawer`, `empty`, `progress`, `switch`, `tooltip`.
- Existing shadcn components were not overwritten.
- Reviewed remaining shadcn candidate dry runs. `sidebar` and `field` would overwrite local components; `input-group`, `pagination`, and `command` are not imported by current source and were left out.

## Block Evidence

| Block id | Commands | Browser/viewports | API checks | Result |
|---|---|---|---|---|
| shell.app | `pnpm typecheck`; `pnpm lint` | pending | role guard preserved by code review; admin nav keeps existing routes and adds `/admin/observability` | code complete; browser pending |
| company.dashboard.metrics | `pnpm typecheck`; `pnpm lint`; `python tools/frontend_backend_binding_audit.py` | pending | dashboard uses `listProjects`, `listBotIntegrations`, and `listConversations`; no invented counts | code complete; browser pending |
| company.dashboard.readiness | `pnpm typecheck`; `pnpm lint`; `python tools/frontend_backend_binding_audit.py` | pending | readiness, health, knowledge-base, and recent-conversation blocks derive from real projects/bots/conversations | code complete; browser pending |
| admin.observability | `.venv/Scripts/python.exe -m unittest backend.tests.test_admin_observability`; `pnpm typecheck`; `pnpm lint`; `python tools/frontend_backend_binding_audit.py` | pending | route uses `require_platform_owner_access`; frontend calls `GET /admin/observability/dashboards` and `GET /admin/observability/summary`; Prometheus/Grafana unavailable states use null/unavailable values rather than fake metrics | code complete; browser pending |

## Final Evidence

Pending:

- `pnpm lint` passed for current slice
- `pnpm typecheck` passed for current slice
- `pnpm build` passed for current slice
- backend admin tests passed: `.venv/Scripts/python.exe -m unittest backend.tests.test_admin_observability backend.tests.test_platform_admin backend.tests.test_admin_service`
- Playwright browser checks
- `tools/frontend_backend_binding_audit.py` passed with one warning for intentionally static `frontend-next/src/app/page.tsx`
