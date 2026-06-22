# 7. Security Center Is Not Properly Gated In The Company Workspace

Date: 2026-06-20  
Source: `report.md`

## Evidence

- A fresh company-admin smoke user could navigate directly to `/security`.
- The page rendered `Security Center`.
- It repeatedly requested:
  - `/api/security/stats` -> `403`
  - `/api/security/events?limit=30` -> `403`
  - `/api/security/events/stream` -> `403`
- Console repeatedly logged SSE disconnected errors.
- `frontend-next/src/lib/auth/permissions.ts` says `canAccessSecurityCenter()` is only platform owner, admin, or security engineer.
- `frontend-next/src/components/layout/Sidebar.tsx` hides the nav item for company admins, but direct route access still renders the page.

## Impact

Users without access see a broken page instead of a clear forbidden state. The SSE retry loop keeps hammering forbidden endpoints.

## Best Fix

Apply a route-level guard to `/security`, not just sidebar hiding. If the user lacks security-center access, redirect to `/forbidden` before mounting `OverviewStats`, `EventsFeed`, or `IncidentsTab`.

Also stop SSE retry loops on `401`/`403`; retries should only happen for transient network or `5xx` failures.

