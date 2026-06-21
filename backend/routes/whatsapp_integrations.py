from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from backend.database import get_db
from backend.database.models import WhatsAppIntegration, User
from backend.security.auth import require_company_dashboard_access
from backend.services.whatsapp_integration_service import WhatsAppIntegrationError, WhatsAppIntegrationService
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp-integrations", tags=["WhatsApp Integrations"])

def get_whatsapp_integration_service() -> WhatsAppIntegrationService:
    return WhatsAppIntegrationService()

class WhatsAppIntegrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=120)
    phone_number: Optional[str] = Field(None, max_length=64)
    show_sources_to_customer: bool = False
    human_handoff_enabled: bool = True
    fallback_message: Optional[str] = Field(None, max_length=1000)
    system_prompt: Optional[str] = Field(None, max_length=4000)

class WhatsAppIntegrationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    show_sources_to_customer: Optional[bool] = None
    human_handoff_enabled: Optional[bool] = None
    fallback_message: Optional[str] = Field(None, max_length=1000)
    system_prompt: Optional[str] = Field(None, max_length=4000)

class WhatsAppIntegrationResponse(BaseModel):
    id: int
    owner_id: int
    project_id: int
    name: str
    phone_number: Optional[str]
    session_id: str
    status: str
    show_sources_to_customer: bool
    human_handoff_enabled: bool
    fallback_message: Optional[str]
    system_prompt: Optional[str]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

def _serialize_integration(integration: WhatsAppIntegration) -> WhatsAppIntegrationResponse:
    return WhatsAppIntegrationResponse(
        id=int(integration.id),
        owner_id=int(integration.owner_id),
        project_id=int(integration.project_id),
        name=str(integration.name),
        phone_number=integration.phone_number,
        session_id=str(integration.session_id),
        status=str(integration.status),
        show_sources_to_customer=bool(integration.show_sources_to_customer),
        human_handoff_enabled=bool(integration.human_handoff_enabled),
        fallback_message=integration.fallback_message,
        system_prompt=integration.system_prompt,
        last_error=integration.last_error,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )

def _map_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, WhatsAppIntegrationError):
        detail = str(exc)
        status_code = 404 if "not found" in detail.lower() else 400
        return HTTPException(status_code=status_code, detail=detail)
    logger.exception("Unexpected whatsapp integration error")
    return HTTPException(status_code=500, detail="Internal server error")

@router.get("", response_model=list[WhatsAppIntegrationResponse])
async def list_whatsapp_integrations(
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
):
    try:
        integrations = await service.list_integrations(db, owner_id=current_user.id)
        return [_serialize_integration(integration) for integration in integrations]
    except Exception as exc:
        raise _map_service_error(exc) from exc

@router.post("", response_model=WhatsAppIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_whatsapp_integration(
    payload: WhatsAppIntegrationCreate,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
):
    try:
        integration = await service.create_integration(
            db,
            owner_id=current_user.id,
            project_id=payload.project_id,
            name=payload.name,
            phone_number=payload.phone_number,
            show_sources_to_customer=payload.show_sources_to_customer,
            human_handoff_enabled=payload.human_handoff_enabled,
            fallback_message=payload.fallback_message,
            system_prompt=payload.system_prompt,
        )
        return _serialize_integration(integration)
    except Exception as exc:
        raise _map_service_error(exc) from exc

@router.get("/{integration_id}", response_model=WhatsAppIntegrationResponse)
async def get_whatsapp_integration(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
):
    try:
        integration = await service.get_integration(db, owner_id=current_user.id, integration_id=integration_id)
        if integration is None:
            raise HTTPException(status_code=404, detail="WhatsApp integration not found")
        return _serialize_integration(integration)
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_service_error(exc) from exc

@router.patch("/{integration_id}", response_model=WhatsAppIntegrationResponse)
@router.put("/{integration_id}", response_model=WhatsAppIntegrationResponse)
async def update_whatsapp_integration(
    integration_id: int,
    payload: WhatsAppIntegrationUpdate,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
):
    try:
        integration = await service.update_integration(
            db,
            owner_id=current_user.id,
            integration_id=integration_id,
            project_id=payload.project_id,
            name=payload.name,
            show_sources_to_customer=payload.show_sources_to_customer,
            human_handoff_enabled=payload.human_handoff_enabled,
            fallback_message=payload.fallback_message,
            system_prompt=payload.system_prompt,
            fallback_message_provided="fallback_message" in payload.model_fields_set,
            system_prompt_provided="system_prompt" in payload.model_fields_set,
        )
        return _serialize_integration(integration)
    except Exception as exc:
        raise _map_service_error(exc) from exc

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_whatsapp_integration(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
):
    try:
        integration = await service.get_integration(db, owner_id=current_user.id, integration_id=integration_id)
        if not integration:
            raise HTTPException(status_code=404, detail="WhatsApp integration not found")
            
        # call bridge to delete session
        bridge_url = "http://whatsapp_bridge:3002"
        async with httpx.AsyncClient() as client:
            try:
                await client.delete(f"{bridge_url}/api/sessions/{integration.session_id}")
            except Exception as bridge_exc:
                logger.warning(f"Could not delete session on bridge: {bridge_exc}")

        await service.delete_integration(db, owner_id=current_user.id, integration_id=integration_id)
        return None
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_service_error(exc) from exc

@router.post("/{integration_id}/connect")
async def connect_whatsapp_session(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
):
    integration = await service.get_integration(db, owner_id=current_user.id, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="WhatsApp integration not found")

    await service.update_status(db, integration=integration, status="initializing")

    bridge_url = "http://whatsapp_bridge:3002"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(f"{bridge_url}/api/sessions/{integration.session_id}")
            res.raise_for_status()
            return {"success": True}
        except httpx.HTTPError as e:
            logger.error(f"Error connecting to bridge: {e}")
            await service.update_status(
                db,
                integration=integration,
                status="error",
                last_error="Failed to connect session on WhatsApp bridge",
            )
            raise HTTPException(status_code=500, detail="Failed to connect session on bridge")

@router.get("/{integration_id}/session-status")
async def get_whatsapp_session_status(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
):
    integration = await service.get_integration(db, owner_id=current_user.id, integration_id=integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="WhatsApp integration not found")

    bridge_url = "http://whatsapp_bridge:3002"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{bridge_url}/api/sessions/{integration.session_id}/status")
            res.raise_for_status()
            payload = res.json()
            bridge_status = str(payload.get("status") or "unknown").lower()
            if bridge_status in {"not_found", "unknown"}:
                return {"status": integration.status, "last_error": integration.last_error}

            updated = await service.update_status(
                db,
                integration=integration,
                status=bridge_status,
                last_error=payload.get("last_error"),
            )
            payload["status"] = updated.status
            payload["last_error"] = updated.last_error
            return payload
        except httpx.HTTPError as e:
            logger.error(f"Error checking session status on bridge: {e}")
            return {"status": integration.status, "last_error": integration.last_error}
