"""Security dashboard routes and simulation endpoints."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.database.models import User, UserAccountStatus
from backend.config import settings
from backend.security.auth import ROLE_PLATFORM_OWNER, get_product_role_for_user, require_security_center_access
from backend.services.security_dashboard_service import security_dashboard_service


router = APIRouter(
    prefix="/security",
    tags=["Security"],
)


class SecurityStatsResponse(BaseModel):
    total_events: int
    login_failures: int
    brute_force_attempts: int
    blocked_uploads: int


class SecurityEventResponse(BaseModel):
    id: UUID
    timestamp: datetime
    event_type: str
    severity: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    message: str
    metadata: Dict[str, Any]


class SecuritySimulationResponse(BaseModel):
    generated_count: int
    escalation_applied: bool = False
    escalation_result: str = "none"
    target_user_id: Optional[int] = None
    stats: SecurityStatsResponse
    events: List[SecurityEventResponse]


class SecurityUserStatusSummaryResponse(BaseModel):
    total_active: int
    total_suspended: int
    total_blocked: int


class SecurityUserStatusEventResponse(BaseModel):
    id: UUID
    timestamp: datetime
    event_type: str
    user_id: Optional[int] = None
    actor: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _extract_client_ip(request: Request) -> Optional[str]:
    forwarded_for = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded_for:
        return forwarded_for[:128]
    if request.client and request.client.host:
        return str(request.client.host)[:128]
    return None


def _to_event_responses(events: List[Dict[str, Any]]) -> List[SecurityEventResponse]:
    return [SecurityEventResponse(**event) for event in events]


def _to_events_export_csv(events: List[Dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "event_id",
        "timestamp",
        "event_type",
        "severity",
        "user_id",
        "username",
        "ip_address",
        "message",
        "metadata_json",
    ])

    for row_id, event in enumerate(events, start=1):
        metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
        writer.writerow([
            str(row_id),
            str(event.get("id") or ""),
            str(event.get("timestamp") or ""),
            str(event.get("event_type") or ""),
            str(event.get("severity") or ""),
            str(event.get("user_id") or ""),
            str(event.get("username") or ""),
            str(event.get("ip_address") or ""),
            str(event.get("message") or ""),
            json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
        ])

    return output.getvalue()


async def _resolve_simulation_target_user_id(
    *,
    db: AsyncSession,
    current_user: User,
    requested_target_user_id: Optional[int],
) -> int:
    """Pick a realistic target for demo escalation with safe fallbacks."""
    if requested_target_user_id is not None:
        explicit_target_stmt = (
            select(User.id)
            .where(User.id == int(requested_target_user_id))
            .limit(1)
        )
        explicit_target = (await db.execute(explicit_target_stmt)).scalar_one_or_none()
        if explicit_target is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found",
            )
        return int(explicit_target)

    # Prefer another ACTIVE user so simulation block is visible without
    # immediately locking the currently operating SOC user.
    active_candidate_stmt = (
        select(User.id)
        .where(
            User.id != int(current_user.id),
            User.status == UserAccountStatus.ACTIVE,
        )
        .order_by(User.id.desc())
        .limit(1)
    )
    active_candidate = (await db.execute(active_candidate_stmt)).scalar_one_or_none()
    if active_candidate is not None:
        return int(active_candidate)

    fallback_candidate_stmt = (
        select(User.id)
        .where(User.id != int(current_user.id))
        .order_by(User.id.desc())
        .limit(1)
    )
    fallback_candidate = (await db.execute(fallback_candidate_stmt)).scalar_one_or_none()
    if fallback_candidate is not None:
        return int(fallback_candidate)

    return int(current_user.id)


@router.get("/stats", response_model=SecurityStatsResponse)
async def security_stats(
    _current_user: User = Depends(require_security_center_access),
):
    """Return aggregated security counters for dashboard cards."""
    return SecurityStatsResponse(**security_dashboard_service.get_stats())


@router.get("/events", response_model=List[SecurityEventResponse])
async def security_events(
    limit: int = Query(default=20, ge=1, le=50),
    _current_user: User = Depends(require_security_center_access),
):
    """Return latest security events for feed widgets."""
    payload = security_dashboard_service.get_dashboard_payload(limit=limit)
    return _to_event_responses(payload["events"])


@router.get("/events/export")
async def security_events_export(
    limit: int = Query(default=1000, ge=1, le=5000),
    _current_user: User = Depends(require_security_center_access),
):
    """Download security events as a CSV file for SOC reporting and evidence retention."""
    events = security_dashboard_service.get_events_for_export(limit=limit)
    csv_payload = _to_events_export_csv(events)
    filename = f"security-events-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=f"\ufeff{csv_payload}",
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/users/status-summary", response_model=SecurityUserStatusSummaryResponse)
async def security_users_status_summary(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_security_center_access),
):
    """Return aggregate account status counters for dashboard widgets."""
    summary = await security_dashboard_service.get_user_status_summary(db=db)
    return SecurityUserStatusSummaryResponse(**summary)


@router.get("/users/events", response_model=List[SecurityUserStatusEventResponse])
async def security_users_events(
    limit: int = Query(default=20, ge=1, le=100),
    _current_user: User = Depends(require_security_center_access),
):
    """Return latest user account status change events (suspend/block/restore)."""
    events = security_dashboard_service.get_user_status_events(limit=limit)
    return [SecurityUserStatusEventResponse(**event) for event in events]


@router.post("/simulate", response_model=SecuritySimulationResponse)
async def simulate_security_attack(
    request: Request,
    target_user_id: Optional[int] = Query(default=None, gt=0),
    escalate_to_block: bool = Query(default=False),
    current_user: User = Depends(require_security_center_access),
    db: AsyncSession = Depends(get_db),
):
    """Generate demo attack events and optionally escalate to real account block."""
    resolved_target_user_id = await _resolve_simulation_target_user_id(
        db=db,
        current_user=current_user,
        requested_target_user_id=target_user_id,
    )

    if escalate_to_block:
        if not settings.security_simulation_destructive_enabled:
            raise HTTPException(
                status_code=403,
                detail="Destructive simulation disabled by configuration",
            )
        if get_product_role_for_user(current_user) != ROLE_PLATFORM_OWNER:
            raise HTTPException(
                status_code=403,
                detail="Only platform owners can run destructive simulations",
            )

    simulation_result = await security_dashboard_service.simulate_attack_with_user_control(
        db=db,
        actor_username=current_user.username,
        actor_user_id=current_user.id,
        ip_address=_extract_client_ip(request),
        target_user_id=resolved_target_user_id,
        escalate_to_block=escalate_to_block,
        block_reason="attack_simulation_escalation",
    )
    await db.commit()

    payload = security_dashboard_service.get_dashboard_payload(limit=20)

    return SecuritySimulationResponse(
        generated_count=int(simulation_result.get("generated_count", 0)),
        escalation_applied=bool(simulation_result.get("escalation_applied", False)),
        escalation_result=str(simulation_result.get("escalation_result", "none")),
        target_user_id=simulation_result.get("target_user_id"),
        stats=SecurityStatsResponse(**payload["stats"]),
        events=_to_event_responses(payload["events"]),
    )


@router.get("/events/stream")
async def security_events_stream(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50),
    _current_user: User = Depends(require_security_center_access),
):
    """Stream security dashboard updates via SSE (events + aggregate stats)."""
    return StreamingResponse(
        security_dashboard_service.stream_dashboard_updates(
            request=request,
            limit=limit,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
