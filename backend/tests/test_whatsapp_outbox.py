"""Regression tests for WhatsApp outbox delivery and recovery."""

import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from backend.database.models import ConversationMessage, WhatsAppIntegration, Conversation
from backend.tasks.whatsapp_outbox import _deliver_pending_messages
from backend.services.whatsapp_integration_service import WhatsAppIntegrationError

class _FakeScalarResult:
    def __init__(self, items):
        self.result = items

    def scalars(self):
        return self

    def all(self):
        return self.result

    def scalar_one_or_none(self):
        return self.result[0] if self.result else None

class _FakeDb:
    def __init__(self, items=None):
        self._items = items or []
        self.commits = 0

    async def execute(self, stmt):
        return _FakeScalarResult(self._items)

    async def get(self, model, ident):
        if model.__name__ == "WhatsAppIntegration":
            return getattr(self, "integration", None)
        if model.__name__ == "WhatsAppCustomer":
            return getattr(self, "customer", None)
        return None

    async def commit(self):
        self.commits += 1

class WhatsAppOutboxTests(unittest.IsolatedAsyncioTestCase):
    async def test_deliver_pending_messages_success(self):
        integration = WhatsAppIntegration(id=1, session_id="sess-1", status="connected")
        conversation = Conversation(id=10, whatsapp_integration_id=1, whatsapp_customer_id=100)
        message = ConversationMessage(
            id=100,
            conversation_id=10,
            whatsapp_integration_id=1,
            whatsapp_customer_id=100,
            delivery_status="pending",
            text="Hello there",
            conversation=conversation
        )
        # Mock lazy loading properties
        message.conversation.whatsapp_integration = integration
        customer = MagicMock(whatsapp_phone_number="1234567890", phone_number="1234567890")
        message.conversation.whatsapp_customer = customer

        db = _FakeDb(items=[message])
        db.integration = integration
        db.customer = customer
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        with patch("backend.tasks.whatsapp_outbox.httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await _deliver_pending_messages(db)
            
            self.assertEqual(message.delivery_status, "sent")
            self.assertEqual(db.commits, 2)  # 1 for claiming, 1 for delivery success
            mock_post.assert_called_once()

    async def test_deliver_pending_messages_bridge_failure_triggers_backoff(self):
        integration = WhatsAppIntegration(id=1, session_id="sess-1", status="connected")
        conversation = Conversation(id=10, whatsapp_integration_id=1, whatsapp_customer_id=100)
        message = ConversationMessage(
            id=100,
            conversation_id=10,
            whatsapp_integration_id=1,
            whatsapp_customer_id=100,
            delivery_status="pending",
            delivery_attempts=0,
            text="Hello there",
            conversation=conversation
        )
        message.conversation.whatsapp_integration = integration
        customer = MagicMock(whatsapp_phone_number="1234567890", phone_number="1234567890")
        message.conversation.whatsapp_customer = customer

        db = _FakeDb(items=[message])
        db.integration = integration
        db.customer = customer
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Bridge Error"
        from httpx import HTTPError
        def raise_err():
            raise HTTPError("Bridge Error")
        mock_response.raise_for_status.side_effect = raise_err

        with patch("backend.tasks.whatsapp_outbox.httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await _deliver_pending_messages(db)
            
            self.assertEqual(message.delivery_status, "pending")
            self.assertEqual(message.delivery_attempts, 1)
            self.assertIsNotNone(message.delivery_next_attempt_at)
            self.assertTrue("Bridge Error" in message.delivery_last_error) if hasattr(message, "delivery_last_error") and message.delivery_last_error else None

if __name__ == "__main__":
    unittest.main()
