"""
Document Routes.
API endpoints for document management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
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

# SECURITY RULE: derive ownership from JWT only, never from request payload.
router = APIRouter(tags=["Documents"], dependencies=[Depends(get_current_db_user)])

# Best-effort ownership binding for process task status checks.
_TASK_OWNER_MAP: Dict[str, int] = {}


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
        _TASK_OWNER_MAP[task.id] = current_user.id

        return asset

    except HTTPException:
        raise
    except ValueError as e:
        if str(e) == "Forbidden":
            raise HTTPException(status_code=403, detail="Forbidden")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        _TASK_OWNER_MAP[task.id] = current_user.id

        return {"task_id": task.id, "status": "queued", "asset_id": asset_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{asset_id}/process-and-index")
async def process_and_index_document(
    asset_id: int,
    payload: ProcessAndIndexRequest,
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController)
):
    """
    Trigger a workflow that:
    1) processes the document
    2) then triggers project-level indexing
    """
    try:
        document = await document_controller.get_document(db=db, asset_id=asset_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        task = process_and_index_workflow.apply_async(
            kwargs={
                "asset_id": asset_id,
                "project_id": document.project_id,
                "do_reset": payload.do_reset,
            },
            queue="file_processing",
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_db_user),
):
    """Check the status of a Celery background task."""
    if _TASK_OWNER_MAP.get(task_id) != current_user.id:
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
