"""
Bot Configuration Routes.
API endpoints for configuring the Telegram bot.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import json
import os
import httpx
from telegram_bot.config import bot_settings
from backend.database import get_db
from backend.database.models import Project
from backend.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/bot", tags=["Bot Config"])

CONFIG_FILE = "bot_config.json"

class BotConfig(BaseModel):
    active_project_id: Optional[int] = None

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def _get_user_bot_config(config: dict, user_id: int) -> dict:
    users_config = config.get("users")
    if not isinstance(users_config, dict):
        users_config = {}
        config["users"] = users_config

    user_key = str(user_id)
    user_config = users_config.get(user_key)
    if not isinstance(user_config, dict):
        user_config = {}
        users_config[user_key] = user_config

    return user_config

@router.get("/config")
async def get_bot_config(current_user: CurrentUser = Depends(get_current_user)):
    """Get current user bot configuration."""
    config = load_config()
    return _get_user_bot_config(config, current_user.user_id)

@router.post("/config")
async def update_bot_config(
    config: BotConfig,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update current user bot configuration (active project)."""
    current_config = load_config()
    user_config = _get_user_bot_config(current_config, current_user.user_id)

    if config.active_project_id is not None:
        stmt = select(Project.id).where(
            Project.id == config.active_project_id,
            Project.user_id == current_user.user_id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Project not found")

        user_config["active_project_id"] = config.active_project_id

    save_config(current_config)
    return user_config

@router.post("/profile")
async def update_bot_profile(
    name: str = Form(...),
    # image: UploadFile = File(None) # Image upload to be implemented if needed
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update Telegram Bot Profile (Name).
    Requires 'setMyName' permission.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Update Name
            url = f"https://api.telegram.org/bot{bot_settings.telegram_bot_token}/setMyName"
            response = await client.post(url, json={"name": name})
            response.raise_for_status()
            
            return {"status": "success", "message": "Bot profile updated"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
