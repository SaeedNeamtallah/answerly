## 7. Account Status Enforcement

### Explanation

User accounts support security states such as `ACTIVE`, `SUSPENDED`, and `BLOCKED`. The account status is enforced on every authenticated request, not only during login. Blocked users are denied access, suspended users are denied access until suspension expiry, and expired suspensions can be automatically restored.

### Path

`backend/security/auth.py`

```python
async def _enforce_account_status_policy(
    *,
    db: AsyncSession,
    request: Request,
    auth_service: AuthService,
    user: User,
) -> None:
    user_status, suspended_until, auto_restored = await auth_service.evaluate_user_status(
        db,
        user=user,
        allow_auto_restore=True,
    )

    if user_status == UserAccountStatus.BLOCKED:
        log_event({
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": user.id,
            "username": user.username,
            "message": "Access denied for blocked account",
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account blocked due to security violation",
        )

    if user_status == UserAccountStatus.SUSPENDED:
        log_event({
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": user.id,
            "username": user.username,
            "message": "Access denied for suspended account",
        })
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
```

---
