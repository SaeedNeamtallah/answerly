"""Telegram webhook service unit tests."""

import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.database.models import BotIntegration
from backend.routes import telegram_webhook
from backend.services.telegram_webhook_service import TelegramWebhookError, TelegramWebhookService


class MissingIntegrationService:
    async def get_integration_by_webhook(self, db, *, integration_id, webhook_secret):
        return None


class FakeDB:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class FakeConversationService:
    def __init__(self):
        self.customer = SimpleNamespace(id=20, is_blocked=False, language_code="en")
        self.conversation = SimpleNamespace(id=30, status="open", needs_human=False)
        self.saved_messages = []

    async def get_or_create_customer(self, db, *, integration, chat_id, telegram_user):
        return self.customer

    async def get_or_create_conversation(self, db, *, integration, customer):
        return self.conversation

    async def save_message(self, db, **kwargs):
        message = SimpleNamespace(
            id=40,
            text=kwargs["text"],
            retrieval_metadata_json=kwargs.get("retrieval_metadata"),
        )
        self.saved_messages.append(kwargs)
        return message, True


class TelegramWebhookServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_route_requires_telegram_secret_header_when_enabled(self):
        source = inspect.getsource(telegram_webhook.telegram_webhook)
        self.assertIn("x-telegram-bot-api-secret-token", source)
        self.assertIn("compare_digest", source)

    def test_webhook_success_path_queues_reply_generation(self):
        source = inspect.getsource(TelegramWebhookService._handle_update_for_integration)
        self.assertNotIn("send_message", source)
        self.assertIn("_enqueue_reply_generation", source)

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

    async def test_text_update_is_persisted_and_reply_task_is_enqueued(self):
        conversation_service = FakeConversationService()
        service = TelegramWebhookService(
            integration_service=object(),
            conversation_service=conversation_service,
            query_service=object(),
            crypto_service=object(),
            telegram_api=object(),
        )
        integration = BotIntegration(
            id=1,
            owner_id=2,
            project_id=3,
            status="active",
            human_handoff_enabled=True,
        )

        with patch.object(TelegramWebhookService, "_enqueue_reply_generation") as enqueue:
            result = await service._handle_update_for_integration(
                db=FakeDB(),
                integration=integration,
                update={
                    "update_id": 100,
                    "message": {
                        "message_id": 200,
                        "text": "hello",
                        "chat": {"id": 10},
                        "from": {"id": 11, "language_code": "en"},
                    },
                },
            )

        self.assertTrue(result["reply_queued"])
        enqueue.assert_called_once_with(40)
        self.assertEqual(conversation_service.saved_messages[0]["sender_type"], "customer")
        self.assertEqual(
            conversation_service.saved_messages[0]["retrieval_metadata"]["reply_generation_status"],
            "queued",
        )


if __name__ == "__main__":
    unittest.main()

