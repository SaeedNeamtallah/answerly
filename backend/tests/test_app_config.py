"""Runtime provider config normalization tests."""

import unittest
from unittest.mock import patch

from backend.routes import app_config as app_config_routes


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


if __name__ == "__main__":
    unittest.main()
