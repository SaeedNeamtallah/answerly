# 9. Host Tooling Was Broken Until Node Path Was Repaired

Date: 2026-06-20  
Source: `report.md`

## Evidence

- Initial `pnpm lint` and `pnpm typecheck` failed because `node.exe` was not on PATH.
- Workaround used `.venv\Lib\site-packages\playwright\driver\node.exe` on PATH.

## Impact

Developer validation commands in `AGENTS.md` can fail misleadingly on this machine.

## Best Fix

Install Node.js normally or update local dev scripts to check and report missing Node clearly. Do not rely on Playwright's private driver Node for normal development.

