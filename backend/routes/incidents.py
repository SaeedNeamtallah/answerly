"""Incident response API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.controllers.incident_controller import IncidentController
from backend.database import get_db
from backend.database.models import IncidentSeverity, IncidentStatus, User
from backend.models.incident_models import (
    IncidentActionRequest,
    IncidentAssignRequest,
    IncidentAssignResponse,
    IncidentDetailsResponse,
    IncidentFalsePositiveUpdateRequest,
    IncidentNotesUpdateRequest,
    IncidentResponse,
    IncidentStatusUpdateRequest,
)
from backend.security.auth import require_incident_access


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
    dependencies=[Depends(require_incident_access)],
)


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[IncidentStatus] = Query(default=None),
    severity: Optional[IncidentSeverity] = Query(default=None),
    false_positive: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    controller: IncidentController = Depends(IncidentController),
):
    """List incidents with optional status/severity filtering."""
    return await controller.list_incidents(
        db=db,
        status=status,
        severity=severity,
        is_false_positive=false_positive,
    )


@router.get("/{incident_id}", response_model=IncidentDetailsResponse)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    controller: IncidentController = Depends(IncidentController),
):
    """Get incident details including all related logs."""
    return await controller.get_incident_details(db=db, incident_id=incident_id)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdateRequest,
    current_user: User = Depends(require_incident_access),
    db: AsyncSession = Depends(get_db),
    controller: IncidentController = Depends(IncidentController),
):
    """Update incident status with enforced lifecycle transitions."""
    return await controller.update_incident_status(
        db=db,
        incident_id=incident_id,
        payload=payload,
        current_user=current_user,
    )


@router.post("/{incident_id}/assign", response_model=IncidentAssignResponse)
async def assign_incident(
    incident_id: int,
    payload: Optional[IncidentAssignRequest] = None,
    current_user: User = Depends(require_incident_access),
    db: AsyncSession = Depends(get_db),
    controller: IncidentController = Depends(IncidentController),
):
    """Assign an incident to the currently authenticated security engineer."""
    return await controller.assign_incident(
        db=db,
        incident_id=incident_id,
        current_user=current_user,
        payload=payload,
    )


@router.post("/{incident_id}/action", response_model=IncidentDetailsResponse)
async def apply_incident_action(
    incident_id: int,
    payload: IncidentActionRequest,
    current_user: User = Depends(require_incident_access),
    db: AsyncSession = Depends(get_db),
    controller: IncidentController = Depends(IncidentController),
):
    """Apply security action to incident and record an audit log entry."""
    return await controller.apply_incident_action(
        db=db,
        incident_id=incident_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{incident_id}/notes", response_model=IncidentDetailsResponse)
async def update_incident_notes(
    incident_id: int,
    payload: IncidentNotesUpdateRequest,
    current_user: User = Depends(require_incident_access),
    db: AsyncSession = Depends(get_db),
    controller: IncidentController = Depends(IncidentController),
):
    """Update investigation notes for an incident."""
    return await controller.update_incident_notes(
        db=db,
        incident_id=incident_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{incident_id}/false-positive", response_model=IncidentDetailsResponse)
async def update_false_positive_flag(
    incident_id: int,
    payload: IncidentFalsePositiveUpdateRequest,
    current_user: User = Depends(require_incident_access),
    db: AsyncSession = Depends(get_db),
    controller: IncidentController = Depends(IncidentController),
):
    """Mark or clear an incident false-positive flag."""
    return await controller.update_false_positive_flag(
        db=db,
        incident_id=incident_id,
        payload=payload,
        current_user=current_user,
    )
