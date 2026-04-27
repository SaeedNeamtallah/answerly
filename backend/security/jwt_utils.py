"""JWT utility helpers for token generation and decoding."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt

from backend.config import settings


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_jwt_access_token(
    *,
    subject: str,
    roles: Optional[List[str]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """Create a signed JWT access token with configurable expiration."""
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
    """Decode and validate JWT access token."""
    return jwt.decode(
        token,
        settings.auth_jwt_secret_key,
        algorithms=[settings.auth_jwt_algorithm],
        options={"require": ["sub", "exp"]},
    )
