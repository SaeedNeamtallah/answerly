"""Conversation route dependency tests."""

import inspect
import unittest

from fastapi.params import Depends as DependsParam

from backend.routes import conversations
from backend.security.auth import require_company_dashboard_access


class ConversationRouteTests(unittest.TestCase):
    def test_conversation_routes_are_company_scoped(self):
        for endpoint in (
            conversations.list_conversations,
            conversations.get_conversation,
            conversations.list_conversation_messages,
            conversations.manual_reply,
            conversations.escalate_conversation,
            conversations.resolve_conversation,
            conversations.block_customer,
        ):
            signature = inspect.signature(endpoint)
            dependency = signature.parameters["current_user"].default
            self.assertIsInstance(dependency, DependsParam)
            self.assertIs(dependency.dependency, require_company_dashboard_access)


if __name__ == "__main__":
    unittest.main()

