"""Security dashboard routes and simulation endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.database.models import User
from backend.security.auth import require_security_center_access
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
    stats: SecurityStatsResponse
    events: List[SecurityEventResponse]


def _extract_client_ip(request: Request) -> Optional[str]:
    forwarded_for = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded_for:
        return forwarded_for[:128]
    if request.client and request.client.host:
        return str(request.client.host)[:128]
    return None


def _to_event_responses(events: List[Dict[str, Any]]) -> List[SecurityEventResponse]:
    return [SecurityEventResponse(**event) for event in events]


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


@router.post("/simulate", response_model=SecuritySimulationResponse)
async def simulate_security_attack(
    request: Request,
    current_user: User = Depends(require_security_center_access),
):
    """Generate fake attack events for demos using the centralized event logger."""
    generated_count = security_dashboard_service.simulate_attack(
        user_id=current_user.id,
        username=current_user.username,
        ip_address=_extract_client_ip(request),
    )
    payload = security_dashboard_service.get_dashboard_payload(limit=20)

    return SecuritySimulationResponse(
        generated_count=generated_count,
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
