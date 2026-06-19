## 18. Security Event Logging

### Explanation

The project has centralized security event logging for login success/failure, signup success/failure, password changes, brute-force attempts, blocked uploads, rate limiting, authorization failures, invalid tokens, simulated XSS/SQL injection attempts, user suspension, blocking, and restoration. Events are stored in an in-memory ring buffer with a maximum of 5,000 events, and actionable events can automatically create incidents.

### Paths

`backend/security/security_event.py`

```python
class SecurityEventType:
    LOGIN_FAIL = "LOGIN_FAIL"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    PASSWORD_CHANGE_SUCCESS = "PASSWORD_CHANGE_SUCCESS"
    PASSWORD_CHANGE_FAIL = "PASSWORD_CHANGE_FAIL"
    SIGNUP_FAIL = "SIGNUP_FAIL"
    SIGNUP_SUCCESS = "SIGNUP_SUCCESS"
    BRUTE_FORCE = "BRUTE_FORCE"
    FILE_UPLOAD_BLOCKED = "FILE_UPLOAD_BLOCKED"
    ATTACK_SIMULATION = "ATTACK_SIMULATION"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTHZ_DENIED = "AUTHZ_DENIED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    RATE_LIMITED = "RATE_LIMITED"
    XSS_ATTEMPT = "XSS_ATTEMPT"
    SQL_INJECTION = "SQL_INJECTION"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_BLOCKED = "USER_BLOCKED"
    USER_RESTORED = "USER_RESTORED"
```

`backend/security/event_service.py`

```python
_MAX_EVENTS = 5000
_EVENTS: Deque[SecurityEvent] = deque(maxlen=_MAX_EVENTS)

def log_event(event_data: SecurityEventCreate | Dict[str, Any]) -> SecurityEvent:
    payload = (
        event_data
        if isinstance(event_data, SecurityEventCreate)
        else SecurityEventCreate.model_validate(event_data)
    )

    event = SecurityEvent(
        event_type=_normalize_event_type(payload.event_type),
        severity=_normalize_severity(payload.severity),
        user_id=payload.user_id,
        username=normalized_username,
        ip_address=_normalize_ip(payload.ip_address),
        message=payload.message,
        metadata=payload.metadata or {},
    )

    with _EVENTS_LOCK:
        _EVENTS.append(event)

    incident_service.trigger_auto_creation(event)

    return event
```

---
