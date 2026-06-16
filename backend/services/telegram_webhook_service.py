"""Webhook orchestration for database-backed Telegram bot integrations."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import BotIntegration
from backend.services.bot_integration_service import BotIntegrationService
from backend.services.conversation_service import ConversationService
from backend.services.customer_bot_query_service import CustomerBotQueryService
from backend.services.telegram_api_service import TelegramAPIService
from backend.services.token_crypto_service import TokenCryptoService

try:
    import redis.asyncio as redis_async
except Exception:  # pragma: no cover - redis is an optional runtime dependency for fallback behavior
    redis_async = None


class TelegramWebhookError(ValueError):
    """Sanitized webhook processing failure."""


class TelegramWebhookThrottle(TelegramWebhookError):
    """Raised when per-integration webhook limits are exceeded."""


class TelegramWebhookService:
    """Process Telegram updates through the bot_integration -> project RAG path."""

    _request_buckets: dict[int, deque[float]] = defaultdict(deque)
    _in_flight: dict[int, int] = defaultdict(int)
    _redis_client = None

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
    def _rate_limit_redis_url(cls) -> str:
        configured = str(settings.telegram_rate_limit_redis_url or "").strip()
        if configured:
            return configured
        backend = str(settings.celery_result_backend or "").strip()
        return backend if backend.startswith(("redis://", "rediss://")) else ""

    @classmethod
    async def _get_redis_client(cls):
        if redis_async is None:
            return None
        if cls._redis_client is not None:
            return cls._redis_client
        url = cls._rate_limit_redis_url()
        if not url:
            return None
        cls._redis_client = redis_async.from_url(url, decode_responses=True)
        return cls._redis_client

    @classmethod
    def _acquire_memory_limit(cls, integration_id: int) -> str:
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
        return "memory"

    @classmethod
    async def _acquire_redis_limit(cls, integration_id: int) -> str | None:
        client = await cls._get_redis_client()
        if client is None:
            return None

        max_requests = max(1, int(settings.telegram_webhook_requests_per_minute))
        max_in_flight = max(1, int(settings.telegram_webhook_max_in_flight))
        minute_bucket = int(time.time() // 60)
        rate_key = f"telegram:webhook:rate:{int(integration_id)}:{minute_bucket}"
        in_flight_key = f"telegram:webhook:inflight:{int(integration_id)}"

        current_count = await client.incr(rate_key)
        if current_count == 1:
            await client.expire(rate_key, 120)
        if int(current_count) > max_requests:
            raise TelegramWebhookThrottle("Telegram webhook rate limit exceeded")

        current_in_flight = await client.incr(in_flight_key)
        await client.expire(in_flight_key, max(30, int(settings.telegram_reply_generation_claim_timeout_seconds)))
        if int(current_in_flight) > max_in_flight:
            await client.decr(in_flight_key)
            raise TelegramWebhookThrottle("Telegram webhook concurrency limit exceeded")

        return "redis"

    @classmethod
    async def _acquire_limit(cls, integration_id: int) -> str:
        try:
            backend = await cls._acquire_redis_limit(integration_id)
            if backend:
                return backend
        except TelegramWebhookThrottle:
            raise
        except Exception:
            # Keep webhook availability during Redis outages; memory fallback is per replica.
            pass

        return cls._acquire_memory_limit(integration_id)

    @classmethod
    async def _release_limit(cls, integration_id: int, backend: str) -> None:
        if backend == "redis":
            try:
                client = await cls._get_redis_client()
                if client is not None:
                    await client.decr(f"telegram:webhook:inflight:{int(integration_id)}")
                    return
            except Exception:
                pass
        cls._in_flight[int(integration_id)] = max(0, cls._in_flight[int(integration_id)] - 1)

    @staticmethod
    def _enqueue_reply_generation(customer_message_id: int) -> None:
        from backend.tasks.telegram_query import generate_bot_reply_task

        generate_bot_reply_task.delay(int(customer_message_id))

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

        limit_backend = await self._acquire_limit(integration.id)
        try:
            return await self._handle_update_for_integration(db, integration=integration, update=update)
        finally:
            await self._release_limit(integration.id, limit_backend)

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
            retrieval_metadata={"reply_generation_status": "queued"},
        )
        try:
            await db.commit()
            self._enqueue_reply_generation(int(customer_message.id))
        except Exception as exc:
            raise TelegramWebhookError("Telegram reply queue is unavailable") from exc

        result = {"ok": True, "conversation_id": conversation.id, "reply_queued": True}
        if not created:
            result["duplicate"] = True
            result["message_id"] = customer_message.id
        return result

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
