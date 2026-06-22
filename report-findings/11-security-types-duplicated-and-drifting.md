# 11. Security Types Are Duplicated And Drifting

Date: 2026-06-20  
Source: `report.md`

## Evidence

- `frontend-next/src/lib/api/security.ts` defines local `SecurityEvent`/`SecurityStats`.
- `frontend-next/src/lib/types/security.ts` defines similar but different `SecurityEvent`/`SecurityStats`.
- Lint errors exist in both files for `Record<string, any>`.

## Impact

Security UI, API clients, and incident components can silently diverge on field shape.

## Best Fix

Keep canonical security types in `src/lib/types/security.ts`; API files should import them. Replace `any` metadata with `Record<string, unknown>` or a narrower discriminated metadata type.

