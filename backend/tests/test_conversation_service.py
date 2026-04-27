"""ConversationService behavior tests that do not require a database."""

import unittest

from backend.services.conversation_service import ConversationError, ConversationService


class ConversationServiceTests(unittest.TestCase):
    def test_clean_message_text_rejects_empty_text(self):
        with self.assertRaisesRegex(ConversationError, "Message text is required"):
            ConversationService._clean_message_text("   ")

    def test_clean_message_text_strips_html(self):
        self.assertEqual(ConversationService._clean_message_text("<b>Hello</b>"), "Hello")

    def test_raw_payload_expiry_is_future(self):
        expiry = ConversationService._raw_payload_expiry()
        self.assertGreater(expiry, ConversationService._now())


if __name__ == "__main__":
    unittest.main()

