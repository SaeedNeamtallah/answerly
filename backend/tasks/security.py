import logging
from backend.celery_app import celery_app
from backend.database.session import AsyncSessionLocal
from backend.database.models import SecurityEventRecord
import asyncio

logger = logging.getLogger(__name__)

async def _persist_security_event(event_dict: dict):
    async with AsyncSessionLocal() as db:
        record = SecurityEventRecord(
            event_type=event_dict["event_type"],
            severity=event_dict["severity"],
            user_id=event_dict.get("user_id"),
            username=event_dict.get("username"),
            ip_address=event_dict.get("ip_address"),
            message=event_dict["message"],
            metadata_=event_dict.get("metadata", {})
        )
        db.add(record)
        await db.commit()

@celery_app.task(name="backend.tasks.security.persist_security_event_task")
def persist_security_event_task(event_dict: dict):
    """Celery task to persist a security event to the database."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(_persist_security_event(event_dict))
