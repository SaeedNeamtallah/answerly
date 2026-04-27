"""Regression tests for B2B Telegram SaaS invariants."""

import inspect
import unittest

from fastapi.params import Depends as DependsParam

from backend.database.models import BotIntegration, User
from backend.routes import admin_console, bot_integrations, conversations
from backend.security.auth import (
    ROLE_COMPANY_ADMIN,
    ROLE_PLATFORM_OWNER,
    get_product_role_for_user,
    require_company_dashboard_access,
    require_platform_owner_access,
)
from backend.services.customer_bot_query_service import CustomerBotQueryService
from backend.services.token_crypto_service import TokenCryptoService


class DummyQueryController:
    async def answer_query(self, *, db, owner_id, project_id, query, top_k, language):
        return {
            "answer": "Customer-safe answer",
            "context_used": 1,
            "sources": [
                {
                    "document_name": "internal-pricing-policy.pdf",
                    "chunk_index": 3,
                    "similarity": 0.91,
                    "asset_id": 10,
                }
            ],
        }


class B2BTelegramSaaSTests(unittest.IsolatedAsyncioTestCase):
    def test_token_crypto_encrypts_and_hashes_tokens(self):
        service = TokenCryptoService(TokenCryptoService.generate_key())
        token = "123456:telegram-secret-token"

        encrypted = service.encrypt_token(token)

        self.assertNotEqual(encrypted, token)
        self.assertEqual(service.decrypt_token(encrypted), token)
        self.assertEqual(service.hash_token(token), service.hash_token(token))
        self.assertNotEqual(service.hash_token(token), token)

    def test_product_role_defaults_to_company_admin(self):
        self.assertEqual(get_product_role_for_user(User(username="company", hashed_password="x")), ROLE_COMPANY_ADMIN)
        self.assertEqual(
            get_product_role_for_user(User(username="owner", hashed_password="x", role=ROLE_PLATFORM_OWNER)),
            ROLE_PLATFORM_OWNER,
        )

    async def test_customer_bot_answers_hide_sources_by_default(self):
        service = CustomerBotQueryService(query_controller=DummyQueryController())
        integration = BotIntegration(
            owner_id=7,
            project_id=11,
            show_sources_to_customer=False,
        )

        result = await service.answer(
            db=None,
            integration=integration,
            query="Question?",
            language="en",
        )

        self.assertEqual(result["customer_answer"], "Customer-safe answer")
        self.assertEqual(result["internal_sources"][0]["document_name"], "internal-pricing-policy.pdf")
        self.assertNotIn("internal-pricing-policy.pdf", result["customer_answer"])

    async def test_customer_bot_answers_show_sources_only_when_enabled(self):
        service = CustomerBotQueryService(query_controller=DummyQueryController())
        integration = BotIntegration(
            owner_id=7,
            project_id=11,
            show_sources_to_customer=True,
        )

        result = await service.answer(
            db=None,
            integration=integration,
            query="Question?",
            language="en",
        )

        self.assertIn("internal-pricing-policy.pdf", result["customer_answer"])

    def test_admin_console_requires_platform_owner_dependency(self):
        signature = inspect.signature(admin_console.admin_overview)
        dependency = signature.parameters["_"].default

        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, require_platform_owner_access)

    def test_company_product_routes_require_company_dashboard_dependency(self):
        for endpoint in (bot_integrations.list_bot_integrations, conversations.list_conversations):
            signature = inspect.signature(endpoint)
            dependency = signature.parameters["current_user"].default

            self.assertIsInstance(dependency, DependsParam)
            self.assertIs(dependency.dependency, require_company_dashboard_access)


if __name__ == "__main__":
    unittest.main()

