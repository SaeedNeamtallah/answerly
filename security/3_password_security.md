## 3. Password Security

### Explanation

Passwords are never stored in plain text. The system hashes passwords using `bcrypt`, validates password length and format, rejects control characters, and prevents leading or trailing spaces. Password verification uses `bcrypt.checkpw`. Changing a password requires the current password, and the new password must be different from the old one.

### Path

`backend/services/auth_service.py`

```python
def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise SignupValidationError("Password must be at least 8 characters")

    if len(password.encode("utf-8")) > 72:
        raise SignupValidationError("Password is too long")

    if password != password.strip():
        raise SignupValidationError("Password cannot start or end with spaces")

    if _PASSWORD_CONTROL_CHAR_RE.search(password):
        raise SignupValidationError("Password contains invalid control characters")


@staticmethod
def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@staticmethod
def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
```

---
