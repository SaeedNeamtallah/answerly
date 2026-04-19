"""
Project Routes.
API endpoints for project management.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.controllers.project_controller import ProjectController
from backend.tasks.data_indexing import index_project_task
from backend.database import get_db
from backend.database.models import User
from backend.security.auth import get_current_db_user
from backend.security.event_service import log_event
from backend.security.sanitization import sanitize_metadata, sanitize_optional_text, sanitize_project_name
from backend.security.security_event import SecurityEventType, SecuritySeverity

# SECURITY RULE: never trust client ownership fields; all access is scoped by JWT user.
router = APIRouter(prefix="/projects", tags=["Projects"], dependencies=[Depends(get_current_db_user)])


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectIndexRequest(BaseModel):
    do_reset: bool = False


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    extra_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedProjectsResponse(BaseModel):
    items: List[ProjectResponse]
    total_count: int


class ProjectStatsResponse(BaseModel):
    project: ProjectResponse
    stats: Dict[str, Any]


def _log_project_denied(*, user_id: int, project_id: int, action: str, message: str) -> None:
    log_event(
        {
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": user_id,
            "message": message,
            "metadata": {"project_id": project_id, "action": action},
        }
    )


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Create a new project."""
    try:
        clean_name = sanitize_project_name(project_data.name)
        if not clean_name:
            raise HTTPException(status_code=400, detail="Project name cannot be empty")

        clean_description = sanitize_optional_text(project_data.description, max_length=4000)
        clean_metadata = sanitize_metadata(project_data.metadata)

        project = await project_controller.create_project(
            db=db,
            owner_id=current_user.id,
            name=clean_name,
            description=clean_description,
            metadata=clean_metadata,
        )
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedProjectsResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    project_controller: ProjectController = Depends(ProjectController),
):
    """List all projects."""
    try:
        projects, total_count = await project_controller.list_projects(
            db=db,
            owner_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        return {"items": projects, "total_count": total_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Get project by ID."""
    try:
        project = await project_controller.get_project(
            db=db,
            project_id=project_id,
            owner_id=current_user.id,
        )
        if not project:
            _log_project_denied(
                user_id=current_user.id,
                project_id=project_id,
                action="get_project",
                message="Project access denied",
            )
            raise HTTPException(status_code=403, detail="Forbidden")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/index")
async def index_project(
    project_id: int,
    payload: ProjectIndexRequest,
    db: AsyncSession = Depends(get_db),
    project_controller: ProjectController = Depends(ProjectController)
):
    """Trigger project-level indexing via Celery."""
    try:
        project = await project_controller.get_project(db=db, project_id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # task = index_project_task.delay(
        #     project_id=project_id,
        #     do_reset=payload.do_reset
        # )

        task = index_project_task.apply_async(
            kwargs={
                "project_id": project_id,
                "do_reset": payload.do_reset
            },
            queue="data_indexing"
        )


        return {
            "task_id": task.id,
            "status": "queued",
            "project_id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Get project statistics."""
    try:
        project = await project_controller.get_project(
            db=db,
            project_id=project_id,
            owner_id=current_user.id,
        )
        if not project:
            _log_project_denied(
                user_id=current_user.id,
                project_id=project_id,
                action="get_project_stats",
                message="Project stats access denied",
            )
            raise HTTPException(status_code=403, detail="Forbidden")

        stats = await project_controller.get_project_stats(
            db=db,
            project_id=project_id,
            owner_id=current_user.id,
        )

        return {
            "project": project,
            "stats": stats,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Update project."""
    try:
        existing_project = await project_controller.get_project(
            db=db,
            project_id=project_id,
            owner_id=current_user.id,
        )
        if not existing_project:
            _log_project_denied(
                user_id=current_user.id,
                project_id=project_id,
                action="update_project",
                message="Project update denied",
            )
            raise HTTPException(status_code=403, detail="Forbidden")

        clean_name = None
        if project_data.name is not None:
            clean_name = sanitize_project_name(project_data.name)
            if not clean_name:
                raise HTTPException(status_code=400, detail="Project name cannot be empty")

        clean_description = sanitize_optional_text(project_data.description, max_length=4000)
        clean_metadata = sanitize_metadata(project_data.metadata)

        project = await project_controller.update_project(
            db=db,
            project_id=project_id,
            owner_id=current_user.id,
            name=clean_name,
            description=clean_description,
            metadata=clean_metadata,
        )
        if not project:
            _log_project_denied(
                user_id=current_user.id,
                project_id=project_id,
                action="update_project_post_check",
                message="Project update denied after ownership check",
            )
            raise HTTPException(status_code=403, detail="Forbidden")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    project_controller: ProjectController = Depends(ProjectController),
):
    """Delete project and all associated data."""
    try:
        deleted = await project_controller.delete_project(
            db=db,
            project_id=project_id,
            owner_id=current_user.id,
        )
        if not deleted:
            _log_project_denied(
                user_id=current_user.id,
                project_id=project_id,
                action="delete_project",
                message="Project delete denied",
            )
            raise HTTPException(status_code=403, detail="Forbidden")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
