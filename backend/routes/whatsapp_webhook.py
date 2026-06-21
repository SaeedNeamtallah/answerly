"""Webhook endpoint for WhatsApp bot integrations from Baileys bridge."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.whatsapp_integration_service import (
    WhatsAppIntegrationError,
    WhatsAppIntegrationService,
)
from backend.services.whatsapp_webhook_service import (
    WhatsAppWebhookError,
    WhatsAppWebhookService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Webhook"])

def get_whatsapp_webhook_service() -> WhatsAppWebhookService:
    return WhatsAppWebhookService()

class WhatsAppStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., min_length=1, max_length=32)
    last_error: str | None = Field(default=None, max_length=1000)

@router.post("/webhook/{session_id}/status")
async def whatsapp_status_update(
    session_id: str,
    payload: WhatsAppStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    integration_service = WhatsAppIntegrationService()
    try:
        integration = await integration_service.update_status_by_session_id(
            db,
            session_id=session_id,
            status=payload.status,
            last_error=payload.last_error,
        )
        return {
            "success": True,
            "status": integration.status,
            "last_error": integration.last_error,
        }
    except WhatsAppIntegrationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.post("/webhook/{session_id}")
async def whatsapp_webhook(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: WhatsAppWebhookService = Depends(get_whatsapp_webhook_service),
):
    try:
        payload: dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid WhatsApp update") from exc

    # lookup integration by session_id
    integration_service = WhatsAppIntegrationService()
    integration = await integration_service.get_integration_by_session_id(db, session_id=session_id)
    if not integration:
        raise HTTPException(status_code=404, detail="WhatsApp integration not found")

    try:
        return await service.handle_update(
            db,
            integration_id=integration.id,
            update=payload,
        )
    except WhatsAppWebhookError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected WhatsApp webhook error")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
