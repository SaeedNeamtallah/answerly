## 1. Security Configuration Layer

### Explanation

The project has a centralized security configuration layer that controls JWT secrets, JWT algorithm, token expiration, admin credentials, mutation protection, default suspension duration, rate limiting, brute-force protection, upload inspection, CORS origins, and service-account credentials.

### Path

`backend/config.py`

```python
# Authentication and Security Configuration
auth_jwt_secret_key: str = Field(default="change-me-in-env", alias="AUTH_JWT_SECRET_KEY")
auth_jwt_algorithm: str = Field(default="HS256", alias="AUTH_JWT_ALGORITHM")
auth_access_token_expire_minutes: int = Field(default=60, alias="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
auth_admin_username: str = Field(default="admin", alias="AUTH_ADMIN_USERNAME")
auth_admin_password: str = Field(default="admin123", alias="AUTH_ADMIN_PASSWORD")
auth_admin_password_hash: str = Field(default="", alias="AUTH_ADMIN_PASSWORD_HASH")
security_require_auth_for_mutations: bool = Field(default=False, alias="SECURITY_REQUIRE_AUTH_FOR_MUTATIONS")
security_user_suspension_default_minutes: int = Field(
    default=30,
    alias="SECURITY_USER_SUSPENSION_DEFAULT_MINUTES"
)
security_login_bruteforce_enabled: bool = Field(
    default=True,
    alias="SECURITY_LOGIN_BRUTEFORCE_ENABLED"
)
security_rate_limit_enabled: bool = Field(default=True, alias="SECURITY_RATE_LIMIT_ENABLED")
security_upload_validate_magic: bool = Field(default=True, alias="SECURITY_UPLOAD_VALIDATE_MAGIC")
security_upload_max_scan_bytes: int = Field(default=8192, alias="SECURITY_UPLOAD_MAX_SCAN_BYTES")
```

---
