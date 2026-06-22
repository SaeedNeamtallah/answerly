# 3. Browser Runtime Uses Docker-Internal Backend Host

Date: 2026-06-20  
Source: `report.md`

## Evidence

- Chrome automation with a fresh valid company-admin token loaded protected pages.
- Browser console/network repeatedly showed:
  - `http://backend:8000/conversations`
  - `net::ERR_NAME_NOT_RESOLVED`
- Affected routes included `/dashboard`, `/conversations`, `/onboarding`, and navigation between company pages.
- `frontend-next/next.config.ts:7-15` rewrites `/api/*` to `process.env.BACKEND_URL || http://localhost:8000`.
- `docker/docker-compose.yml:46-54` sets `NEXT_PUBLIC_API_BASE_URL=/api` and `BACKEND_URL=http://backend:8000`.
- `frontend-next/src/components/security/EventsFeed.tsx:61` and `:121` manually build URLs from `NEXT_PUBLIC_API_BASE_URL`.

## Impact

Some frontend requests are leaking an internal Docker hostname into browser-side fetches. Browser clients cannot resolve `backend`, so key pages hang, produce console errors, and can fail `networkidle` waits.

## Best Fix

Keep browser-facing API URLs relative (`/api`) and keep Docker-internal hostnames only in server-side rewrites.

- Audit all direct `fetch(...)` calls and route them through `apiRequest` or a helper that normalizes `/api`.
- Never expose `http://backend:8000` through `NEXT_PUBLIC_*`.
- For SSE/export paths in `EventsFeed`, use `/api/security/events/stream` and `/api/security/events/export`, or a shared `getBrowserApiBaseUrl()` that returns `/api` in browser builds.
- Rebuild the frontend image after changing env/build args because `NEXT_PUBLIC_*` is baked into client bundles.

