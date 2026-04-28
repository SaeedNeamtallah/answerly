"""
Celery application configuration.
Standalone entry point for Celery workers.
"""
from celery import Celery
from backend.config import settings

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.providers.llm.factory import LLMProviderFactory
from backend.providers.vectordb.factory import VectorDBProviderFactory
from backend.services.embedding_service import EmbeddingService
from backend.services.chunking_service import ChunkingService
from backend.services.document_loader import DocumentLoaderService
from backend.services.file_service import FileService

async def get_setup_utils():
    """
    Create independent DB engine and service instances for Celery worker tasks.
    """
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

# 1. تعريف الـ App بالاسم والـ Broker
celery_app = Celery(
    "ragmind",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.tasks.file_processing",
    ],
)

# 2. الإعدادات الجوهرية (Simplified)
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # ضمان وصول المهمة حتى لو السيرفر رستر
    broker_connection_retry_on_startup=True,
    
    # تحديد الطابور الافتراضي
    task_default_queue="default",
    
    # تعطيل الـ Routes المعقدة حالياً لضمان التشغيل
    task_routes=None,
    
    # إعدادات الـ Result
    task_ignore_result=False,
    result_expires=3600,
)