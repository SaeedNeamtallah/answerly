"""Unauthenticated Telegram webhook endpoint for DB-backed integrations."""
from __future__ import annotations

import logging
from hmac import compare_digest
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.config import settings
from backend.services.telegram_webhook_service import (
    TelegramWebhookError,
    TelegramWebhookService,
    TelegramWebhookThrottle,
)
from backend.services.token_crypto_service import SecretConfigurationError


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])


def get_telegram_webhook_service() -> TelegramWebhookService:
    return TelegramWebhookService()


@router.post("/webhook/{integration_id}/{webhook_secret}")
async def telegram_webhook(
    integration_id: int,
    webhook_secret: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: TelegramWebhookService = Depends(get_telegram_webhook_service),
):
    if settings.telegram_webhook_require_secret_header:
        header_secret = str(request.headers.get("x-telegram-bot-api-secret-token") or "")
        if not compare_digest(header_secret, str(webhook_secret)):
            raise HTTPException(status_code=404, detail="Bot integration not found")

    try:
        payload: dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Telegram update") from exc

    try:
        return await service.handle_update(
            db,
            integration_id=integration_id,
            webhook_secret=webhook_secret,
            update=payload,
        )
    except TelegramWebhookThrottle as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except TelegramWebhookError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SecretConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Bot token encryption is not configured") from exc
    except Exception as exc:
        logger.exception("Unexpected Telegram webhook error")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
