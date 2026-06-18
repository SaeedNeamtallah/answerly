"""Service layer for security dashboard data, simulation, and realtime stream payloads."""
from __future__ import annotations

import asyncio
import json
import random
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User, UserAccountStatus
from backend.security.event_service import get_security_stats, list_events, log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.services.incident_management_service import IncidentManagementService


class SecurityDashboardService:
    """Central security dashboard business logic built on the shared event system."""

    _USER_STATUS_EVENT_TYPES = {
        SecurityEventType.USER_SUSPENDED,
        SecurityEventType.USER_BLOCKED,
        SecurityEventType.USER_RESTORED,
    }
    _MAX_EXPORT_EVENTS = 5000

    def __init__(self) -> None:
        # Reuse the existing status-control service to keep simulation behavior
        # consistent with production account enforcement and audit logging.
        self._incident_management_service = IncidentManagementService()

    @staticmethod
    def normalize_limit(limit: int) -> int:
        return 50 if int(limit) == 50 else 20

    async def get_stats(self, *, db: AsyncSession) -> Dict[str, int]:
        return await get_security_stats(db)

    async def get_events(self, *, db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        safe_limit = self.normalize_limit(limit)
        return await list_events(db=db, limit=safe_limit)

    async def get_events_for_export(self, *, db: AsyncSession, limit: int = 1000) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(int(limit or 1000), self._MAX_EXPORT_EVENTS))
        return await list_events(db=db, limit=safe_limit)

    async def get_dashboard_payload(self, *, db: AsyncSession, limit: int = 20) -> Dict[str, Any]:
        safe_limit = self.normalize_limit(limit)
        return {
            "stats": await self.get_stats(db=db),
            "events": await self.get_events(db=db, limit=safe_limit),
        }

    @staticmethod
    def _normalize_account_status(value: Any) -> str:
        if isinstance(value, UserAccountStatus):
            return value.value

        normalized = str(value or UserAccountStatus.ACTIVE.value).strip().upper()
        if normalized.startswith("USERACCOUNTSTATUS."):
            normalized = normalized.split(".", 1)[1]
        if normalized not in {
            UserAccountStatus.ACTIVE.value,
            UserAccountStatus.SUSPENDED.value,
            UserAccountStatus.BLOCKED.value,
        }:
            return UserAccountStatus.ACTIVE.value
        return normalized

    async def get_user_status_summary(self, *, db: AsyncSession) -> Dict[str, int]:
        """Return aggregate counts for ACTIVE/SUSPENDED/BLOCKED users."""
        summary = {
            "total_active": 0,
            "total_suspended": 0,
            "total_blocked": 0,
        }

        stmt = select(User.status, func.count(User.id)).group_by(User.status)
        result = await db.execute(stmt)
        rows = result.all()

        for status_value, count in rows:
            normalized_status = self._normalize_account_status(status_value)
            count_value = int(count or 0)

            if normalized_status == UserAccountStatus.ACTIVE.value:
                summary["total_active"] = count_value
            elif normalized_status == UserAccountStatus.SUSPENDED.value:
                summary["total_suspended"] = count_value
            elif normalized_status == UserAccountStatus.BLOCKED.value:
                summary["total_blocked"] = count_value

        return summary

    async def get_user_status_events(self, *, db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent account status change events for dashboard activity feed."""
        safe_limit = max(1, min(int(limit or 20), 100))
        candidate_limit = min(1000, max(200, safe_limit * 12))
        candidate_events = await list_events(db=db, limit=candidate_limit)

        payload_events: List[Dict[str, Any]] = []
        for event in candidate_events:
            if event["event_type"] not in self._USER_STATUS_EVENT_TYPES:
                continue

            payload = event
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            actor = str(metadata.get("actor") or payload.get("username") or "system").strip() or "system"
            reason = str(metadata.get("reason") or "").strip()

            payload["actor"] = actor
            payload["reason"] = reason
            payload_events.append(payload)

            if len(payload_events) >= safe_limit:
                break

        return payload_events

    def simulate_attack(self, *, user_id: int, username: Optional[str], ip_address: Optional[str]) -> int:
        """Generate demo attack events exclusively through the central event logger."""
        login_failures = random.randint(5, 10)
        generated_count = 0

        for attempt in range(1, login_failures + 1):
            log_event(
                {
                    "event_type": SecurityEventType.LOGIN_FAIL,
                    "severity": SecuritySeverity.MEDIUM,
                    "user_id": user_id,
                    "username": username,
                    "ip_address": ip_address,
                    "message": f"Invalid password attempt #{attempt} (simulation)",
                    "is_simulation": True,
                    "metadata": {
                        "simulation": True,
                        "attack": "credential_stuffing",
                        "attempt": attempt,
                    },
                }
            )
            generated_count += 1

        log_event(
            {
                "event_type": SecurityEventType.BRUTE_FORCE,
                "severity": SecuritySeverity.HIGH,
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "message": "Multiple attempts detected (simulation)",
                "is_simulation": True,
                "metadata": {
                    "simulation": True,
                    "attack": "brute_force",
                },
            }
        )
        generated_count += 1

        log_event(
            {
                "event_type": SecurityEventType.XSS_ATTEMPT,
                "severity": SecuritySeverity.HIGH,
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "message": "Reflected XSS payload detected (simulation)",
                "is_simulation": True,
                "metadata": {
                    "simulation": True,
                    "attack": "xss",
                    "payload": "<script>alert(1)</script>",
                },
            }
        )
        generated_count += 1

        log_event(
            {
                "event_type": SecurityEventType.SQL_INJECTION,
                "severity": SecuritySeverity.CRITICAL,
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "message": "SQL injection pattern detected (simulation)",
                "is_simulation": True,
                "metadata": {
                    "simulation": True,
                    "attack": "sql_injection",
                    "payload": "' OR 1=1 --",
                },
            }
        )
        generated_count += 1

        return generated_count

    async def simulate_attack_with_user_control(
        self,
        *,
        db: AsyncSession,
        actor_username: str,
        actor_user_id: int,
        ip_address: Optional[str],
        target_user_id: Optional[int] = None,
        escalate_to_block: bool = True,
        block_reason: str = "attack_simulation_escalation",
    ) -> Dict[str, Any]:
        """Run simulation events and optionally enforce a real user block.

        This keeps demo mode realistic: telemetry and account control are produced
        by the same services used in real incidents, so the dashboard reflects SOC
        workflows instead of synthetic counters only.
        """
        generated_count = self.simulate_attack(
            user_id=actor_user_id,
            username=actor_username,
            ip_address=ip_address,
        )

        resolved_target_user_id = int(target_user_id or actor_user_id)
        escalation_applied = False
        escalation_result = "none"

        if escalate_to_block:
            await self._incident_management_service.block_user(
                user_id=resolved_target_user_id,
                reason=str(block_reason or "attack_simulation_escalation"),
                actor=actor_username,
                db=db,
            )
            escalation_applied = True
            escalation_result = "blocked"

            # Emit an explicit simulation marker so demos can distinguish
            # simulation-driven enforcement from organic incidents.
            log_event(
                {
                    "event_type": SecurityEventType.ATTACK_SIMULATION,
                    "severity": SecuritySeverity.HIGH,
                    "user_id": resolved_target_user_id,
                    "username": actor_username,
                    "ip_address": ip_address,
                    "message": "Attack simulation escalated to account block",
                    "is_simulation": True,
                    "metadata": {
                        "simulation": True,
                        "escalation": escalation_result,
                        "target_user_id": resolved_target_user_id,
                        "reason": str(block_reason or "attack_simulation_escalation"),
                    },
                }
            )

        return {
            "generated_count": int(generated_count),
            "escalation_applied": escalation_applied,
            "escalation_result": escalation_result,
            "target_user_id": resolved_target_user_id,
        }

    async def stream_dashboard_updates(
        self,
        *,
        request: Request,
        db: AsyncSession,
        limit: int = 20,
    ) -> AsyncIterator[str]:
        """Yield SSE chunks containing dashboard payload updates from the event system."""
        safe_limit = self.normalize_limit(limit)
        last_signature: Optional[str] = None
        idle_ticks = 0

        while True:
            if await request.is_disconnected():
                break

            payload = await self.get_dashboard_payload(db=db, limit=safe_limit)
            stats = payload["stats"]
            events = payload["events"]

            newest_id = events[0]["id"] if events else "none"
            signature = (
                f"{newest_id}:{stats['total_events']}:{stats['login_failures']}:"
                f"{stats['brute_force_attempts']}:{stats['blocked_uploads']}"
            )

            if signature != last_signature:
                yield f"event: security-update\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"
                last_signature = signature
                idle_ticks = 0
            else:
                idle_ticks += 1

            if idle_ticks >= 15:
                yield ": keep-alive\n\n"
                idle_ticks = 0

            await asyncio.sleep(1)


security_dashboard_service = SecurityDashboardService()
