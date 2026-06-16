# Implementation Notes: Incremental UI/UX Upgrade

## Ground Rules

- Production work stays in `frontend-next/`.
- Do not recreate the deleted legacy `frontend/` directory.
- Do not use static operational data for product surfaces unless it is explicitly an empty/unavailable fallback.
- Every upgraded route must keep its real `frontend-next/src/lib/api/*` calls, TanStack Query keys, auth guard, and mutation invalidation.
- Each block must be validated before it is marked complete in `tasks.md`.

## Current Progress

- T001 completed: implementation notes created.
- T002 completed: added `@tanstack/react-table`, `recharts`, and `@playwright/test`.
- T003 completed: added safe shadcn components `chart`, `checkbox`, `drawer`, `empty`, `progress`, `switch`, and `tooltip`. Follow-up CLI dry runs reviewed `sidebar`, `field`, `input-group`, `pagination`, and `command`; no current source imports those skipped primitives, and the registry paths would either overwrite customized local components or fail under the local Node/shadcn resolver, so they were intentionally not added.
- T004 completed: screenshot design reference created.
- T005 completed: route-to-backend API binding inventory created.
- T016 completed: backend observability route tests assert platform-owner dependency, allowlisted dashboard URLs, and unavailable-state behavior.
- T019-T020 completed: backend exposes platform-owner-only `/admin/observability/dashboards` and `/admin/observability/summary`.
- T021-T024 completed: frontend observability types, API client, page, and panel are wired to the new backend routes.
- T025 completed for the current shell slice: app shell/sidebar/topbar were upgraded while preserving role guards.
- T027 completed for the current company dashboard slice: metrics and panels use only projects, bot integrations, and conversations returned by backend APIs.
- T040-T041 completed for the current slice: the binding audit passes without failures and validation evidence is recorded.

## Known Implementation Constraint

The shadcn CLI dry runs showed `sidebar` and `field` would overwrite existing local shadcn components, while `input-group`, `pagination`, and `command` were not needed by current imports and were unstable under the local registry resolver. If a later block imports one of these primitives, manually inspect the registry diff first and merge only the new component surface without overwriting local customizations.

Browser checks and production build are still pending for the completed code slices.
