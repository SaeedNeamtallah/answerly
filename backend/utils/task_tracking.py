import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CeleryTaskExecution
from backend.utils.idempotency_manager import IdempotencyManager

logger = logging.getLogger(__name__)

_TASK_OWNER_MAP: dict[str, int] = {}
_WORKFLOW_TASK_NAME = "backend.tasks.process_workflow.process_and_index_workflow"


async def record_task_owner(
    db: AsyncSession,
    *,
    task_id: str,
    owner_id: int,
    task_name: str,
    task_args: dict[str, Any] | None,
) -> None:
    _TASK_OWNER_MAP[task_id] = owner_id

    payload_args = dict(task_args or {})
    payload_args["owner_id"] = owner_id

    try:
        manager = IdempotencyManager()
        await manager.upsert_task_record(
            db=db,
            task_name=task_name,
            task_args=payload_args,
            celery_task_id=task_id,
            status="PENDING",
        )
    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to persist task owner mapping",
            extra={"task_id": task_id, "owner_id": owner_id},
        )


async def get_tracked_task_record(
    db: AsyncSession,
    *,
    task_id: str,
):
    manager = IdempotencyManager()
    return await manager.get_task_by_celery_id(db, task_id)


async def task_belongs_to_user(
    db: AsyncSession,
    *,
    task_id: str,
    owner_id: int,
) -> bool:
    cached_owner = _TASK_OWNER_MAP.get(task_id)
    if cached_owner is not None:
        return cached_owner == owner_id

    try:
        task_record = await get_tracked_task_record(db, task_id=task_id)
    except Exception:
        logger.exception("Failed to load task owner mapping", extra={"task_id": task_id})
        return False

    if not task_record or not isinstance(task_record.task_args, dict):
        return False

    db_owner_id = task_record.task_args.get("owner_id")
    try:
        normalized_owner_id = int(db_owner_id)
    except (TypeError, ValueError):
        return False

    if normalized_owner_id == owner_id:
        _TASK_OWNER_MAP[task_id] = owner_id
        return True

    return False


async def reconcile_process_and_index_workflow(
    db: AsyncSession,
    *,
    workflow_task_id: str,
) -> CeleryTaskExecution | None:
    manager = IdempotencyManager()
    workflow_task = await manager.get_task_by_celery_id(db, workflow_task_id)
    if workflow_task is None or workflow_task.task_name != _WORKFLOW_TASK_NAME:
        return workflow_task

    payload = dict(workflow_task.result or {})
    process_task_id = payload.get("process_task_id")
    index_task_id = payload.get("index_task_id")

    if not process_task_id and not index_task_id:
        return workflow_task

    component_tasks: dict[str, Any] = {}
    first_error: str | None = None
    all_success = True

    for label, child_task_id in (("process", process_task_id), ("index", index_task_id)):
        if not child_task_id:
            all_success = False
            continue

        child_task = await manager.get_task_by_celery_id(db, child_task_id)
        child_status = child_task.status if child_task is not None else "PENDING"
        child_payload = child_task.result if child_task is not None else None

        snapshot: dict[str, Any] = {
            "task_id": child_task_id,
            "status": child_status,
        }

        if child_status == "SUCCESS":
            if child_payload is not None:
                snapshot["result"] = child_payload
        else:
            all_success = False
            if child_status == "FAILURE":
                error_message = (
                    child_payload.get("error")
                    if isinstance(child_payload, dict)
                    else str(child_payload)
                )
                snapshot["error"] = error_message
                if first_error is None:
                    first_error = error_message

        component_tasks[label] = snapshot

    payload["component_tasks"] = component_tasks

    if first_error is not None:
        payload["status"] = "failed"
        payload["error"] = first_error
        await manager.update_task_status(
            db=db,
            execution_id=workflow_task.execution_id,
            status="FAILURE",
            result=payload,
        )
        return await manager.get_task_by_celery_id(db, workflow_task_id)

    if all_success and component_tasks:
        payload["status"] = "completed"
        await manager.update_task_status(
            db=db,
            execution_id=workflow_task.execution_id,
            status="SUCCESS",
            result=payload,
        )
        return await manager.get_task_by_celery_id(db, workflow_task_id)

    payload["status"] = "running"
    payload["stage"] = (
        "indexing"
        if component_tasks.get("process", {}).get("status") == "SUCCESS"
        else "processing"
    )
    workflow_task.status = "STARTED"
    workflow_task.result = payload
    await db.commit()
    await db.refresh(workflow_task)
    return workflow_task
