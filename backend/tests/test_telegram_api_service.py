"""Telegram API service tests with mocked HTTP responses."""

import unittest
from unittest.mock import AsyncMock, patch

import httpx

from backend.services.telegram_api_service import TelegramAPIError, TelegramAPIService


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True, "result": {}}

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, response=None, error=None, calls=None, **kwargs):
        self.response = response or FakeResponse()
        self.error = error
        self.calls = calls if calls is not None else []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None):
        self.calls.append((url, json))
        if self.error:
            raise self.error
        return self.response


class TelegramAPIServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_validate_token_returns_bot_identity(self):
        calls = []
        response = FakeResponse(payload={"ok": True, "result": {"id": 123, "username": "support_bot"}})

        with patch("backend.services.telegram_api_service.httpx.AsyncClient", lambda *a, **k: FakeAsyncClient(response=response, calls=calls)):
            result = await TelegramAPIService().validate_token("123:secret-token")

        self.assertEqual(result["telegram_bot_id"], "123")
        self.assertEqual(result["telegram_username"], "support_bot")
        self.assertIn("/bot123:secret-token/getMe", calls[0][0])

    async def test_set_webhook_and_send_message_use_expected_methods(self):
        calls = []

        with patch("backend.services.telegram_api_service.httpx.AsyncClient", lambda *a, **k: FakeAsyncClient(calls=calls)):
            service = TelegramAPIService()
            await service.set_webhook("123:secret", "https://example.test/webhook")
            await service.send_message("123:secret", "456", "hello")

        self.assertIn("/setWebhook", calls[0][0])
        self.assertEqual(calls[0][1]["url"], "https://example.test/webhook")
        self.assertIn("/sendMessage", calls[1][0])
        self.assertEqual(calls[1][1]["chat_id"], "456")

    async def test_get_webhook_info_returns_sanitized_payload(self):
        calls = []
        response = FakeResponse(
            payload={
                "ok": True,
                "result": {
                    "url": "https://example.test/webhook",
                    "pending_update_count": 2,
                    "last_error_message": "Connection timeout",
                },
            }
        )

        with patch("backend.services.telegram_api_service.httpx.AsyncClient", lambda *a, **k: FakeAsyncClient(response=response, calls=calls)):
            result = await TelegramAPIService().get_webhook_info("123:secret")

        self.assertIn("/getWebhookInfo", calls[0][0])
        self.assertEqual(result["url"], "https://example.test/webhook")
        self.assertEqual(result["pending_update_count"], 2)
        self.assertEqual(result["last_error_message"], "Connection timeout")

    async def test_errors_are_sanitized_and_do_not_include_token(self):
        token = "123:super-secret"

        with patch(
            "backend.services.telegram_api_service.httpx.AsyncClient",
            lambda *a, **k: FakeAsyncClient(error=httpx.ConnectError(f"failed {token}")),
        ):
            with self.assertRaises(TelegramAPIError) as ctx:
                await TelegramAPIService().validate_token(token)

        self.assertNotIn(token, str(ctx.exception))
        self.assertIn("unreachable", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

