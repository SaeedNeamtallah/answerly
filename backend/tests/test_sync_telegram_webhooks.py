"""Telegram webhook sync script tests."""

import inspect
import unittest
from unittest.mock import patch

from backend.scripts import sync_telegram_webhooks
from backend.scripts.sync_telegram_webhooks import WebhookPreflightError, _preflight_webhook_url


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {
            "ok": True,
            "ignored": True,
            "reason": "unsupported_update",
        }

    def json(self):
        return self._payload


class _FakeAsyncClient:
    response = _FakeResponse()
    calls = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, *, headers, json):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return self.response


class SyncTelegramWebhooksTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        _FakeAsyncClient.response = _FakeResponse()
        _FakeAsyncClient.calls = []

    async def test_preflight_posts_safe_unsupported_update_to_webhook(self):
        with patch("backend.scripts.sync_telegram_webhooks.httpx.AsyncClient", _FakeAsyncClient):
            await _preflight_webhook_url("https://api.example.com/telegram/webhook/4/secret", "secret")

        self.assertEqual(len(_FakeAsyncClient.calls), 1)
        self.assertEqual(_FakeAsyncClient.calls[0]["headers"]["X-Telegram-Bot-Api-Secret-Token"], "secret")
        self.assertEqual(_FakeAsyncClient.calls[0]["json"], {"update_id": 0})

    async def test_preflight_rejects_public_url_that_returns_404(self):
        _FakeAsyncClient.response = _FakeResponse(status_code=404, payload={"detail": "Not Found"})

        with patch("backend.scripts.sync_telegram_webhooks.httpx.AsyncClient", _FakeAsyncClient):
            with self.assertRaisesRegex(WebhookPreflightError, "HTTP 404"):
                await _preflight_webhook_url("https://bad.example.com/telegram/webhook/4/secret", "secret")

    def test_sync_retries_error_integrations_after_url_fix(self):
        source = inspect.getsource(sync_telegram_webhooks.sync_active_webhooks)
        self.assertIn('status.in_(("active", "error"))', source)
