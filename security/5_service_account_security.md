## 5. Service Account Security

### Explanation

The project includes managed service-account logic for admin and bot accounts. These usernames are reserved and cannot be used by normal users during signup. Successful service-account login can provision or sync a real database-backed user row. Admin passwords support either plain comparison or PBKDF2-SHA256 hash verification, with constant-time comparison to reduce timing-attack risk.

### Path

`backend/security/auth.py`

```python
def get_service_account_credentials(username: str) -> ServiceAccountCredentials | None:
    normalized_username = _normalize_username(username)
    if not normalized_username:
        return None

    bot_account = _configured_bot_service_account()
    if bot_account and bot_account.username == normalized_username:
        return bot_account

    admin_account = _configured_admin_service_account()
    if admin_account and admin_account.username == normalized_username:
        return admin_account

    return None


def get_reserved_service_account_usernames() -> Set[str]:
    reserved_usernames: Set[str] = set()
    for account in (_configured_bot_service_account(), _configured_admin_service_account()):
        if account is not None and account.username:
            reserved_usernames.add(account.username)
    return reserved_usernames


def verify_service_account_password(
    service_account: ServiceAccountCredentials,
    password: str,
) -> bool:
    if service_account.password_hash:
        return _verify_pbkdf2_sha256(password, service_account.password_hash)
    if service_account.plain_password is None:
        return False
    return compare_digest(password, service_account.plain_password)
```

---
