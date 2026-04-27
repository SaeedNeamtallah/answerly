"""CustomerBotQueryService tests."""

import unittest

from backend.database.models import BotIntegration
from backend.services.customer_bot_query_service import CustomerBotQueryService


class DummyQueryController:
    async def answer_query(self, *, db, owner_id, project_id, query, top_k, language):
        return {
            "answer": "Customer-safe answer",
            "context_used": 1,
            "sources": [
                {
                    "document_name": "internal-policy.pdf",
                    "chunk_index": 1,
                    "similarity": 0.9,
                    "asset_id": 2,
                }
            ],
        }


class CustomerBotQueryServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_hides_sources_by_default(self):
        service = CustomerBotQueryService(query_controller=DummyQueryController())
        integration = BotIntegration(owner_id=1, project_id=2, show_sources_to_customer=False)

        result = await service.answer(db=None, integration=integration, query="Question?", language="en")

        self.assertEqual(result["customer_answer"], "Customer-safe answer")
        self.assertNotIn("internal-policy.pdf", result["customer_answer"])
        self.assertEqual(result["internal_sources"][0]["document_name"], "internal-policy.pdf")


if __name__ == "__main__":
    unittest.main()

