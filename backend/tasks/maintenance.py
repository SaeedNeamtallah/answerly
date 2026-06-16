import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import update

from backend.celery_app import celery_app, get_setup_utils
from backend.database.models import ConversationMessage
from backend.utils.idempotency_manager import IdempotencyManager

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.maintenance.clean_celery_executions_table",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    queue="default",
)
def clean_celery_executions_table(self):
    return asyncio.run(_clean_celery_executions_table())


@celery_app.task(
    bind=True,
    name="backend.tasks.maintenance.clean_expired_telegram_raw_payloads",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    queue="default",
)
def clean_expired_telegram_raw_payloads(self):
    return asyncio.run(_clean_expired_telegram_raw_payloads())


async def _clean_celery_executions_table():
    db_engine = None

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

        idempotency_manager = IdempotencyManager()

        async with session_maker() as db:
            deleted_count = await idempotency_manager.cleanup_old_tasks(
                db=db,
                time_retention=86400,  # 24 hours
            )

        logger.info(f"Cleaned old celery task executions: {deleted_count}")
        return {
            "status": "success",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        logger.error(f"Failed to clean celery task executions: {str(e)}")
        raise

    finally:
        try:
            if db_engine:
                await db_engine.dispose()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


async def _clean_expired_telegram_raw_payloads():
    db_engine = None

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
            result = await db.execute(
                update(ConversationMessage)
                .where(
                    ConversationMessage.raw_payload_expires_at.is_not(None),
                    ConversationMessage.raw_payload_expires_at < datetime.now(timezone.utc),
                )
                .values(raw_payload_json=None, raw_payload_expires_at=None)
            )
            await db.commit()
            cleaned_count = int(result.rowcount or 0)

        logger.info("Cleaned expired Telegram raw payloads: %s", cleaned_count)
        return {
            "status": "success",
            "cleaned_count": cleaned_count,
        }

    except Exception as e:
        logger.error(f"Failed to clean expired Telegram raw payloads: {str(e)}")
        raise

    finally:
        try:
            if db_engine:
                await db_engine.dispose()
        except Exception as e:
            logger.error(f"Error during telegram raw payload cleanup: {str(e)}")
