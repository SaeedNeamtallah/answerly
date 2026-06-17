"""Focused regression tests for the production security fixes round."""

import inspect
import unittest

from fastapi.params import Depends as DependsParam

from backend.config import Settings, _validate_production_secrets
from backend.main import app
from backend.routes import app_config, health
from backend.security.auth import get_current_db_user
from backend.tasks.telegram_outbox import deliver_pending_messages
from backend.celery_app import celery_app


class ProductionSecurityFixesTests(unittest.TestCase):
    def test_production_secret_validation_rejects_weak_jwt_secret(self):
        settings_obj = Settings(
            ENVIRONMENT="production",
            AUTH_JWT_SECRET_KEY="change-me-in-env",
            AUTH_ADMIN_PASSWORD="admin123",
            BOT_TOKEN_ENCRYPTION_KEY="some-key",
        )
        with self.assertRaises(SystemExit):
            _validate_production_secrets(settings_obj)

    def test_production_secret_validation_rejects_new_weak_jwt_secret(self):
        settings_obj = Settings(
            ENVIRONMENT="production",
            AUTH_JWT_SECRET_KEY="change-me-to-a-strong-random-secret-at-least-32-chars",
            AUTH_ADMIN_PASSWORD="change-me-to-a-strong-password",
            BOT_TOKEN_ENCRYPTION_KEY="some-key",
        )
        with self.assertRaises(SystemExit):
            _validate_production_secrets(settings_obj)

    def test_production_secret_validation_allows_weak_jwt_secret_in_development(self):
        settings_obj = Settings(
            ENVIRONMENT="development",
            AUTH_JWT_SECRET_KEY="change-me-in-env",
            AUTH_ADMIN_PASSWORD="admin123",
            BOT_TOKEN_ENCRYPTION_KEY="",
        )
        _validate_production_secrets(settings_obj)

    def test_production_secret_validation_allows_new_weak_jwt_secret_in_development(self):
        settings_obj = Settings(
            ENVIRONMENT="development",
            AUTH_JWT_SECRET_KEY="change-me-to-a-strong-random-secret-at-least-32-chars",
            AUTH_ADMIN_PASSWORD="change-me-to-a-strong-password",
            BOT_TOKEN_ENCRYPTION_KEY="",
        )
        _validate_production_secrets(settings_obj)

    def test_get_providers_requires_authenticated_user_dependency(self):
        signature = inspect.signature(app_config.get_providers)
        dependency = signature.parameters["_current_user"].default
        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, get_current_db_user)

    def test_health_live_endpoint_exists(self):
        routes = {getattr(route, "path", None) for route in app.routes}
        self.assertIn("/health/live", routes)

    def test_health_live_is_async(self):
        self.assertTrue(inspect.iscoroutinefunction(health.health_live))

    def test_telegram_outbox_task_is_registered_in_beat_schedule(self):
        self.assertIn("deliver-pending-telegram-messages", celery_app.conf.beat_schedule)

    def test_telegram_outbox_task_name_is_stable(self):
        self.assertEqual(
            deliver_pending_messages.name,
            "backend.tasks.telegram_outbox.deliver_pending_messages",
        )


if __name__ == "__main__":
    unittest.main()
