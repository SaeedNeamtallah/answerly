import asyncio
import logging
import time

from sqlalchemy import select

from backend.celery_app import celery_app, get_setup_utils
from backend.config import settings
from backend.database.models import Project, Chunk
from backend.monitoring.metrics import CELERY_TASK_DURATION_SECONDS
from backend.providers.llm.exceptions import provider_error_payload
from backend.utils.idempotency_manager import IdempotencyManager
from backend.utils.task_tracking import reconcile_process_and_index_workflow

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.data_indexing.index_project_task",
    queue="default",
    # autoretry_for=(Exception,),
    # retry_kwargs={"max_retries": 3, "countdown": 60},
)
def index_project_task(self, project_id: int, do_reset: bool = False):
    return asyncio.run(_index_project(self, project_id, do_reset))


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


async def _index_project(task_instance, project_id: int, do_reset: bool):
    task_start = time.perf_counter()
    task_status = "failure"
    task_record = None
    session_maker = None
    try:
        (
            _db_engine,
            session_maker,
            document_loader,
            chunking_service,
            embedding_service,
            vector_db,
            file_service,
        ) = await get_setup_utils()

        async with session_maker() as db:
            idempotency_manager = IdempotencyManager()
            task_args = {
                "project_id": project_id,
                "do_reset": do_reset,
            }
            task_name = "backend.tasks.data_indexing.index_project_task"

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
                task_status = "success"
                return {
                    "status": "skipped",
                    "message": f"Task already exists with status: {existing_task.status}",
                    "existing_execution_id": existing_task.execution_id,
                    "existing_result": existing_task.result,
                }

            if current_task is None:
                task_record = await idempotency_manager.create_task_record(
                    db=db,
                    task_name=task_name,
                    task_args=task_args,
                    celery_task_id=task_instance.request.id,
                )
            else:
                task_record = current_task

            await idempotency_manager.update_task_status(
                db=db,
                execution_id=task_record.execution_id,
                status="STARTED",
            )

            # 1) Check project exists
            project_stmt = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_stmt)
            project = project_result.scalar_one_or_none()

            if project is None:
                # task_instance.update_state(
                #     state="FAILURE",
                #     meta={"error": f"Project not found: {project_id}"}
                # )
                raise ValueError(f"Project not found: {project_id}")

            # 2) Get all chunks for project
            chunk_stmt = (
                select(Chunk)
                .where(Chunk.project_id == project_id)
                .order_by(Chunk.asset_id, Chunk.chunk_index)
            )
            chunk_result = await db.execute(chunk_stmt)
            chunks = list(chunk_result.scalars().all())

            if not chunks:
                # task_instance.update_state(
                #     state="FAILURE",
                #     meta={"error": f"No chunks found for project: {project_id}"}
                # )
                raise ValueError(f"No chunks found for project: {project_id}")

            task_record = await idempotency_manager.upsert_task_record(
                db=db,
                task_name=task_name,
                task_args={
                    **task_args,
                    "owner_id": project.owner_id,
                },
                celery_task_id=task_instance.request.id,
                status=None,
            )

            # 3) Create/reset collection if needed
            collection_name = f"project_{project_id}"

            # use embedding size from one generated vector later if provider doesn't expose size
            texts = [chunk.content for chunk in chunks]

            logger.info(f"Generating embeddings for project {project_id} ({len(texts)} chunks)")
            embeddings = await embedding_service.generate_embeddings(texts)
            if not embeddings:
                raise ValueError(f"No embeddings generated for project: {project_id}")

            dimension = len(embeddings[0]) if embeddings else 0

            await vector_db.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                do_reset=do_reset,
                session_maker=session_maker,
            )

            # 4) Add vectors
            chunk_ids = [chunk.id for chunk in chunks]
            vector_metadata = [
                {
                    "owner_id": project.owner_id,
                    "asset_id": chunk.asset_id,
                    "project_id": chunk.project_id,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ]

            await vector_db.add_vectors(
                collection_name=collection_name,
                vectors=embeddings,
                ids=chunk_ids,
                metadata=vector_metadata,
                session_maker=session_maker,
            )

            logger.info(
                f"Completed project indexing for project {project_id}: "
                f"{len(chunks)} chunks indexed"
            )

            final_result = {
                "project_id": project_id,
                "status": "completed",
                "total_chunks": len(chunks),
                "do_reset": do_reset,
            }
            await idempotency_manager.update_task_status(
                db=db,
                execution_id=task_record.execution_id,
                status="SUCCESS",
                result=final_result,
            )
            await _reconcile_parent_workflow_if_needed(db, task_record=task_record)
            task_status = "success"
            return final_result

    except Exception as e:
        logger.error("Task failed for project_id=%s: %s", project_id, provider_error_payload(e)["message"])
        if task_record is not None and session_maker is not None:
            try:
                async with session_maker() as db:
                    idempotency_manager = IdempotencyManager()
                    await idempotency_manager.update_task_status(
                        db=db,
                        execution_id=task_record.execution_id,
                        status="FAILURE",
                        result=provider_error_payload(e),
                    )
                    await _reconcile_parent_workflow_if_needed(db, task_record=task_record)
            except Exception as update_error:
                logger.error(f"Failed to update index task status: {str(update_error)}")
        raise
    finally:
        CELERY_TASK_DURATION_SECONDS.labels(
            task_name="index_project_task",
            status=task_status,
        ).observe(time.perf_counter() - task_start)
