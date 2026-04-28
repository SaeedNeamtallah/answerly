"""
Document Controller.
Business logic for document upload and processing.
"""
from typing import Optional, List, Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import Asset, Chunk, Project
from backend.services.file_service import FileService
from backend.runtime_config import get_runtime_value
from backend.config import settings
from backend.providers.vectordb.factory import VectorDBProviderFactory
from datetime import datetime
from fastapi import Depends
import logging

# إعداد الـ Logger
logger = logging.getLogger(__name__)

class DocumentController:
    """Controller for document operations."""
    
    def __init__(self, file_service: FileService = Depends(FileService)):
        """Initialize document controller."""
        self.file_service = file_service
        # Lazy imports لسرعة التشغيل وتجنب الـ circular-import
        from backend.services.document_loader import DocumentLoaderService
        from backend.services.chunking_service import ChunkingService
        from backend.services.embedding_service import EmbeddingService

        self.document_loader = DocumentLoaderService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.vector_db = VectorDBProviderFactory.create_provider()

    def _as_dict(self, asset: Asset) -> Dict[str, Any]:
        """محول يدوي للـ Asset عشان نضمن إن الـ JSON يرجع صح لـ Swagger"""
        return {
            "id": asset.id,
            "project_id": asset.project_id,
            "filename": asset.filename,
            "original_filename": asset.original_filename,
            "file_size": asset.file_size,
            "file_type": asset.file_type,
            "status": asset.status,
            "error_message": asset.error_message,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "processed_at": asset.processed_at.isoformat() if asset.processed_at else None,
            "extra_metadata": asset.extra_metadata or {}
        }

    async def upload_document(
        self,
        db: AsyncSession,
        project_id: int,
        file_content: bytes,
        filename: str,
        file_size: int
    ) -> Dict[str, Any]:
        """رفع الملف وتسجيله - تم التعديل ليرجع Dictionary"""
        try:
            # التحقق من الملف
            is_valid, error_msg = self.file_service.validate_file(filename, file_size)
            if not is_valid:
                raise ValueError(error_msg)
            
            # التأكد من وجود المشروع
            project_stmt = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_stmt)
            project = project_result.scalar_one_or_none()
            if not project:
                raise ValueError(f"Project not found: {project_id}")
            
            # حفظ الملف في الـ Storage
            unique_filename, file_path = await self.file_service.save_upload_file(
                file_content=file_content,
                filename=filename,
                project_id=project_id
            )
            
            from pathlib import Path
            file_type = Path(filename).suffix.lstrip('.')
            
            # إنشاء السجل
            asset = Asset(
                project_id=project_id,
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                status="uploaded",
                extra_metadata={"progress": 0, "stage": "uploaded"}
            )
            
            db.add(asset)
            await db.commit()
            await db.refresh(asset)
            
            logger.info(f"Successfully uploaded: {asset.id}")
            # بنرجع Dictionary عشان Swagger ميهنجش بـ 500
            return self._as_dict(asset)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Upload failed: {str(e)}")
            raise

    async def process_document(self, asset_id: int, **_kw) -> bool:
        """Process document (Background task)."""
        from backend.database.connection import async_session_maker
        async with async_session_maker() as db:
            return await self._process_document_impl(db, asset_id)

    async def _process_document_impl(self, db: AsyncSession, asset_id: int) -> bool:
        """العملية المعقدة: extraction -> chunking -> embedding -> vector db"""
        try:
            asset_stmt = select(Asset).where(Asset.id == asset_id)
            asset_result = await db.execute(asset_stmt)
            asset = asset_result.scalar_one_or_none()
            
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")
            
            asset.status = "processing"
            await db.commit()
            
            try:
                # 1. Extract
                text = await self.document_loader.load_document(asset.file_path)
                
                # 2. Chunking
                chunks_data = await self.chunking_service.chunk_document(
                    text=text,
                    document_name=asset.original_filename,
                    additional_metadata={'asset_id': asset.id}
                )
                
                chunk_records = [
                    Chunk(
                        project_id=asset.project_id,
                        asset_id=asset.id,
                        content=c['content'],
                        chunk_index=i,
                        extra_metadata=c['metadata']
                    ) for i, c in enumerate(chunks_data)
                ]

                db.add_all(chunk_records)
                await db.flush()

                # 3. Embedding
                total_chunks = len(chunk_records)
                texts = [c.content for c in chunk_records]

                async def on_embed_batch(processed: int, total: int) -> None:
                    # تحديث التقدم بدون ما نهنج السيستم
                    pass 

                embeddings = await self.embedding_service.generate_embeddings(
                    texts, on_batch=on_embed_batch
                )
                
                # 4. Vector Storage (Qdrant)
                chunk_ids = [c.id for c in chunk_records]
                await self.vector_db.add_vectors(
                    collection_name=f"project_{asset.project_id}",
                    vectors=embeddings,
                    ids=chunk_ids,
                    metadata=[{"asset_id": asset.id} for _ in chunk_ids]
                )
                
                asset.status = "completed"
                asset.processed_at = datetime.utcnow()
                await db.commit()
                return True
                
            except Exception as e:
                asset.status = "failed"
                asset.error_message = str(e)
                await db.commit()
                raise
                
        except Exception as e:
            logger.error(f"Process failed: {str(e)}")
            raise

    async def _update_asset_progress(self, db: AsyncSession, asset: Asset, **kwargs) -> None:
        """تحديث بيانات الـ progress بشكل آمن"""
        meta = dict(asset.extra_metadata or {})
        meta.update(kwargs)
        asset.extra_metadata = meta
        flag_modified(asset, "extra_metadata")
        await db.commit()

    async def list_project_documents(self, db: AsyncSession, project_id: int) -> List[Dict[str, Any]]:
        """قائمة الملفات"""
        stmt = select(Asset).where(Asset.project_id == project_id).order_by(Asset.created_at.desc())
        result = await db.execute(stmt)
        return [self._as_dict(a) for a in result.scalars().all()]