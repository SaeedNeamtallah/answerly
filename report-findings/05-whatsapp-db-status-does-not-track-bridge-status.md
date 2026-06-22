# 5. WhatsApp DB Status Does Not Track Bridge Status

Date: 2026-06-20  
Source: `report.md`

## Evidence

- Created a smoke project and WhatsApp integration under an isolated audit user.
- `POST /whatsapp-integrations/{id}/connect` returned `200`.
- `GET /whatsapp-integrations/{id}/session-status` later returned `{"status":"qr_ready","qr":"..."}`.
- `GET /whatsapp-integrations/{id}` still returned `"status":"pending"`.
- `backend/services/whatsapp_integration_service.py:48` initializes `status="pending"`.
- `backend/routes/whatsapp_integrations.py:214-229` reads status from the bridge but does not persist it.
- `whatsapp-bridge/src/whatsappClient.ts:53-74` updates only in-memory bridge status.

## Impact

The UI and backend API can disagree about integration truth. Lists and dashboards that read the DB can show stale status even when the bridge has a QR ready or is connected/disconnected.

## Best Fix

Introduce a backend status update contract from the bridge to FastAPI:

- On QR ready: persist `status="qr_ready"` or `status="connecting"` plus optional `last_qr_at`.
- On open: persist `status="connected"`.
- On close/logged out: persist `status="disconnected"` and `last_error`.
- Keep QR payload out of the DB unless there is a short-lived encrypted cache requirement.

