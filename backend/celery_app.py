"""
Celery application configuration.
Standalone entry point for Celery workers, separate from FastAPI main.py.
"""
from celery import Celery
from typing import Tuple

from backend.config import settings

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.providers.vectordb.factory import VectorDBProviderFactory
from backend.services.embedding_service import EmbeddingService
from backend.services.chunking_service import ChunkingService
from backend.services.document_loader import DocumentLoaderService
from backend.services.file_service import FileService


SetupUtils = Tuple[
    object,
    async_sessionmaker,
    DocumentLoaderService,
    ChunkingService,
    EmbeddingService,
    object,
    FileService,
]

def _build_setup_utils() -> SetupUtils:
    """Create fresh DB/session/service instances for one Celery task run."""
    db_engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=5,
        max_overflow=2,
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

    document_loader = DocumentLoaderService()
    chunking_service = ChunkingService()
    embedding_service = EmbeddingService()
    vector_db = VectorDBProviderFactory.create_provider()
    file_service = FileService()

    return (
        db_engine,
        session_maker,
        document_loader,
        chunking_service,
        embedding_service,
        vector_db,
        file_service,
    )


async def get_setup_utils():
    """
    Return fresh DB engine, session, and service instances for the current task.

    Provider-dependent services are intentionally not cached so runtime config
    updates made through /config/providers affect uploads, indexing, and queries
    without restarting Celery workers.

    Returns a tuple of (db_engine, async_session_maker, document_loader,
                        chunking_service, embedding_service, vector_db, file_service)
    """
    return _build_setup_utils()


# Create Celery application instance
celery_app = Celery(
    "ragmind",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.monitoring.celery_metrics",
        "backend.tasks.file_processing",
        "backend.tasks.data_indexing",
        "backend.tasks.process_workflow",
        "backend.tasks.maintenance",
        "backend.tasks.telegram_outbox",
        "backend.tasks.telegram_query",
    ],
)

# Configure Celery with essential settings
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_task_serializer,
    accept_content=[settings.celery_task_serializer],

    # Task safety - Late acknowledgment prevents task loss on worker crash
    task_acks_late=settings.celery_task_acks_late,

    # Time limits - Prevent hanging tasks
    task_time_limit=settings.celery_task_time_limit,

    # Result backend - Store results for status tracking
    task_ignore_result=False,
    result_expires=3600,

    # Worker settings
    worker_concurrency=settings.celery_worker_concurrency,

    # Connection settings for better reliability
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    worker_cancel_long_running_tasks_on_connection_loss=True,

# Task routing
task_routes = {
    "backend.tasks.file_processing.process_document_task": {
        "queue": "file_processing"
    },
    "backend.tasks.data_indexing.index_project_task": {
        "queue": "default"
    },
    "backend.tasks.process_workflow.process_and_index_workflow": {
        "queue": "file_processing"
    },
    "backend.tasks.process_workflow.push_after_process_task": {
        "queue": "default"
    },
    "backend.tasks.maintenance.clean_celery_executions_table": {
        "queue": "default"
    },
    "backend.tasks.telegram_outbox.deliver_pending_messages": {
        "queue": "default"
    },
    "backend.tasks.telegram_query.generate_bot_reply": {
        "queue": "default"
    },
    
},


    beat_schedule={
        "cleanup-old-task-records": {
            "task": "backend.tasks.maintenance.clean_celery_executions_table",
            "schedule": 24*3600,  # every 24 hours
            "args": (),
        },
        "deliver-pending-telegram-messages": {
            "task": "backend.tasks.telegram_outbox.deliver_pending_messages",
            "schedule": settings.telegram_outbox_poll_interval_seconds,
            "args": (),
        },
        "cleanup-expired-telegram-raw-payloads": {
            "task": "backend.tasks.maintenance.clean_expired_telegram_raw_payloads",
            "schedule": settings.telegram_raw_payload_cleanup_interval_seconds,
            "args": (),
        },
    },

    timezone="UTC",
)

celery_app.conf.task_default_queue = "default"
