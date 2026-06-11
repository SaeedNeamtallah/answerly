"""Regression tests for recently fixed security and safety behaviors."""

import io
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.params import Depends as DependsParam
from starlette.datastructures import UploadFile

from backend.config import settings
from backend.main import app
from backend.providers.vectordb.pgvector_provider import PGVectorProvider
from backend.routes import app_config, documents, stats
from backend.routes import security as security_routes
from backend.security.client_ip import get_optional_client_ip
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
        dependency = signature.parameters["current_user"].default
        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, get_current_db_user)

    def test_client_ip_ignores_forwarded_for_from_untrusted_client(self):
        request = SimpleNamespace(
            headers={"x-forwarded-for": "203.0.113.9"},
            client=SimpleNamespace(host="198.51.100.25"),
        )

        with patch.object(settings, "security_trusted_proxy_ips", "127.0.0.1,::1"):
            self.assertEqual(get_optional_client_ip(request), "198.51.100.25")

    def test_client_ip_honors_forwarded_for_from_trusted_proxy(self):
        request = SimpleNamespace(
            headers={"x-forwarded-for": "203.0.113.9, 10.0.0.1"},
            client=SimpleNamespace(host="127.0.0.1"),
        )

        with patch.object(settings, "security_trusted_proxy_ips", "127.0.0.1,::1"):
            self.assertEqual(get_optional_client_ip(request), "203.0.113.9")

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

    async def test_pgvector_add_vectors_raises_when_chunk_update_is_missing(self):
        class FakeUpdateResult:
            rowcount = 0

        class FakeSession:
            async def execute(self, *_args, **_kwargs):
                return FakeUpdateResult()

            async def flush(self):
                return None

        provider = PGVectorProvider()

        with (
            patch.object(PGVectorProvider, "_is_native_pgvector_column", return_value=True),
            patch.object(PGVectorProvider, "_ensure_ann_index", new=AsyncMock(return_value=None)),
        ):
            with self.assertRaisesRegex(RuntimeError, "Could not update embeddings"):
                await provider.add_vectors(
                    collection_name="project_1",
                    vectors=[[0.1, 0.2]],
                    ids=[123],
                    session=FakeSession(),
                )


if __name__ == "__main__":
    unittest.main()
