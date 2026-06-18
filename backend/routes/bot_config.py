"""
Bot Configuration Routes.
API endpoints for configuring the Telegram bot.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.connection import get_db
from backend.database.models import Project, User
from backend.security.auth import get_current_db_user
from backend.security.client_ip import get_optional_client_ip
from backend.security.event_service import log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.security.sanitization import sanitize_text
from backend.shared_config_paths import get_bot_config_path
from telegram_bot.config import bot_settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["Bot Config"])


class BotConfig(BaseModel):
    active_project_id: Optional[int] = None


def _load_config(config_path: Path) -> dict[str, Any]:
    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _save_config(config_path: Path, config: dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)


_LEGACY_BOT_CONFIG_WARNING = (
    "Deprecated legacy demo configuration. Production Telegram support uses "
    "database-backed /bot-integrations and /telegram/webhook routes."
)


@router.get("/config")
async def get_bot_config(
    request: Request,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    """Get deprecated legacy bot configuration with owner-aware access control."""
    config = _load_config(get_bot_config_path())
    active_project_id = config.get("active_project_id")

    if active_project_id is not None:
        try:
            normalized_project_id = int(active_project_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="Invalid active_project_id in legacy bot config") from exc

        stmt = select(Project.id).where(
            Project.id == normalized_project_id,
            Project.owner_id == current_user.id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            log_event(
                {
                    "event_type": SecurityEventType.AUTHZ_DENIED,
                    "severity": SecuritySeverity.HIGH,
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "ip_address": get_optional_client_ip(request),
                    "message": "Legacy bot config read denied",
                    "metadata": {
                        "path": request.url.path,
                        "method": request.method,
                        "active_project_id": normalized_project_id,
                    },
                }
            )
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        normalized_project_id = None

    return {
        "active_project_id": normalized_project_id,
        "legacy": True,
        "warning": _LEGACY_BOT_CONFIG_WARNING,
    }


@router.post("/config")
async def update_bot_config(
    config: BotConfig,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    """Update deprecated legacy bot configuration (active project)."""
    if config.active_project_id is None:
        raise HTTPException(status_code=400, detail="active_project_id is required")

    if config.active_project_id <= 0:
        raise HTTPException(status_code=400, detail="active_project_id must be a positive integer")

    configured_bot_username = (
        (os.getenv("BOT_API_USERNAME") or "").strip()
        or str(settings.auth_admin_username or "").strip()
    ).lower()
    config_owner_id = current_user.id

    if configured_bot_username:
        bot_user_stmt = (
            select(User.id)
            .where(func.lower(User.username) == configured_bot_username)
            .order_by(User.id.asc())
            .limit(1)
        )
        bot_user_result = await db.execute(bot_user_stmt)
        bot_user_id = bot_user_result.scalar_one_or_none()
        if bot_user_id is not None:
            config_owner_id = int(bot_user_id)

    stmt = select(Project.id).where(
        Project.id == config.active_project_id,
        Project.owner_id == config_owner_id,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    config_path = get_bot_config_path()
    current_config = _load_config(config_path)
    current_config["active_project_id"] = config.active_project_id
    current_config["legacy"] = True
    current_config["warning"] = _LEGACY_BOT_CONFIG_WARNING
    _save_config(config_path, current_config)
    return current_config


@router.post("/profile")
async def update_bot_profile(
    name: str = Form(...),
    current_user: User = Depends(get_current_db_user),
    # image: UploadFile = File(None) # Image upload to be implemented if needed
):
    """
    Update Telegram Bot Profile (Name).
    Requires 'setMyName' permission.
    """
    try:
        _ = current_user
        clean_name = sanitize_text(name, max_length=64, strip_html=True, allow_newlines=False)
        if not clean_name:
            raise HTTPException(status_code=400, detail="Bot name cannot be empty")

        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{bot_settings.telegram_bot_token}/setMyName"
            response = await client.post(url, json={"name": clean_name})
            response.raise_for_status()
            return {"status": "success", "message": "Bot profile updated"}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while updating bot profile")
        raise HTTPException(status_code=500, detail="Internal server error")
