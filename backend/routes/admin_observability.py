"""Platform-owner-only observability dashboard routes."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.database.models import User
from backend.security.auth import require_platform_owner_access
from backend.services.observability_service import ObservabilityService


router = APIRouter(prefix="/admin/observability", tags=["Admin Observability"])


class AdminObservabilityDashboardResponse(BaseModel):
    uid: str
    title: str
    category: str
    description: str
    url: str
    embed_url: Optional[str] = None


class AdminObservabilityEndpointStatus(BaseModel):
    status: str
    public_url: Optional[str] = None
    embedding_enabled: Optional[bool] = None
    version: Optional[str] = None
    database: Optional[str] = None
    base_url_configured: Optional[bool] = None


class AdminObservabilityTarget(BaseModel):
    job: str
    label: str
    health: str
    last_scrape: Optional[datetime | str] = None
    scrape_url: Optional[str] = None
    last_error: Optional[str] = None


class AdminObservabilityMetric(BaseModel):
    key: str
    label: str
    unit: str
    value: Optional[float] = None
    status: str
    description: str


class AdminObservabilitySummaryResponse(BaseModel):
    range: str
    generated_at: datetime
    grafana: AdminObservabilityEndpointStatus
    prometheus: AdminObservabilityEndpointStatus
    targets: list[AdminObservabilityTarget]
    metrics: list[AdminObservabilityMetric]


@router.get("/dashboards", response_model=list[AdminObservabilityDashboardResponse])
async def list_observability_dashboards(
    range: str = "1h",
    _: User = Depends(require_platform_owner_access),
):
    return ObservabilityService().list_dashboards(range)


@router.get("/summary", response_model=AdminObservabilitySummaryResponse)
async def get_observability_summary(
    range: str = "1h",
    _: User = Depends(require_platform_owner_access),
):
    return await ObservabilityService().build_summary(range)
