"""Business logic for incident management APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database.connection import async_session_maker
from backend.database.models import (
    AuditLog,
    Incident,
    IncidentLog,
    IncidentSeverity,
    IncidentStatus,
    User,
    UserAccountStatus,
)
from backend.models.incident_models import (
    IncidentActionRequest,
    IncidentAssignRequest,
    IncidentAssignResponse,
    IncidentDetailsResponse,
    IncidentFalsePositiveUpdateRequest,
    IncidentLogResponse,
    IncidentNotesUpdateRequest,
    IncidentResponse,
    IncidentStatusUpdateRequest,
)
from backend.security.event_service import log_event
from backend.security.security_event import SecurityEventType
from backend.services.auth_service import AuthService


_ALLOWED_STATUS_TRANSITIONS: Dict[IncidentStatus, IncidentStatus] = {
    IncidentStatus.OPEN: IncidentStatus.INVESTIGATING,
    IncidentStatus.INVESTIGATING: IncidentStatus.RESOLVED,
    IncidentStatus.RESOLVED: IncidentStatus.CLOSED,
}


_ACTION_LABELS: Dict[str, str] = {
    "block_user": "Block user",
    "suspend_user": "Suspend user",
    "reactivate_user": "Restore user",
    "ignore": "Ignore",
}


_AUDIT_ACTIONS: Dict[str, str] = {
    "block_user": "user_blocked",
    "suspend_user": "user_suspended",
    "reactivate_user": "user_reactivated",
    "ignore": "incident_ignored",
}


_STATUS_AUDIT_ACTIONS: Dict[IncidentStatus, str] = {
    IncidentStatus.OPEN: "incident_opened",
    IncidentStatus.INVESTIGATING: "incident_investigating",
    IncidentStatus.RESOLVED: "incident_resolved",
    IncidentStatus.CLOSED: "incident_closed",
}


class IncidentManagementService:
    """Service containing incident read/update business rules."""

    _MAX_NOTES_LENGTH = 8000
    _MAX_STATUS_REASON_LENGTH = 255

    _STATUS_EVENT_SUSPENDED = SecurityEventType.USER_SUSPENDED
    _STATUS_EVENT_BLOCKED = SecurityEventType.USER_BLOCKED
    _STATUS_EVENT_RESTORED = SecurityEventType.USER_RESTORED

    @staticmethod
    def _enum_value(value: Any) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)

    @staticmethod
    def _normalize_metadata_dict(value: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        return {}

    def _normalize_notes(self, value: Any) -> str:
        # Keep notes bounded so a single incident cannot bloat payloads/logs.
        normalized = str(value or "").strip()
        if len(normalized) > self._MAX_NOTES_LENGTH:
            return normalized[: self._MAX_NOTES_LENGTH]
        return normalized

    @staticmethod
    def _build_incident_target_ref(incident_id: int) -> str:
        return f"incident_{int(incident_id)}"

    @staticmethod
    def _normalize_actor(actor: Any, *, fallback: str = "system") -> str:
        normalized = str(actor or "").strip()[:64]
        if normalized:
            return normalized
        return fallback

    def _normalize_status_reason(self, reason: Any, *, fallback: str) -> str:
        normalized = str(reason or "").strip()
        if not normalized:
            normalized = fallback
        if len(normalized) > self._MAX_STATUS_REASON_LENGTH:
            return normalized[: self._MAX_STATUS_REASON_LENGTH]
        return normalized

    def _log_status_action_event(
        self,
        *,
        event_type: str,
        user_id: int,
        actor: str,
        reason: str,
        severity: str = "HIGH",
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata = {
            "actor": actor,
            "reason": reason,
            "timestamp": now_iso,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        log_event(
            {
                "event_type": event_type,
                "severity": severity,
                "user_id": int(user_id),
                "username": actor,
                "message": f"Account status action: {event_type}",
                "metadata": metadata,
            }
        )

    async def suspend_user(
        self,
        user_id: int,
        reason: str,
        duration_minutes: int,
        actor: str = "system",
        *,
        db: Optional[AsyncSession] = None,
        auth_service: Optional[AuthService] = None,
    ) -> User:
        """Suspend a user account for a bounded duration and emit a security audit event."""
        resolved_actor = self._normalize_actor(actor, fallback="system")
        resolved_reason = self._normalize_status_reason(
            reason,
            fallback="temporary_security_suspension",
        )
        resolved_duration_minutes = int(duration_minutes)
        if resolved_duration_minutes <= 0:
            raise ValueError("duration_minutes must be a positive integer")

        resolved_auth_service = auth_service or AuthService()

        if db is None:
            async with async_session_maker() as local_db:
                updated_user = await resolved_auth_service.set_user_status(
                    local_db,
                    user_id=int(user_id),
                    status=UserAccountStatus.SUSPENDED,
                    suspension_minutes=resolved_duration_minutes,
                    status_reason=resolved_reason,
                    status_changed_by=resolved_actor,
                )

                self._log_status_action_event(
                    event_type=self._STATUS_EVENT_SUSPENDED,
                    user_id=updated_user.id,
                    actor=resolved_actor,
                    reason=resolved_reason,
                    severity="HIGH",
                    extra_metadata={
                        "duration_minutes": resolved_duration_minutes,
                        "suspended_until": (
                            updated_user.suspended_until.isoformat()
                            if updated_user.suspended_until is not None
                            else None
                        ),
                        "new_status": UserAccountStatus.SUSPENDED.value,
                    },
                )
                await local_db.commit()
                await local_db.refresh(updated_user)
                return updated_user

        updated_user = await resolved_auth_service.set_user_status(
            db,
            user_id=int(user_id),
            status=UserAccountStatus.SUSPENDED,
            suspension_minutes=resolved_duration_minutes,
            status_reason=resolved_reason,
            status_changed_by=resolved_actor,
        )

        self._log_status_action_event(
            event_type=self._STATUS_EVENT_SUSPENDED,
            user_id=updated_user.id,
            actor=resolved_actor,
            reason=resolved_reason,
            severity="HIGH",
            extra_metadata={
                "duration_minutes": resolved_duration_minutes,
                "suspended_until": (
                    updated_user.suspended_until.isoformat()
                    if updated_user.suspended_until is not None
                    else None
                ),
                "new_status": UserAccountStatus.SUSPENDED.value,
            },
        )
        return updated_user

    async def block_user(
        self,
        user_id: int,
        reason: str,
        actor: str = "system",
        *,
        db: Optional[AsyncSession] = None,
        auth_service: Optional[AuthService] = None,
    ) -> User:
        """Block a user account and emit a security audit event."""
        resolved_actor = self._normalize_actor(actor, fallback="system")
        resolved_reason = self._normalize_status_reason(
            reason,
            fallback="confirmed_malicious_activity",
        )

        resolved_auth_service = auth_service or AuthService()

        if db is None:
            async with async_session_maker() as local_db:
                updated_user = await resolved_auth_service.set_user_status(
                    local_db,
                    user_id=int(user_id),
                    status=UserAccountStatus.BLOCKED,
                    status_reason=resolved_reason,
                    status_changed_by=resolved_actor,
                )

                self._log_status_action_event(
                    event_type=self._STATUS_EVENT_BLOCKED,
                    user_id=updated_user.id,
                    actor=resolved_actor,
                    reason=resolved_reason,
                    severity="CRITICAL",
                    extra_metadata={
                        "new_status": UserAccountStatus.BLOCKED.value,
                    },
                )
                await local_db.commit()
                await local_db.refresh(updated_user)
                return updated_user

        updated_user = await resolved_auth_service.set_user_status(
            db,
            user_id=int(user_id),
            status=UserAccountStatus.BLOCKED,
            status_reason=resolved_reason,
            status_changed_by=resolved_actor,
        )

        self._log_status_action_event(
            event_type=self._STATUS_EVENT_BLOCKED,
            user_id=updated_user.id,
            actor=resolved_actor,
            reason=resolved_reason,
            severity="CRITICAL",
            extra_metadata={
                "new_status": UserAccountStatus.BLOCKED.value,
            },
        )
        return updated_user

    async def restore_user(
        self,
        user_id: int,
        actor: str = "admin",
        *,
        db: Optional[AsyncSession] = None,
        auth_service: Optional[AuthService] = None,
    ) -> User:
        """Restore a user account back to ACTIVE and emit a security audit event."""
        resolved_actor = self._normalize_actor(actor, fallback="admin")
        resolved_reason = self._normalize_status_reason(
            f"restored_by_{resolved_actor}",
            fallback="manual_restore",
        )

        resolved_auth_service = auth_service or AuthService()

        if db is None:
            async with async_session_maker() as local_db:
                updated_user = await resolved_auth_service.set_user_status(
                    local_db,
                    user_id=int(user_id),
                    status=UserAccountStatus.ACTIVE,
                    status_reason=resolved_reason,
                    status_changed_by=resolved_actor,
                )

                self._log_status_action_event(
                    event_type=self._STATUS_EVENT_RESTORED,
                    user_id=updated_user.id,
                    actor=resolved_actor,
                    reason=resolved_reason,
                    severity="LOW",
                    extra_metadata={
                        "new_status": UserAccountStatus.ACTIVE.value,
                    },
                )
                await local_db.commit()
                await local_db.refresh(updated_user)
                return updated_user

        updated_user = await resolved_auth_service.set_user_status(
            db,
            user_id=int(user_id),
            status=UserAccountStatus.ACTIVE,
            status_reason=resolved_reason,
            status_changed_by=resolved_actor,
        )

        self._log_status_action_event(
            event_type=self._STATUS_EVENT_RESTORED,
            user_id=updated_user.id,
            actor=resolved_actor,
            reason=resolved_reason,
            severity="LOW",
            extra_metadata={
                "new_status": UserAccountStatus.ACTIVE.value,
            },
        )
        return updated_user

    @staticmethod
    def _resolve_reason(metadata: Dict[str, Any], *, fallback: str) -> str:
        reason = str(metadata.get("reason", "")).strip()
        if reason:
            return reason
        return fallback

    @staticmethod
    def _normalize_log_result(value: Any) -> Literal["success", "failed"]:
        normalized = str(value or "").strip().lower()
        if normalized in {"failed", "failure", "error", "denied", "blocked", "false"}:
            return "failed"
        return "success"

    def _resolve_incident_log_result(self, log: IncidentLog) -> Literal["success", "failed"]:
        metadata = log.extra_metadata if isinstance(log.extra_metadata, dict) else {}
        if "result" in metadata:
            return self._normalize_log_result(metadata.get("result"))

        event_type = str(log.event_type or "").upper()
        if any(token in event_type for token in ("FAIL", "DENY", "ERROR", "INVALID")):
            return "failed"
        return "success"

    def _serialize_incident_log(self, log: IncidentLog) -> IncidentLogResponse:
        return IncidentLogResponse(
            id=log.id,
            incident_id=log.incident_id,
            event_type=log.event_type,
            severity=log.severity,
            result=self._resolve_incident_log_result(log),
            actor_id=log.actor_id,
            actor_username=log.actor.username if log.actor else None,
            message=log.message,
            extra_metadata=log.extra_metadata or {},
            created_at=log.created_at,
        )

    def _serialize_incident(self, incident: Incident) -> IncidentResponse:
        return IncidentResponse(
            id=incident.id,
            type=incident.type,
            severity=self._enum_value(incident.severity),
            status=self._enum_value(incident.status),
            actor_id=incident.actor_id,
            actor_username=incident.actor.username if incident.actor else None,
            created_by=incident.created_by,
            assigned_to=incident.assigned_to,
            assigned_to_username=incident.assignee.username if incident.assignee else None,
            description=incident.description,
            notes=self._normalize_notes(getattr(incident, "notes", "")),
            is_false_positive=bool(getattr(incident, "false_positive", False)),
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )

    def _serialize_incident_details(self, incident: Incident) -> IncidentDetailsResponse:
        ordered_logs = sorted(
            incident.logs or [],
            key=lambda item: item.created_at.timestamp() if item.created_at else 0.0,
        )

        return IncidentDetailsResponse(
            **self._serialize_incident(incident).model_dump(),
            logs=[self._serialize_incident_log(item) for item in ordered_logs],
        )

    async def _get_incident_or_404(self, db: AsyncSession, incident_id: int) -> Incident:
        stmt = (
            select(Incident)
            .where(Incident.id == incident_id)
            .options(
                selectinload(Incident.actor),
                selectinload(Incident.assignee),
                selectinload(Incident.logs).selectinload(IncidentLog.actor),
            )
        )
        result = await db.execute(stmt)
        incident = result.scalar_one_or_none()
        if incident is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        return incident

    async def _append_incident_log(
        self,
        *,
        db: AsyncSession,
        incident: Incident,
        actor: Optional[User],
        event_type: str,
        message: str,
        severity: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        metadata_payload: Dict[str, Any] = dict(metadata or {})
        metadata_payload.setdefault("result", "success")

        db.add(
            IncidentLog(
                incident_id=incident.id,
                event_type=event_type,
                severity=severity,
                actor_id=actor.id if actor else None,
                message=message,
                extra_metadata=metadata_payload,
            )
        )

    def _append_audit_log(
        self,
        *,
        db: AsyncSession,
        actor: Optional[User],
        action: str,
        target_incident_id: int,
        target_user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        actor_label = str(actor.username if actor and actor.username else "security_engineer").strip()[:64]
        if not actor_label:
            actor_label = "security_engineer"

        metadata_payload = self._normalize_metadata_dict(metadata)
        metadata_payload.setdefault("target_ref", self._build_incident_target_ref(target_incident_id))
        metadata_payload.setdefault("target_type", "incident")
        metadata_payload.setdefault("reason", "not_provided")

        if target_user_id is not None:
            metadata_payload.setdefault("target_user_ref", f"user_{int(target_user_id)}")

        db.add(
            AuditLog(
                actor_id=actor.id if actor else None,
                actor=actor_label,
                action=action,
                target=int(target_incident_id),
                target_user_id=target_user_id,
                extra_metadata=metadata_payload,
            )
        )

    async def list_incidents(
        self,
        db: AsyncSession,
        *,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        is_false_positive: Optional[bool] = None,
    ) -> List[IncidentResponse]:
        """List incidents with optional status and severity filtering."""
        stmt = (
            select(Incident)
            .options(selectinload(Incident.actor), selectinload(Incident.assignee))
            .order_by(Incident.created_at.desc())
        )

        if status is not None:
            stmt = stmt.where(Incident.status == status)
        if severity is not None:
            stmt = stmt.where(Incident.severity == severity)
        if is_false_positive is not None:
            stmt = stmt.where(Incident.false_positive.is_(bool(is_false_positive)))

        result = await db.execute(stmt)
        incidents = result.scalars().all()
        return [self._serialize_incident(item) for item in incidents]

    async def get_incident_details(self, db: AsyncSession, incident_id: int) -> IncidentDetailsResponse:
        """Get incident details including timeline logs."""
        incident = await self._get_incident_or_404(db, incident_id)
        return self._serialize_incident_details(incident)

    async def update_incident_status(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentStatusUpdateRequest,
        current_user: User,
    ) -> IncidentResponse:
        """Update incident status while enforcing the lifecycle transition chain."""
        incident = await self._get_incident_or_404(db, incident_id)

        current_status = incident.status
        if not isinstance(current_status, IncidentStatus):
            try:
                current_status = IncidentStatus(str(current_status))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Incident has invalid current status") from exc
        next_allowed = _ALLOWED_STATUS_TRANSITIONS.get(current_status)

        if payload.status == current_status:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid transition from {self._enum_value(current_status)} "
                    f"to {self._enum_value(payload.status)}"
                ),
            )

        if next_allowed is None or payload.status != next_allowed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid transition from {self._enum_value(current_status)} "
                    f"to {self._enum_value(payload.status)}"
                ),
            )

        previous_status = self._enum_value(current_status)
        next_status = self._enum_value(payload.status)
        request_metadata = self._normalize_metadata_dict(payload.metadata)
        reason = self._resolve_reason(
            request_metadata,
            fallback=f"status transition {previous_status} to {next_status}",
        )
        request_metadata["reason"] = reason

        incident.status = payload.status

        status_log_metadata = {
            "from": previous_status,
            "to": next_status,
            "updated_by": current_user.username,
            **request_metadata,
        }

        await self._append_incident_log(
            db=db,
            incident=incident,
            actor=current_user,
            event_type="STATUS_UPDATED",
            severity="LOW",
            message=(
                f"Incident status updated from {previous_status} "
                f"to {self._enum_value(payload.status)}"
            ),
            metadata=status_log_metadata,
        )

        self._append_audit_log(
            db=db,
            actor=current_user,
            action=_STATUS_AUDIT_ACTIONS.get(payload.status, "incident_status_updated"),
            target_incident_id=incident.id,
            metadata={
                "incident_id": incident.id,
                "from": previous_status,
                "to": next_status,
                "actor": current_user.username,
                **request_metadata,
            },
        )

        log_event(
            {
                "event_type": "INCIDENT_STATUS_UPDATED",
                "severity": "LOW",
                "user_id": current_user.id,
                "username": current_user.username,
                "message": "Incident status changed",
                "metadata": {
                    "incident_id": incident.id,
                    "from": previous_status,
                    "to": next_status,
                    "reason": reason,
                },
            }
        )

        await db.commit()
        await db.refresh(incident)
        return self._serialize_incident(incident)

    async def assign_incident(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        current_user: User,
        payload: Optional[IncidentAssignRequest] = None,
    ) -> IncidentAssignResponse:
        """Assign an incident to the currently authenticated security engineer."""
        incident = await self._get_incident_or_404(db, incident_id)

        request_metadata = self._normalize_metadata_dict(payload.metadata if payload else None)
        reason = self._resolve_reason(request_metadata, fallback="manual incident assignment")
        request_metadata["reason"] = reason

        incident.assigned_to = current_user.id

        assign_log_metadata = {
            "assigned_to": current_user.username,
            "assigned_to_id": current_user.id,
            **request_metadata,
        }

        await self._append_incident_log(
            db=db,
            incident=incident,
            actor=current_user,
            event_type="ASSIGNED",
            severity="LOW",
            message="Incident assigned to security engineer",
            metadata=assign_log_metadata,
        )

        self._append_audit_log(
            db=db,
            actor=current_user,
            action="incident_assigned",
            target_incident_id=incident.id,
            metadata={
                "incident_id": incident.id,
                "assigned_to": current_user.username,
                "assigned_to_id": current_user.id,
                **request_metadata,
            },
        )

        log_event(
            {
                "event_type": "INCIDENT_ASSIGNED",
                "severity": "LOW",
                "user_id": current_user.id,
                "username": current_user.username,
                "message": "Incident assigned",
                "metadata": {
                    "incident_id": incident.id,
                    "assigned_to": current_user.username,
                    "reason": reason,
                },
            }
        )

        await db.commit()
        await db.refresh(incident)

        return IncidentAssignResponse(
            id=incident.id,
            assigned_to=incident.assigned_to,
            assigned_to_username=current_user.username,
            status=self._enum_value(incident.status),
        )

    async def apply_incident_action(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentActionRequest,
        current_user: User,
        auth_service: AuthService,
    ) -> IncidentDetailsResponse:
        """Apply an incident action and persist related incident/audit logs."""
        incident = await self._get_incident_or_404(db, incident_id)
        action_type = payload.action_type
        request_metadata = self._normalize_metadata_dict(payload.metadata)
        reason = self._resolve_reason(request_metadata, fallback=f"{action_type} action applied")
        request_metadata["reason"] = reason

        if action_type in {"block_user", "suspend_user", "reactivate_user"} and incident.actor_id is None:
            raise HTTPException(status_code=400, detail="Incident has no actor to apply this action")

        target_user: Optional[User] = None
        if incident.actor_id is not None:
            target_user_stmt = select(User).where(User.id == int(incident.actor_id)).limit(1)
            target_user_result = await db.execute(target_user_stmt)
            target_user = target_user_result.scalar_one_or_none()

        if action_type in {"block_user", "suspend_user", "reactivate_user"} and target_user is None:
            raise HTTPException(status_code=404, detail="Target user not found")

        action_label = _ACTION_LABELS[action_type]
        audit_action = _AUDIT_ACTIONS[action_type]
        target_user_id: Optional[int] = None

        if action_type == "block_user":
            try:
                updated_user = await self.block_user(
                    int(incident.actor_id),
                    reason,
                    actor=current_user.username,
                    db=db,
                    auth_service=auth_service,
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail="Target user not found") from exc
            target_user_id = updated_user.id

        elif action_type == "suspend_user":
            raw_suspension_minutes = request_metadata.get(
                "suspension_minutes",
                settings.security_user_suspension_default_minutes,
            )
            try:
                suspension_minutes = int(raw_suspension_minutes)
            except (TypeError, ValueError) as exc:
                raise HTTPException(
                    status_code=400,
                    detail="suspension_minutes must be a positive integer",
                ) from exc

            if suspension_minutes <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="suspension_minutes must be a positive integer",
                )

            try:
                updated_user = await self.suspend_user(
                    int(incident.actor_id),
                    reason,
                    suspension_minutes,
                    actor=current_user.username,
                    db=db,
                    auth_service=auth_service,
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail="Target user not found") from exc

            request_metadata["suspension_minutes"] = suspension_minutes
            if updated_user.suspended_until is not None:
                request_metadata["suspended_until"] = updated_user.suspended_until.isoformat()
            target_user_id = updated_user.id

        elif action_type == "reactivate_user":
            try:
                updated_user = await self.restore_user(
                    int(incident.actor_id),
                    actor=current_user.username,
                    db=db,
                    auth_service=auth_service,
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail="Target user not found") from exc
            target_user_id = updated_user.id

        if action_type == "ignore":
            target_user_id = incident.actor_id
            incident.false_positive = True

        self._append_audit_log(
            db=db,
            actor=current_user,
            action=audit_action,
            target_incident_id=incident.id,
            target_user_id=target_user_id,
            metadata={
                "incident_id": incident.id,
                "action": audit_action,
                "action_type": action_type,
                "target_actor_id": target_user_id,
                "actor": current_user.username,
                **request_metadata,
            },
        )

        action_log_metadata = {
            "actor": current_user.username,
            "action": audit_action,
            "target": target_user_id,
            "incident_id": incident.id,
            "action_type": action_type,
            "performed_by": current_user.username,
            "performed_by_id": current_user.id,
            "target_actor_id": target_user_id,
            **request_metadata,
        }

        await self._append_incident_log(
            db=db,
            incident=incident,
            actor=current_user,
            event_type=audit_action.upper(),
            severity="MEDIUM",
            message=f"{action_label} action applied",
            metadata=action_log_metadata,
        )

        log_event(
            {
                "event_type": "INCIDENT_ACTION",
                "severity": "MEDIUM",
                "user_id": current_user.id,
                "username": current_user.username,
                "message": f"Incident action applied: {action_type}",
                "metadata": {
                    "incident_id": incident.id,
                    "action": audit_action,
                    "action_type": action_type,
                    "target_actor_id": target_user_id,
                    "reason": reason,
                },
            }
        )

        await db.commit()

        updated_incident = await self._get_incident_or_404(db, incident_id)
        return self._serialize_incident_details(updated_incident)

    async def update_incident_notes(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentNotesUpdateRequest,
        current_user: User,
    ) -> IncidentDetailsResponse:
        """Update investigation notes for an incident."""
        incident = await self._get_incident_or_404(db, incident_id)

        normalized_notes = self._normalize_notes(payload.notes)
        previous_length = len(self._normalize_notes(getattr(incident, "notes", "")))
        incident.notes = normalized_notes

        request_metadata = self._normalize_metadata_dict(payload.metadata)
        reason = self._resolve_reason(
            request_metadata,
            fallback="investigation notes updated",
        )
        request_metadata["reason"] = reason

        await self._append_incident_log(
            db=db,
            incident=incident,
            actor=current_user,
            event_type="NOTES_UPDATED",
            severity="LOW",
            message="Investigation notes updated",
            metadata={
                "previous_length": previous_length,
                "new_length": len(normalized_notes),
                "has_notes": bool(normalized_notes),
                "updated_by": current_user.username,
                **request_metadata,
            },
        )

        self._append_audit_log(
            db=db,
            actor=current_user,
            action="incident_notes_updated",
            target_incident_id=incident.id,
            metadata={
                "incident_id": incident.id,
                "previous_length": previous_length,
                "new_length": len(normalized_notes),
                "has_notes": bool(normalized_notes),
                "actor": current_user.username,
                **request_metadata,
            },
        )

        log_event(
            {
                "event_type": "INCIDENT_NOTES_UPDATED",
                "severity": "LOW",
                "user_id": current_user.id,
                "username": current_user.username,
                "message": "Incident investigation notes updated",
                "metadata": {
                    "incident_id": incident.id,
                    "new_length": len(normalized_notes),
                    "reason": reason,
                },
            }
        )

        await db.commit()
        updated_incident = await self._get_incident_or_404(db, incident_id)
        return self._serialize_incident_details(updated_incident)

    async def update_incident_false_positive(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentFalsePositiveUpdateRequest,
        current_user: User,
    ) -> IncidentDetailsResponse:
        """Mark or clear the incident false-positive flag."""
        incident = await self._get_incident_or_404(db, incident_id)

        previous_value = bool(getattr(incident, "false_positive", False))
        next_value = bool(payload.is_false_positive)
        incident.false_positive = next_value

        request_metadata = self._normalize_metadata_dict(payload.metadata)
        reason = self._resolve_reason(
            request_metadata,
            fallback="false-positive flag updated",
        )
        request_metadata["reason"] = reason

        event_type = "FALSE_POSITIVE_MARKED" if next_value else "FALSE_POSITIVE_CLEARED"
        audit_action = "incident_false_positive_marked" if next_value else "incident_false_positive_cleared"
        message = "Incident marked as false positive" if next_value else "False-positive flag cleared"

        await self._append_incident_log(
            db=db,
            incident=incident,
            actor=current_user,
            event_type=event_type,
            severity="LOW",
            message=message,
            metadata={
                "previous": previous_value,
                "current": next_value,
                "updated_by": current_user.username,
                **request_metadata,
            },
        )

        self._append_audit_log(
            db=db,
            actor=current_user,
            action=audit_action,
            target_incident_id=incident.id,
            metadata={
                "incident_id": incident.id,
                "previous": previous_value,
                "current": next_value,
                "actor": current_user.username,
                **request_metadata,
            },
        )

        log_event(
            {
                "event_type": "INCIDENT_FALSE_POSITIVE_UPDATED",
                "severity": "LOW",
                "user_id": current_user.id,
                "username": current_user.username,
                "message": message,
                "metadata": {
                    "incident_id": incident.id,
                    "previous": previous_value,
                    "current": next_value,
                    "reason": reason,
                },
            }
        )

        await db.commit()
        updated_incident = await self._get_incident_or_404(db, incident_id)
        return self._serialize_incident_details(updated_incident)
