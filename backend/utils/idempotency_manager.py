import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CeleryTaskExecution


class IdempotencyManager:
    def create_args_hash(self, task_name: str, task_args: dict) -> str:
        combined_data = {
            **task_args,
            "task_name": task_name,
        }
        json_string = json.dumps(combined_data, sort_keys=True, default=str)
        return hashlib.sha256(json_string.encode()).hexdigest()

    async def create_task_record(
        self,
        db: AsyncSession,
        task_name: str,
        task_args: dict,
        celery_task_id: str | None = None,
    ) -> CeleryTaskExecution:
        args_hash = self.create_args_hash(task_name, task_args)

        task_record = CeleryTaskExecution(
            task_name=task_name,
            task_args_hash=args_hash,
            task_args=task_args,
            celery_task_id=celery_task_id,
            status="PENDING",
            started_at=datetime.utcnow(),
        )
        db.add(task_record)
        await db.commit()
        await db.refresh(task_record)
        return task_record

    async def update_task_status(
        self,
        db: AsyncSession,
        execution_id: int,
        status: str,
        result: dict | None = None,
    ) -> None:
        task_record = await db.get(CeleryTaskExecution, execution_id)
        if task_record:
            task_record.status = status
            if result is not None:
                task_record.result = result
            if status in ["SUCCESS", "FAILURE"]:
                task_record.completed_at = datetime.utcnow()
            await db.commit()

    async def get_existing_task(
        self,
        db: AsyncSession,
        task_name: str,
        task_args: dict,
    ) -> Optional[CeleryTaskExecution]:
        args_hash = self.create_args_hash(task_name, task_args)

        stmt = (
            select(CeleryTaskExecution)
            .where(
                CeleryTaskExecution.task_name == task_name,
                CeleryTaskExecution.task_args_hash == args_hash,
            )
            .order_by(CeleryTaskExecution.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def should_execute_task(
        self,
        db: AsyncSession,
        task_name: str,
        task_args: dict,
        task_time_limit: int = 600,
    ) -> Tuple[bool, Optional[CeleryTaskExecution]]:
        existing_task = await self.get_existing_task(db, task_name, task_args)

        if not existing_task:
            return True, None

        if existing_task.status == "SUCCESS":
            return False, existing_task

        if existing_task.status in ["PENDING", "STARTED", "RETRY"]:
            if existing_task.started_at:
                time_elapsed = (datetime.utcnow() - existing_task.started_at).total_seconds()
                if time_elapsed > (task_time_limit + 60):
                    return True, existing_task
            return False, existing_task

        return True, existing_task

    async def cleanup_old_tasks(
        self,
        db: AsyncSession,
        time_retention: int = 86400,
    ) -> int:
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_retention)

        stmt = delete(CeleryTaskExecution).where(
            CeleryTaskExecution.created_at < cutoff_time
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0