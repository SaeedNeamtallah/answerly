"""Regression tests for query controller failure semantics."""

import unittest
from unittest.mock import AsyncMock

from backend.controllers.query_controller import QueryController, QueryInfrastructureError


class QueryControllerRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_infrastructure_errors_are_raised(self):
        controller = object.__new__(QueryController)
        controller.query_service = AsyncMock()
        controller.answer_service = AsyncMock()
        controller.query_service.search_similar_chunks.side_effect = RuntimeError("vector db unavailable")

        with self.assertRaises(QueryInfrastructureError):
            await controller.answer_query(
                db=None,
                owner_id=1,
                project_id=10,
                query="What happened?",
                language="en",
            )


if __name__ == "__main__":
    unittest.main()
