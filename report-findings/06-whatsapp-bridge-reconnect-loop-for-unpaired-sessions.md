# 6. WhatsApp Bridge Reconnect Loop Can Run Forever For Unpaired Sessions

Date: 2026-06-20  
Source: `report.md`

## Evidence

- `docker logs ragmind-whatsapp-bridge` repeatedly shows `Error: QR refs attempts ended`.
- The same old session reconnects continuously:
  - `Connection closed for session 2398ff62-f930-441e-8f96-849aa46a7999. Reconnecting: true`
- `whatsapp-bridge/src/whatsappClient.ts:68-72` deletes the in-memory session and reconnects after 5 seconds whenever `shouldReconnect` is true.

## Impact

An abandoned QR flow can create endless reconnect churn and noisy logs. At scale this can become resource waste and makes real bridge failures harder to spot.

## Best Fix

Add session lifecycle limits:

- Track QR attempt count and last activity time.
- Stop reconnecting after a configurable expiry window, e.g. 5-10 minutes unpaired.
- Persist a backend `last_error`/`disconnected` status when QR expires.
- Require the user to click "Connect WhatsApp" again to restart a fresh QR session.

