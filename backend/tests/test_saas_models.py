"""Schema metadata tests for the B2B Telegram SaaS models."""

import unittest

from backend.database.models import (
    Base,
    BotIntegration,
    Conversation,
    ConversationMessage,
    TelegramCustomer,
    User,
    UserRole,
)


class SaaSModelMetadataTests(unittest.TestCase):
    def test_user_has_product_role_and_company_fields(self):
        columns = User.__table__.columns

        self.assertIn("role", columns)
        self.assertIn("company_name", columns)
        self.assertIn("company_website", columns)
        self.assertEqual(str(columns["role"].default.arg), UserRole.COMPANY_ADMIN.value)

    def test_saas_tables_are_registered(self):
        for table_name in (
            "bot_integrations",
            "telegram_customers",
            "conversations",
            "conversation_messages",
        ):
            self.assertIn(table_name, Base.metadata.tables)

    def test_bot_integration_secret_columns_are_not_plain_token_columns(self):
        columns = BotIntegration.__table__.columns

        self.assertIn("token_encrypted", columns)
        self.assertIn("token_hash", columns)
        self.assertNotIn("bot_token", columns)
        self.assertFalse(columns["token_encrypted"].nullable)

    def test_customer_and_message_idempotency_indexes_exist(self):
        customer_indexes = {index.name for index in TelegramCustomer.__table__.indexes}
        message_indexes = {index.name for index in ConversationMessage.__table__.indexes}

        self.assertIn("ix_telegram_customers_bot_chat", customer_indexes)
        self.assertIn("ix_conversation_messages_update_unique", message_indexes)
        self.assertIn("ix_conversation_messages_message_unique", message_indexes)
        self.assertIn("ix_conversation_messages_delivery_status", message_indexes)

    def test_conversation_message_has_outbox_delivery_columns(self):
        columns = ConversationMessage.__table__.columns

        self.assertIn("delivery_status", columns)
        self.assertIn("delivery_attempts", columns)

    def test_conversation_status_supports_required_values_by_convention(self):
        columns = Conversation.__table__.columns

        self.assertIn("status", columns)
        self.assertEqual(str(columns["status"].default.arg), "open")
        self.assertIn("needs_human", columns)


if __name__ == "__main__":
    unittest.main()

