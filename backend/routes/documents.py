"""
Document Routes.
API endpoints for document management.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.database import get_db
from backend.database.models import CeleryTaskExecution, User
from backend.controllers.document_controller import DocumentController
from backend.controllers.project_controller import ProjectController
from backend.tasks.file_processing import process_document_task
from backend.celery_app import celery_app
from backend.tasks.process_workflow import process_and_index_workflow
from backend.security.auth import get_current_db_user
from backend.security.event_service import log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.security.sanitization import sanitize_filename


logger = logging.getLogger(__name__)

# SECURITY RULE: derive ownership from JWT only, never from request payload.
router = APIRouter(tags=["Documents"], dependencies=[Depends(get_current_db_user)])

# Best-effort ownership binding for process task status checks.
_TASK_OWNER_MAP: Dict[str, int] = {}


async def _record_task_owner(
    db: AsyncSession,
    *,
    task_id: str,
    owner_id: int,
    task_name: str,
    task_args: Dict[str, Any],
) -> None:
    """Persist task ownership so status checks survive API process restarts."""
    _TASK_OWNER_MAP[task_id] = owner_id

    try:
        task_uuid = UUID(str(task_id))
    except ValueError:
        logger.warning("Task id '%s' is not a UUID; skipping persistent owner mapping", task_id)
        return

    payload_args: Dict[str, Any] = dict(task_args or {})
    payload_args["owner_id"] = owner_id
    payload_args["task_id"] = str(task_id)

    try:
        existing_stmt = (
            select(CeleryTaskExecution)
            .where(CeleryTaskExecution.celery_task_id == task_uuid)
            .order_by(CeleryTaskExecution.created_at.desc())
        )
        existing_record = (await db.execute(existing_stmt)).scalars().first()

        if existing_record is None:
            db.add(
                CeleryTaskExecution(
                    task_name=task_name,
                    task_args_hash=f"owner:{owner_id}:{task_id}",
                    celery_task_id=task_uuid,
                    status="PENDING",
                    task_args=payload_args,
                    started_at=datetime.utcnow(),
                )
            )
        else:
            existing_record.task_name = task_name
            existing_record.task_args = payload_args
            if not existing_record.status:
                existing_record.status = "PENDING"
            if existing_record.started_at is None:
                existing_record.started_at = datetime.utcnow()

        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("Failed to persist task owner mapping", extra={"task_id": task_id, "owner_id": owner_id})


async def _task_belongs_to_user(
    db: AsyncSession,
    *,
    task_id: str,
    owner_id: int,
) -> bool:
    """Check task ownership from cache first, then durable DB mapping."""
    cached_owner = _TASK_OWNER_MAP.get(task_id)
    if cached_owner is not None:
        return cached_owner == owner_id

    try:
        task_uuid = UUID(str(task_id))
    except ValueError:
        return False

    try:
        stmt = (
            select(CeleryTaskExecution.task_args)
            .where(CeleryTaskExecution.celery_task_id == task_uuid)
            .order_by(CeleryTaskExecution.created_at.desc())
        )
        task_args = (await db.execute(stmt)).scalars().first() or {}
    except Exception:
        logger.exception("Failed to load task owner mapping", extra={"task_id": task_id})
        return False

    db_owner_id = task_args.get("owner_id")
    try:
        normalized_db_owner_id = int(db_owner_id)
    except (TypeError, ValueError):
        return False

    if normalized_db_owner_id == owner_id:
        _TASK_OWNER_MAP[task_id] = owner_id
        return True

    return False


# Response Models
class AssetResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    extra_metadata: Dict[str, Any]
    
class ProcessAndIndexRequest(BaseModel):
    do_reset: bool = False

    class Config:
        from_attributes = True


async def _ensure_owned_project(
    db: AsyncSession,
    project_id: int,
    current_user: User,
    project_controller: ProjectController,
):
    """Ensure project exists and belongs to the current authenticated user."""
    project = await project_controller.get_project(
        db=db,
        project_id=project_id,
        owner_id=current_user.id,
    )
    if not project:
        log_event(
            {
                "event_type": SecurityEventType.AUTHZ_DENIED,
                "severity": SecuritySeverity.HIGH,
                "user_id": current_user.id,
                "message": "Project document access denied",
                "metadata": {"project_id": project_id, "action": "ensure_owned_project"},
            }
        )
        raise HTTPException(status_code=403, detail="Forbidden")
    return project


async def _ensure_owned_document(
    db: AsyncSession,
    asset_id: int,
    current_user: User,
    document_controller: DocumentController,
    project_controller: ProjectController,
):
    """Ensure document exists and its parent project belongs to the current user."""
    document = await document_controller.get_document(
        db=db,
        asset_id=asset_id,
        owner_id=current_user.id,
    )
    if not document:
        log_event(
            {
                "event_type": SecurityEventType.AUTHZ_DENIED,
                "severity": SecuritySeverity.HIGH,
                "user_id": current_user.id,
                "message": "Document access denied",
                "metadata": {"asset_id": asset_id, "action": "ensure_owned_document"},
            }
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    await _ensure_owned_project(
        db=db,
        project_id=document.project_id,
        current_user=current_user,
        project_controller=project_controller,
    )
    return document


# Routes
@router.post("/projects/{project_id}/documents", response_model=AssetResponse, status_code=201)
async def upload_document(
    project_id: int,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController),
    project_controller: ProjectController = Depends(ProjectController),
):
    """
    Upload document to project.
    Document will be processed in background via Celery.
    """
    try:
        client_ip = request.client.host if request and request.client else None

        await _ensure_owned_project(
            db=db,
            project_id=project_id,
            current_user=current_user,
            project_controller=project_controller,
        )

        incoming_name = sanitize_filename(file.filename or "upload.bin")

        # Read file
        file_content = await file.read()
        file_size = len(file_content)
        if file_size <= 0:
            log_event(
                {
                    "event_type": SecurityEventType.FILE_UPLOAD_BLOCKED,
                    "severity": SecuritySeverity.HIGH,
                    "user_id": current_user.id,
                    "ip_address": client_ip,
                    "message": "Blocked malicious file upload",
                    "metadata": {
                        "project_id": project_id,
                        "filename": incoming_name,
                        "reason": "empty_file",
                    },
                }
            )
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Upload document
        asset = await document_controller.upload_document(
            db=db,
            owner_id=current_user.id,
            project_id=project_id,
            file_content=file_content,
            filename=incoming_name,
            file_size=file_size,
            content_type=file.content_type,
            ip_address=client_ip,
        )

        # Dispatch processing to Celery worker
        task = process_document_task.delay(asset_id=asset.id)
        await _record_task_owner(
            db,
            task_id=task.id,
            owner_id=current_user.id,
            task_name="backend.tasks.file_processing.process_document_task",
            task_args={"asset_id": asset.id},
        )

        return asset

    except HTTPException:
        raise
    except ValueError as e:
        if str(e) == "Forbidden":
            raise HTTPException(status_code=403, detail="Forbidden")
        raise HTTPException(status_code=400, detail="Invalid document upload request")
    except Exception:
        logger.exception("Unexpected error while uploading document")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/projects/{project_id}/documents", response_model=List[AssetResponse])
async def list_project_documents(
    project_id: int,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController),
    project_controller: ProjectController = Depends(ProjectController),
):
    """List all documents in project."""
    try:
        await _ensure_owned_project(
            db=db,
            project_id=project_id,
            current_user=current_user,
            project_controller=project_controller,
        )

        documents = await document_controller.list_project_documents(
            db=db,
            project_id=project_id,
            owner_id=current_user.id,
        )
        return documents
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while listing project documents")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{asset_id}", response_model=AssetResponse)
async def get_document(
    asset_id: int,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Get document by ID."""
    try:
        document = await _ensure_owned_document(
            db=db,
            asset_id=asset_id,
            current_user=current_user,
            document_controller=document_controller,
            project_controller=project_controller,
        )
        return document
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while fetching document")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{asset_id}/process")
async def process_document(
    asset_id: int,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Manually trigger document processing via Celery."""
    try:
        await _ensure_owned_document(
            db=db,
            asset_id=asset_id,
            current_user=current_user,
            document_controller=document_controller,
            project_controller=project_controller,
        )

        # Dispatch to Celery
        task = process_document_task.delay(asset_id=asset_id)
        await _record_task_owner(
            db,
            task_id=task.id,
            owner_id=current_user.id,
            task_name="backend.tasks.file_processing.process_document_task",
            task_args={"asset_id": asset_id},
        )

        return {"task_id": task.id, "status": "queued", "asset_id": asset_id}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while queueing document processing")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{asset_id}/process-and-index")
async def process_and_index_document(
    asset_id: int,
    payload: ProcessAndIndexRequest,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController),
    project_controller: ProjectController = Depends(ProjectController),
):
    """
    Trigger a workflow that:
    1) processes the document
    2) then triggers project-level indexing
    """
    try:
        document = await _ensure_owned_document(
            db=db,
            asset_id=asset_id,
            current_user=current_user,
            document_controller=document_controller,
            project_controller=project_controller,
        )

        task = process_and_index_workflow.apply_async(
            kwargs={
                "asset_id": asset_id,
                "project_id": document.project_id,
                "do_reset": payload.do_reset,
            },
            queue="file_processing",
        )
        await _record_task_owner(
            db,
            task_id=task.id,
            owner_id=current_user.id,
            task_name="backend.tasks.process_workflow.process_and_index_workflow",
            task_args={
                "asset_id": asset_id,
                "project_id": document.project_id,
                "do_reset": payload.do_reset,
            },
        )

        return {
            "workflow_task_id": task.id,
            "status": "queued",
            "asset_id": asset_id,
            "project_id": document.project_id,
            "do_reset": payload.do_reset,
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while queueing process-and-index workflow")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/documents/{asset_id}", status_code=204)
async def delete_document(
    asset_id: int,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Delete document."""
    try:
        await _ensure_owned_document(
            db=db,
            asset_id=asset_id,
            current_user=current_user,
            document_controller=document_controller,
            project_controller=project_controller,
        )

        deleted = await document_controller.delete_document(
            db=db,
            asset_id=asset_id,
            owner_id=current_user.id,
        )
        if not deleted:
            raise HTTPException(status_code=403, detail="Forbidden")
        return None
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while deleting document")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    """Check the status of a Celery background task."""
    if not await _task_belongs_to_user(db, task_id=task_id, owner_id=current_user.id):
        log_event(
            {
                "event_type": SecurityEventType.AUTHZ_DENIED,
                "severity": SecuritySeverity.HIGH,
                "user_id": current_user.id,
                "message": "Task status access denied",
                "metadata": {"task_id": task_id, "action": "get_task_status"},
            }
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": result.status,
    }
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)
    elif result.info:
        response["meta"] = result.info
    return response
