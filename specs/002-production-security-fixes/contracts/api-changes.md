# API Contract Changes: Production Security Fixes

**Date**: 2026-04-29  
**Branch**: `002-production-security-fixes`

## Changed Endpoints

### `POST /auth/login` — Cookie-based auth

**Before**: Returns `{"access_token": "...", "token_type": "bearer"}` in JSON body only.

**After**: Returns the same JSON body **and** sets an `HttpOnly` cookie:

```
Set-Cookie: ragmind_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=3600
```

**Backward compatibility**: API clients can still read the JSON body and send `Authorization: Bearer <token>`. The cookie is additive.

---

### `POST /auth/logout` (NEW)

**Purpose**: Clear the auth cookie.

**Response**:
```json
{"detail": "Logged out"}
```
**Cookie**: `Set-Cookie: ragmind_token=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`

---

### `GET /config/providers` — Auth required

**Before**: No authentication required.

**After**: Requires `Authorization: Bearer <token>` header or `ragmind_token` cookie.

**Response**: Unchanged.

---

### `POST /security/simulate` — Safe defaults

**Before**: `escalate_to_block` defaults to `True`.

**After**: `escalate_to_block` defaults to `False`.

**New behavior**:
- If `escalate_to_block=true` and `SECURITY_SIMULATION_DESTRUCTIVE_ENABLED=false` → returns `403`.
- If `escalate_to_block=true` and caller is not `platform_owner` → returns `403`.

---

### `GET /health/live` (NEW)

**Purpose**: Lightweight liveness probe for container orchestrators.

**Response**:
```json
{"status": "alive"}
```

**No dependencies checked**. Always returns `200` if the process is running.

---

## Auth Resolution Order

The `get_current_db_user` dependency resolves credentials in this order:

1. `Authorization: Bearer <token>` header (existing behavior)
2. `ragmind_token` cookie (new)

If both are present, the header takes precedence.
