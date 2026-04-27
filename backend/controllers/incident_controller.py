"""Controller layer for incident routes."""

from typing import List, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
from backend.services.auth_service import AuthService
from backend.services.incident_management_service import IncidentManagementService


class IncidentController:
    """Orchestrates incident APIs and delegates business logic to services."""

    def __init__(
        self,
        incident_service: IncidentManagementService = Depends(IncidentManagementService),
        auth_service: AuthService = Depends(AuthService),
    ):
        self.incident_service = incident_service
        self.auth_service = auth_service

    async def list_incidents(
        self,
        db: AsyncSession,
        *,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        is_false_positive: Optional[bool] = None,
    ) -> List[IncidentResponse]:
        return await self.incident_service.list_incidents(
            db,
            status=status,
            severity=severity,
            is_false_positive=is_false_positive,
        )

    async def get_incident_details(self, db: AsyncSession, *, incident_id: int) -> IncidentDetailsResponse:
        return await self.incident_service.get_incident_details(db, incident_id)

    async def update_incident_status(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentStatusUpdateRequest,
        current_user: User,
    ) -> IncidentResponse:
        return await self.incident_service.update_incident_status(
            db,
            incident_id=incident_id,
            payload=payload,
            current_user=current_user,
        )

    async def assign_incident(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        current_user: User,
        payload: Optional[IncidentAssignRequest] = None,
    ) -> IncidentAssignResponse:
        return await self.incident_service.assign_incident(
            db,
            incident_id=incident_id,
            current_user=current_user,
            payload=payload,
        )

    async def apply_incident_action(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentActionRequest,
        current_user: User,
    ) -> IncidentDetailsResponse:
        return await self.incident_service.apply_incident_action(
            db,
            incident_id=incident_id,
            payload=payload,
            current_user=current_user,
            auth_service=self.auth_service,
        )

    async def update_incident_notes(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentNotesUpdateRequest,
        current_user: User,
    ) -> IncidentDetailsResponse:
        return await self.incident_service.update_incident_notes(
            db,
            incident_id=incident_id,
            payload=payload,
            current_user=current_user,
        )

    async def update_false_positive_flag(
        self,
        db: AsyncSession,
        *,
        incident_id: int,
        payload: IncidentFalsePositiveUpdateRequest,
        current_user: User,
    ) -> IncidentDetailsResponse:
        return await self.incident_service.update_incident_false_positive(
            db,
            incident_id=incident_id,
            payload=payload,
            current_user=current_user,
        )
