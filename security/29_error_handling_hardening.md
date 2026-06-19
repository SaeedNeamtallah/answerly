## 29. Error Handling Hardening

### Explanation

Several backend routes catch unexpected exceptions and return generic error messages such as `Internal server error`, `Login failed`, or `Forbidden`. This prevents leaking stack traces or internal implementation details to clients, while detailed logs are still recorded server-side for debugging and monitoring.

### Paths

`backend/routes/auth.py`

```python
except Exception as exc:
    logger.exception("Unexpected error during login")
    log_event({
        "event_type": SecurityEventType.LOGIN_FAIL,
        "severity": SecuritySeverity.HIGH,
        "username": tracking_username,
        "ip_address": tracking_ip,
        "message": "Login failed due to internal error",
        "metadata": {"username": tracking_username, "reason": "internal_error"},
    })
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Login failed",
    ) from exc
```

`backend/routes/query.py`

```python
except Exception:
    logger.exception("Unexpected error while querying project")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---
