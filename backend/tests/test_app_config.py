"""Runtime provider config normalization tests."""

import asyncio
import unittest
from unittest.mock import patch

from backend.routes import app_config as app_config_routes
from backend.routes.app_config import ProviderUpdate


class AppConfigNormalizationTests(unittest.TestCase):
    def test_normalize_provider_runtime_config_migrates_invalid_values(self):
        runtime_config = {
            "llm_provider": "voyage",
            "embedding_provider": "bge-m3",
            "vector_db_provider": "legacy-vectordb",
        }

        with (
            patch("backend.routes.app_config.load_runtime_config", return_value=runtime_config),
            patch("backend.routes.app_config.update_runtime_config") as update_mock,
            patch("backend.routes.app_config.LLMProviderFactory.get_available_providers", return_value=["gemini", "openrouter-free"]),
            patch("backend.routes.app_config.LLMProviderFactory.get_available_embedding_providers", return_value=["gemini", "cohere"]),
            patch("backend.routes.app_config.VectorDBProviderFactory.get_available_providers", return_value=["pgvector", "qdrant"]),
        ):
            result = app_config_routes.normalize_provider_runtime_config()

        self.assertTrue(result["migrated"])
        self.assertEqual(result["llm_provider"], "gemini")
        self.assertEqual(result["embedding_provider"], "gemini")
        self.assertEqual(result["vector_db_provider"], "pgvector")
        update_mock.assert_called_once_with(
            {
                "llm_provider": "gemini",
                "embedding_provider": "gemini",
                "vector_db_provider": "pgvector",
            }
        )

    def test_normalize_provider_runtime_config_keeps_valid_values(self):
        runtime_config = {
            "llm_provider": "openrouter-free",
            "embedding_provider": "cohere",
            "vector_db_provider": "qdrant",
        }

        with (
            patch("backend.routes.app_config.load_runtime_config", return_value=runtime_config),
            patch("backend.routes.app_config.update_runtime_config") as update_mock,
            patch("backend.routes.app_config.LLMProviderFactory.get_available_providers", return_value=["gemini", "openrouter-free"]),
            patch("backend.routes.app_config.LLMProviderFactory.get_available_embedding_providers", return_value=["gemini", "cohere"]),
            patch("backend.routes.app_config.VectorDBProviderFactory.get_available_providers", return_value=["pgvector", "qdrant"]),
        ):
            result = app_config_routes.normalize_provider_runtime_config()

        self.assertFalse(result["migrated"])
        self.assertEqual(result["updated_fields"], [])
        update_mock.assert_not_called()


class AppConfigRouteTests(unittest.TestCase):
    @patch("backend.routes.app_config.get_runtime_value")
    @patch("backend.routes.app_config.normalize_provider_runtime_config")
    @patch("backend.routes.app_config.LLMProviderFactory")
    @patch("backend.routes.app_config.VectorDBProviderFactory")
    def test_get_providers_masks_keys(self, mock_vector, mock_llm, mock_normalize, mock_get_runtime_val):
        mock_normalize.return_value = {
            "llm_provider": "gemini",
            "embedding_provider": "cohere",
            "vector_db_provider": "pgvector",
            "migrated": False,
            "updated_fields": []
        }
        mock_llm.get_available_providers.return_value = ["gemini"]
        mock_llm.get_available_embedding_providers.return_value = ["cohere"]
        mock_vector.get_available_providers.return_value = ["pgvector"]

        # Mock get_runtime_value to return some keys and config values
        def side_effect(key, default=None):
            if key == "gemini_api_key":
                return "secret-gemini-key"
            if key == "cohere_api_key":
                return ""  # Empty key
            if "api_key" in key:
                return ""
            return default

        mock_get_runtime_val.side_effect = side_effect

        result = asyncio.run(app_config_routes.get_providers())
        self.assertEqual(result["gemini_api_key"], "••••••••")
        self.assertEqual(result["cohere_api_key"], "")
        self.assertEqual(result["openrouter_api_key"], "")

    @patch("backend.routes.app_config.update_runtime_config")
    @patch("backend.routes.app_config.LLMProviderFactory")
    @patch("backend.routes.app_config.VectorDBProviderFactory")
    def test_update_providers_handles_masked_and_new_keys(self, mock_vector, mock_llm, mock_update_config):
        mock_llm.get_available_providers.return_value = ["gemini"]
        mock_llm.get_available_embedding_providers.return_value = ["cohere"]
        mock_vector.get_available_providers.return_value = ["pgvector"]

        # Simulate update_runtime_config returning the merged config
        mock_update_config.return_value = {
            "llm_provider": "gemini",
            "embedding_provider": "cohere",
            "gemini_api_key": "new-gemini-key",
            "cohere_api_key": "old-cohere-key"
        }

        payload = ProviderUpdate(
            llm_provider="gemini",
            embedding_provider="cohere",
            gemini_api_key="new-gemini-key",  # updated key
            cohere_api_key="••••••••"  # masked (should be ignored)
        )

        result = asyncio.run(app_config_routes.update_providers(payload))

        # Assert update_runtime_config was called only with updated non-masked values
        mock_update_config.assert_called_once()
        called_args = mock_update_config.call_args[0][0]
        self.assertEqual(called_args["gemini_api_key"], "new-gemini-key")
        self.assertNotIn("cohere_api_key", called_args)

        self.assertEqual(result["gemini_api_key"], "••••••••")
        self.assertEqual(result["cohere_api_key"], "••••••••")


if __name__ == "__main__":
    unittest.main()
