import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select

from backend.celery_app import celery_app, get_setup_utils
from backend.config import settings
from backend.database.models import BotIntegration, ConversationMessage, TelegramCustomer
from backend.services.telegram_api_service import TelegramAPIError, TelegramAPIService
from backend.services.token_crypto_service import TokenCryptoService

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.telegram_outbox.deliver_pending_messages",
    queue="default",
)
def deliver_pending_messages(self):
    return asyncio.run(_deliver_pending_messages())


async def _deliver_pending_messages() -> dict[str, object]:
    db_engine = None

    claimed_count = 0
    sent_count = 0
    failed_count = 0
    retried_count = 0
    recovered_count = 0

    crypto_service = TokenCryptoService()
    telegram_api = TelegramAPIService()
    max_attempts = max(1, int(settings.telegram_outbox_max_delivery_attempts))
    claim_timeout_seconds = max(1, int(settings.telegram_outbox_claim_timeout_seconds))
    stale_claim_cutoff = datetime.now(timezone.utc) - timedelta(seconds=claim_timeout_seconds)

    try:
        (
            db_engine,
            session_maker,
            document_loader,
            chunking_service,
            embedding_service,
            vector_db,
            file_service,
        ) = await get_setup_utils()

        async with session_maker() as db:
            stmt = (
                select(ConversationMessage)
                .where(
                    or_(
                        ConversationMessage.delivery_status == "pending",
                        and_(
                            ConversationMessage.delivery_status == "sending",
                            or_(
                                ConversationMessage.delivery_claimed_at.is_(None),
                                ConversationMessage.delivery_claimed_at < stale_claim_cutoff,
                            ),
                        ),
                    ),
                    ConversationMessage.delivery_attempts < max_attempts,
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
                    failed_count += 1
                    await db.commit()
                    continue

                integration = None
                customer = None

                if message.bot_integration_id is None or message.telegram_customer_id is None:
                    message.delivery_status = "failed"
                    message.delivery_claimed_at = None
                    failed_count += 1
                    await db.commit()
                    continue

                integration = await db.get(BotIntegration, int(message.bot_integration_id))
                customer = await db.get(TelegramCustomer, int(message.telegram_customer_id))
                if integration is None or customer is None or not getattr(customer, "chat_id", None):
                    message.delivery_status = "failed"
                    message.delivery_claimed_at = None
                    failed_count += 1
                    await db.commit()
                    continue

                try:
                    token = crypto_service.decrypt_token(integration.token_encrypted)
                except Exception:
                    message.delivery_status = "failed"
                    message.delivery_claimed_at = None
                    failed_count += 1
                    await db.commit()
                    continue

                # Claim before external call to reduce duplicate sends across workers.
                message.delivery_status = "sending"
                message.delivery_claimed_at = datetime.now(timezone.utc)
                message.delivery_attempts = int(message.delivery_attempts or 0) + 1
                claimed_count += 1
                if was_stale_claim:
                    recovered_count += 1
                await db.commit()

                try:
                    result_payload = await telegram_api.send_message(token, customer.chat_id, message_text)
                except TelegramAPIError as exc:
                    logger.warning("Telegram outbox delivery failed: %s", str(exc))
                    if message.delivery_attempts >= max_attempts:
                        message.delivery_status = "failed"
                        failed_count += 1
                    else:
                        message.delivery_status = "pending"
                        retried_count += 1
                    message.delivery_claimed_at = None
                    await db.commit()
                    continue
                except Exception as exc:
                    logger.exception("Unexpected telegram outbox error: %s", str(exc))
                    if message.delivery_attempts >= max_attempts:
                        message.delivery_status = "failed"
                        failed_count += 1
                    else:
                        message.delivery_status = "pending"
                        retried_count += 1
                    message.delivery_claimed_at = None
                    await db.commit()
                    continue

                message.delivery_status = "sent"
                message.delivery_claimed_at = None
                telegram_message_id = result_payload.get("message_id") if isinstance(result_payload, dict) else None
                message.telegram_message_id = str(telegram_message_id) if telegram_message_id is not None else None
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
            if db_engine:
                await db_engine.dispose()
        except Exception as exc:
            logger.error("Error disposing telegram outbox DB engine: %s", str(exc))
