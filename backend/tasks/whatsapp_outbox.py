import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.celery_app import celery_app
from backend.config import settings
from backend.database.models import WhatsAppIntegration, ConversationMessage, WhatsAppCustomer


logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.whatsapp_outbox.deliver_pending_messages",
    queue="default",
)
def deliver_pending_messages(self):
    return asyncio.run(_deliver_pending_messages())


async def _deliver_pending_messages(test_db: AsyncSession | None = None) -> dict[str, object]:
    claimed_count = 0
    sent_count = 0
    failed_count = 0
    retried_count = 0
    recovered_count = 0


    max_attempts = max(1, int(settings.whatsapp_outbox_max_delivery_attempts))
    claim_timeout_seconds = max(1, int(settings.whatsapp_outbox_claim_timeout_seconds))
    now = datetime.now(timezone.utc)
    stale_claim_cutoff = now - timedelta(seconds=claim_timeout_seconds)
    retry_base_seconds = max(1, int(settings.whatsapp_outbox_retry_base_seconds))
    retry_max_seconds = max(retry_base_seconds, int(settings.whatsapp_outbox_retry_max_seconds))

    db_engine = None
    if not test_db:
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
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def get_db():
            if test_db:
                yield test_db
            else:
                async with session_maker() as db:
                    yield db

        async with get_db() as db:
            stmt = (
                select(ConversationMessage)
                .where(
                    or_(
                        and_(
                            ConversationMessage.delivery_status == "pending",
                            or_(
                                ConversationMessage.delivery_next_attempt_at.is_(None),
                                ConversationMessage.delivery_next_attempt_at <= now,
                            ),
                        ),
                        and_(
                            ConversationMessage.delivery_status == "sending",
                            or_(
                                ConversationMessage.delivery_claimed_at.is_(None),
                                ConversationMessage.delivery_claimed_at < stale_claim_cutoff,
                            ),
                        ),
                    ),
                    ConversationMessage.delivery_attempts < max_attempts,
                    ConversationMessage.whatsapp_integration_id.is_not(None),
                )
                .order_by(ConversationMessage.created_at.asc())
                .limit(50)
                .with_for_update(skip_locked=True)
            )
            result = await db.execute(stmt)
            messages = list(result.scalars().all())

            for message in messages:
                was_stale_claim = str(message.delivery_status or "") == "sending"
                message_text = str(message.text or "").strip()
                if not message_text:
                    message.delivery_status = "failed"
                    message.delivery_claimed_at = None
                    message.delivery_next_attempt_at = None
                    failed_count += 1
                    await db.commit()
                    continue

                integration = None
                customer = None

                if message.whatsapp_integration_id is None or message.whatsapp_customer_id is None:
                    message.delivery_status = "failed"
                    message.delivery_claimed_at = None
                    message.delivery_next_attempt_at = None
                    failed_count += 1
                    await db.commit()
                    continue

                integration = await db.get(WhatsAppIntegration, int(message.whatsapp_integration_id))
                customer = await db.get(WhatsAppCustomer, int(message.whatsapp_customer_id))
                if integration is None or customer is None or not getattr(customer, "phone_number", None):
                    message.delivery_status = "failed"
                    message.delivery_claimed_at = None
                    message.delivery_next_attempt_at = None
                    failed_count += 1
                    await db.commit()
                    continue

                # Claim before external call to reduce duplicate sends across workers.
                message.delivery_status = "sending"
                message.delivery_claimed_at = datetime.now(timezone.utc)
                message.delivery_next_attempt_at = None
                message.delivery_attempts = int(message.delivery_attempts or 0) + 1
                claimed_count += 1
                if was_stale_claim:
                    recovered_count += 1
                await db.commit()

                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"http://whatsapp_bridge:3002/api/sessions/{integration.session_id}/send",
                            json={
                                "jid": customer.phone_number if "@" in customer.phone_number else customer.phone_number + "@s.whatsapp.net",
                                "text": message_text,
                            },
                            timeout=15.0,
                        )
                        response.raise_for_status()
                        result_payload = response.json()
                except httpx.HTTPError as exc:
                    logger.warning("WhatsApp outbox delivery failed: %s", str(exc))
                    if message.delivery_attempts >= max_attempts:
                        message.delivery_status = "failed"
                        message.delivery_next_attempt_at = None
                        failed_count += 1
                    else:
                        message.delivery_status = "pending"
                        delay_seconds = min(
                            retry_max_seconds,
                            retry_base_seconds * (2 ** max(0, int(message.delivery_attempts or 1) - 1)),
                        )
                        message.delivery_next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
                        retried_count += 1
                    message.delivery_claimed_at = None
                    await db.commit()
                    continue
                except Exception as exc:
                    logger.exception("Unexpected WhatsApp outbox error: %s", str(exc))
                    if message.delivery_attempts >= max_attempts:
                        message.delivery_status = "failed"
                        message.delivery_next_attempt_at = None
                        failed_count += 1
                    else:
                        message.delivery_status = "pending"
                        delay_seconds = min(
                            retry_max_seconds,
                            retry_base_seconds * (2 ** max(0, int(message.delivery_attempts or 1) - 1)),
                        )
                        message.delivery_next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
                        retried_count += 1
                    message.delivery_claimed_at = None
                    await db.commit()
                    continue

                message.delivery_status = "sent"
                message.delivery_claimed_at = None
                message.delivery_next_attempt_at = None
                whatsapp_message_id = result_payload.get("message_id") if isinstance(result_payload, dict) else None
                message.whatsapp_message_id = str(whatsapp_message_id) if whatsapp_message_id is not None else None
                sent_count += 1
                await db.commit()

        return {
            "status": "success",
            "claimed": claimed_count,
            "sent": sent_count,
            "failed": failed_count,
            "retried": retried_count,
            "recovered": recovered_count,
        }
    finally:
        try:
            await db_engine.dispose()
        except Exception as exc:
            logger.error("Error disposing telegram outbox DB engine: %s", str(exc))
