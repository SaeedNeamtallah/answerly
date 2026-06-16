"""Synchronize recoverable Telegram bot webhooks with PUBLIC_WEBHOOK_BASE_URL."""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

import httpx
from sqlalchemy import select

from backend.database.connection import async_session_maker, close_db
from backend.database.models import BotIntegration
from backend.services.bot_integration_service import BotIntegrationService
from backend.services.telegram_api_service import TelegramAPIError
from backend.services.token_crypto_service import SecretConfigurationError


class WebhookPreflightError(RuntimeError):
    """Raised when PUBLIC_WEBHOOK_BASE_URL does not reach this backend webhook route."""


def _result_payload(
    integration: BotIntegration,
    *,
    ok: bool,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "id": int(integration.id),
        "name": str(integration.name),
        "telegram_username": integration.telegram_username,
        "status": str(integration.status),
        "webhook_url": BotIntegrationService.redact_webhook_url(integration.webhook_url),
        "ok": bool(ok),
        "error": error,
    }


async def _preflight_webhook_url(webhook_url: str | None, webhook_secret: str) -> None:
    if not webhook_url:
        raise WebhookPreflightError("PUBLIC_WEBHOOK_BASE_URL is not configured")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                str(webhook_url),
                headers={"X-Telegram-Bot-Api-Secret-Token": str(webhook_secret)},
                json={"update_id": 0},
            )
    except httpx.HTTPError as exc:
        raise WebhookPreflightError("PUBLIC_WEBHOOK_BASE_URL is unreachable") from exc

    if response.status_code != 200:
        raise WebhookPreflightError(
            f"PUBLIC_WEBHOOK_BASE_URL preflight returned HTTP {response.status_code}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise WebhookPreflightError("PUBLIC_WEBHOOK_BASE_URL preflight returned non-JSON response") from exc

    if data.get("ok") is not True or data.get("reason") != "unsupported_update":
        raise WebhookPreflightError("PUBLIC_WEBHOOK_BASE_URL does not reach the Telegram webhook route")


async def sync_active_webhooks(*, json_output: bool = False) -> int:
    service = BotIntegrationService()
    results: list[dict[str, Any]] = []

    async with async_session_maker() as db:
        result = await db.execute(
            select(BotIntegration)
            .where(BotIntegration.status.in_(("active", "error")))
            .order_by(BotIntegration.id.asc())
        )
        integrations = list(result.scalars().all())

        for integration in integrations:
            try:
                integration.webhook_url = service._build_webhook_url(integration.id, integration.webhook_secret)
                await _preflight_webhook_url(integration.webhook_url, integration.webhook_secret)
                token = service.crypto_service.decrypt_token(integration.token_encrypted)
                registered = await service.register_webhook(
                    integration,
                    token,
                    drop_pending_updates=False,
                )
                if not registered:
                    integration.status = "error"
                    integration.last_error = "PUBLIC_WEBHOOK_BASE_URL is not configured"
                    results.append(_result_payload(integration, ok=False, error=integration.last_error))
                else:
                    integration.status = "active"
                    integration.last_error = None
                    results.append(_result_payload(integration, ok=True))
            except WebhookPreflightError as exc:
                integration.status = "error"
                integration.last_error = str(exc)
                results.append(_result_payload(integration, ok=False, error=str(exc)))
            except (SecretConfigurationError, TelegramAPIError) as exc:
                integration.status = "error"
                integration.last_error = str(exc)
                results.append(_result_payload(integration, ok=False, error=str(exc)))
            except Exception:
                integration.status = "error"
                integration.last_error = "Unable to synchronize Telegram webhook"
                results.append(_result_payload(integration, ok=False, error=integration.last_error))

            db.add(integration)
            await db.commit()

    summary = {
        "total": len(results),
        "succeeded": sum(1 for item in results if item["ok"]),
        "failed": sum(1 for item in results if not item["ok"]),
        "results": results,
    }

    if json_output:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"Telegram webhook sync: {summary['succeeded']} succeeded, {summary['failed']} failed")
        for item in results:
            status = "ok" if item["ok"] else "failed"
            suffix = f" ({item['error']})" if item.get("error") else ""
            print(f"- #{item['id']} {item.get('telegram_username') or item['name']}: {status} {item['webhook_url']}{suffix}")

    return 0 if summary["failed"] == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    return parser.parse_args()


async def run(json_output: bool) -> int:
    try:
        return await sync_active_webhooks(json_output=json_output)
    finally:
        await close_db()


def main() -> int:
    args = parse_args()
    return asyncio.run(run(json_output=bool(args.json)))


if __name__ == "__main__":
    raise SystemExit(main())
