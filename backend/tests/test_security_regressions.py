"""Regression tests for recently fixed security and safety behaviors."""

import io
import inspect
import unittest

from fastapi.params import Depends as DependsParam
from starlette.datastructures import UploadFile

from backend.config import settings
from backend.main import app
from backend.providers.vectordb.pgvector_provider import PGVectorProvider
from backend.routes import app_config, documents, stats
from backend.routes import security as security_routes
from backend.security.auth import get_current_db_user


class SecurityRegressionTests(unittest.IsolatedAsyncioTestCase):
    def test_cors_uses_configured_origins(self):
        cors = next((m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"), None)
        self.assertIsNotNone(cors, "CORS middleware must be registered")
        self.assertEqual(cors.kwargs.get("allow_origins"), settings.cors_origins)

    def test_provider_update_requires_authenticated_user_dependency(self):
        signature = inspect.signature(app_config.update_providers)
        dependency = signature.parameters["_current_user"].default
        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, get_current_db_user)

    def test_provider_get_requires_authenticated_user_dependency(self):
        signature = inspect.signature(app_config.get_providers)
        dependency = signature.parameters["_current_user"].default
        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, get_current_db_user)

    def test_stats_requires_authenticated_user_dependency(self):
        signature = inspect.signature(stats.get_global_stats)
        dependency = signature.parameters["_current_user"].default
        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, get_current_db_user)

    def test_security_simulation_is_non_destructive_by_default(self):
        signature = inspect.signature(security_routes.simulate_security_attack)
        default_param = signature.parameters["escalate_to_block"].default
        self.assertEqual(getattr(default_param, "default", None), False)

    async def test_upload_read_is_bounded_by_size_limit(self):
        upload = UploadFile(filename="oversized.txt", file=io.BytesIO(b"a" * 64))
        content, size = await documents._read_upload_with_size_limit(upload, max_size_bytes=10)
        self.assertEqual(size, 11)
        self.assertEqual(len(content), 11)

    async def test_pgvector_delete_rejects_empty_filter(self):
        provider = PGVectorProvider()
        with self.assertRaisesRegex(ValueError, "filter_dict is required"):
            await provider.delete_vectors(collection_name="project_1", filter_dict={})

    async def test_pgvector_delete_rejects_unknown_filter_keys(self):
        provider = PGVectorProvider()
        with self.assertRaisesRegex(ValueError, "Unsupported filter keys"):
            await provider.delete_vectors(collection_name="project_1", filter_dict={"foo": "bar"})

    async def test_pgvector_delete_rejects_null_only_filters(self):
        provider = PGVectorProvider()
        with self.assertRaisesRegex(ValueError, "At least one non-null filter key"):
            await provider.delete_vectors(
                collection_name="project_1",
                filter_dict={"asset_id": None, "project_id": None, "owner_id": None},
            )


if __name__ == "__main__":
    unittest.main()
