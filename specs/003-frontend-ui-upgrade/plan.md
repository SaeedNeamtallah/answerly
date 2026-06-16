# Implementation Plan: Incremental UI/UX Upgrade

**Branch**: `003-frontend-ui-upgrade` | **Date**: 2026-06-13 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/003-frontend-ui-upgrade/spec.md`

## Summary

Upgrade the current `frontend-next` product interface block by block, preserving all existing user journeys and backend bindings while moving the UI toward the dashboard reference style in `screens/*.png`: dark fixed product sidebar, light dense workspace, compact metric cards, table-first operations, right-side drawers, clear badges, chart panels, and role-aware admin surfaces.

The implementation should not replace the app wholesale. Existing pages, components, API clients, auth guards, and business workflows remain the baseline. A separate `new front` folder may be used only as an optional visual prototype or staging reference if needed; production code stays in `frontend-next`.

The main feature expansion is a platform-owner observability page that integrates the already provisioned Grafana and Prometheus dashboards through guarded backend contracts, so product owners can review RAGMind Overview, FastAPI, Postgres, and node/system dashboards without exposing raw local infrastructure or credentials in the frontend.

## Technical Context

**Language/Version**: TypeScript 5, Next.js App Router 16.2.4 currently installed, React 19.2.4, Tailwind CSS v4. Current npm latest check on 2026-06-13 showed Next.js 16.2.9, TanStack Query 5.101.0, TanStack Table 8.21.3, Recharts 3.8.1, shadcn 4.11.0, Tailwind CSS 4.3.1.  
**Primary Dependencies**: Next.js, TypeScript, Tailwind CSS v4, shadcn/ui radix-nova, TanStack Query, TanStack Table, React Hook Form, Zod, Recharts, Zustand, Lucide Icons, sonner. Add missing runtime dependencies `@tanstack/react-table` and `recharts`; add missing shadcn components via CLI rather than custom markup.  
**Storage**: No new user data storage for the UI refresh. Observability uses existing Prometheus/Grafana runtime data plus a backend-owned dashboard catalog/config.  
**Testing**: Frontend `pnpm lint`, `pnpm typecheck`, `pnpm build`, Playwright browser smoke/responsive checks, targeted component/page tests where a runner is added, backend pytest for new admin observability routes, and existing authenticated smoke checks through `tools/test_all.py` when stack validation is required.  
**Target Platform**: Web app served from `frontend-next` on `http://127.0.0.1:3001`, FastAPI backend on `http://127.0.0.1:8000`, local Grafana on `http://127.0.0.1:3000`, local Prometheus on `http://127.0.0.1:9090`.  
**Project Type**: SaaS web application with FastAPI backend and Next.js App Router frontend.  
**Performance Goals**: Keep existing critical journeys responsive; avoid added client waterfalls; keep table filtering/searching immediate for current result sizes; lazy-load heavy chart/dashboard blocks where practical.  
**Constraints**: Preserve existing API contracts and auth model; platform-owner observability only; no frontend secrets; no direct Prometheus/Grafana credential leakage; no replacement of whole routes when localized block upgrades are sufficient; all changes are validated per block before the next unrelated block is marked ready.  
**Scale/Scope**: All current `frontend-next` route surfaces: auth, company dashboard, onboarding, knowledge bases, knowledge-base detail, smart chat, Telegram bots, bot detail, conversations, conversation detail, AI settings, account, admin overview, companies, company detail, admin conversations, admin bot list, admin error fallback, admin stats/observability.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The repository constitution file still contains template placeholders and no enforceable project-specific principles. The practical gate is therefore the repo guidance in `AGENTS.md` plus the feature spec.

Pre-design gates:

- Incremental delivery: PASS - plan upgrades bounded blocks and keeps production code in `frontend-next`.
- Existing behavior preservation: PASS - current routes, components, API clients, auth guards, and role boundaries are part of the contract.
- Security and ownership: PASS - new observability access is platform-owner-only and backend-mediated.
- Framework correctness: PASS - local Next.js docs were checked under `frontend-next/node_modules/next/dist/docs`, and shadcn project context was checked with `pnpm dlx shadcn@latest info --json`.
- Testability: PASS - plan defines frontend, backend, and browser validation gates.

Post-design gates:

- Research resolves all technical unknowns with concrete decisions.
- Contracts include block-level UI validation and admin observability API behavior.
- Data model names only planning/domain entities and avoids unnecessary persistence.
- No constitution violations require complexity tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-frontend-ui-upgrade/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- admin-observability-api.md
|   `-- ui-block-upgrade-contract.md
`-- tasks.md
```

### Source Code (repository root)

```text
frontend-next/
|-- src/app/
|   |-- (auth)/
|   |-- (company)/
|   `-- (admin)/
|-- src/components/
|   |-- admin/
|   |-- bots/
|   |-- conversations/
|   |-- dashboard/
|   |-- knowledge-bases/
|   |-- layout/
|   |-- shared/
|   `-- ui/
|-- src/lib/
|   |-- api/
|   |-- auth/
|   |-- types/
|   `-- utils/
`-- src/store/

backend/
|-- routes/
|-- services/
|-- monitoring/
`-- tests/

docker/
|-- grafana/
|   |-- dashboards/
|   `-- provisioning/
`-- prometheus.yml

screens/
`-- *.png
```

**Structure Decision**: Use the existing `frontend-next` app as the production frontend. Do not recreate the deleted legacy `frontend/` path. Do not create a second production app under `new front`; if a visual scratch area is needed, keep it clearly non-runtime and do not wire scripts or docs to it as the active frontend.

## Complexity Tracking

No constitution violations.

The only added architectural surface is admin observability. It is justified because the frontend cannot safely query or embed Grafana/Prometheus with raw credentials. A backend-mediated, platform-owner-only contract is the simpler secure boundary compared with exposing infrastructure endpoints directly to the browser.
