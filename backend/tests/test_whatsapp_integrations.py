"""Regression tests for WhatsApp integration tenant scoping and connection."""

import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import HTTPException

from backend.database.models import WhatsAppIntegration, Project, User
from backend.services.whatsapp_integration_service import (
    WhatsAppIntegrationService,
    WhatsAppIntegrationError,
)
from backend.routes import whatsapp_integrations

class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value
        
    def scalars(self):
        class _FakeScalars:
            def all(self):
                return [self._value] if self._value else []
        return _FakeScalars()

class _FakeDb:
    def __init__(self, execute_result=None):
        self.execute_result = execute_result
        self.adds = []
        self.commits = 0
        self.refreshes = 0
        self.deletes = 0

    async def execute(self, stmt):
        return _FakeScalarResult(self.execute_result)

    def add(self, model):
        self.adds.append(model)

    async def commit(self):
        self.commits += 1

    async def refresh(self, model):
        self.refreshes += 1

    async def delete(self, model):
        self.deletes += 1


class WhatsAppIntegrationsTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_integration_tenant_scoping(self):
        integration = WhatsAppIntegration(id=1, owner_id=10, project_id=100)
        db = _FakeDb(execute_result=integration)
        
        result = await WhatsAppIntegrationService().get_integration(
            db=db,
            integration_id=1,
            owner_id=10,
        )
        self.assertEqual(result.id, 1)

    async def test_get_integration_tenant_scoping_fails_for_wrong_owner(self):
        db = _FakeDb(execute_result=None)
        service = WhatsAppIntegrationService()

        result = await service.get_integration(db, owner_id=99, integration_id=1)
        self.assertIsNone(result)

    async def test_delete_integration_tenant_scoping(self):
        integration = WhatsAppIntegration(id=1, owner_id=10, project_id=100)
        db = _FakeDb(execute_result=integration)
        
        # Test delete
        await WhatsAppIntegrationService().delete_integration(
            db=db,
            integration_id=1,
            owner_id=10,
        )
        self.assertEqual(db.deletes, 1)

    async def test_connect_whatsapp_session_success(self):
        integration = WhatsAppIntegration(id=1, owner_id=10, session_id="test-sess")
        db = _FakeDb(execute_result=integration)
        current_user = User(id=10)

        with patch("backend.routes.whatsapp_integrations.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with patch("backend.routes.whatsapp_integrations.WhatsAppIntegrationService") as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance
                mock_instance.get_integration.return_value = integration

                result = await whatsapp_integrations.connect_whatsapp_session(
                    integration_id=1,
                    db=db,
                    current_user=current_user,
                    service=mock_instance,
                )
                self.assertEqual(result, {"success": True})

    async def test_connect_route_handles_bridge_failure(self):
        integration = WhatsAppIntegration(id=1, owner_id=10, session_id="test-sess")
        db = _FakeDb(execute_result=integration)
        current_user = User(id=10)

        with patch("backend.routes.whatsapp_integrations.WhatsAppIntegrationService") as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_integration.return_value = integration
            mock_instance.connect_bridge.side_effect = WhatsAppIntegrationError("Bridge offline")

            with self.assertRaises(HTTPException) as exc:
                await whatsapp_integrations.connect_whatsapp_session(
                    integration_id=1,
                    db=db,
                    current_user=current_user,
                    service=mock_instance,
                )
            self.assertEqual(exc.exception.status_code, 500)
            self.assertEqual(exc.exception.detail, "Failed to connect session on bridge")

if __name__ == "__main__":
    unittest.main()
