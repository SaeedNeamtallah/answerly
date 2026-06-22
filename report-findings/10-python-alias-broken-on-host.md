# 10. `python` Alias Is Broken On Host

Date: 2026-06-20  
Source: `report.md`

## Evidence

- `python tools/frontend_backend_binding_audit.py` failed with Microsoft Store alias error.
- `.venv\Scripts\python.exe tools\frontend_backend_binding_audit.py` passed.

## Impact

Docs that say `python ...` may fail on this Windows machine unless the venv Python is used.

## Best Fix

Use `.venv\Scripts\python.exe` in Windows validation docs/scripts, or ensure Python launcher/PATH is configured.

