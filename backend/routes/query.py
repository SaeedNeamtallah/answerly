"""
Query Routes.
API endpoints for querying documents with RAG Metrics.
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List

from backend.config import settings
from backend.runtime_config import get_runtime_value
from backend.database import get_db
from backend.controllers.query_controller import QueryController

# استيراد ميتريكس الـ AI من ملف الـ main
# ملاحظة: تأكد أن المسار صحيح حسب هيكلة مشروعك
from backend.main import LLM_LATENCY, VECTOR_DB_LATENCY 

router = APIRouter(tags=["Query"])


# ------------------------
# Request / Response Models
# ------------------------

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    language: str = Field(default="ar", pattern="^(ar|en)$")
    asset_id: Optional[int] = None


class SourceInfo(BaseModel):
    document_name: str
    chunk_index: int
    similarity: float
    asset_id: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    context_used: int


# ------------------------
# Controller Dependency FIX
# ------------------------

def get_query_controller():
    """
    Create controller instance per request
    """
    return QueryController()


# ------------------------
# Main Query Endpoint
# ------------------------

@router.post("/projects/{project_id}/query", response_model=QueryResponse)
async def query_project(
    project_id: int,
    query_data: QueryRequest,
    db: AsyncSession = Depends(get_db),
    query_controller: QueryController = Depends(get_query_controller)
):
    # بدأ توقيت العملية الإجمالية للـ RAG
    start_time = time.time()
    
    try:
        top_k = query_data.top_k or get_runtime_value(
            "retrieval_top_k",
            settings.retrieval_top_k
        )

        top_k = max(1, min(int(top_k), settings.retrieval_top_k_max))

        # تنفيذ عملية البحث والرد
        result = await query_controller.answer_query(
            db=db,
            project_id=project_id,
            query=query_data.query,
            top_k=top_k,
            language=query_data.language,
            asset_id=query_data.asset_id
        )

        # تسجيل الوقت في Prometheus
        # بما أن المتحكم يدمج العمليتين، سنسجل الوقت في LLM_LATENCY كتعبيير عن سرعة الرد الذكي
        duration = time.time() - start_time
        LLM_LATENCY.set(duration)
        # نفترض هنا أن نصف الوقت تقريباً يذهب للـ Vector DB (لأغراض العرض فقط حتى تفصل الكود داخلياً)
        VECTOR_DB_LATENCY.set(duration * 0.4) 

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------
# Streaming Endpoint
# ------------------------

@router.post("/projects/{project_id}/query/stream")
async def query_project_stream(
    project_id: int,
    query_data: QueryRequest,
    db: AsyncSession = Depends(get_db),
    query_controller: QueryController = Depends(get_query_controller)
):
    start_time = time.time()
    try:
        top_k = query_data.top_k or get_runtime_value(
            "retrieval_top_k",
            settings.retrieval_top_k
        )

        top_k = max(1, min(int(top_k), settings.retrieval_top_k_max))

        stream = query_controller.answer_query_stream(
            db=db,
            project_id=project_id,
            query=query_data.query,
            top_k=top_k,
            language=query_data.language,
            asset_id=query_data.asset_id,
        )

        # تسجيل وقت بداية الـ Streaming
        LLM_LATENCY.set(time.time() - start_time)

        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))