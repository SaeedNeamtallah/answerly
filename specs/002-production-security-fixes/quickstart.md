# Quickstart: Production Security Fixes

**Date**: 2026-04-29  
**Branch**: `002-production-security-fixes`

## Prerequisites

- Existing RAGMind development environment working via `scripts/dev/start.bat`
- Docker Compose running all services
- Python 3.11+ with project dependencies installed

## Verification Steps

After implementing all tasks, verify the fixes in this order:

### 1. Secret Validation

```powershell
# Set production mode with weak secret — should fail to start
$env:ENVIRONMENT = "production"
$env:AUTH_JWT_SECRET_KEY = "change-me-in-env"
python -c "from backend.config import settings"
# Expected: SystemExit or RuntimeError with clear message
```

### 2. Simulation Safety

```powershell
# Call simulate without escalate_to_block — should log events only
curl -X POST http://localhost:8000/security/simulate `
  -H "Authorization: Bearer $TOKEN"
# Expected: escalation_applied=false, no users blocked

# Call simulate with escalate_to_block=true — should return 403 by default
curl -X POST "http://localhost:8000/security/simulate?escalate_to_block=true" `
  -H "Authorization: Bearer $TOKEN"
# Expected: 403 unless SECURITY_SIMULATION_DESTRUCTIVE_ENABLED=true AND user is platform_owner
```

### 3. Cookie Auth

```powershell
# Login — should set cookie
curl -v -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=your_password"
# Expected: Set-Cookie header with ragmind_token

# Access /auth/me with cookie — should work
curl http://localhost:8000/auth/me -b "ragmind_token=<token>"
# Expected: user info returned
```

### 4. Config Provider Auth

```powershell
# Unauthenticated GET /config/providers — should fail
curl http://localhost:8000/config/providers
# Expected: 401

# Authenticated — should work
curl http://localhost:8000/config/providers -H "Authorization: Bearer $TOKEN"
# Expected: provider list
```

### 5. Health Liveness

```powershell
curl http://localhost:8000/health/live
# Expected: {"status": "alive"} — always returns 200
```

### 6. Telegram Outbox (requires bot integration)

```powershell
# Send a message to a configured Telegram bot
# Check conversation_messages table:
# - Bot reply should have delivery_status = "sent"
# - telegram_message_id should be populated
```

## Key Files Modified

| Area                  | Files                                                           |
|-----------------------|-----------------------------------------------------------------|
| Secret validation     | `backend/config.py`                                            |
| Cookie auth           | `backend/security/auth.py`, `backend/routes/auth.py`, `frontend/login.html`, `frontend/app.js` |
| Simulation safety     | `backend/routes/security.py`, `backend/services/security_dashboard_service.py` |
| Telegram outbox       | `backend/services/telegram_webhook_service.py`, `backend/tasks/telegram_outbox.py`, `backend/database/models.py` |
| Config concurrency    | `backend/runtime_config.py`                                    |
| RAG token budget      | `backend/services/answer_service.py`                           |
| Provider auth         | `backend/routes/app_config.py`                                 |
| Health liveness       | `backend/routes/health.py`                                     |
| Structured logging    | `backend/logging_config.py` (new)                              |
| Controller cleanup    | `backend/controllers/document_controller.py`                   |
