"""Centralized in-memory security event service."""
from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Any, Deque, Dict, Iterable, List, Optional

from backend.security.security_event import (
    SecurityEvent,
    SecurityEventCreate,
    SecurityEventType,
    SecuritySeverity,
)
from backend.services.incident_service import incident_service


_MAX_EVENTS = 5000
_ALLOWED_SEVERITIES = {
    SecuritySeverity.LOW,
    SecuritySeverity.MEDIUM,
    SecuritySeverity.HIGH,
    SecuritySeverity.CRITICAL,
}

_EVENTS: Deque[SecurityEvent] = deque(maxlen=_MAX_EVENTS)
_EVENTS_LOCK = Lock()
_USERNAME_BY_USER_ID: Dict[int, str] = {}


def _normalize_severity(value: str) -> str:
    severity = str(value or SecuritySeverity.MEDIUM).strip().upper()
    if severity not in _ALLOWED_SEVERITIES:
        return SecuritySeverity.MEDIUM
    return severity


def _normalize_event_type(value: str) -> str:
    event_type = str(value or SecurityEventType.ATTACK_SIMULATION).strip().upper()
    if not event_type:
        return SecurityEventType.ATTACK_SIMULATION
    return event_type[:64]


def _normalize_ip(ip_address: Optional[str]) -> Optional[str]:
    if ip_address is None:
        return None
    clean = str(ip_address).strip()
    return clean[:128] if clean else None


def _normalize_username(username: Optional[str]) -> Optional[str]:
    if username is None:
        return None
    clean = str(username).strip()
    return clean[:150] if clean else None


def log_event(event_data: SecurityEventCreate | Dict[str, Any]) -> SecurityEvent:
    """Store a security event in the centralized in-memory event feed."""
    payload = (
        event_data
        if isinstance(event_data, SecurityEventCreate)
        else SecurityEventCreate.model_validate(event_data)
    )

    metadata_username = None
    if isinstance(payload.metadata, dict):
        metadata_username = payload.metadata.get("username")

    normalized_username = _normalize_username(payload.username or metadata_username)

    if payload.user_id is not None:
        user_id_key = int(payload.user_id)
        if normalized_username:
            _USERNAME_BY_USER_ID[user_id_key] = normalized_username
        else:
            normalized_username = _USERNAME_BY_USER_ID.get(user_id_key) or f"user_{user_id_key}"

    event = SecurityEvent(
        event_type=_normalize_event_type(payload.event_type),
        severity=_normalize_severity(payload.severity),
        user_id=payload.user_id,
        username=normalized_username,
        ip_address=_normalize_ip(payload.ip_address),
        message=payload.message,
        metadata=payload.metadata or {},
    )

    with _EVENTS_LOCK:
        _EVENTS.append(event)

    # Detection -> incident automation for actionable abuse events.
    incident_service.trigger_auto_creation(event)

    return event


def list_events(
    *,
    limit: int = 200,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
) -> List[SecurityEvent]:
    """Return recent security events (most recent first)."""
    normalized_type = _normalize_event_type(event_type) if event_type else None
    normalized_severity = _normalize_severity(severity) if severity else None
    safe_limit = max(1, min(int(limit or 200), _MAX_EVENTS))

    with _EVENTS_LOCK:
        items: Iterable[SecurityEvent] = reversed(_EVENTS)
        filtered = []
        for event in items:
            if normalized_type and event.event_type != normalized_type:
                continue
            if normalized_severity and event.severity != normalized_severity:
                continue
            filtered.append(event)
            if len(filtered) >= safe_limit:
                break

    return filtered


def clear_events() -> None:
    """Clear all in-memory events (for demos/tests)."""
    with _EVENTS_LOCK:
        _EVENTS.clear()
        _USERNAME_BY_USER_ID.clear()


def get_security_stats() -> Dict[str, int]:
    """Compute aggregate counters used by the security dashboard."""
    with _EVENTS_LOCK:
        events = list(_EVENTS)

    return {
        "total_events": len(events),
        "login_failures": sum(1 for e in events if e.event_type == SecurityEventType.LOGIN_FAIL),
        "brute_force_attempts": sum(1 for e in events if e.event_type == SecurityEventType.BRUTE_FORCE),
        "blocked_uploads": sum(1 for e in events if e.event_type == SecurityEventType.FILE_UPLOAD_BLOCKED),
    }
