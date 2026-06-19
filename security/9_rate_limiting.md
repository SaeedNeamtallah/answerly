## 9. Rate Limiting

### Explanation

The backend has a dedicated `SecurityRateLimitMiddleware` for abuse-sensitive endpoints such as login, chat/query, document upload, and project creation. It supports endpoint-specific sliding-window limits, optional global fallback limits, exempt paths such as `/health` and `/docs`, JWT-subject-based keys for authenticated users, IP-based keys for anonymous users, max in-flight request limits, and rate-limit response headers.

### Path

`backend/security/middleware.py`

```python
class SecurityRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply configurable, endpoint-focused throttling for abuse-sensitive actions."""

    _RATE_LIMIT_ABUSE_THRESHOLD = 3
    _RATE_LIMIT_ABUSE_WINDOW_SECONDS = 300

    def __init__(self, app):
        super().__init__(app)

        self._rules: list[EndpointRateRule] = []

        self._rules.append(
            EndpointRateRule(
                name="chat",
                methods={"POST"},
                path_pattern=re.compile(r"^/projects/\d+/query(?:/stream)?/?$"),
                limiter=InMemoryRateLimiter(
                    max_requests=settings.security_rate_limit_chat_requests_per_window,
                    window_seconds=settings.security_rate_limit_chat_window_seconds,
                ),
                max_in_flight=max(0, settings.security_rate_limit_chat_max_in_flight),
            )
        )

        self._rules.append(
            EndpointRateRule(
                name="auth_login",
                methods={"POST"},
                path_pattern=re.compile(r"^/auth/login/?$"),
                limiter=InMemoryRateLimiter(
                    max_requests=settings.security_rate_limit_login_requests_per_window,
                    window_seconds=settings.security_rate_limit_login_window_seconds,
                ),
                max_in_flight=max(0, settings.security_rate_limit_login_max_in_flight),
            )
        )
```

---
