## 6. Role-Based Access Control

### Explanation

The system supports role-based access control with roles such as `user`, `admin`, `security_engineer`, and `cybersecurity_engineer`. Normal users can access standard application features, while admins and security engineers can access Security Center and incident-management features. Unauthorized role checks are logged as `AUTHZ_DENIED`.

### Path

`backend/security/auth.py`

```python
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SECURITY_ENGINEER = "security_engineer"
ROLE_CYBERSECURITY_ENGINEER = "cybersecurity_engineer"


def resolve_roles_for_username(username: str) -> List[str]:
    normalized_username = _normalize_username(username)
    resolved_roles: List[str] = []

    if normalized_username and normalized_username == _normalize_username(settings.auth_admin_username):
        resolved_roles.append(ROLE_ADMIN)

    if normalized_username and normalized_username in _configured_cybersecurity_engineer_usernames():
        resolved_roles.append(ROLE_SECURITY_ENGINEER)
        resolved_roles.append(ROLE_CYBERSECURITY_ENGINEER)

    resolved_roles.append(ROLE_USER)
    return list(dict.fromkeys(resolved_roles))


async def require_security_center_access(
    request: Request,
    current_user: User = Depends(get_current_db_user),
) -> User:
    roles = resolve_roles_for_username(current_user.username)
    if has_security_engineer_role(roles) or has_role(roles, ROLE_ADMIN):
        return current_user

    log_event({
        "event_type": SecurityEventType.AUTHZ_DENIED,
        "severity": SecuritySeverity.HIGH,
        "user_id": current_user.id,
        "username": current_user.username,
        "message": "Security Center access denied",
    })
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
```

---
