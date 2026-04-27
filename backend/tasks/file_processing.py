"""
Celery task for document processing.
Extracts text, chunks, embeds, and stores vectors in the background.
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm.attributes import flag_modified

from backend.celery_app import celery_app, get_setup_utils
from backend.config import settings
from backend.database.models import Asset, Chunk, Project
from backend.runtime_config import get_runtime_value
from backend.utils.idempotency_manager import IdempotencyManager
from backend.utils.task_tracking import reconcile_process_and_index_workflow

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.file_processing.process_document_task",
)
def process_document_task(self, asset_id: int):
    return asyncio.run(_process_document(self, asset_id))


async def _cleanup_stale_asset_vectors(
    db,
    *,
    asset: Asset,
    vector_db,
    session_maker,
) -> None:
    filter_dict = {
        "asset_id": asset.id,
        "project_id": asset.project_id,
    }
    try:
        await vector_db.delete_vectors(
            collection_name=f"project_{asset.project_id}",
            filter_dict=filter_dict,
            session_maker=session_maker,
        )
    except Exception as cleanup_error:
        logger.warning(
            "Failed to delete stale vectors for asset %s: %s",
            asset.id,
            cleanup_error,
        )

    await db.execute(delete(Chunk).where(Chunk.asset_id == asset.id))
    await db.commit()


async def _reconcile_parent_workflow_if_needed(db, *, task_record) -> None:
    if task_record is None or not isinstance(task_record.task_args, dict):
        return

    workflow_task_id = task_record.task_args.get("workflow_task_id")
    if not workflow_task_id:
        return

    await reconcile_process_and_index_workflow(
        db,
        workflow_task_id=str(workflow_task_id),
    )


async def _process_document(task_instance, asset_id: int):
    db_engine = None
    session_maker = None
    task_record = None

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
            task_args = {
                "asset_id": asset_id,
            }
            task_name = "backend.tasks.file_processing.process_document_task"

            should_execute, existing_task = await idempotency_manager.should_execute_task(
                db=db,
                task_name=task_name,
                task_args=task_args,
                task_time_limit=settings.celery_task_time_limit,
                celery_task_id=task_instance.request.id,
            )

            current_task = await idempotency_manager.get_task_by_celery_id(
                db=db,
                celery_task_id=task_instance.request.id,
            )

            if not should_execute:
                if current_task is None:
                    current_task = await idempotency_manager.create_task_record(
                        db=db,
                        task_name=task_name,
                        task_args=task_args,
                        celery_task_id=task_instance.request.id,
                    )
                await idempotency_manager.update_task_status(
                    db=db,
                    execution_id=current_task.execution_id,
                    status="SUCCESS",
                    result={
                        "status": "skipped",
                        "message": f"Task already exists with status: {existing_task.status}",
                        "existing_execution_id": existing_task.execution_id,
                        "existing_result": existing_task.result,
                    },
                )
                await _reconcile_parent_workflow_if_needed(db, task_record=current_task)
                return {
                    "status": "skipped",
                    "message": f"Task already exists with status: {existing_task.status}",
                    "existing_execution_id": existing_task.execution_id,
                    "existing_result": existing_task.result,
                }

            if current_task is not None:
                task_record = current_task
            else:
                task_record = await idempotency_manager.create_task_record(
                    db=db,
                    task_name=task_name,
                    task_args=task_args,
                    celery_task_id=task_instance.request.id,
                )

            await idempotency_manager.update_task_status(
                db=db,
                execution_id=task_record.execution_id,
                status="STARTED",
            )

            asset_stmt = select(Asset).where(Asset.id == asset_id)
            asset_result = await db.execute(asset_stmt)
            asset = asset_result.scalar_one_or_none()

            if asset is None:

                error_result = {"error": f"Asset not found: {asset_id}"}
                await idempotency_manager.update_task_status(
                    db=db,
                    execution_id=task_record.execution_id,
                    status="FAILURE",
                    result=error_result,
                )
                await _reconcile_parent_workflow_if_needed(db, task_record=task_record)
                task_instance.update_state(state="FAILURE", meta=error_result)
                raise ValueError(f"Asset not found: {asset_id}")

            # SECURITY RULE: owner_id is persisted in vector payload for strict isolation.
            owner_stmt = select(Project.owner_id).where(Project.id == asset.project_id)
            owner_result = await db.execute(owner_stmt)
            owner_id = owner_result.scalar_one_or_none()
            if owner_id is None:
                raise ValueError(f"Project owner not found for project {asset.project_id}")

            task_record = await idempotency_manager.upsert_task_record(
                db=db,
                task_name=task_name,
                task_args={
                    **task_args,
                    "owner_id": owner_id,
                },
                celery_task_id=task_instance.request.id,
                status=None,
            )

            if asset.status == "completed":
                final_result = {
                    "asset_id": asset.id,
                    "status": "completed",
                    "total_chunks": asset.extra_metadata.get("total_chunks", 0) if asset.extra_metadata else 0,
                    "message": "Document already processed",
                }
                await idempotency_manager.update_task_status(
                    db=db,
                    execution_id=task_record.execution_id,
                    status="SUCCESS",
                    result=final_result,
                )
                await _reconcile_parent_workflow_if_needed(db, task_record=task_record)
                return final_result

            await _cleanup_stale_asset_vectors(
                db,
                asset=asset,
                vector_db=vector_db,
                session_maker=session_maker,
            )

            # Mark as processing

            asset.status = "processing"
            asset.error_message = None
            await db.commit()

            try:
                logger.info(f"Extracting text from {asset.original_filename}")
                text = await document_loader.load_document(asset.file_path)

                logger.info(f"Chunking text ({len(text)} characters)")
                await _update_progress(db, asset, "chunking", 0, 0, 0)

                chunk_strategy = get_runtime_value("chunk_strategy", settings.chunk_strategy)
                chunk_size = get_runtime_value("chunk_size", settings.chunk_size)
                chunk_overlap = get_runtime_value("chunk_overlap", settings.chunk_overlap)
                parent_chunk_size = get_runtime_value("parent_chunk_size", settings.parent_chunk_size)
                parent_chunk_overlap = get_runtime_value("parent_chunk_overlap", settings.parent_chunk_overlap)

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

                logger.info(f"Generating embeddings for {total_chunks} chunks")
                texts = [c.content for c in chunk_records]
                embeddings = await embedding_service.generate_embeddings(texts)
                if not embeddings:
                    raise ValueError("No embeddings generated for processed document chunks")
                embedding_dimension = len(embeddings[0]) if embeddings else 0

                chunk_ids = [c.id for c in chunk_records]
                vector_metadata = [
                    {
                        "owner_id": owner_id,
                        "asset_id": c.asset_id,
                        "project_id": c.project_id,
                        "chunk_index": c.chunk_index,
                    }
                    for c in chunk_records
                ]

                await _update_progress(db, asset, "indexing", total_chunks, total_chunks, 95)

                await vector_db.create_collection(
                    collection_name=f"project_{asset.project_id}",
                    dimension=embedding_dimension,
                    session_maker=session_maker,
                )

                await vector_db.add_vectors(
                    collection_name=f"project_{asset.project_id}",
                    vectors=embeddings,
                    ids=chunk_ids,
                    metadata=vector_metadata,
                    session_maker=session_maker,
                )

                asset.status = "completed"
                asset.error_message = None
                asset.processed_at = datetime.utcnow()

                meta = dict(asset.extra_metadata or {})
                meta["total_chunks"] = total_chunks
                asset.extra_metadata = meta
                flag_modified(asset, "extra_metadata")

                await _update_progress(db, asset, "completed", total_chunks, total_chunks, 100)
                await db.commit()

                final_result = {
                    "asset_id": asset.id,
                    "status": "completed",
                    "total_chunks": total_chunks,
                }

                await idempotency_manager.update_task_status(
                    db=db,
                    execution_id=task_record.execution_id,
                    status="SUCCESS",
                    result=final_result,
                )
                await _reconcile_parent_workflow_if_needed(db, task_record=task_record)

                logger.info(f"Completed processing document {asset.id}: {total_chunks} chunks created")
                return final_result

            except Exception as e:
                await _cleanup_stale_asset_vectors(
                    db,
                    asset=asset,
                    vector_db=vector_db,
                    session_maker=session_maker,
                )
                asset.status = "failed"
                asset.error_message = str(e)
                await db.commit()

                await idempotency_manager.update_task_status(
                    db=db,
                    execution_id=task_record.execution_id,
                    status="FAILURE",
                    result={"error": str(e)},
                )
                await _reconcile_parent_workflow_if_needed(db, task_record=task_record)
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


async def _update_progress(db, asset: Asset, stage: str, processed: int, total: int, progress: int) -> None:
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
