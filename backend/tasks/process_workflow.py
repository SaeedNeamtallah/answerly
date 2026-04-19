import asyncio
import logging

from celery import chain

from backend.celery_app import celery_app
from backend.tasks.file_processing import process_document_task
from backend.tasks.data_indexing import index_project_task
from backend.utils.idempotency_manager import IdempotencyManager
from backend.config import settings
from backend.database.connection import async_session_maker

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.process_workflow.push_after_process_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    queue="default",
)
def push_after_process_task(self, prev_task_result, project_id: int, do_reset: bool = False):
    logger.info(
        f"Starting push_after_process_task for project_id={project_id}, do_reset={do_reset}"
    )

    task = index_project_task.apply_async(
        kwargs={
            "project_id": project_id,
            "do_reset": do_reset,
        },
        queue="default",
    )

    return {
        "status": "queued",
        "project_id": project_id,
        "do_reset": do_reset,
        "index_task_id": task.id,
        "previous_task_result": prev_task_result,
    }


@celery_app.task(
    bind=True,
    name="backend.tasks.process_workflow.process_and_index_workflow",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    queue="default",
)
def process_and_index_workflow(
    self,
    asset_id: int,
    project_id: int,
    do_reset: bool = False,
):
    return asyncio.run(
        _process_and_index_workflow(
            self,
            asset_id=asset_id,
            project_id=project_id,
            do_reset=do_reset,
        )
    )


async def _process_and_index_workflow(
    task_instance,
    asset_id: int,
    project_id: int,
    do_reset: bool = False,
):
    logger.info(
        f"Starting process_and_index_workflow for asset_id={asset_id}, "
        f"project_id={project_id}, do_reset={do_reset}"
    )

    idempotency_manager = IdempotencyManager()
    task_record = None

    try:
        async with async_session_maker() as db:
            task_args = {
                "asset_id": asset_id,
                "project_id": project_id,
                "do_reset": do_reset,
            }

            task_name = "backend.tasks.process_workflow.process_and_index_workflow"

            should_execute, existing_task = await idempotency_manager.should_execute_task(
                db=db,
                task_name=task_name,
                task_args=task_args,
                task_time_limit=settings.celery_task_time_limit,
            )

            if not should_execute:
                return {
                    "status": "skipped",
                    "message": f"Task already exists with status: {existing_task.status}",
                    "existing_execution_id": existing_task.execution_id,
                    "existing_result": existing_task.result,
                }

            if existing_task:
                await idempotency_manager.update_task_status(
                    db=db,
                    execution_id=existing_task.execution_id,
                    status="PENDING",
                )
                task_record = existing_task
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

        workflow = chain(
            process_document_task.s(asset_id=asset_id).set(queue="file_processing"),
            push_after_process_task.s(project_id=project_id, do_reset=do_reset).set(queue="default"),
        )

        result = workflow.apply_async()

        final_result = {
            "status": "queued",
            "workflow_task_id": result.id,
            "asset_id": asset_id,
            "project_id": project_id,
            "do_reset": do_reset,
            "tasks": [
                "backend.tasks.file_processing.process_document_task",
                "backend.tasks.process_workflow.push_after_process_task",
            ],
        }

        async with async_session_maker() as db:
            await idempotency_manager.update_task_status(
                db=db,
                execution_id=task_record.execution_id,
                status="SUCCESS",
                result=final_result,
            )

        return final_result

    except Exception as e:
        logger.error(f"Task failed in process_and_index_workflow: {str(e)}")

        if task_record is not None:
            try:
                async with async_session_maker() as db:
                    await idempotency_manager.update_task_status(
                        db=db,
                        execution_id=task_record.execution_id,
                        status="FAILURE",
                        result={"error": str(e)},
                    )
            except Exception as update_error:
                logger.error(f"Failed to update idempotency task status: {str(update_error)}")

        raise