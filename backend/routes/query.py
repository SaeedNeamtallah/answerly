"""
Query Routes.
API endpoints for querying documents.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from functools import lru_cache
from backend.config import settings
from backend.runtime_config import get_runtime_value
from backend.database import get_db
from backend.database.models import User
from backend.controllers.project_controller import ProjectController
from backend.controllers.document_controller import DocumentController
from backend.controllers.query_controller import QueryController, QueryInfrastructureError
from backend.security.auth import get_current_db_user
from backend.security.event_service import log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.security.sanitization import sanitize_text


logger = logging.getLogger(__name__)

# SECURITY RULE: query access is always scoped to JWT current_user ownership.
router = APIRouter(tags=["Query"], dependencies=[Depends(get_current_db_user)])


@lru_cache(maxsize=1)
def get_query_controller() -> QueryController:
    return QueryController()


@lru_cache(maxsize=1)
def get_project_controller() -> ProjectController:
    return ProjectController()


@lru_cache(maxsize=1)
def get_document_controller() -> DocumentController:
    return DocumentController()


# Request/Response Models
class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


async def _ensure_query_scope(
    db: AsyncSession,
    project_id: int,
    current_user: User,
    project_controller: ProjectController,
    document_controller: DocumentController,
    asset_id: Optional[int],
) -> None:
    """Validate that project/document scope belongs to the authenticated user."""
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
                "message": "Query access denied: project ownership mismatch",
                "metadata": {"project_id": project_id, "asset_id": asset_id},
            }
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    if asset_id is not None:
        document = await document_controller.get_document(
            db=db,
            asset_id=asset_id,
            owner_id=current_user.id,
        )
        if not document or document.project_id != project_id:
            log_event(
                {
                    "event_type": SecurityEventType.AUTHZ_DENIED,
                    "severity": SecuritySeverity.HIGH,
                    "user_id": current_user.id,
                    "message": "Query access denied: document scope mismatch",
                    "metadata": {"project_id": project_id, "asset_id": asset_id},
                }
            )
            raise HTTPException(status_code=403, detail="Forbidden")


# Routes
@router.post("/projects/{project_id}/query", response_model=QueryResponse)
async def query_project(
    project_id: int,
    query_data: QueryRequest,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    query_controller: QueryController = Depends(get_query_controller),
    project_controller: ProjectController = Depends(get_project_controller),
    document_controller: DocumentController = Depends(get_document_controller),
):
    """
    Ask a question about project documents.
    Returns AI-generated answer with sources.
    """
    try:
        await _ensure_query_scope(
            db=db,
            project_id=project_id,
            current_user=current_user,
            project_controller=project_controller,
            document_controller=document_controller,
            asset_id=query_data.asset_id,
        )

        clean_query = sanitize_text(query_data.query, max_length=4000, strip_html=True, allow_newlines=True)
        if not clean_query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        result = await query_controller.answer_query(
            db=db,
            owner_id=current_user.id,
            project_id=project_id,
            query=clean_query,
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

    except HTTPException:
        raise
    except QueryInfrastructureError:
        logger.exception("Query infrastructure failure while executing project query")
        raise HTTPException(status_code=503, detail="Query service unavailable")
    except Exception:
        logger.exception("Unexpected error while executing query")
        raise HTTPException(status_code=500, detail="Internal server error")
