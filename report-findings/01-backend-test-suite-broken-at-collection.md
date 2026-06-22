# 1. Backend Test Suite Is Broken At Collection

Date: 2026-06-20  
Source: `report.md`

## Evidence

- `.venv\Scripts\python.exe -m pytest -q backend/tests` fails during collection.
- Error: `ImportError: cannot import name 'auth_mfa' from 'backend.routes'`.
- `backend/tests/test_security_regressions.py:16` imports `auth_mfa`.
- `backend/tests/test_security_regressions.py:194-198` patches and calls `auth_mfa.verify_mfa(...)`.
- `backend/routes/auth_mfa.py` is absent.
- `backend/main.py:186-187` registers only `auth` and `auth_oauth`, not an MFA route.

## Impact

No backend regression suite can run until collection is fixed. This blocks reliable validation for security, auth, and the new WhatsApp work.

## Best Fix

Decide whether MFA was intentionally removed or accidentally deleted.

- If MFA should remain: restore `backend/routes/auth_mfa.py`, register it in `backend/main.py`, and make tests match the current MFA API.
- If MFA was intentionally removed: delete or rewrite the stale MFA route tests and update `AGENTS.md` because it still describes MFA-enforced privileged access.

