"""Centralized in-memory security event service."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

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
        if not normalized_username:
            normalized_username = f"user_{payload.user_id}"

    event = SecurityEvent(
        event_type=_normalize_event_type(payload.event_type),
        severity=_normalize_severity(payload.severity),
        user_id=payload.user_id,
        username=normalized_username,
        ip_address=_normalize_ip(payload.ip_address),
        message=payload.message,
        metadata=payload.metadata or {},
    )

    # Trigger Celery task to persist event
    from backend.tasks.security import persist_security_event_task
    persist_security_event_task.delay(event.model_dump(mode="json"))

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

    stmt = select(SecurityEventRecord).order_by(SecurityEventRecord.created_at.desc(), SecurityEventRecord.id.desc()).limit(safe_limit)
    if normalized_type:
        stmt = stmt.where(SecurityEventRecord.event_type == normalized_type)
    if normalized_severity:
        stmt = stmt.where(SecurityEventRecord.severity == normalized_severity)

    result = await db.execute(stmt)
    records = result.scalars().all()
    
    events = []
    for r in records:
        events.append({
            "id": str(r.id), # UUID expected by frontend? Wait, id is integer.
            "timestamp": r.created_at.isoformat(),
            "event_type": r.event_type,
            "severity": r.severity,
            "user_id": r.user_id,
            "username": r.username,
            "ip_address": r.ip_address,
            "message": r.message,
            "metadata": r.metadata_
        })
    return events


async def get_security_stats(db: Any) -> Dict[str, int]:
    """Compute aggregate counters used by the security dashboard."""
    from sqlalchemy import select, func
    from backend.database.models import SecurityEventRecord
    
    total_events = await db.scalar(select(func.count(SecurityEventRecord.id)))
    login_failures = await db.scalar(select(func.count(SecurityEventRecord.id)).where(SecurityEventRecord.event_type == SecurityEventType.LOGIN_FAIL))
    brute_force_attempts = await db.scalar(select(func.count(SecurityEventRecord.id)).where(SecurityEventRecord.event_type == SecurityEventType.BRUTE_FORCE))
    blocked_uploads = await db.scalar(select(func.count(SecurityEventRecord.id)).where(SecurityEventRecord.event_type == SecurityEventType.FILE_UPLOAD_BLOCKED))

    return {
        "total_events": total_events or 0,
        "login_failures": login_failures or 0,
        "brute_force_attempts": brute_force_attempts or 0,
        "blocked_uploads": blocked_uploads or 0,
    }
