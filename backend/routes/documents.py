"""
Document Routes.
API endpoints for document management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.database import get_db
from backend.controllers.document_controller import DocumentController
from backend.tasks.file_processing import process_document_task
from backend.celery_app import celery_app
from backend.tasks.process_workflow import process_and_index_workflow
router = APIRouter(tags=["Documents"])


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


# Routes
@router.post("/projects/{project_id}/documents", response_model=AssetResponse, status_code=201)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
,
    document_controller: DocumentController = Depends(DocumentController)
):
    """
    Upload document to project.
    Document will be processed in background via Celery.
    """
    try:
        # Read file
        file_content = await file.read()
        file_size = len(file_content)

        # Upload document
        asset = await document_controller.upload_document(
            db=db,
            project_id=project_id,
            file_content=file_content,
            filename=file.filename,
            file_size=file_size
        )

        # Dispatch processing to Celery worker
        process_document_task.delay(asset_id=asset.id)

        return asset

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/documents", response_model=List[AssetResponse])
async def list_project_documents(
    project_id: int,
    db: AsyncSession = Depends(get_db)
,
    document_controller: DocumentController = Depends(DocumentController)
):
    """List all documents in project."""
    try:
        documents = await document_controller.list_project_documents(
            db=db,
            project_id=project_id
        )
        return documents
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documents/{asset_id}", response_model=AssetResponse)
async def get_document(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
,
    document_controller: DocumentController = Depends(DocumentController)
):
    """Get document by ID."""
    try:
        document = await document_controller.get_document(db=db, asset_id=asset_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/{asset_id}/process")
async def process_document(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
,
    document_controller: DocumentController = Depends(DocumentController)
):
    """Manually trigger document processing via Celery."""
    try:
        # Verify asset exists
        document = await document_controller.get_document(db=db, asset_id=asset_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Dispatch to Celery
        task = process_document_task.delay(asset_id=asset_id)

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
    db: AsyncSession = Depends(get_db)
,
    document_controller: DocumentController = Depends(DocumentController)
):
    """Delete document."""
    try:
        deleted = await document_controller.delete_document(db=db, asset_id=asset_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Check the status of a Celery background task."""
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
