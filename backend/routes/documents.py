"""
Document Routes.
API endpoints for document management.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.database import get_db
from backend.database.models import User
from backend.controllers.document_controller import DocumentController
from backend.controllers.project_controller import ProjectController
from backend.tasks.file_processing import process_document_task
from backend.celery_app import celery_app
from backend.tasks.process_workflow import process_and_index_workflow
from backend.security.auth import get_current_db_user
from backend.security.event_service import log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.security.sanitization import sanitize_filename
from backend.config import settings
from backend.utils.idempotency_manager import IdempotencyManager
from backend.utils.task_tracking import (
    get_tracked_task_record,
    reconcile_process_and_index_workflow,
    record_task_owner,
    task_belongs_to_user,
)


logger = logging.getLogger(__name__)
from backend.services.auth_service import AuthService
from backend.services.incident_management_service import IncidentManagementService

# SECURITY RULE: derive ownership from JWT only, never from request payload.
router = APIRouter(tags=["Documents"], dependencies=[Depends(get_current_db_user)])

_TERMINAL_TASK_STATUSES = {"SUCCESS", "FAILURE"}


async def _sync_tracked_task_from_celery(
    db: AsyncSession,
    *,
    task_record,
    celery_result,
):
    if task_record is None or task_record.status in _TERMINAL_TASK_STATUSES:
        return task_record
    if not celery_result.ready():
        return task_record

    manager = IdempotencyManager()
    status = "SUCCESS" if celery_result.successful() else "FAILURE"
    result = celery_result.result if celery_result.successful() else {"error": str(celery_result.result)}
    await manager.update_task_status(
        db=db,
        execution_id=task_record.execution_id,
        status=status,
        result=result,
    )
    return await get_tracked_task_record(db, task_id=str(task_record.celery_task_id))


async def _resolve_workflow_task_status(
    db: AsyncSession,
    *,
    task_record,
):
    return await reconcile_process_and_index_workflow(
        db,
        workflow_task_id=str(task_record.celery_task_id),
    )


def _build_tracked_task_response(task_id: str, task_record) -> Dict[str, Any]:
    response: Dict[str, Any] = {
        "task_id": task_id,
        "status": task_record.status,
    }
    payload = task_record.result
    if task_record.status == "SUCCESS":
        if payload is not None:
            response["result"] = payload
    elif task_record.status == "FAILURE":
        if isinstance(payload, dict) and payload.get("error"):
            response["error"] = payload["error"]
        elif payload is not None:
            response["error"] = str(payload)
    elif payload:
        response["meta"] = payload
    return response


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


def _is_malicious_upload_error(error_message: str) -> bool:
    normalized = str(error_message or "").strip().lower()
    if not normalized:
        return False

    suspicious_patterns = (
        "blocked file extension",
        "invalid content type",
        "does not match",
        "invalid docx",
        "binary content",
    )
    return any(pattern in normalized for pattern in suspicious_patterns)


async def _read_upload_with_size_limit(file: UploadFile, *, max_size_bytes: int) -> tuple[bytes, int]:
    """Read at most max_size + 1 bytes so oversized uploads are capped in memory."""
    file_content = await file.read(max_size_bytes + 1)
    return file_content, len(file_content)


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
    auth_service: AuthService = Depends(AuthService),
    incident_management_service: IncidentManagementService = Depends(IncidentManagementService),
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
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024

        file_content, file_size = await _read_upload_with_size_limit(
            file,
            max_size_bytes=max_size_bytes,
        )

        if file_size > max_size_bytes:
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
                        "reason": "file_too_large",
                        "file_size": file_size,
                        "max_size_bytes": max_size_bytes,
                    },
                }
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB",
            )

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
        await record_task_owner(
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

        if _is_malicious_upload_error(str(e)):
            await incident_management_service.block_user(
                current_user.id,
                reason=f"malicious_upload_detected:{str(e)}",
                actor="system",
                db=db,
                auth_service=auth_service,
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account blocked due to security violation",
            )

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
        await record_task_owner(
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
        await record_task_owner(
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
    if not await task_belongs_to_user(db, task_id=task_id, owner_id=current_user.id):
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

    tracked_task = await get_tracked_task_record(db, task_id=task_id)
    result = celery_app.AsyncResult(task_id)

    if tracked_task is not None:
        if tracked_task.task_name == "backend.tasks.process_workflow.process_and_index_workflow":
            tracked_task = await _resolve_workflow_task_status(db, task_record=tracked_task)
        else:
            tracked_task = await _sync_tracked_task_from_celery(
                db,
                task_record=tracked_task,
                celery_result=result,
            )

        response = _build_tracked_task_response(task_id, tracked_task)
        if "meta" not in response and tracked_task.status not in _TERMINAL_TASK_STATUSES and result.info:
            response["meta"] = result.info
        return response

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
