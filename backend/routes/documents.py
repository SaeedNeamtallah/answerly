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
    
    class Config:
        from_attributes = True

# --- الأوامر الأساسية ---

@router.post("/{project_id}/documents", status_code=201)
async def upload_document(
    project_id: int,
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
            project_id=project_id,
            file_content=file_content,
            filename=file.filename,
            file_size=file_size
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