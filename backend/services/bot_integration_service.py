"""Company-scoped Telegram bot integration management."""
from __future__ import annotations

import asyncio
import secrets
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import BotIntegration, Chunk, Project
from backend.providers.llm.factory import LLMProviderFactory
from backend.providers.vectordb.factory import VectorDBProviderFactory
from backend.runtime_config import get_runtime_value
from backend.security.sanitization import sanitize_optional_text, sanitize_text
from backend.services.telegram_api_service import TelegramAPIError, TelegramAPIService
from backend.services.token_crypto_service import TokenCryptoService


class BotIntegrationError(ValueError):
    """Validation error for bot integration operations."""


class BotIntegrationService:
    """Service enforcing owner/project scope for production Telegram integrations."""

    def __init__(
        self,
        crypto_service: TokenCryptoService | None = None,
        telegram_api: TelegramAPIService | None = None,
    ):
        self._crypto_service = crypto_service
        self.telegram_api = telegram_api or TelegramAPIService()

    @property
    def crypto_service(self) -> TokenCryptoService:
        if self._crypto_service is None:
            self._crypto_service = TokenCryptoService()
        return self._crypto_service

    @staticmethod
    def _build_webhook_url(integration_id: int, webhook_secret: str) -> str | None:
        base_url = str(settings.public_webhook_base_url or "").strip().rstrip("/")
        if not base_url:
            return None
        return f"{base_url}/telegram/webhook/{int(integration_id)}/{webhook_secret}"

    @staticmethod
    def _sanitize_name(value: str) -> str:
        name = sanitize_text(value, max_length=120, strip_html=True, allow_newlines=False)
        if not name:
            raise BotIntegrationError("Integration name is required")
        return name

    @staticmethod
    def _has_llm_credentials(provider_name: str) -> bool:
        provider = str(provider_name or "").strip().lower()
        if provider.startswith("gemini"):
            return bool(str(settings.gemini_api_key or "").strip())
        if provider.startswith("openrouter"):
            return bool(str(settings.openrouter_api_key or "").strip())
        if provider.startswith("groq"):
            return bool(str(settings.groq_api_key or "").strip())
        if provider.startswith("cerebras"):
            return bool(str(settings.cerebras_api_key or "").strip())
        return False

    @staticmethod
    def _has_embedding_credentials(provider_name: str) -> bool:
        provider = str(provider_name or "").strip().lower()
        if provider == "gemini":
            return bool(str(settings.gemini_api_key or "").strip())
        if provider == "cohere":
            return bool(str(settings.cohere_api_key or "").strip())
        return False

    async def _check_vector_backend(
        self,
        db: AsyncSession,
        *,
        provider_name: str,
        provider_instance: Any,
    ) -> bool:
        normalized = str(provider_name or "").strip().lower()
        if normalized == "pgvector":
            await db.execute(text("SELECT 1"))
            return True
        if normalized == "qdrant":
            client = getattr(provider_instance, "client", None)
            if client is None:
                return False
            await asyncio.to_thread(client.get_collections)
            return True
        return provider_instance is not None

    @staticmethod
    async def _get_owned_project(db: AsyncSession, *, owner_id: int, project_id: int) -> Project:
        stmt = select(Project).where(Project.id == int(project_id), Project.owner_id == int(owner_id))
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if project is None:
            raise BotIntegrationError("Project not found")
        return project

    async def list_integrations(self, db: AsyncSession, *, owner_id: int) -> list[BotIntegration]:
        result = await db.execute(
            select(BotIntegration)
            .where(BotIntegration.owner_id == int(owner_id))
            .order_by(BotIntegration.created_at.desc(), BotIntegration.id.desc())
        )
        return list(result.scalars().all())

    async def get_integration(self, db: AsyncSession, *, owner_id: int, integration_id: int) -> BotIntegration | None:
        result = await db.execute(
            select(BotIntegration).where(
                BotIntegration.id == int(integration_id),
                BotIntegration.owner_id == int(owner_id),
            )
        )
        return result.scalar_one_or_none()

    async def get_integration_by_webhook(
        self,
        db: AsyncSession,
        *,
        integration_id: int,
        webhook_secret: str,
    ) -> BotIntegration | None:
        result = await db.execute(
            select(BotIntegration).where(
                BotIntegration.id == int(integration_id),
                BotIntegration.webhook_secret == str(webhook_secret),
            )
        )
        return result.scalar_one_or_none()

    async def create_integration(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        project_id: int,
        name: str,
        bot_token: str,
        show_sources_to_customer: bool = False,
        human_handoff_enabled: bool = True,
        fallback_message: str | None = None,
        created_by_user_id: int | None = None,
    ) -> BotIntegration:
        await self._get_owned_project(db, owner_id=owner_id, project_id=project_id)
        bot_info = await self.telegram_api.validate_token(bot_token)
        token_hash = self.crypto_service.hash_token(bot_token)

        integration = BotIntegration(
            owner_id=int(owner_id),
            project_id=int(project_id),
            name=self._sanitize_name(name),
            telegram_bot_id=str(bot_info["telegram_bot_id"]),
            telegram_username=sanitize_optional_text(bot_info.get("telegram_username"), 120),
            token_encrypted=self.crypto_service.encrypt_token(bot_token),
            token_hash=token_hash,
            webhook_secret=secrets.token_urlsafe(48),
            status="active",
            show_sources_to_customer=bool(show_sources_to_customer),
            human_handoff_enabled=bool(human_handoff_enabled),
            fallback_message=sanitize_optional_text(fallback_message, 1000),
            created_by_user_id=created_by_user_id,
        )
        db.add(integration)
        try:
            await db.commit()
            await db.refresh(integration)
        except IntegrityError as exc:
            await db.rollback()
            raise BotIntegrationError("Telegram bot token is already connected") from exc

        integration.webhook_url = self._build_webhook_url(integration.id, integration.webhook_secret)
        if integration.webhook_url:
            try:
                await self.telegram_api.set_webhook(bot_token, integration.webhook_url)
            except TelegramAPIError as exc:
                integration.status = "error"
                integration.last_error = str(exc)

        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        return integration

    async def update_integration(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        integration_id: int,
        name: str | None = None,
        project_id: int | None = None,
        show_sources_to_customer: bool | None = None,
        human_handoff_enabled: bool | None = None,
        fallback_message: str | None = None,
    ) -> BotIntegration:
        integration = await self.get_integration(db, owner_id=owner_id, integration_id=integration_id)
        if integration is None:
            raise BotIntegrationError("Bot integration not found")

        if project_id is not None:
            await self._get_owned_project(db, owner_id=owner_id, project_id=project_id)
            integration.project_id = int(project_id)
        if name is not None:
            integration.name = self._sanitize_name(name)
        if show_sources_to_customer is not None:
            integration.show_sources_to_customer = bool(show_sources_to_customer)
        if human_handoff_enabled is not None:
            integration.human_handoff_enabled = bool(human_handoff_enabled)
        if fallback_message is not None:
            integration.fallback_message = sanitize_optional_text(fallback_message, 1000)

        integration.webhook_url = self._build_webhook_url(integration.id, integration.webhook_secret)
        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        return integration

    async def rotate_token(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        integration_id: int,
        bot_token: str,
    ) -> BotIntegration:
        integration = await self.get_integration(db, owner_id=owner_id, integration_id=integration_id)
        if integration is None:
            raise BotIntegrationError("Bot integration not found")

        bot_info = await self.telegram_api.validate_token(bot_token)
        integration.telegram_bot_id = str(bot_info["telegram_bot_id"])
        integration.telegram_username = sanitize_optional_text(bot_info.get("telegram_username"), 120)
        integration.token_encrypted = self.crypto_service.encrypt_token(bot_token)
        integration.token_hash = self.crypto_service.hash_token(bot_token)
        integration.webhook_url = self._build_webhook_url(integration.id, integration.webhook_secret)
        integration.status = "active"
        integration.last_error = None

        if integration.webhook_url:
            try:
                await self.telegram_api.set_webhook(bot_token, integration.webhook_url)
            except TelegramAPIError as exc:
                integration.status = "error"
                integration.last_error = str(exc)

        db.add(integration)
        try:
            await db.commit()
            await db.refresh(integration)
        except IntegrityError as exc:
            await db.rollback()
            raise BotIntegrationError("Telegram bot token is already connected") from exc
        return integration

    async def set_status(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        integration_id: int,
        status: str,
    ) -> BotIntegration:
        integration = await self.get_integration(db, owner_id=owner_id, integration_id=integration_id)
        if integration is None:
            raise BotIntegrationError("Bot integration not found")
        integration.status = status
        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        return integration

    async def delete_integration(self, db: AsyncSession, *, owner_id: int, integration_id: int) -> None:
        integration = await self.get_integration(db, owner_id=owner_id, integration_id=integration_id)
        if integration is None:
            raise BotIntegrationError("Bot integration not found")
        try:
            token = self.crypto_service.decrypt_token(integration.token_encrypted)
            await self.telegram_api.delete_webhook(token)
        except Exception:
            pass
        await db.delete(integration)
        await db.commit()

    async def readiness(self, db: AsyncSession, *, owner_id: int, integration_id: int) -> dict[str, Any]:
        integration = await self.get_integration(db, owner_id=owner_id, integration_id=integration_id)
        if integration is None:
            raise BotIntegrationError("Bot integration not found")

        llm_provider = str(get_runtime_value("llm_provider", settings.llm_provider) or "").strip().lower()
        embedding_provider = str(get_runtime_value("embedding_provider", settings.embedding_provider) or "").strip().lower()
        vector_db_provider = str(get_runtime_value("vector_db_provider", settings.vector_db_provider) or "").strip().lower()

        llm_available = set(LLMProviderFactory.get_available_providers())
        embedding_available = set(LLMProviderFactory.get_available_embedding_providers())
        vector_available = set(VectorDBProviderFactory.get_available_providers())

        checks = {
            "token_stored": bool(integration.token_encrypted),
            "token_decryptable": False,
            "token_valid": False,
            "token_matches_stored_bot": False,
            "webhook_configured": bool(integration.webhook_url),
            "telegram_webhook_registered": False,
            "telegram_webhook_matches_expected": False,
            "telegram_webhook_has_error": False,
            "linked_project_exists": False,
            "linked_project_owned": False,
            "usable_chunks": 0,
            "integration_active": integration.status == "active",
            "llm_provider": llm_provider,
            "llm_provider_supported": llm_provider in llm_available,
            "llm_credentials_configured": self._has_llm_credentials(llm_provider),
            "llm_provider_ready": False,
            "embedding_provider": embedding_provider,
            "embedding_provider_supported": embedding_provider in embedding_available,
            "embedding_credentials_configured": self._has_embedding_credentials(embedding_provider),
            "embedding_provider_ready": False,
            "vector_db_provider": vector_db_provider,
            "vector_db_provider_supported": vector_db_provider in vector_available,
            "vector_db_provider_ready": False,
            "last_error": integration.last_error,
        }

        project: Project | None = None
        try:
            project = await self._get_owned_project(db, owner_id=owner_id, project_id=integration.project_id)
            checks["linked_project_exists"] = True
            checks["linked_project_owned"] = True
        except BotIntegrationError as exc:
            checks["project_error"] = str(exc)

        if project is not None:
            try:
                chunks_result = await db.execute(
                    select(func.count(Chunk.id)).where(Chunk.project_id == project.id, Chunk.embedding.is_not(None))
                )
                checks["usable_chunks"] = int(chunks_result.scalar_one() or 0)
            except Exception:
                checks["chunk_error"] = "Unable to verify indexed chunks"

        decrypted_token = ""
        if checks["token_stored"]:
            try:
                decrypted_token = self.crypto_service.decrypt_token(integration.token_encrypted)
                checks["token_decryptable"] = bool(decrypted_token)
            except Exception as exc:
                checks["token_error"] = str(exc)

        if decrypted_token:
            try:
                bot_info = await self.telegram_api.validate_token(decrypted_token)
                checks["token_valid"] = True
                checks["token_matches_stored_bot"] = (
                    str(bot_info.get("telegram_bot_id") or "") == str(integration.telegram_bot_id)
                )
            except TelegramAPIError as exc:
                checks["token_error"] = str(exc)
            except Exception:
                checks["token_error"] = "Unable to validate Telegram bot token"

            if checks["webhook_configured"]:
                try:
                    webhook_info = await self.telegram_api.get_webhook_info(decrypted_token)
                    actual_webhook_url = str(webhook_info.get("url") or "").strip()
                    checks["telegram_webhook_registered"] = bool(actual_webhook_url)
                    checks["telegram_webhook_matches_expected"] = (
                        actual_webhook_url == str(integration.webhook_url or "").strip()
                    )
                    checks["telegram_webhook_has_error"] = bool(webhook_info.get("last_error_message"))
                    if checks["telegram_webhook_has_error"]:
                        checks["telegram_webhook_error"] = "Telegram reports webhook delivery errors"
                except TelegramAPIError as exc:
                    checks["telegram_webhook_error"] = str(exc)
                except Exception:
                    checks["telegram_webhook_error"] = "Unable to verify Telegram webhook state"

        if checks["llm_provider_supported"] and checks["llm_credentials_configured"]:
            try:
                llm_instance = LLMProviderFactory.create_provider(llm_provider)
                checks["llm_provider_ready"] = bool(llm_instance.get_model_name())
            except Exception:
                checks["llm_provider_error"] = "LLM provider initialization failed"

        if checks["embedding_provider_supported"] and checks["embedding_credentials_configured"]:
            try:
                embedding_instance = LLMProviderFactory.create_embedding_provider(embedding_provider)
                checks["embedding_provider_ready"] = embedding_instance.get_embedding_dimension() > 0
            except Exception:
                checks["embedding_provider_error"] = "Embedding provider initialization failed"

        if checks["vector_db_provider_supported"]:
            try:
                vector_instance = VectorDBProviderFactory.create_provider(vector_db_provider)
                checks["vector_db_provider_ready"] = await self._check_vector_backend(
                    db,
                    provider_name=vector_db_provider,
                    provider_instance=vector_instance,
                )
                if not checks["vector_db_provider_ready"]:
                    checks["vector_db_provider_error"] = "Vector store is not reachable"
            except Exception:
                checks["vector_db_provider_error"] = "Vector provider initialization failed"

        checks["ready"] = all(
            [
                checks["token_stored"],
                checks["token_decryptable"],
                checks["token_valid"],
                checks["token_matches_stored_bot"],
                checks["webhook_configured"],
                checks["telegram_webhook_registered"],
                checks["telegram_webhook_matches_expected"],
                not checks["telegram_webhook_has_error"],
                checks["linked_project_exists"],
                checks["linked_project_owned"],
                checks["usable_chunks"] > 0,
                checks["integration_active"],
                checks["llm_provider_ready"],
                checks["embedding_provider_ready"],
                checks["vector_db_provider_ready"],
            ]
        )
        return checks
