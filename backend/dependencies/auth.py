"""Auth dependencies.

Parses a JWT-like bearer token payload and enforces required claims.
"""
from __future__ import annotations

import base64
import json
import time
from typing import Any, Dict

from fastapi import Header, HTTPException, status
from pydantic import BaseModel


class CurrentUser(BaseModel):
    """Normalized authenticated user extracted from access token."""

    user_id: int
    email: str
    role: str


def _decode_payload(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    payload_b64 = parts[1]
    padding = "=" * ((4 - len(payload_b64) % 4) % 4)
    decoded = base64.urlsafe_b64decode(payload_b64 + padding)
    payload = json.loads(decoded.decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Invalid JWT payload")
    return payload


def _validate_payload(payload: Dict[str, Any]) -> CurrentUser:
    required_claims = {"user_id", "email", "role", "exp"}
    missing = [claim for claim in required_claims if claim not in payload]
    if missing:
        raise ValueError(f"Missing required claims: {', '.join(missing)}")

    try:
        exp = int(payload["exp"])
    except (TypeError, ValueError):
        raise ValueError("Invalid exp claim")

    now = int(time.time())
    if exp <= now:
        raise ValueError("Token expired")

    try:
        user_id = int(payload["user_id"])
    except (TypeError, ValueError):
        raise ValueError("Invalid user_id claim")

    email = str(payload["email"]).strip()
    role = str(payload["role"]).strip()
    if not email or not role:
        raise ValueError("Invalid user claims")

    return CurrentUser(user_id=user_id, email=email, role=role)


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """Extract current user from bearer token.

    Raises 401 when token is missing or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
        )

    try:
        payload = _decode_payload(token.strip())
        return _validate_payload(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
