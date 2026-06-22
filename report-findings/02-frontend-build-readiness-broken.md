# 2. Frontend Build Readiness Is Broken

Date: 2026-06-20  
Source: `report.md`

## Evidence

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

## Impact

The frontend cannot be treated as build-clean. The WhatsApp detail page is currently typecheck-blocking in the local install.

## Best Fix

Run a clean install from `frontend-next` and commit/update the lockfile if needed:

```powershell
cd frontend-next
pnpm install
pnpm typecheck
pnpm lint
```

Then fix the actual lint errors rather than suppressing them. For the QR effect, prefer deriving QR data with React Query/select or a guarded async effect that does not synchronously clear state inside the effect body.

