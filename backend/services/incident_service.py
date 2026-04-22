"""Incident automation service for converting security detections into incidents."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

from sqlalchemy import func, select

from backend.config import settings
from backend.database.connection import async_session_maker
from backend.database.models import Incident, IncidentLog, IncidentSeverity, IncidentStatus, User, UserAccountStatus
from backend.security.security_event import SecurityEvent, SecurityEventType

logger = logging.getLogger(__name__)


class IncidentService:
    """Handles automatic incident creation for high-value security detections."""

    _TYPE_MAP = {
        SecurityEventType.BRUTE_FORCE: "Brute Force",
        SecurityEventType.FILE_UPLOAD_BLOCKED: "Upload Attack",
        SecurityEventType.RATE_LIMITED: "Rate Limit Abuse",
    }

    _SEVERITY_MAP = {
        SecurityEventType.BRUTE_FORCE: IncidentSeverity.HIGH,
        SecurityEventType.FILE_UPLOAD_BLOCKED: IncidentSeverity.HIGH,
        SecurityEventType.RATE_LIMITED: IncidentSeverity.MEDIUM,
    }

    _ACTIVE_ASSIGNMENT_LOAD_STATUSES = (
        IncidentStatus.OPEN,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.RESOLVED,
    )

    @staticmethod
    def _normalize_username(value: str) -> str:
        return str(value or "").strip().lower()

    def _configured_engineer_usernames(self) -> set[str]:
        configured_values = [
            os.getenv("SECURITY_ENGINEER_USERNAMES", ""),
            os.getenv("SECURITY_CYBERSECURITY_ENGINEER_USERNAMES", ""),
            getattr(settings, "security_cybersecurity_engineer_usernames", ""),
        ]

        usernames: set[str] = set()
        for raw in configured_values:
            for chunk in str(raw or "").split(","):
                normalized = self._normalize_username(chunk)
                if normalized:
                    usernames.add(normalized)
        return usernames

    async def _resolve_auto_assignee(self, session) -> tuple[Optional[int], Optional[str], int]:
        engineer_usernames = self._configured_engineer_usernames()
        if not engineer_usernames:
            return None, None, 0

        users_stmt = (
            select(User)
            .where(
                func.lower(User.username).in_(sorted(engineer_usernames)),
                User.status == UserAccountStatus.ACTIVE,
            )
            .order_by(User.id.asc())
        )
        users_result = await session.execute(users_stmt)
        candidate_users = users_result.scalars().all()

        if not candidate_users:
            return None, None, 0

        candidate_ids = [int(user.id) for user in candidate_users]
        load_stmt = (
            select(Incident.assigned_to, func.count(Incident.id))
            .where(
                Incident.assigned_to.in_(candidate_ids),
                Incident.status.in_(self._ACTIVE_ASSIGNMENT_LOAD_STATUSES),
                Incident.false_positive.is_(False),
            )
            .group_by(Incident.assigned_to)
        )
        load_result = await session.execute(load_stmt)
        load_map = {
            int(assigned_to): int(count)
            for assigned_to, count in load_result.all()
            if assigned_to is not None
        }

        selected_user = min(
            candidate_users,
            key=lambda user: (load_map.get(int(user.id), 0), int(user.id)),
        )
        selected_load = load_map.get(int(selected_user.id), 0)
        return int(selected_user.id), str(selected_user.username), int(selected_load)

    def should_create_incident(self, event_type: str) -> bool:
        return str(event_type or "").strip().upper() in self._TYPE_MAP

    async def create_from_security_event(self, event: SecurityEvent) -> Optional[int]:
        """Create incident + initial incident log from a security event."""
        normalized_type = str(event.event_type or "").strip().upper()
        if normalized_type not in self._TYPE_MAP:
            return None

        incident_type = self._TYPE_MAP[normalized_type]
        incident_severity = self._SEVERITY_MAP[normalized_type]

        metadata: dict[str, Any] = event.metadata if isinstance(event.metadata, dict) else {}
        details: list[str] = [str(event.message or "").strip() or "Security detection triggered"]
        if event.username:
            details.append(f"Username: {event.username}")
        if event.ip_address:
            details.append(f"IP: {event.ip_address}")

        async with async_session_maker() as session:
            assignee_id, assignee_username, assignee_load = await self._resolve_auto_assignee(session)

            incident = Incident(
                type=incident_type,
                severity=incident_severity,
                status=IncidentStatus.OPEN,
                actor_id=event.user_id,
                created_by="system",
                assigned_to=assignee_id,
                description=" | ".join(details),
                notes="",
                false_positive=False,
            )
            session.add(incident)
            await session.flush()

            incident_log = IncidentLog(
                incident_id=incident.id,
                event_type=normalized_type,
                severity=str(event.severity or "").upper() or None,
                actor_id=event.user_id,
                message=str(event.message or "").strip() or "Detection event recorded",
                extra_metadata={
                    **metadata,
                    "security_event_id": str(event.id),
                    "security_event_timestamp": event.timestamp.isoformat(),
                    "username": event.username,
                    "ip_address": event.ip_address,
                    "auto_created": True,
                    "auto_assigned": bool(assignee_id),
                    "auto_assigned_to_id": assignee_id,
                    "auto_assigned_to_username": assignee_username,
                    "result": "success",
                },
            )
            session.add(incident_log)

            if assignee_id is not None:
                session.add(
                    IncidentLog(
                        incident_id=incident.id,
                        event_type="AUTO_ASSIGNED",
                        severity="LOW",
                        actor_id=None,
                        message=f"Incident auto-assigned to {assignee_username} based on current load",
                        extra_metadata={
                            "auto_assigned": True,
                            "assigned_to_id": assignee_id,
                            "assigned_to_username": assignee_username,
                            "assignee_open_load": assignee_load,
                            "assignment_strategy": "least_active_incident_load",
                            "result": "success",
                        },
                    )
                )

            await session.commit()
            return incident.id

    def trigger_auto_creation(self, event: SecurityEvent) -> None:
        """Best-effort non-blocking trigger for incident creation."""
        if not self.should_create_incident(event.event_type):
            return

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._safe_create(event))
        except RuntimeError:
            # Fallback for sync-only contexts where no event loop is active.
            asyncio.run(self._safe_create(event))

    async def _safe_create(self, event: SecurityEvent) -> None:
        try:
            await self.create_from_security_event(event)
        except Exception as exc:
            logger.warning("Failed to auto-create incident from event %s: %s", event.event_type, exc)


incident_service = IncidentService()
