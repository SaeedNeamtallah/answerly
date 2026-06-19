"""Regression tests for recently fixed security and safety behaviors."""

import io
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.params import Depends as DependsParam
from starlette.datastructures import UploadFile

from backend.config import settings
from backend.database.models import AuditLog, RoleAssignmentHistory, SecurityEventRecord, User, UserRole
from backend.main import app
from backend.providers.vectordb.pgvector_provider import PGVectorProvider
from backend.routes import admin_roles, app_config, auth_mfa, bot_config, documents, stats
from backend.routes import security as security_routes
from backend.security.client_ip import get_optional_client_ip
from backend.security.auth import AuthUser, get_current_db_user, require_platform_owner_access
from backend.security.sanitization import sanitize_text
from backend.security.security_event import SecurityEventType
from backend.services.mfa_service import mfa_service


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

    def test_bot_config_read_requires_authenticated_user_dependency(self):
        signature = inspect.signature(bot_config.get_bot_config)
        dependency = signature.parameters["current_user"].default
        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, get_current_db_user)

    def test_bot_config_write_requires_authenticated_user_dependency(self):
        signature = inspect.signature(bot_config.update_bot_config)
        dependency = signature.parameters["current_user"].default
        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, get_current_db_user)

    def test_bot_profile_write_requires_authenticated_user_dependency(self):
        signature = inspect.signature(bot_config.update_bot_profile)
        dependency = signature.parameters["current_user"].default
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

    def test_security_simulation_destructive_mode_requires_explicit_target(self):
        source = inspect.getsource(security_routes.simulate_security_attack)
        self.assertIn("Destructive simulation requires an explicit target_user_id", source)

    def test_security_event_model_has_retention_indexes_and_delivery_fields(self):
        columns = SecurityEventRecord.__table__.columns
        indexes = {index.name for index in SecurityEventRecord.__table__.indexes}

        self.assertIn("is_simulation", columns)
        self.assertIn("delivery_status", columns)
        self.assertIn("ix_security_events_severity_created", indexes)
        self.assertIn("ix_security_events_user_created", indexes)
        self.assertIn("ix_security_events_simulation_created", indexes)
        self.assertIn("ix_security_events_delivery_created", indexes)
        self.assertGreaterEqual(settings.security_event_retention_days, 180)

    async def test_bot_config_read_returns_public_safe_fields_only(self):
        user = User(id=7, username="company", hashed_password="hash")
        request = SimpleNamespace(
            url=SimpleNamespace(path="/bot/config"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )

        with patch.object(bot_config, "_load_config", return_value={"active_project_id": None, "token": "secret"}):
            response = await bot_config.get_bot_config(request, current_user=user, db=object())

        self.assertEqual(set(response), {"active_project_id", "legacy", "warning"})
        self.assertIsNone(response["active_project_id"])
        self.assertNotIn("token", response)

    async def test_privileged_platform_owner_without_mfa_is_denied(self):
        request = SimpleNamespace(
            state=SimpleNamespace(auth_user=AuthUser(username="owner", roles=["user"], mfa_verified=False)),
            url=SimpleNamespace(path="/admin/roles/users"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        user = User(id=1, username="owner", hashed_password="hash", role=UserRole.PLATFORM_OWNER.value)

        with self.assertRaisesRegex(Exception, "MFA setup required"):
            await require_platform_owner_access(request=request, current_user=user)

    async def test_privileged_platform_owner_requires_mfa_verified_token(self):
        request = SimpleNamespace(
            state=SimpleNamespace(auth_user=AuthUser(username="owner", roles=["user"], mfa_verified=False)),
            url=SimpleNamespace(path="/admin/roles/users"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        user = User(
            id=1,
            username="owner",
            hashed_password="hash",
            role=UserRole.PLATFORM_OWNER.value,
            mfa_enabled=True,
        )

        with self.assertRaisesRegex(Exception, "MFA verification required"):
            await require_platform_owner_access(request=request, current_user=user)

    async def test_privileged_platform_owner_with_verified_mfa_is_allowed(self):
        request = SimpleNamespace(
            state=SimpleNamespace(auth_user=AuthUser(username="owner", roles=["user"], mfa_verified=True)),
            url=SimpleNamespace(path="/admin/roles/users"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        user = User(
            id=1,
            username="owner",
            hashed_password="hash",
            role=UserRole.PLATFORM_OWNER.value,
            mfa_enabled=True,
        )

        self.assertIs(await require_platform_owner_access(request=request, current_user=user), user)

    def test_recovery_codes_are_hashed_and_one_time_use(self):
        code = "abc12345-def67890"
        stored = mfa_service.hash_recovery_codes([code])

        self.assertNotIn(code, stored)
        self.assertTrue(stored[0].startswith("sha256$"))

        consumed, remaining = mfa_service.consume_recovery_code(stored, code)
        self.assertTrue(consumed)
        self.assertEqual(remaining, [])

        consumed_again, _remaining_again = mfa_service.consume_recovery_code(remaining, code)
        self.assertFalse(consumed_again)

    async def test_mfa_verify_persists_hashed_recovery_codes(self):
        class FakeDb:
            async def commit(self):
                return None

        user = User(id=10, username="mfa-user", hashed_password="hash", mfa_secret="secret")

        with (
            patch.object(auth_mfa.mfa_service, "verify_totp", return_value=True),
            patch.object(auth_mfa.mfa_service, "generate_recovery_codes", return_value=["code-one", "code-two"]),
        ):
            response = await auth_mfa.verify_mfa(
                auth_mfa.MFAVerifyRequest(token="123456"),
                current_user=user,
                db=FakeDb(),
            )

        self.assertEqual(response.recovery_codes, ["code-one", "code-two"])
        self.assertNotEqual(user.mfa_recovery_codes, response.recovery_codes)
        self.assertTrue(all(str(code).startswith("sha256$") for code in user.mfa_recovery_codes))

    def test_suspicious_input_logs_redacted_event(self):
        with patch("backend.security.event_service.log_event") as log_event:
            self.assertEqual(sanitize_text("<script>alert(1)</script>", strip_html=True), "")

        payload = log_event.call_args.args[0]
        self.assertEqual(payload["event_type"], SecurityEventType.SUSPICIOUS_INPUT)
        self.assertIn("evidence_sha256", payload["metadata"])
        self.assertNotIn("snippet", payload["metadata"])
        self.assertNotIn("payload", payload["metadata"])

    async def test_role_management_prevents_last_platform_owner_demotion(self):
        class FakeDb:
            async def scalar(self, _stmt):
                return 1

        target = User(id=1, username="owner", role=UserRole.PLATFORM_OWNER.value)

        with self.assertRaisesRegex(Exception, "last platform_owner"):
            await admin_roles._reject_last_platform_owner_demotion(
                db=FakeDb(),
                target_user=target,
                new_role=UserRole.COMPANY_ADMIN.value,
            )

    async def test_role_assignment_writes_history_and_audit_log(self):
        class FakeResult:
            def __init__(self, user):
                self.user = user

            def scalar_one_or_none(self):
                return self.user

        class FakeDb:
            def __init__(self, user):
                self.user = user
                self.added = []

            async def execute(self, _stmt):
                return FakeResult(self.user)

            def add(self, value):
                self.added.append(value)

            async def commit(self):
                return None

        target = User(id=2, username="target", role=UserRole.COMPANY_ADMIN.value)
        admin = User(id=1, username="owner", role=UserRole.PLATFORM_OWNER.value, mfa_enabled=True)
        db = FakeDb(target)

        with patch("backend.routes.admin_roles.log_event"):
            response = await admin_roles.assign_user_role(
                admin_roles.UpdateRoleRequest(role=UserRole.PLATFORM_OWNER.value, reason="security handoff"),
                user_id=target.id,
                current_admin=admin,
                db=db,
            )

        self.assertTrue(response.success)
        self.assertTrue(any(isinstance(item, RoleAssignmentHistory) for item in db.added))
        self.assertTrue(any(isinstance(item, AuditLog) for item in db.added))

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
