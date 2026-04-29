"""Telegram outbox worker unit tests (no real DB)."""

import unittest
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import backend.tasks.telegram_outbox as telegram_outbox


@dataclass
class FakeMessage:
    id: int
    text: str
    bot_integration_id: int | None
    telegram_customer_id: int | None
    delivery_status: str = "pending"
    delivery_attempts: int = 0
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


class TelegramOutboxTaskTests(unittest.IsolatedAsyncioTestCase):
    async def test_outbox_worker_claims_and_sends_pending_message(self):
        message = FakeMessage(id=1, text="hello", bot_integration_id=10, telegram_customer_id=20)
        integration = SimpleNamespace(token_encrypted="encrypted")
        customer = SimpleNamespace(chat_id="123")
        fake_db = FakeDB([message], integration, customer)
        session_maker = FakeSessionMaker(fake_db)

        async def fake_get_setup_utils():
            return (None, session_maker, None, None, None, None, None)

        with (
            patch("backend.tasks.telegram_outbox.get_setup_utils", side_effect=fake_get_setup_utils),
            patch("backend.tasks.telegram_outbox.TokenCryptoService.decrypt_token", return_value="token"),
            patch("backend.tasks.telegram_outbox.TelegramAPIService.send_message", new=AsyncMock(return_value={"message_id": 42})),
        ):
            result = await telegram_outbox._deliver_pending_messages()

        self.assertEqual(result["sent"], 1)
        self.assertEqual(message.delivery_status, "sent")
        self.assertEqual(message.telegram_message_id, "42")
        self.assertGreaterEqual(fake_db.commits, 2)


if __name__ == "__main__":
    unittest.main()

