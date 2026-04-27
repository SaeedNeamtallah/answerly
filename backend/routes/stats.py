"""
Stats Routes.
API endpoints for global statistics.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from backend.database import get_db
from backend.database.models import Project, Asset, Chunk, User
from backend.security.auth import get_current_db_user


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/")
async def get_global_stats(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_db_user),
):
    """Get global statistics."""
    try:
        row = (await db.execute(
            select(
                select(func.count(Project.id)).scalar_subquery().label('p'),
                select(func.count(Asset.id)).scalar_subquery().label('d'),
                select(func.count(Chunk.id)).scalar_subquery().label('c'),
            )
        )).one()
        return {"projects": row.p or 0, "documents": row.d or 0, "chunks": row.c or 0}
    except Exception:
        logger.exception("Unexpected error while fetching global stats")
        raise HTTPException(status_code=500, detail="Internal server error")
