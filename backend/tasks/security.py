import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.celery_app import celery_app
from backend.config import settings
from backend.database.models import SecurityEventRecord

logger = logging.getLogger(__name__)

async def _persist_security_event(event_dict: dict):
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
            record = SecurityEventRecord(
                event_type=event_dict["event_type"],
                severity=event_dict["severity"],
                user_id=event_dict.get("user_id"),
                username=event_dict.get("username"),
                ip_address=event_dict.get("ip_address"),
                message=event_dict["message"],
                metadata_=event_dict.get("metadata", {}),
                is_simulation=bool(event_dict.get("is_simulation", False)),
                delivery_status=str(event_dict.get("delivery_status") or "PENDING")[:32],
            )
            db.add(record)
            await db.commit()
    finally:
        await db_engine.dispose()


@celery_app.task(name="backend.tasks.security.persist_security_event_task")
def persist_security_event_task(event_dict: dict):
    """Persist a security event to the database in a Celery worker."""
    return asyncio.run(
        _persist_security_event(event_dict)
    )
