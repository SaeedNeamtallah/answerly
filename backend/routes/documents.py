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

# --- الأوامر الأساسية ---

@router.post("/{project_id}/documents", status_code=201)
async def upload_document(
    project_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController)
):
    try:
        # 1. قراءة الملف
        file_content = await file.read()
        file_size = len(file_content)

        # 2. حفظ في قاعدة البيانات (يرجع Asset Object)
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

        # 3. استخراج الـ ID بأمان سواء كان Object أو Dict
        # جربنا الطريقتين عشان نضمن إن الـ Task تتبعت فعلاً
        asset_id = asset.id if hasattr(asset, 'id') else asset.get('id')
        
        print(f"🚀 [DEBUG] Sending Asset ID {asset_id} to Celery Worker...")

        # 4. إرسال المهمة لـ Celery
        process_document_task.delay(asset_id=asset_id)

        return asset

    except Exception as e:
        print(f"❌ [ERROR] Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/documents", response_model=List[AssetResponse])
async def list_project_documents(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController)
):
    return await document_controller.list_project_documents(db=db, project_id=project_id)

@router.get("/documents/{asset_id}", response_model=AssetResponse)
async def get_document(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController)
):
    document = await document_controller.get_document(db=db, asset_id=asset_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.post("/documents/{asset_id}/process")
async def process_document(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController)
):
    document = await document_controller.get_document(db=db, asset_id=asset_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    task = process_document_task.delay(asset_id=asset_id)
    return {"task_id": task.id, "status": "queued", "asset_id": asset_id}

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
    db: AsyncSession = Depends(get_db),
    document_controller: DocumentController = Depends(DocumentController)
):
    deleted = await document_controller.delete_document(db=db, asset_id=asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return None

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    response = {"task_id": task_id, "status": result.status}
    if result.ready():
        response["result"] = result.result if result.successful() else str(result.result)
    return response