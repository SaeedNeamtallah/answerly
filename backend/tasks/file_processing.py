"""
Celery task for document processing.
Extracts text, chunks, embeds, and stores vectors in the background.
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from backend.celery_app import celery_app, get_setup_utils
from backend.config import settings
from backend.database.models import Asset, Chunk, Project
from backend.runtime_config import get_runtime_value
from backend.providers.vectordb.factory import VectorDBProviderFactory

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.file_processing.process_document_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def process_document_task(self, asset_id: int):
    """
    Celery entry point. Runs the async processing logic
    inside a new event loop (Celery workers are synchronous).
    """
    asyncio.run(_process_document(self, asset_id))


async def _process_document(task_instance, asset_id: int):
    """
    Full document processing pipeline executed inside a Celery worker.
    Opens its own DB engine and cleans up in `finally`.
    """
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
            # Fetch asset
            asset_stmt = select(Asset).where(Asset.id == asset_id)
            asset_result = await db.execute(asset_stmt)
            asset = asset_result.scalar_one_or_none()

            if asset is None:
                task_instance.update_state(
                    state="FAILURE",
                    meta={"error": f"Asset not found: {asset_id}"},
                )
                raise ValueError(f"Asset not found: {asset_id}")

            # Mark as processing
            asset.status = "processing"
            await db.commit()

            try:
                # 1. Extract text
                logger.info(f"Extracting text from {asset.original_filename}")
                text = await document_loader.load_document(asset.file_path)

                # 2. Chunk text
                logger.info(f"Chunking text ({len(text)} characters)")
                await _update_progress(db, asset, "chunking", 0, 0, 0)

                chunk_strategy = get_runtime_value(
                    "chunk_strategy", settings.chunk_strategy
                )
                chunk_size = get_runtime_value("chunk_size", settings.chunk_size)
                chunk_overlap = get_runtime_value("chunk_overlap", settings.chunk_overlap)
                parent_chunk_size = get_runtime_value(
                    "parent_chunk_size", settings.parent_chunk_size
                )
                parent_chunk_overlap = get_runtime_value(
                    "parent_chunk_overlap", settings.parent_chunk_overlap
                )

                from backend.services.chunking_service import ChunkingService as CS

                active_chunking = CS(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    parent_chunk_size=parent_chunk_size,
                    parent_chunk_overlap=parent_chunk_overlap,
                )

                chunks_data = await active_chunking.chunk_document(
                    text=text,
                    document_name=asset.original_filename,
                    additional_metadata={
                        "file_type": asset.file_type,
                        "asset_id": asset.id,
                    },
                    chunk_strategy=chunk_strategy,
                )

                # 3. Create chunk DB records
                chunk_records = []
                for i, chunk_data in enumerate(chunks_data):
                    chunk_records.append(
                        Chunk(
                            project_id=asset.project_id,
                            asset_id=asset.id,
                            content=chunk_data["content"],
                            chunk_index=i,
                            extra_metadata=chunk_data["metadata"],
                        )
                    )

                db.add_all(chunk_records)
                await db.flush()

                total_chunks = len(chunk_records)
                await _update_progress(db, asset, "embedding", 0, total_chunks, 0)

                # 4. Generate embeddings
                logger.info(f"Generating embeddings for {total_chunks} chunks")
                texts = [c.content for c in chunk_records]

                embeddings = await embedding_service.generate_embeddings(texts)

                # 5. Store vectors
                chunk_ids = [c.id for c in chunk_records]
                vector_metadata = [
                    {
                        "asset_id": c.asset_id,
                        "project_id": c.project_id,
                        "chunk_index": c.chunk_index,
                    }
                    for c in chunk_records
                ]

                await _update_progress(
                    db, asset, "indexing", total_chunks, total_chunks, 95
                )

                await vector_db.add_vectors(
                    collection_name=f"project_{asset.project_id}",
                    vectors=embeddings,
                    ids=chunk_ids,
                    metadata=vector_metadata,
                )

                # 6. Mark completed
                asset.status = "completed"
                asset.processed_at = datetime.utcnow()
                await _update_progress(
                    db, asset, "completed", total_chunks, total_chunks, 100
                )
                await db.commit()

                logger.info(
                    f"Completed processing document {asset.id}: "
                    f"{total_chunks} chunks created"
                )

                return {
                    "asset_id": asset.id,
                    "status": "completed",
                    "total_chunks": total_chunks,
                }

            except Exception as e:
                asset.status = "failed"
                asset.error_message = str(e)
                await db.commit()
                raise

    except Exception as e:
        logger.error(f"Task failed for asset_id={asset_id}: {str(e)}")
        raise

    finally:
        try:
            if db_engine:
                await db_engine.dispose()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


async def _update_progress(
    db, asset: Asset, stage: str, processed: int, total: int, progress: int
) -> None:
    """Helper to persist processing progress in asset metadata."""
    meta = dict(asset.extra_metadata or {})
    meta.update(
        {
            "stage": stage,
            "processed_chunks": int(processed),
            "total_chunks": int(total),
            "progress": int(progress),
        }
    )
    asset.extra_metadata = meta
    flag_modified(asset, "extra_metadata")
    await db.commit()
