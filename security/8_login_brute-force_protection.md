## 8. Login Brute-Force Protection

### Explanation

Login is protected against brute-force attacks by tracking failed attempts per username and per IP address. The system uses sliding-window thresholds, temporary blocking, retry-after calculations, and progressive delays. Repeated suspicious login failures are logged as `BRUTE_FORCE` and can lead to suspension or blocking.

### Paths

`backend/services/login_security_service.py`

```python
def record_failed_login(
    self,
    *,
    username: str,
    ip_address: str | None,
    reason: str,
    message: str,
    severity: str = SecuritySeverity.MEDIUM,
) -> FailureRegistration:
    normalized_username = self.normalize_username(username)
    normalized_ip = self.normalize_ip(ip_address)

    log_event({
        "event_type": SecurityEventType.LOGIN_FAIL,
        "severity": severity,
        "username": normalized_username,
        "ip_address": normalized_ip,
        "message": message,
        "metadata": {"username": normalized_username, "reason": reason},
    })

    failure_state = self._tracker.register_failure(
        username_key=normalized_username,
        ip_key=normalized_ip,
    )

    if failure_state.threshold_crossed or failure_state.newly_blocked:
        log_event({
            "event_type": SecurityEventType.BRUTE_FORCE,
            "severity": SecuritySeverity.HIGH,
            "username": normalized_username,
            "ip_address": normalized_ip,
            "message": "Multiple failed login attempts detected",
        })

    return failure_state
```

`backend/routes/auth.py`

```python
async def _apply_progressive_login_delay(failure_state: FailureRegistration) -> None:
    delay_seconds = _resolve_progressive_login_delay_seconds(failure_state)
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)
```

---
