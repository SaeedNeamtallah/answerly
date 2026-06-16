"""Small Telegram Bot API client that never logs bot tokens."""
from __future__ import annotations

from typing import Any

import httpx


class TelegramAPIError(RuntimeError):
    """Raised for sanitized Telegram API failures."""


class TelegramAPIService:
    """Wrapper around Telegram Bot API methods used by product integrations."""

    base_url = "https://api.telegram.org"

    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds

    async def _post(self, token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        clean_token = str(token or "").strip()
        if not clean_token:
            raise TelegramAPIError("Telegram bot token is required")

        url = f"{self.base_url}/bot{clean_token}/{method}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload or {})
        except httpx.HTTPError as exc:
            raise TelegramAPIError("Telegram API is unreachable") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise TelegramAPIError("Telegram API returned an invalid response") from exc

        if response.status_code >= 400 or not data.get("ok"):
            raise TelegramAPIError("Telegram API rejected the request")

        return data

    async def validate_token(self, token: str) -> dict[str, Any]:
        data = await self._post(token, "getMe")
        result = data.get("result") or {}
        bot_id = result.get("id")
        if bot_id is None:
            raise TelegramAPIError("Telegram token validation failed")
        return {
            "telegram_bot_id": str(bot_id),
            "telegram_username": result.get("username"),
            "first_name": result.get("first_name"),
        }

    async def set_webhook(
        self,
        token: str,
        webhook_url: str,
        *,
        drop_pending_updates: bool = False,
        secret_token: str | None = None,
    ) -> None:
        clean_url = str(webhook_url or "").strip()
        if not clean_url:
            raise TelegramAPIError("Webhook URL is required")
        payload: dict[str, Any] = {
            "url": clean_url,
            "drop_pending_updates": bool(drop_pending_updates),
        }
        if secret_token:
            payload["secret_token"] = str(secret_token)
        await self._post(
            token,
            "setWebhook",
            payload,
        )

    async def delete_webhook(self, token: str) -> None:
        await self._post(token, "deleteWebhook", {"drop_pending_updates": False})

    async def get_webhook_info(self, token: str) -> dict[str, Any]:
        data = await self._post(token, "getWebhookInfo")
        result = data.get("result")
        if not isinstance(result, dict):
            raise TelegramAPIError("Telegram webhook info is unavailable")
        return {
            "url": result.get("url"),
            "pending_update_count": int(result.get("pending_update_count") or 0),
            "last_error_date": result.get("last_error_date"),
            "last_error_message": result.get("last_error_message"),
            "max_connections": result.get("max_connections"),
            "ip_address": result.get("ip_address"),
        }

    async def send_message(self, token: str, chat_id: str, text: str) -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if not clean_text:
            raise TelegramAPIError("Message text is required")
        data = await self._post(
            token,
            "sendMessage",
            {
                "chat_id": str(chat_id),
                "text": clean_text[:4096],
                "disable_web_page_preview": True,
            },
        )
        return data.get("result") or {}

