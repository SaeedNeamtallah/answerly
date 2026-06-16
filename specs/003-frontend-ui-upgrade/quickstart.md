# Quickstart: Incremental UI/UX Upgrade

## 1. Confirm Feature Context

```powershell
git status --short --branch
Get-Content .specify/feature.json
```

Expected branch: `003-frontend-ui-upgrade`  
Expected feature directory: `specs/003-frontend-ui-upgrade`

## 2. Work In The Existing Frontend

Production frontend source remains in `frontend-next/`.

Do not recreate the deleted legacy `frontend/` directory. Do not switch scripts to a second production app under `new front`. If a `new front` folder is created later, keep it as a visual prototype only and do not wire it into runtime startup.

## 3. Install Planned Frontend Dependencies

Run from `frontend-next/` during implementation:

```powershell
pnpm add @tanstack/react-table recharts
```

Add missing shadcn components through the CLI after reviewing docs/diffs:

```powershell
pnpm dlx shadcn@latest docs sidebar chart field input-group empty progress tooltip checkbox switch pagination drawer command
pnpm dlx shadcn@latest add sidebar chart field input-group empty progress tooltip checkbox switch pagination drawer command
```

Use `--dry-run` and `--diff` when updating existing components.

## 4. Implement By Blocks

Recommended order:

1. Design foundation: tokens, shell, sidebar, topbar, shared cards, badges, empty/loading/error states.
2. Shared data layer: query key factories, API error handling polish, TanStack Table wrapper.
3. Company dashboard and onboarding blocks.
4. Knowledge bases list/detail, documents table, upload card, linked bots, test chat.
5. Telegram bots list/detail, create/edit drawer, readiness, token rotation.
6. Conversations list/detail, thread, metadata, source panel, reply composer.
7. AI settings and account forms.
8. Admin overview, companies, company detail, bots, conversations, errors.
9. Platform-owner observability page and backend contracts.

Before editing each block, identify existing components and API functions so nothing disappears.

## 5. Observability Integration

Backend work should add platform-owner-only routes described in `contracts/admin-observability-api.md`.

Use existing infrastructure:

- `docker/prometheus.yml`
- `docker/grafana/dashboards/ragmind-overview.json`
- `docker/grafana/dashboards/fastapi-observability-18739.json`
- `docker/grafana/dashboards/postgres-exporter-12485.json`
- `docker/grafana/dashboards/node-exporter-full-1860.json`

Frontend work should add an admin Observability surface or upgrade `/admin/stats` into that surface.

## 6. Validate Each Block

Run from `frontend-next/`:

```powershell
pnpm lint
pnpm typecheck
pnpm build
```

For backend observability routes:

```powershell
pytest backend/tests/test_platform_admin.py backend/tests/test_admin_service.py
```

For full local smoke when the stack is running:

```powershell
python tools/test_all.py
```

Use browser checks for:

- Desktop layout.
- Tablet layout.
- Mobile layout.
- Keyboard navigation.
- Table filtering/sorting/pagination.
- Form validation.
- Admin forbidden/allowed access.
- Grafana/Prometheus unavailable fallback.
