"""Bot integration route serialization and ownership guard tests."""

import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from backend.config import settings
from backend.database.models import BotIntegration, Project
from backend.routes.bot_integrations import _serialize_integration
from backend.services.bot_integration_service import BotIntegrationError, BotIntegrationService


class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeDB:
    def __init__(self, chunk_count=1):
        self.chunk_count = chunk_count

    async def execute(self, stmt):
        sql = str(stmt).lower()
        if "count(chunks.id)" in sql:
            return _FakeScalarResult(self.chunk_count)
        return _FakeScalarResult(1)


class _FakeCryptoService:
    def decrypt_token(self, _encrypted):
        return "123:secret-token"


class _FakeTelegramAPI:
    def __init__(self, webhook_url="https://example.test/webhook"):
        self.webhook_url = webhook_url
        self.set_webhook_calls = []

    async def validate_token(self, _token):
        return {"telegram_bot_id": "123", "telegram_username": "support_bot"}

    async def set_webhook(self, token, webhook_url):
        self.set_webhook_calls.append((token, webhook_url))

    async def get_webhook_info(self, _token):
        return {
            "url": self.webhook_url,
            "pending_update_count": 0,
            "last_error_message": None,
        }


class _FakeMutationDB:
    def add(self, _obj):
        return None

    async def commit(self):
        return None

    async def refresh(self, _obj):
        return None


class BotIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def test_serialized_integration_does_not_expose_tokens_or_hashes(self):
        integration = BotIntegration(
            id=1,
            owner_id=2,
            project_id=3,
            name="Support",
            telegram_bot_id="123",
            telegram_username="support_bot",
            token_encrypted="encrypted",
            token_hash="hash",
            webhook_secret="secret",
            webhook_url="https://example.test/webhook",
            status="active",
            show_sources_to_customer=False,
            human_handoff_enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        data = _serialize_integration(integration).model_dump()

        self.assertNotIn("token_encrypted", data)
        self.assertNotIn("token_hash", data)
        self.assertNotIn("webhook_secret", data)
        self.assertNotIn("webhook_url", data)
        self.assertTrue(data["webhook_configured"])

    async def test_owned_project_guard_rejects_missing_project(self):
        class FakeResult:
            def scalar_one_or_none(self):
                return None

        class FakeDB:
            async def execute(self, _stmt):
                return FakeResult()

        with self.assertRaisesRegex(BotIntegrationError, "Project not found"):
            await BotIntegrationService._get_owned_project(FakeDB(), owner_id=1, project_id=99)

    async def test_readiness_reports_ready_when_stack_checks_pass(self):
        integration = BotIntegration(
            id=1,
            owner_id=2,
            project_id=3,
            name="Support",
            telegram_bot_id="123",
            telegram_username="support_bot",
            token_encrypted="encrypted",
            token_hash="hash",
            webhook_secret="secret",
            webhook_url="https://example.test/webhook",
            status="active",
            show_sources_to_customer=False,
            human_handoff_enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        service = BotIntegrationService(
            crypto_service=_FakeCryptoService(),
            telegram_api=_FakeTelegramAPI(),
        )
        service.get_integration = AsyncMock(return_value=integration)
        service._get_owned_project = AsyncMock(return_value=Project(id=3, owner_id=2, name="Demo"))

        runtime_values = {
            "llm_provider": "gemini",
            "embedding_provider": "gemini",
            "vector_db_provider": "pgvector",
        }

        with (
            patch("backend.services.bot_integration_service.get_runtime_value", side_effect=lambda key, default=None: runtime_values.get(key, default)),
            patch.object(BotIntegrationService, "_has_llm_credentials", return_value=True),
            patch.object(BotIntegrationService, "_has_embedding_credentials", return_value=True),
            patch("backend.services.bot_integration_service.LLMProviderFactory.get_available_providers", return_value=["gemini"]),
            patch("backend.services.bot_integration_service.LLMProviderFactory.get_available_embedding_providers", return_value=["gemini"]),
            patch("backend.services.bot_integration_service.VectorDBProviderFactory.get_available_providers", return_value=["pgvector"]),
            patch("backend.services.bot_integration_service.LLMProviderFactory.create_provider") as llm_create,
            patch("backend.services.bot_integration_service.LLMProviderFactory.create_embedding_provider") as embedding_create,
            patch("backend.services.bot_integration_service.VectorDBProviderFactory.create_provider", return_value=object()),
        ):
            llm_create.return_value.get_model_name.return_value = "gemini-2.5-flash"
            embedding_create.return_value.get_embedding_dimension.return_value = 3072

            checks = await service.readiness(_FakeDB(chunk_count=5), owner_id=2, integration_id=1)

        self.assertTrue(checks["ready"])
        self.assertTrue(checks["token_valid"])
        self.assertTrue(checks["telegram_webhook_matches_expected"])
        self.assertTrue(checks["llm_provider_ready"])
        self.assertTrue(checks["embedding_provider_ready"])
        self.assertTrue(checks["vector_db_provider_ready"])

    async def test_update_integration_can_clear_fallback_message(self):
        integration = BotIntegration(
            id=3,
            owner_id=2,
            project_id=3,
            name="Support",
            telegram_bot_id="123",
            telegram_username="support_bot",
            token_encrypted="encrypted",
            token_hash="hash",
            webhook_secret="secret",
            webhook_url="https://example.test/webhook",
            status="active",
            show_sources_to_customer=False,
            human_handoff_enabled=True,
            fallback_message="Old fallback",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        service = BotIntegrationService()
        service.get_integration = AsyncMock(return_value=integration)

        updated = await service.update_integration(
            _FakeMutationDB(),
            owner_id=2,
            integration_id=3,
            fallback_message=None,
            fallback_message_provided=True,
        )

        self.assertIsNone(updated.fallback_message)

    async def test_create_integration_requires_public_webhook_base_url(self):
        service = BotIntegrationService()

        with (
            patch.object(settings, "public_webhook_base_url", ""),
            self.assertRaisesRegex(BotIntegrationError, "PUBLIC_WEBHOOK_BASE_URL"),
        ):
            await service.create_integration(
                _FakeMutationDB(),
                owner_id=2,
                project_id=3,
                name="Support",
                bot_token="123:secret-token",
            )

    async def test_rotate_token_requires_public_webhook_base_url(self):
        service = BotIntegrationService()

        with (
            patch.object(settings, "public_webhook_base_url", ""),
            self.assertRaisesRegex(BotIntegrationError, "PUBLIC_WEBHOOK_BASE_URL"),
        ):
            await service.rotate_token(
                _FakeMutationDB(),
                owner_id=2,
                integration_id=3,
                bot_token="123:secret-token",
            )

    async def test_update_integration_registers_webhook_for_existing_bot(self):
        integration = BotIntegration(
            id=4,
            owner_id=2,
            project_id=3,
            name="Support",
            telegram_bot_id="123",
            telegram_username="support_bot",
            token_encrypted="encrypted",
            token_hash="hash",
            webhook_secret="secret",
            webhook_url=None,
            status="error",
            last_error="missing webhook",
            show_sources_to_customer=False,
            human_handoff_enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        telegram_api = _FakeTelegramAPI()
        service = BotIntegrationService(
            crypto_service=_FakeCryptoService(),
            telegram_api=telegram_api,
        )
        service.get_integration = AsyncMock(return_value=integration)

        with patch.object(settings, "public_webhook_base_url", "https://hooks.example.test"):
            updated = await service.update_integration(_FakeMutationDB(), owner_id=2, integration_id=4)

        self.assertEqual(updated.webhook_url, "https://hooks.example.test/telegram/webhook/4/secret")
        self.assertEqual(updated.status, "active")
        self.assertIsNone(updated.last_error)
        self.assertEqual(telegram_api.set_webhook_calls, [("123:secret-token", updated.webhook_url)])

    async def test_readiness_detects_webhook_mismatch(self):
        integration = BotIntegration(
            id=2,
            owner_id=2,
            project_id=3,
            name="Support",
            telegram_bot_id="123",
            telegram_username="support_bot",
            token_encrypted="encrypted",
            token_hash="hash",
            webhook_secret="secret",
            webhook_url="https://example.test/webhook",
            status="active",
            show_sources_to_customer=False,
            human_handoff_enabled=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        service = BotIntegrationService(
            crypto_service=_FakeCryptoService(),
            telegram_api=_FakeTelegramAPI(webhook_url="https://example.test/other"),
        )
        service.get_integration = AsyncMock(return_value=integration)
        service._get_owned_project = AsyncMock(return_value=Project(id=3, owner_id=2, name="Demo"))

        with (
            patch.object(BotIntegrationService, "_has_llm_credentials", return_value=False),
            patch.object(BotIntegrationService, "_has_embedding_credentials", return_value=False),
            patch("backend.services.bot_integration_service.get_runtime_value", side_effect=lambda key, default=None: default),
            patch("backend.services.bot_integration_service.LLMProviderFactory.get_available_providers", return_value=["gemini"]),
            patch("backend.services.bot_integration_service.LLMProviderFactory.get_available_embedding_providers", return_value=["gemini"]),
            patch("backend.services.bot_integration_service.VectorDBProviderFactory.get_available_providers", return_value=["pgvector"]),
            patch("backend.services.bot_integration_service.VectorDBProviderFactory.create_provider", return_value=object()),
        ):
            checks = await service.readiness(_FakeDB(chunk_count=5), owner_id=2, integration_id=2)

        self.assertFalse(checks["ready"])
        self.assertFalse(checks["telegram_webhook_matches_expected"])


if __name__ == "__main__":
    unittest.main()
