"""Webhook orchestration for database-backed Telegram bot integrations."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.controllers.query_controller import QueryInfrastructureError
from backend.database.models import BotIntegration
from backend.monitoring.metrics import TELEGRAM_WEBHOOK_FAILURES_TOTAL
from backend.services.bot_integration_service import BotIntegrationService
from backend.services.conversation_service import ConversationService
from backend.services.customer_bot_query_service import CustomerBotQueryService
from backend.services.telegram_api_service import TelegramAPIService
from backend.services.token_crypto_service import TokenCryptoService


class TelegramWebhookError(ValueError):
    """Sanitized webhook processing failure."""


class TelegramWebhookThrottle(TelegramWebhookError):
    """Raised when per-integration webhook limits are exceeded."""


class TelegramWebhookService:
    """Process Telegram updates through the bot_integration -> project RAG path."""

    _request_buckets: dict[int, deque[float]] = defaultdict(deque)
    _in_flight: dict[int, int] = defaultdict(int)

    def __init__(
        self,
        integration_service: BotIntegrationService | None = None,
        conversation_service: ConversationService | None = None,
        query_service: CustomerBotQueryService | None = None,
        crypto_service: TokenCryptoService | None = None,
        telegram_api: TelegramAPIService | None = None,
    ):
        self._crypto_service = crypto_service
        self.telegram_api = telegram_api or TelegramAPIService()
        self._integration_service = integration_service
        self._conversation_service = conversation_service
        self.query_service = query_service or CustomerBotQueryService()

    @property
    def crypto_service(self) -> TokenCryptoService:
        if self._crypto_service is None:
            self._crypto_service = TokenCryptoService()
        return self._crypto_service

    @property
    def integration_service(self) -> BotIntegrationService:
        if self._integration_service is None:
            self._integration_service = BotIntegrationService(
                crypto_service=self.crypto_service,
                telegram_api=self.telegram_api,
            )
        return self._integration_service

    @property
    def conversation_service(self) -> ConversationService:
        if self._conversation_service is None:
            self._conversation_service = ConversationService(
                crypto_service=self.crypto_service,
                telegram_api=self.telegram_api,
            )
        return self._conversation_service

    @classmethod
    def _acquire_limit(cls, integration_id: int) -> None:
        now = time.monotonic()
        bucket = cls._request_buckets[int(integration_id)]
        window_seconds = 60.0
        while bucket and (now - bucket[0]) > window_seconds:
            bucket.popleft()

        if len(bucket) >= max(1, int(settings.telegram_webhook_requests_per_minute)):
            raise TelegramWebhookThrottle("Telegram webhook rate limit exceeded")
        if cls._in_flight[int(integration_id)] >= max(1, int(settings.telegram_webhook_max_in_flight)):
            raise TelegramWebhookThrottle("Telegram webhook concurrency limit exceeded")

        bucket.append(now)
        cls._in_flight[int(integration_id)] += 1

    @classmethod
    def _release_limit(cls, integration_id: int) -> None:
        cls._in_flight[int(integration_id)] = max(0, cls._in_flight[int(integration_id)] - 1)

    @staticmethod
    def _extract_message(update: dict[str, Any]) -> dict[str, Any] | None:
        for key in ("message", "edited_message"):
            value = update.get(key)
            if isinstance(value, dict):
                return value
        return None

    @staticmethod
    def _language_for_customer(message: dict[str, Any]) -> str:
        user = message.get("from") if isinstance(message.get("from"), dict) else {}
        language_code = str(user.get("language_code") or "").lower()
        return "en" if language_code.startswith("en") else "ar"

    async def handle_update(
        self,
        db: AsyncSession,
        *,
        integration_id: int,
        webhook_secret: str,
        update: dict[str, Any],
    ) -> dict[str, Any]:
        integration = await self.integration_service.get_integration_by_webhook(
            db,
            integration_id=integration_id,
            webhook_secret=webhook_secret,
        )
        if integration is None:
            raise TelegramWebhookError("Bot integration not found")

        self._acquire_limit(integration.id)
        try:
            return await self._handle_update_for_integration(db, integration=integration, update=update)
        finally:
            self._release_limit(integration.id)

    async def _handle_update_for_integration(
        self,
        db: AsyncSession,
        *,
        integration: BotIntegration,
        update: dict[str, Any],
    ) -> dict[str, Any]:
        if integration.status not in {"active", "error"}:
            return {"ok": True, "ignored": True, "reason": "integration_disabled"}

        message = self._extract_message(update)
        if message is None:
            return {"ok": True, "ignored": True, "reason": "unsupported_update"}

        text = str(message.get("text") or "").strip()
        if not text:
            return {"ok": True, "ignored": True, "reason": "non_text_message"}

        chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
        chat_id = chat.get("id")
        if chat_id is None:
            return {"ok": True, "ignored": True, "reason": "missing_chat"}

        customer = await self.conversation_service.get_or_create_customer(
            db,
            integration=integration,
            chat_id=str(chat_id),
            telegram_user=message.get("from") if isinstance(message.get("from"), dict) else None,
        )
        conversation = await self.conversation_service.get_or_create_conversation(
            db,
            integration=integration,
            customer=customer,
        )

        if customer.is_blocked:
            await db.commit()
            return {"ok": True, "ignored": True, "reason": "customer_blocked"}

        customer_message, created = await self.conversation_service.save_message(
            db,
            integration=integration,
            conversation=conversation,
            customer=customer,
            sender_type="customer",
            text=text,
            telegram_update_id=str(update.get("update_id")) if update.get("update_id") is not None else None,
            telegram_message_id=str(message.get("message_id")) if message.get("message_id") is not None else None,
            raw_payload=update,
        )
        if not created:
            await db.commit()
            return {"ok": True, "duplicate": True, "message_id": customer_message.id}

        language = self._language_for_customer(message)
        try:
            answer_result = await self.query_service.answer(
                db,
                integration=integration,
                query=text,
                language=language,
            )
            reply_text = answer_result["customer_answer"]
            if int(answer_result.get("context_used") or 0) <= 0 and integration.human_handoff_enabled:
                conversation.needs_human = True
                conversation.status = "escalated"
                if integration.fallback_message:
                    reply_text = integration.fallback_message

            await self.conversation_service.save_message(
                db,
                integration=integration,
                conversation=conversation,
                customer=customer,
                sender_type="bot",
                text=reply_text,
                telegram_message_id=None,
                delivery_status="pending",
                answer_sources=answer_result.get("internal_sources") or [],
                retrieval_metadata={"context_used": answer_result.get("context_used")},
            )
            integration.status = "active"
            integration.last_error = None
            db.add(integration)
            await db.commit()
            return {"ok": True, "conversation_id": conversation.id}
        except QueryInfrastructureError:
            TELEGRAM_WEBHOOK_FAILURES_TOTAL.labels(reason="query_infrastructure").inc()
            fallback = integration.fallback_message or "Support is temporarily unavailable. Please try again later."
            return await self._handle_failure(
                db,
                integration=integration,
                conversation=conversation,
                customer=customer,
                fallback=fallback,
                error="Query service unavailable",
            )
        except Exception:
            TELEGRAM_WEBHOOK_FAILURES_TOTAL.labels(reason="processing").inc()
            fallback = integration.fallback_message or "Support is temporarily unavailable. Please try again later."
            return await self._handle_failure(
                db,
                integration=integration,
                conversation=conversation,
                customer=customer,
                fallback=fallback,
                error="Telegram webhook processing failed",
            )

    async def _handle_failure(
        self,
        db: AsyncSession,
        *,
        integration: BotIntegration,
        conversation,
        customer,
        fallback: str,
        error: str,
    ) -> dict[str, Any]:
        integration.status = "error"
        integration.last_error = error
        conversation.last_error = error
        if integration.human_handoff_enabled:
            conversation.needs_human = True
            conversation.status = "escalated"
        db.add(integration)
        db.add(conversation)

        await self.conversation_service.save_message(
            db,
            integration=integration,
            conversation=conversation,
            customer=customer,
            sender_type="error",
            text=error,
            delivery_status="none",
        )
        await self.conversation_service.save_message(
            db,
            integration=integration,
            conversation=conversation,
            customer=customer,
            sender_type="bot",
            text=fallback,
            telegram_message_id=None,
            delivery_status="pending",
        )
        await db.commit()
        return {"ok": True, "conversation_id": conversation.id, "fallback": True}
