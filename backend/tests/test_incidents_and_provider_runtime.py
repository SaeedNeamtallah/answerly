"""Regression tests for incident schema and provider runtime behavior."""

import ast
import inspect
import unittest
from pathlib import Path

from backend.providers.llm.exceptions import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from backend.providers.llm.factory import LLMProviderFactory
from backend.routes import incidents, query
from backend.security.auth import require_incident_access


REPO_ROOT = Path(__file__).resolve().parents[2]


class IncidentAndProviderRuntimeTests(unittest.TestCase):
    def test_incident_migration_creates_required_tables(self):
        migration = REPO_ROOT / "backend/alembic/versions/20260428_01_add_incident_response_tables.py"
        text = migration.read_text(encoding="utf-8")
        for table_name in ("incidents", "incident_logs", "audit_logs"):
            self.assertIn(f'"{table_name}"', text)
            self.assertIn(f'op.create_table(\n            "{table_name}"', text)

    def test_incident_routes_require_incident_access(self):
        dependency = incidents.router.dependencies[0].dependency
        self.assertIs(dependency, require_incident_access)

    def test_query_controller_dependency_is_not_lru_cached(self):
        self.assertFalse(hasattr(query.get_query_controller, "cache_info"))

    def test_llm_factory_does_not_cache_provider_instances(self):
        source = inspect.getsource(LLMProviderFactory.create_embedding_provider)
        self.assertNotIn("_embedding_instances", source)
        source = inspect.getsource(LLMProviderFactory.create_provider)
        self.assertNotIn("_llm_instances", source)

    def test_provider_specific_exceptions_exist(self):
        for exc_type in (
            ProviderUnavailableError,
            ProviderAuthError,
            ProviderRateLimitError,
            ProviderTimeoutError,
        ):
            self.assertTrue(issubclass(exc_type, RuntimeError))

    def test_file_processing_does_not_cleanup_before_embedding(self):
        task_path = REPO_ROOT / "backend/tasks/file_processing.py"
        tree = ast.parse(task_path.read_text(encoding="utf-8"))
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "id", None) or getattr(func, "attr", None)
                if name in {"generate_embeddings", "_delete_chunk_ids", "_cleanup_stale_asset_vectors"}:
                    calls.append((name, node.lineno))

        first_embedding = min(line for name, line in calls if name == "generate_embeddings")
        cleanup_lines = [line for name, line in calls if name == "_cleanup_stale_asset_vectors"]
        replacement_delete_lines = [line for name, line in calls if name == "_delete_chunk_ids"]

        self.assertFalse(cleanup_lines, "_cleanup_stale_asset_vectors must not be called during processing")
        self.assertTrue(
            any(line > first_embedding for line in replacement_delete_lines),
            "old chunks should be deleted only after new embedding/vector work starts",
        )


if __name__ == "__main__":
    unittest.main()
