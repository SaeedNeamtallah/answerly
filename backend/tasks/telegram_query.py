import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm.attributes import flag_modified

from backend.celery_app import celery_app
from backend.config import settings
from backend.controllers.query_controller import QueryInfrastructureError
from backend.database.models import BotIntegration, Conversation, ConversationMessage, TelegramCustomer
from backend.monitoring.metrics import TELEGRAM_WEBHOOK_FAILURES_TOTAL
from backend.services.conversation_service import ConversationService
from backend.services.customer_bot_query_service import CustomerBotQueryService

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _metadata(message: ConversationMessage) -> dict[str, Any]:
    raw = message.retrieval_metadata_json
    return dict(raw) if isinstance(raw, dict) else {}


def _mark_generation_status(message: ConversationMessage, status: str, **extra: Any) -> None:
    metadata = _metadata(message)
    metadata["reply_generation_status"] = status
    metadata.update(extra)
    message.retrieval_metadata_json = metadata
    flag_modified(message, "retrieval_metadata_json")


def _language_for_customer(customer: TelegramCustomer | None) -> str:
    language_code = str(getattr(customer, "language_code", "") or "").lower()
    return "en" if language_code.startswith("en") else "ar"


async def _claim_customer_message(db: AsyncSession, customer_message_id: int) -> ConversationMessage | None:
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.id == int(customer_message_id))
        .with_for_update()
    )
    message = result.scalar_one_or_none()
    if message is None or str(message.sender_type) != "customer":
        return None

    metadata = _metadata(message)
    status = str(metadata.get("reply_generation_status") or "").lower()
    if status == "done":
        return None

    if status == "processing":
        started_raw = metadata.get("reply_generation_started_at")
        try:
            started_at = datetime.fromisoformat(str(started_raw))
        except Exception:
            started_at = None
        if started_at is not None and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        timeout = timedelta(seconds=max(1, int(settings.telegram_reply_generation_claim_timeout_seconds)))
        if started_at is not None and started_at > (_now() - timeout):
            return None

    _mark_generation_status(
        message,
        "processing",
        reply_generation_started_at=_now().isoformat(),
    )
    db.add(message)
    await db.commit()
    return message


async def _save_failure_reply(
    db: AsyncSession,
    *,
    integration: BotIntegration,
    conversation: Conversation,
    customer: TelegramCustomer,
    customer_message: ConversationMessage,
    fallback: str,
    error: str,
) -> None:
    conversation_service = ConversationService()
    integration.status = "error"
    integration.last_error = error
    conversation.last_error = error
    if integration.human_handoff_enabled:
        conversation.needs_human = True
        conversation.status = "escalated"
    db.add(integration)
    db.add(conversation)

    reply_metadata = {"reply_to_customer_message_id": int(customer_message.id)}
    await conversation_service.save_message(
        db,
        integration=integration,
        conversation=conversation,
        customer=customer,
        sender_type="error",
        text=error,
        delivery_status="none",
        retrieval_metadata=reply_metadata,
    )
    await conversation_service.save_message(
        db,
        integration=integration,
        conversation=conversation,
        customer=customer,
        sender_type="bot",
        text=fallback,
        telegram_message_id=None,
        delivery_status="pending",
        retrieval_metadata={**reply_metadata, "fallback": True},
    )
    _mark_generation_status(
        customer_message,
        "done",
        reply_generation_finished_at=_now().isoformat(),
        reply_generation_error=error,
    )
    db.add(customer_message)
    await db.commit()


async def _generate_bot_reply(customer_message_id: int) -> dict[str, object]:
    db_engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=2,
        max_overflow=1,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    try:
        async with session_maker() as db:
            customer_message = await _claim_customer_message(db, int(customer_message_id))
            if customer_message is None:
                return {"status": "skipped", "customer_message_id": int(customer_message_id)}

            integration = await db.get(BotIntegration, int(customer_message.bot_integration_id))
            conversation = await db.get(Conversation, int(customer_message.conversation_id))
            customer = await db.get(TelegramCustomer, int(customer_message.telegram_customer_id or 0))
            if integration is None or conversation is None or customer is None:
                _mark_generation_status(
                    customer_message,
                    "done",
                    reply_generation_finished_at=_now().isoformat(),
                    reply_generation_error="Conversation context is unavailable",
                )
                db.add(customer_message)
                await db.commit()
                return {"status": "failed", "reason": "missing_context", "customer_message_id": int(customer_message_id)}

            query_service = CustomerBotQueryService()
            conversation_service = ConversationService()
            reply_metadata = {"reply_to_customer_message_id": int(customer_message.id)}
            language = _language_for_customer(customer)

            try:
                answer_result = await query_service.answer(
                    db,
                    integration=integration,
                    query=str(customer_message.text or ""),
                    language=language,
                )
                reply_text = str(answer_result.get("customer_answer") or "").strip()
                if int(answer_result.get("context_used") or 0) <= 0 and integration.human_handoff_enabled:
                    conversation.needs_human = True
                    conversation.status = "escalated"
                    if integration.fallback_message:
                        reply_text = integration.fallback_message

                if not reply_text:
                    reply_text = integration.fallback_message or "Support is temporarily unavailable. Please try again later."

                await conversation_service.save_message(
                    db,
                    integration=integration,
                    conversation=conversation,
                    customer=customer,
                    sender_type="bot",
                    text=reply_text,
                    telegram_message_id=None,
                    delivery_status="pending",
                    answer_sources=answer_result.get("internal_sources") or [],
                    retrieval_metadata={
                        **reply_metadata,
                        "context_used": answer_result.get("context_used"),
                    },
                )
                integration.status = "active"
                integration.last_error = None
                _mark_generation_status(
                    customer_message,
                    "done",
                    reply_generation_finished_at=_now().isoformat(),
                )
                db.add(integration)
                db.add(customer_message)
                await db.commit()
                return {"status": "success", "customer_message_id": int(customer_message.id)}
            except QueryInfrastructureError:
                TELEGRAM_WEBHOOK_FAILURES_TOTAL.labels(reason="query_infrastructure").inc()
                fallback = integration.fallback_message or "Support is temporarily unavailable. Please try again later."
                await _save_failure_reply(
                    db,
                    integration=integration,
                    conversation=conversation,
                    customer=customer,
                    customer_message=customer_message,
                    fallback=fallback,
                    error="Query service unavailable",
                )
                return {"status": "fallback", "customer_message_id": int(customer_message.id)}
            except Exception:
                logger.exception("Telegram reply generation failed")
                TELEGRAM_WEBHOOK_FAILURES_TOTAL.labels(reason="processing").inc()
                fallback = integration.fallback_message or "Support is temporarily unavailable. Please try again later."
                await _save_failure_reply(
                    db,
                    integration=integration,
                    conversation=conversation,
                    customer=customer,
                    customer_message=customer_message,
                    fallback=fallback,
                    error="Telegram reply generation failed",
                )
                return {"status": "fallback", "customer_message_id": int(customer_message.id)}
    finally:
        await db_engine.dispose()


@celery_app.task(
    bind=True,
    name="backend.tasks.telegram_query.generate_bot_reply",
    queue="default",
)
def generate_bot_reply_task(self, customer_message_id: int):
    return asyncio.run(_generate_bot_reply(int(customer_message_id)))
