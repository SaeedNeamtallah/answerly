"""
Celery application configuration.
Standalone entry point for Celery workers, separate from FastAPI main.py.
"""
from celery import Celery
from typing import Optional, Tuple

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

_setup_utils_cache: Optional[SetupUtils] = None


def _build_setup_utils() -> SetupUtils:
    """Create shared DB/session/service instances for the current Celery worker process."""
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
    Return shared DB engine, session, and service instances for the current worker.
    Initialized lazily once per Celery worker process.

    Returns a tuple of (db_engine, async_session_maker, document_loader,
                        chunking_service, embedding_service, vector_db, file_service)
    """
    global _setup_utils_cache
    if _setup_utils_cache is None:
        _setup_utils_cache = _build_setup_utils()
    return _setup_utils_cache


# Create Celery application instance
celery_app = Celery(
    "ragmind",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.tasks.file_processing",
        "backend.tasks.data_indexing",
        "backend.tasks.process_workflow",
        "backend.tasks.maintenance",
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
        "queue": "data_indexing"
    },
    "backend.tasks.process_workflow.process_and_index_workflow": {
        "queue": "file_processing"
    },
    "backend.tasks.process_workflow.push_after_process_task": {
        "queue": "data_indexing"
    },
    "backend.tasks.maintenance.clean_celery_executions_table": {
        "queue": "default"
    },
    
},


    beat_schedule={
        "cleanup-old-task-records": {
            "task": "backend.tasks.maintenance.clean_celery_executions_table",
            "schedule": 24*3600,  # every 24 hours
            "args": (),
        }
    },

    timezone="UTC",
)

celery_app.conf.task_default_queue = "default"
