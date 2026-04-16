"""
Query Routes.
API endpoints for querying documents.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from backend.config import settings
from backend.runtime_config import get_runtime_value
from backend.database import get_db
from backend.controllers.query_controller import QueryController
from backend.dependencies import CurrentUser, get_current_user

router = APIRouter(tags=["Query"])


# Request/Response Models
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


# Routes
@router.post("/projects/{project_id}/query", response_model=QueryResponse)
async def query_project(
    project_id: int,
    query_data: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    query_controller: QueryController = Depends(QueryController)
):
    """
    Ask a question about project documents.
    Returns AI-generated answer with sources.
    """
    try:
        result = await query_controller.answer_query(
            db=db,
            user_id=current_user.user_id,
            project_id=project_id,
            query=query_data.query,
            top_k=max(
                1,
                min(
                    int(
                        query_data.top_k
                        if query_data.top_k is not None
                        else get_runtime_value("retrieval_top_k", settings.retrieval_top_k)
                    ),
                    settings.retrieval_top_k_max
                )
            ),
            language=query_data.language,
            asset_id=query_data.asset_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/query/stream")
async def query_project_stream(
    project_id: int,
    query_data: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    query_controller: QueryController = Depends(QueryController)
):
    """
    Stream an AI-generated answer via Server-Sent Events.
    Emits: sources event, then token events, then [DONE].
    """
    top_k = max(
        1,
        min(
            int(
                query_data.top_k
                if query_data.top_k is not None
                else get_runtime_value("retrieval_top_k", settings.retrieval_top_k)
            ),
            settings.retrieval_top_k_max,
        ),
    )

    return StreamingResponse(
        query_controller.answer_query_stream(
            db=db,
            user_id=current_user.user_id,
            project_id=project_id,
            query=query_data.query,
            top_k=top_k,
            language=query_data.language,
            asset_id=query_data.asset_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
