## 23. Security Center Dashboard APIs

### Explanation

Security Center APIs are protected by security-engineer/admin RBAC. They include security stats, security events, event export, user account status summary, recent user status events, real-time events through Server-Sent Events, and attack simulation. The event stream uses no-cache headers and keepalive behavior.

### Path

`backend/routes/security.py`

```python
@router.get("/stats", response_model=SecurityStatsResponse)
async def security_stats(
    _current_user: User = Depends(require_security_center_access),
):
    return SecurityStatsResponse(**security_dashboard_service.get_stats())


@router.get("/events", response_model=List[SecurityEventResponse])
async def security_events(
    limit: int = Query(default=20, ge=1, le=50),
    _current_user: User = Depends(require_security_center_access),
):
    payload = security_dashboard_service.get_dashboard_payload(limit=limit)
    return _to_event_responses(payload["events"])


@router.get("/users/status-summary", response_model=SecurityUserStatusSummaryResponse)
async def security_users_status_summary(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_security_center_access),
):
    return SecurityUserStatusSummaryResponse(
        **await security_dashboard_service.get_user_status_summary(db=db)
    )
```

---
