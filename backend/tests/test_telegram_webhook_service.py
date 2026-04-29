"""Telegram webhook service unit tests."""

import inspect
import unittest

from backend.database.models import BotIntegration
from backend.services.telegram_webhook_service import TelegramWebhookError, TelegramWebhookService


class MissingIntegrationService:
    async def get_integration_by_webhook(self, db, *, integration_id, webhook_secret):
        return None


class TelegramWebhookServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_webhook_success_path_does_not_send_inline(self):
        source = inspect.getsource(TelegramWebhookService._handle_update_for_integration)
        self.assertNotIn("send_message", source)
        self.assertIn("delivery_status=\"pending\"", source)

    def test_webhook_failure_path_does_not_send_inline(self):
        source = inspect.getsource(TelegramWebhookService._handle_failure)
        self.assertNotIn("send_message", source)
        self.assertIn("delivery_status=\"pending\"", source)

    async def test_invalid_secret_raises_sanitized_not_found_error(self):
        service = TelegramWebhookService(
            integration_service=MissingIntegrationService(),
            conversation_service=object(),
            query_service=object(),
            crypto_service=object(),
            telegram_api=object(),
        )

        with self.assertRaisesRegex(TelegramWebhookError, "Bot integration not found"):
            await service.handle_update(db=None, integration_id=1, webhook_secret="bad", update={})

    async def test_disabled_integration_is_ignored_before_customer_creation(self):
        service = TelegramWebhookService(
            integration_service=object(),
            conversation_service=object(),
            query_service=object(),
            crypto_service=object(),
            telegram_api=object(),
        )
        integration = BotIntegration(id=1, owner_id=2, project_id=3, status="disabled")

        result = await service._handle_update_for_integration(
            db=None,
            integration=integration,
            update={"message": {"text": "hello", "chat": {"id": 10}}},
        )

        self.assertEqual(result["reason"], "integration_disabled")

    async def test_non_text_update_is_ignored(self):
        service = TelegramWebhookService(
            integration_service=object(),
            conversation_service=object(),
            query_service=object(),
            crypto_service=object(),
            telegram_api=object(),
        )
        integration = BotIntegration(id=1, owner_id=2, project_id=3, status="active")

        result = await service._handle_update_for_integration(
            db=None,
            integration=integration,
            update={"message": {"photo": [], "chat": {"id": 10}}},
        )

        self.assertEqual(result["reason"], "non_text_message")


if __name__ == "__main__":
    unittest.main()

