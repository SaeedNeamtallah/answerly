"""Regression tests for WhatsApp webhook handling and idempotency."""

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from backend.database.models import WhatsAppIntegration, ConversationMessage
from backend.services.whatsapp_webhook_service import WhatsAppWebhookService
from backend.routes import whatsapp_webhook

class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

class _FakeDb:
    def __init__(self, execute_result=None):
        self.execute_result = execute_result
        self.adds = []
        self.commits = 0

    async def get(self, model, ident):
        if model.__name__ == "WhatsAppIntegration":
            from backend.database.models import WhatsAppIntegration
            return WhatsAppIntegration(id=1, status="active")
        return self.execute_result

    async def flush(self):
        pass

    async def execute(self, stmt):
        stmt_str = str(stmt).lower()
        if "whatsapp_customers" in stmt_str:
            from backend.database.models import WhatsAppCustomer
            return _FakeScalarResult(WhatsAppCustomer(id=1))
        if "conversations" in stmt_str:
            from backend.database.models import Conversation
            return _FakeScalarResult(Conversation(id=1))
        return _FakeScalarResult(self.execute_result)

    def add(self, model):
        self.adds.append(model)

    async def commit(self):
        self.commits += 1

class WhatsAppWebhookTests(unittest.IsolatedAsyncioTestCase):
    async def test_webhook_idempotency_ignores_duplicate_message_id(self):
        # If the database already has a message with this telegram_message_id (which we map from whatsapp messageId),
        # the service should return Early without adding a new message or invoking Celery.
        existing_msg = ConversationMessage(id=5, telegram_message_id="msg-123")
        db = _FakeDb(execute_result=existing_msg)
        
        service = WhatsAppWebhookService()
        
        update = {
            "remoteJid": "1234567890@s.whatsapp.net",
            "pushName": "John Doe",
            "text": "Hello",
            "messageId": "msg-123",
            "timestamp": 1600000000
        }

        with patch.object(service, "_enqueue_reply_generation") as mock_enqueue:
            result = await service.handle_update(db, integration_id=1, update=update)
            
            # Since the message already exists, we should return success and NOT call enqueue
            self.assertEqual(result, {"success": True, "reason": "idempotent_skip"})
            self.assertEqual(len([x for x in db.adds if isinstance(x, ConversationMessage)]), 0)
            mock_enqueue.assert_not_called()

if __name__ == "__main__":
    unittest.main()
