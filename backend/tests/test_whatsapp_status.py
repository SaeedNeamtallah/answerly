"""Regression tests for WhatsApp bridge status persistence."""

import unittest
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, patch

from fastapi import HTTPException

from backend.database.models import WhatsAppIntegration
from backend.routes import whatsapp_webhook
from backend.services.whatsapp_integration_service import (
    WhatsAppIntegrationError,
    WhatsAppIntegrationService,
)


class _FakeDb:
    def __init__(self) -> None:
        self.commits = 0
        self.refreshes = 0

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _value) -> None:
        self.refreshes += 1


class WhatsAppStatusTests(unittest.IsolatedAsyncioTestCase):
    async def test_connected_status_clears_stale_error(self):
        integration = WhatsAppIntegration(status="error", last_error="old failure")
        db = _FakeDb()

        updated = await WhatsAppIntegrationService().update_status(
            db,
            integration=integration,
            status="connected",
            last_error="ignored",
        )

        self.assertIs(updated, integration)
        self.assertEqual(integration.status, "connected")
        self.assertIsNone(integration.last_error)
        self.assertIsNotNone(integration.last_update_at)
        self.assertEqual(db.commits, 1)
        self.assertEqual(db.refreshes, 1)

    async def test_unknown_bridge_status_is_normalized(self):
        integration = WhatsAppIntegration(status="pending")
        db = _FakeDb()

        await WhatsAppIntegrationService().update_status(
            db,
            integration=integration,
            status="unexpected-value",
            last_error="unsupported state",
        )

        self.assertEqual(integration.status, "unknown")
        self.assertEqual(integration.last_error, "unsupported state")

    async def test_bridge_status_callback_persists_status(self):
        fake_service = SimpleNamespace(
            update_status_by_session_id=AsyncMock(
                return_value=SimpleNamespace(status="qr_ready", last_error=None)
            )
        )

        with patch.object(
            whatsapp_webhook,
            "WhatsAppIntegrationService",
            return_value=fake_service,
        ):
            response = await whatsapp_webhook.whatsapp_status_update(
                "session-123",
                whatsapp_webhook.WhatsAppStatusUpdate(status="qr_ready"),
                db=object(),
            )

        self.assertEqual(response, {"success": True, "status": "qr_ready", "last_error": None})
        fake_service.update_status_by_session_id.assert_awaited_once_with(
            ANY,
            session_id="session-123",
            status="qr_ready",
            last_error=None,
        )

    async def test_bridge_status_callback_returns_not_found(self):
        fake_service = SimpleNamespace(
            update_status_by_session_id=AsyncMock(
                side_effect=WhatsAppIntegrationError("WhatsApp integration not found")
            )
        )

        with patch.object(
            whatsapp_webhook,
            "WhatsAppIntegrationService",
            return_value=fake_service,
        ):
            with self.assertRaises(HTTPException) as raised:
                await whatsapp_webhook.whatsapp_status_update(
                    "missing-session",
                    whatsapp_webhook.WhatsAppStatusUpdate(status="connected"),
                    db=object(),
                )

        self.assertEqual(raised.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
