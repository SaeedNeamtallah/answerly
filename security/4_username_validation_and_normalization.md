## 4. Username Validation and Normalization

### Explanation

Usernames are sanitized and converted to lowercase before database use. The system enforces a strict username format using a regex that allows only lowercase letters, numbers, dots, underscores, and hyphens. Reserved service-account usernames are blocked from normal signup, and duplicate username checks are handled case-insensitively.

### Path

`backend/services/auth_service.py`

```python
_USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,50}$")

def _normalize_username(username: str) -> str:
    cleaned = sanitize_text(
        username,
        max_length=150,
        strip_html=True,
        allow_newlines=False,
    ).lower()

    if not cleaned:
        raise SignupValidationError("Username is required")

    if not _USERNAME_RE.match(cleaned):
        raise SignupValidationError(
            "Username must be 3-50 chars and contain only lowercase letters, numbers, ., _, or -"
        )

    return cleaned
```

---
