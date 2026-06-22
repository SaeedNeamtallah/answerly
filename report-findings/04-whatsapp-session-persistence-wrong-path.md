# 4. WhatsApp Session Persistence Is Pointed At The Wrong Path

Date: 2026-06-20  
Source: `report.md`

## Evidence

- `docker/docker-compose.yml:296` mounts `../uploads/whatsapp_sessions:/app/sessions`.
- `whatsapp-bridge/src/whatsappClient.ts:15` uses:
  - `path.join(__dirname, '../../uploads/whatsapp_sessions')`
- In the container, compiled `__dirname` is `/app/dist`, so the code resolves to `/uploads/whatsapp_sessions`, not `/app/sessions`.
- Container inspection showed `/app/sessions` exists but the session directories are under `/uploads/whatsapp_sessions`.

## Impact

Baileys auth state is not using the mounted persistent volume. Sessions may not survive container rebuilds/restarts as intended, violating `specs/007-whatsapp-integration/spec.md` FR-002.

## Best Fix

Make the session directory explicit and environment-driven:

```ts
const sessionsDir = process.env.WHATSAPP_SESSION_DIR || "/app/sessions";
```

Set `WHATSAPP_SESSION_DIR=/app/sessions` in compose and production infrastructure. Add a bridge health/debug endpoint or startup log showing the resolved session path.

