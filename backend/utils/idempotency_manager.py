import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CeleryTaskExecution


class IdempotencyManager:
    TRACKING_TASK_ARG_KEYS = frozenset(
        {
            "owner_id",
            "task_id",
            "workflow_task_id",
            "process_task_id",
            "index_task_id",
            "component_tasks",
        }
    )

    def _clone_task_args(self, task_args: dict | None) -> dict[str, Any]:
        return dict(task_args or {})

    def _get_hashable_task_args(self, task_args: dict | None) -> dict[str, Any]:
        payload = self._clone_task_args(task_args)
        return {
            key: value
            for key, value in payload.items()
            if key not in self.TRACKING_TASK_ARG_KEYS
        }

    def create_args_hash(self, task_name: str, task_args: dict | None) -> str:
        combined_data = {
            **self._get_hashable_task_args(task_args),
            "task_name": task_name,
        }
        json_string = json.dumps(combined_data, sort_keys=True, default=str)
        return hashlib.sha256(json_string.encode()).hexdigest()

    def normalize_celery_task_id(self, celery_task_id: str | UUID | None) -> UUID | None:
        if celery_task_id is None:
            return None
        if isinstance(celery_task_id, UUID):
            return celery_task_id
        try:
            return UUID(str(celery_task_id))
        except (TypeError, ValueError):
            return None

    def _merge_task_args(
        self,
        existing_task_args: dict | None,
        new_task_args: dict | None,
    ) -> dict[str, Any]:
        merged = self._clone_task_args(existing_task_args)
        for key, value in self._clone_task_args(new_task_args).items():
            if value is not None:
                merged[key] = value
        return merged

    def _merge_missing_task_args(
        self,
        primary_task_args: dict | None,
        secondary_task_args: dict | None,
    ) -> dict[str, Any]:
        merged = self._clone_task_args(primary_task_args)
        for key, value in self._clone_task_args(secondary_task_args).items():
            if key not in merged or merged.get(key) is None:
                if value is not None:
                    merged[key] = value
        return merged

    def _merge_result_payloads(
        self,
        primary_result: dict | Any | None,
        secondary_result: dict | Any | None,
    ) -> dict | Any | None:
        if primary_result is None:
            return secondary_result
        if secondary_result is None:
            return primary_result
        if isinstance(primary_result, dict) and isinstance(secondary_result, dict):
            merged = dict(primary_result)
            for key, value in secondary_result.items():
                if key not in merged or merged.get(key) is None:
                    merged[key] = value
            return merged
        return primary_result

    def _task_status_priority(self, status: str | None) -> int:
        return {
            "FAILURE": 5,
            "SUCCESS": 4,
            "STARTED": 3,
            "RETRY": 2,
            "PENDING": 1,
        }.get((status or "").upper(), 0)

    def _task_record_sort_key(self, task_record: CeleryTaskExecution) -> tuple[Any, ...]:
        zero_time = datetime.min.replace(tzinfo=timezone.utc)
        return (
            self._task_status_priority(task_record.status),
            task_record.completed_at or zero_time,
            task_record.updated_at or zero_time,
            task_record.created_at or zero_time,
            task_record.execution_id or 0,
        )

    async def _deduplicate_task_records(
        self,
        db: AsyncSession,
        task_records: list[CeleryTaskExecution],
    ) -> Optional[CeleryTaskExecution]:
        if not task_records:
            return None
        if len(task_records) == 1:
            return task_records[0]

        ordered_records = sorted(
            task_records,
            key=self._task_record_sort_key,
            reverse=True,
        )
        canonical = ordered_records[0]
        merged_task_args = self._clone_task_args(canonical.task_args)
        merged_result = canonical.result
        earliest_started_at = canonical.started_at
        latest_completed_at = canonical.completed_at

        for duplicate in ordered_records[1:]:
            merged_task_args = self._merge_missing_task_args(
                merged_task_args,
                duplicate.task_args,
            )
            merged_result = self._merge_result_payloads(merged_result, duplicate.result)

            if earliest_started_at is None or (
                duplicate.started_at is not None and duplicate.started_at < earliest_started_at
            ):
                earliest_started_at = duplicate.started_at
            if latest_completed_at is None or (
                duplicate.completed_at is not None and duplicate.completed_at > latest_completed_at
            ):
                latest_completed_at = duplicate.completed_at

        canonical.task_args = merged_task_args or None
        canonical.task_args_hash = self.create_args_hash(canonical.task_name, merged_task_args)
        canonical.result = merged_result
        canonical.started_at = earliest_started_at
        canonical.completed_at = (
            latest_completed_at if canonical.status in {"SUCCESS", "FAILURE"} else None
        )

        duplicate_execution_ids = [
            record.execution_id
            for record in ordered_records[1:]
            if record.execution_id is not None
        ]
        if duplicate_execution_ids:
            await db.execute(
                delete(CeleryTaskExecution).where(
                    CeleryTaskExecution.execution_id.in_(duplicate_execution_ids)
                )
            )
        await db.commit()
        await db.refresh(canonical)
        return canonical

    async def deduplicate_task_records(
        self,
        db: AsyncSession,
    ) -> int:
        duplicate_id_stmt = (
            select(CeleryTaskExecution.celery_task_id)
            .where(CeleryTaskExecution.celery_task_id.is_not(None))
            .group_by(CeleryTaskExecution.celery_task_id)
            .having(func.count(CeleryTaskExecution.execution_id) > 1)
        )
        duplicate_id_rows = await db.execute(duplicate_id_stmt)
        duplicate_task_ids = [row[0] for row in duplicate_id_rows.all()]

        deleted_count = 0
        for duplicate_task_id in duplicate_task_ids:
            task_stmt = (
                select(CeleryTaskExecution)
                .where(CeleryTaskExecution.celery_task_id == duplicate_task_id)
                .order_by(CeleryTaskExecution.created_at.desc(), CeleryTaskExecution.execution_id.desc())
            )
            task_rows = await db.execute(task_stmt)
            task_records = list(task_rows.scalars().all())
            if len(task_records) <= 1:
                continue
            deleted_count += len(task_records) - 1
            await self._deduplicate_task_records(db, task_records)

        return deleted_count

    async def get_task_by_celery_id(
        self,
        db: AsyncSession,
        celery_task_id: str | UUID | None,
    ) -> Optional[CeleryTaskExecution]:
        task_uuid = self.normalize_celery_task_id(celery_task_id)
        if task_uuid is None:
            return None

        stmt = (
            select(CeleryTaskExecution)
            .where(CeleryTaskExecution.celery_task_id == task_uuid)
            .order_by(CeleryTaskExecution.created_at.desc(), CeleryTaskExecution.execution_id.desc())
        )
        result = await db.execute(stmt)
        task_records = list(result.scalars().all())
        if not task_records:
            return None
        return await self._deduplicate_task_records(db, task_records)

    async def upsert_task_record(
        self,
        db: AsyncSession,
        task_name: str,
        task_args: dict | None,
        celery_task_id: str | UUID | None = None,
        status: str | None = "PENDING",
    ) -> CeleryTaskExecution:
        task_uuid = self.normalize_celery_task_id(celery_task_id)
        payload_args = self._clone_task_args(task_args)
        if task_uuid is not None:
            payload_args.setdefault("task_id", str(task_uuid))

        args_hash = self.create_args_hash(task_name, payload_args)
        task_record = await self.get_task_by_celery_id(db, task_uuid)

        if task_record is None:
            task_record = CeleryTaskExecution(
                task_name=task_name,
                task_args_hash=args_hash,
                task_args=payload_args,
                celery_task_id=task_uuid,
                status=status or "PENDING",
                started_at=datetime.utcnow(),
            )
            db.add(task_record)
        else:
            task_record.task_name = task_name
            task_record.task_args_hash = args_hash
            task_record.task_args = self._merge_task_args(task_record.task_args, payload_args)
            if status is not None:
                task_record.status = status
            if task_record.started_at is None:
                task_record.started_at = datetime.utcnow()

        await db.commit()
        await db.refresh(task_record)
        return task_record

    async def create_task_record(
        self,
        db: AsyncSession,
        task_name: str,
        task_args: dict | None,
        celery_task_id: str | UUID | None = None,
    ) -> CeleryTaskExecution:
        return await self.upsert_task_record(
            db=db,
            task_name=task_name,
            task_args=task_args,
            celery_task_id=celery_task_id,
            status="PENDING",
        )

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
            else:
                task_record.completed_at = None
            await db.commit()

    async def get_existing_task(
        self,
        db: AsyncSession,
        task_name: str,
        task_args: dict | None,
        exclude_celery_task_id: str | UUID | None = None,
    ) -> Optional[CeleryTaskExecution]:
        args_hash = self.create_args_hash(task_name, task_args)
        excluded_task_uuid = self.normalize_celery_task_id(exclude_celery_task_id)

        stmt = (
            select(CeleryTaskExecution)
            .where(
                CeleryTaskExecution.task_name == task_name,
                CeleryTaskExecution.task_args_hash == args_hash,
            )
            .order_by(CeleryTaskExecution.created_at.desc())
        )
        if excluded_task_uuid is not None:
            stmt = stmt.where(
                or_(
                    CeleryTaskExecution.celery_task_id.is_(None),
                    CeleryTaskExecution.celery_task_id != excluded_task_uuid,
                )
            )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def should_execute_task(
        self,
        db: AsyncSession,
        task_name: str,
        task_args: dict | None,
        task_time_limit: int = 600,
        celery_task_id: str | UUID | None = None,
    ) -> Tuple[bool, Optional[CeleryTaskExecution]]:
        existing_task = await self.get_existing_task(
            db,
            task_name,
            task_args,
            exclude_celery_task_id=celery_task_id,
        )

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
        deduplicated_count = await self.deduplicate_task_records(db)
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_retention)

        stmt = delete(CeleryTaskExecution).where(
            CeleryTaskExecution.created_at < cutoff_time
        )
        result = await db.execute(stmt)
        await db.commit()
        return deduplicated_count + (result.rowcount or 0)
