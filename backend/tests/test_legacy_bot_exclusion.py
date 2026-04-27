"""Static checks that production Telegram services do not use legacy bot globals."""

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class LegacyBotExclusionTests(unittest.TestCase):
    def test_product_services_do_not_reference_legacy_project_selection(self):
        product_files = [
            REPO_ROOT / "backend/services/bot_integration_service.py",
            REPO_ROOT / "backend/services/customer_bot_query_service.py",
            REPO_ROOT / "backend/services/telegram_webhook_service.py",
            REPO_ROOT / "backend/routes/bot_integrations.py",
            REPO_ROOT / "backend/routes/telegram_webhook.py",
        ]
        forbidden = ("active_project_id", "bot_config", "BOT_API_USERNAME", "AUTH_ADMIN_USERNAME")

        for path in product_files:
            text = path.read_text(encoding="utf-8")
            for term in forbidden:
                self.assertNotIn(term, text, f"{term} found in {path}")


if __name__ == "__main__":
    unittest.main()

