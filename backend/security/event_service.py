"""Centralized security event service."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from backend.config import settings
from backend.security.security_event import (
    SecurityEvent,
    SecurityEventCreate,
    SecurityEventType,
    SecuritySeverity,
)
from backend.services.incident_service import incident_service


_MAX_EVENTS = 5000
logger = logging.getLogger(__name__)
_ALLOWED_SEVERITIES = {
    SecuritySeverity.LOW,
    SecuritySeverity.MEDIUM,
    SecuritySeverity.HIGH,
    SecuritySeverity.CRITICAL,
}
_SENSITIVE_METADATA_KEYS = {
    "api_key",
    "authorization",
    "credential",
    "password",
    "payload",
    "secret",
    "token",
    "token_encrypted",
}




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


def _normalize_delivery_status(value: str | None) -> str:
    clean = str(value or "PENDING").strip().upper()
    if clean not in {"PENDING", "DELIVERED", "FAILED"}:
        return "PENDING"
    return clean


def _metadata_marks_simulation(metadata: Dict[str, Any]) -> bool:
    return bool(metadata.get("simulation") or metadata.get("is_simulation"))


def _redact_metadata_value(key: str, value: Any) -> Any:
    key_lower = str(key or "").lower()
    if any(marker in key_lower for marker in _SENSITIVE_METADATA_KEYS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return _redact_metadata(value)
    if isinstance(value, list):
        return [_redact_metadata_value(key, item) for item in value[:20]]
    if isinstance(value, str):
        clean = value.strip()
        if len(clean) > 300:
            return f"{clean[:300]}...[TRUNCATED]"
        return clean
    return value


def _redact_metadata(metadata: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    redacted: Dict[str, Any] = {}
    for idx, (key, value) in enumerate(metadata.items()):
        if idx >= 64:
            redacted["truncated"] = True
            break
        redacted[str(key)[:80]] = _redact_metadata_value(str(key), value)
    return redacted


def _enqueue_persistence(event: SecurityEvent) -> None:
    """Enqueue persistence without blocking request handling on broker availability."""
    def _send() -> None:
        try:
            from backend.tasks.security import persist_security_event_task
            persist_security_event_task.delay(event.model_dump(mode="json"))
        except Exception:
            logger.exception("Failed to enqueue security event persistence")

    threading.Thread(target=_send, name="security-event-persist", daemon=True).start()


def security_event_retention_days() -> int:
    return max(1, int(getattr(settings, "security_event_retention_days", 180) or 180))


def _retention_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=security_event_retention_days())


def log_event(event_data: SecurityEventCreate | Dict[str, Any]) -> SecurityEvent:
    """Create a normalized security event and enqueue durable persistence."""
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
        if not normalized_username:
            normalized_username = f"user_{payload.user_id}"

    metadata = _redact_metadata(payload.metadata or {})
    is_simulation = bool(payload.is_simulation or _metadata_marks_simulation(metadata))

    event = SecurityEvent(
        event_type=_normalize_event_type(payload.event_type),
        severity=_normalize_severity(payload.severity),
        user_id=payload.user_id,
        username=normalized_username,
        ip_address=_normalize_ip(payload.ip_address),
        message=payload.message,
        metadata=metadata,
        is_simulation=is_simulation,
        delivery_status=_normalize_delivery_status(payload.delivery_status),
    )

    _enqueue_persistence(event)

    # Detection -> incident automation for actionable abuse events.
    incident_service.trigger_auto_creation(event)

    return event


async def list_events(
    *,
    db: Any,  # AsyncSession
    limit: int = 200,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return recent security events (most recent first) from DB."""
    from sqlalchemy import select
    from backend.database.models import SecurityEventRecord
    
    normalized_type = _normalize_event_type(event_type) if event_type else None
    normalized_severity = _normalize_severity(severity) if severity else None
    safe_limit = max(1, min(int(limit or 200), _MAX_EVENTS))

    stmt = select(SecurityEventRecord).where(SecurityEventRecord.created_at >= _retention_cutoff())
    if normalized_type:
        stmt = stmt.where(SecurityEventRecord.event_type == normalized_type)
    if normalized_severity:
        stmt = stmt.where(SecurityEventRecord.severity == normalized_severity)
    stmt = stmt.order_by(SecurityEventRecord.created_at.desc(), SecurityEventRecord.id.desc()).limit(safe_limit)

    result = await db.execute(stmt)
    records = result.scalars().all()
    
    events = []
    for r in records:
        events.append({
            "id": int(r.id),
            "timestamp": r.created_at.isoformat(),
            "event_type": r.event_type,
            "severity": r.severity,
            "user_id": r.user_id,
            "username": r.username,
            "ip_address": r.ip_address,
            "message": r.message,
            "metadata": _redact_metadata(r.metadata_),
            "is_simulation": bool(getattr(r, "is_simulation", False)),
            "delivery_status": _normalize_delivery_status(getattr(r, "delivery_status", "PENDING")),
        })
    return events


async def get_security_stats(db: Any) -> Dict[str, int]:
    """Compute aggregate counters used by the security dashboard."""
    from sqlalchemy import select, func
    from backend.database.models import SecurityEventRecord
    cutoff = _retention_cutoff()
    
    total_events = await db.scalar(select(func.count(SecurityEventRecord.id)).where(SecurityEventRecord.created_at >= cutoff))
    login_failures = await db.scalar(select(func.count(SecurityEventRecord.id)).where(SecurityEventRecord.created_at >= cutoff, SecurityEventRecord.event_type == SecurityEventType.LOGIN_FAIL))
    brute_force_attempts = await db.scalar(select(func.count(SecurityEventRecord.id)).where(SecurityEventRecord.created_at >= cutoff, SecurityEventRecord.event_type == SecurityEventType.BRUTE_FORCE))
    blocked_uploads = await db.scalar(select(func.count(SecurityEventRecord.id)).where(SecurityEventRecord.created_at >= cutoff, SecurityEventRecord.event_type == SecurityEventType.FILE_UPLOAD_BLOCKED))

    return {
        "total_events": total_events or 0,
        "login_failures": login_failures or 0,
        "brute_force_attempts": brute_force_attempts or 0,
        "blocked_uploads": blocked_uploads or 0,
    }


async def purge_expired_security_events(*, db: Any) -> int:
    """Delete events older than the configured retention window."""
    from sqlalchemy import delete
    from backend.database.models import SecurityEventRecord

    result = await db.execute(
        delete(SecurityEventRecord).where(SecurityEventRecord.created_at < _retention_cutoff())
    )
    return int(getattr(result, "rowcount", 0) or 0)
