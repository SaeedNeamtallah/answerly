"""Security event models and shared constants."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SecurityEventType:
    """Common security event types."""

    LOGIN_FAIL = "LOGIN_FAIL"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    PASSWORD_CHANGE_SUCCESS = "PASSWORD_CHANGE_SUCCESS"
    PASSWORD_CHANGE_FAIL = "PASSWORD_CHANGE_FAIL"
    SIGNUP_FAIL = "SIGNUP_FAIL"
    SIGNUP_SUCCESS = "SIGNUP_SUCCESS"
    BRUTE_FORCE = "BRUTE_FORCE"
    FILE_UPLOAD_BLOCKED = "FILE_UPLOAD_BLOCKED"
    ATTACK_SIMULATION = "ATTACK_SIMULATION"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTHZ_DENIED = "AUTHZ_DENIED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    RATE_LIMITED = "RATE_LIMITED"
    XSS_ATTEMPT = "XSS_ATTEMPT"
    SQL_INJECTION = "SQL_INJECTION"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_BLOCKED = "USER_BLOCKED"
    USER_RESTORED = "USER_RESTORED"


class SecuritySeverity:
    """Supported severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityEventCreate(BaseModel):
    """Payload accepted by the security event logger."""

    event_type: str = Field(..., min_length=1, max_length=64)
    severity: str = Field(default=SecuritySeverity.LOW, min_length=1, max_length=16)
    user_id: Optional[int] = None
    username: Optional[str] = Field(default=None, max_length=150)
    ip_address: Optional[str] = Field(default=None, max_length=128)
    message: str = Field(..., min_length=1, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityEvent(BaseModel):
    """Persistent security event model."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = Field(..., min_length=1, max_length=64)
    severity: str = Field(..., min_length=1, max_length=16)
    user_id: Optional[int] = None
    username: Optional[str] = Field(default=None, max_length=150)
    ip_address: Optional[str] = Field(default=None, max_length=128)
    message: str = Field(..., min_length=1, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)
