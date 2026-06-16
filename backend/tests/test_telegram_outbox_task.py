"""Telegram outbox worker unit tests (no real DB)."""

import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import backend.tasks.telegram_outbox as telegram_outbox
from backend.services.telegram_api_service import TelegramAPIError


@dataclass
class FakeMessage:
    id: int
    text: str
    bot_integration_id: int | None
    telegram_customer_id: int | None
    delivery_status: str = "pending"
    delivery_attempts: int = 0
    delivery_claimed_at: object | None = None
    delivery_next_attempt_at: object | None = None
    created_at: object | None = None
    telegram_message_id: str | None = None


class FakeResult:
    def __init__(self, messages):
        self._messages = messages

    def scalars(self):
        return self

    def all(self):
        return list(self._messages)


class FakeDB:
    def __init__(self, messages, integration, customer):
        self._messages = messages
        self._integration = integration
        self._customer = customer
        self.commits = 0

    async def execute(self, _stmt):
        return FakeResult(self._messages)

    async def get(self, model, _id):
        if model.__name__ == "BotIntegration":
            return self._integration
        if model.__name__ == "TelegramCustomer":
            return self._customer
        return None

    async def commit(self):
        self.commits += 1

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSessionMaker:
    def __init__(self, db):
        self._db = db

    def __call__(self):
        return self._db


class FakeEngine:
    async def dispose(self):
        return None


class TelegramOutboxTaskTests(unittest.IsolatedAsyncioTestCase):
    async def test_outbox_worker_claims_and_sends_pending_message(self):
        message = FakeMessage(id=1, text="hello", bot_integration_id=10, telegram_customer_id=20)
        integration = SimpleNamespace(token_encrypted="encrypted")
        customer = SimpleNamespace(chat_id="123")
        fake_db = FakeDB([message], integration, customer)
        session_maker = FakeSessionMaker(fake_db)

        with (
            patch("backend.tasks.telegram_outbox.create_async_engine", return_value=FakeEngine()),
            patch("backend.tasks.telegram_outbox.async_sessionmaker", return_value=session_maker),
            patch("backend.tasks.telegram_outbox.TokenCryptoService.decrypt_token", return_value="token"),
            patch("backend.tasks.telegram_outbox.TelegramAPIService.send_message", new=AsyncMock(return_value={"message_id": 42})),
        ):
            result = await telegram_outbox._deliver_pending_messages()

        self.assertEqual(result["sent"], 1)
        self.assertEqual(message.delivery_status, "sent")
        self.assertEqual(message.telegram_message_id, "42")
        self.assertGreaterEqual(fake_db.commits, 2)

    async def test_outbox_worker_recovers_stale_sending_message(self):
        message = FakeMessage(
            id=2,
            text="retry me",
            bot_integration_id=10,
            telegram_customer_id=20,
            delivery_status="sending",
            delivery_attempts=1,
        )
        integration = SimpleNamespace(token_encrypted="encrypted")
        customer = SimpleNamespace(chat_id="123")
        fake_db = FakeDB([message], integration, customer)
        session_maker = FakeSessionMaker(fake_db)

        with (
            patch("backend.tasks.telegram_outbox.create_async_engine", return_value=FakeEngine()),
            patch("backend.tasks.telegram_outbox.async_sessionmaker", return_value=session_maker),
            patch("backend.tasks.telegram_outbox.TokenCryptoService.decrypt_token", return_value="token"),
            patch("backend.tasks.telegram_outbox.TelegramAPIService.send_message", new=AsyncMock(return_value={"message_id": 43})),
        ):
            result = await telegram_outbox._deliver_pending_messages()

        self.assertEqual(result["recovered"], 1)
        self.assertEqual(result["sent"], 1)
        self.assertEqual(message.delivery_status, "sent")
        self.assertEqual(message.delivery_attempts, 2)

    async def test_outbox_worker_schedules_backoff_after_transient_failure(self):
        message = FakeMessage(id=3, text="retry later", bot_integration_id=10, telegram_customer_id=20)
        integration = SimpleNamespace(token_encrypted="encrypted")
        customer = SimpleNamespace(chat_id="123")
        fake_db = FakeDB([message], integration, customer)
        session_maker = FakeSessionMaker(fake_db)

        with (
            patch("backend.tasks.telegram_outbox.create_async_engine", return_value=FakeEngine()),
            patch("backend.tasks.telegram_outbox.async_sessionmaker", return_value=session_maker),
            patch("backend.tasks.telegram_outbox.TokenCryptoService.decrypt_token", return_value="token"),
            patch(
                "backend.tasks.telegram_outbox.TelegramAPIService.send_message",
                new=AsyncMock(side_effect=TelegramAPIError("temporary")),
            ),
        ):
            before = datetime.now(timezone.utc)
            result = await telegram_outbox._deliver_pending_messages()

        self.assertEqual(result["retried"], 1)
        self.assertEqual(message.delivery_status, "pending")
        self.assertIsNotNone(message.delivery_next_attempt_at)
        self.assertGreater(message.delivery_next_attempt_at, before)


if __name__ == "__main__":
    unittest.main()
