"""Database-backed Telegram bot integration routes."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.database.models import BotIntegration, User
from backend.security.auth import require_company_dashboard_access
from backend.services.bot_integration_service import BotIntegrationError, BotIntegrationService
from backend.services.telegram_api_service import TelegramAPIError
from backend.services.token_crypto_service import SecretConfigurationError


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bot-integrations", tags=["Bot Integrations"])


def get_bot_integration_service() -> BotIntegrationService:
    return BotIntegrationService()


class BotIntegrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=120)
    bot_token: str = Field(..., min_length=10, max_length=256)
    show_sources_to_customer: bool = False
    human_handoff_enabled: bool = True
    fallback_message: Optional[str] = Field(None, max_length=1000)


class BotIntegrationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    show_sources_to_customer: Optional[bool] = None
    human_handoff_enabled: Optional[bool] = None
    fallback_message: Optional[str] = Field(None, max_length=1000)


class BotTokenRotateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bot_token: str = Field(..., min_length=10, max_length=256)


class BotIntegrationResponse(BaseModel):
    id: int
    owner_id: int
    project_id: int
    name: str
    telegram_bot_id: str
    telegram_username: Optional[str]
    webhook_configured: bool
    status: str
    show_sources_to_customer: bool
    human_handoff_enabled: bool
    fallback_message: Optional[str]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


def _serialize_integration(integration: BotIntegration) -> BotIntegrationResponse:
    return BotIntegrationResponse(
        id=int(integration.id),
        owner_id=int(integration.owner_id),
        project_id=int(integration.project_id),
        name=str(integration.name),
        telegram_bot_id=str(integration.telegram_bot_id),
        telegram_username=integration.telegram_username,
        webhook_configured=bool(integration.webhook_url),
        status=str(integration.status),
        show_sources_to_customer=bool(integration.show_sources_to_customer),
        human_handoff_enabled=bool(integration.human_handoff_enabled),
        fallback_message=integration.fallback_message,
        last_error=integration.last_error,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


def _map_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SecretConfigurationError):
        return HTTPException(status_code=503, detail="Bot token encryption is not configured")
    if isinstance(exc, TelegramAPIError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, BotIntegrationError):
        detail = str(exc)
        status_code = 404 if "not found" in detail.lower() else 400
        return HTTPException(status_code=status_code, detail=detail)
    logger.exception("Unexpected bot integration error")
    return HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=list[BotIntegrationResponse])
async def list_bot_integrations(
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        integrations = await service.list_integrations(db, owner_id=current_user.id)
        return [_serialize_integration(integration) for integration in integrations]
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.post("/", response_model=BotIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_bot_integration(
    payload: BotIntegrationCreate,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        integration = await service.create_integration(
            db,
            owner_id=current_user.id,
            project_id=payload.project_id,
            name=payload.name,
            bot_token=payload.bot_token,
            show_sources_to_customer=payload.show_sources_to_customer,
            human_handoff_enabled=payload.human_handoff_enabled,
            fallback_message=payload.fallback_message,
            created_by_user_id=current_user.id,
        )
        return _serialize_integration(integration)
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.get("/{integration_id}", response_model=BotIntegrationResponse)
async def get_bot_integration(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        integration = await service.get_integration(db, owner_id=current_user.id, integration_id=integration_id)
        if integration is None:
            raise HTTPException(status_code=404, detail="Bot integration not found")
        return _serialize_integration(integration)
    except HTTPException:
        raise
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.patch("/{integration_id}", response_model=BotIntegrationResponse)
@router.put("/{integration_id}", response_model=BotIntegrationResponse)
async def update_bot_integration(
    integration_id: int,
    payload: BotIntegrationUpdate,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
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
            fallback_message_provided="fallback_message" in payload.model_fields_set,
        )
        return _serialize_integration(integration)
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.post("/{integration_id}/rotate-token", response_model=BotIntegrationResponse)
async def rotate_bot_token(
    integration_id: int,
    payload: BotTokenRotateRequest,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        integration = await service.rotate_token(
            db,
            owner_id=current_user.id,
            integration_id=integration_id,
            bot_token=payload.bot_token,
        )
        return _serialize_integration(integration)
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.post("/{integration_id}/enable", response_model=BotIntegrationResponse)
async def enable_bot_integration(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        integration = await service.set_status(db, owner_id=current_user.id, integration_id=integration_id, status="active")
        return _serialize_integration(integration)
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.post("/{integration_id}/disable", response_model=BotIntegrationResponse)
async def disable_bot_integration(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        integration = await service.set_status(db, owner_id=current_user.id, integration_id=integration_id, status="disabled")
        return _serialize_integration(integration)
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.get("/{integration_id}/readiness")
@router.post("/{integration_id}/test")
async def bot_integration_readiness(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        return await service.readiness(db, owner_id=current_user.id, integration_id=integration_id)
    except Exception as exc:
        raise _map_service_error(exc) from exc


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot_integration(
    integration_id: int,
    current_user: User = Depends(require_company_dashboard_access),
    db: AsyncSession = Depends(get_db),
    service: BotIntegrationService = Depends(get_bot_integration_service),
):
    try:
        await service.delete_integration(db, owner_id=current_user.id, integration_id=integration_id)
        return None
    except Exception as exc:
        raise _map_service_error(exc) from exc
