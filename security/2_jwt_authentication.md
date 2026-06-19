## 2. JWT Authentication

### Explanation

The backend uses JWT-based authentication. After login, the system issues a signed access token containing `sub`, `roles`, `iat`, and `exp`. Token expiration is enforced, and tokens missing required fields or containing invalid data are rejected. The JWT subject is resolved against the database on every protected request, so deleted or invalid users cannot continue using old tokens.

### Path

`backend/security/jwt_utils.py`

```python
def create_jwt_access_token(
    *,
    subject: str,
    roles: Optional[List[str]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    ttl_minutes = int(expires_minutes or settings.auth_access_token_expire_minutes or 60)
    issued_at = _now_utc()
    expires_at = issued_at + timedelta(minutes=max(1, ttl_minutes))

    payload = {
        "sub": subject,
        "roles": roles or ["user"],
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.auth_jwt_secret_key,
        algorithm=settings.auth_jwt_algorithm,
    )


def decode_jwt_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token,
        settings.auth_jwt_secret_key,
        algorithms=[settings.auth_jwt_algorithm],
        options={"require": ["sub", "exp"]},
    )
```

---
