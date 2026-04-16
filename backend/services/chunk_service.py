"""Chunk Service.
User-scoped chunk operations for tenant-safe access.
"""
from __future__ import annotations

from typing import List, Dict, Any

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Chunk, Project


class ChunkService:
    """Service for chunk operations with strict user isolation."""

    async def get_user_project_chunks_paginated(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> List[Chunk]:
        """Return paginated chunks for a user-owned project only."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1

        offset = (page - 1) * page_size

        stmt = (
            select(Chunk)
            .join(Project, Project.id == Chunk.project_id)
            .where(
                Chunk.project_id == project_id,
                Project.user_id == user_id,
            )
            .order_by(Chunk.id.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_project_chunk_count(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int,
    ) -> int:
        """Count chunks for a user-owned project only."""
        stmt = (
            select(func.count(Chunk.id))
            .join(Project, Project.id == Chunk.project_id)
            .where(
                Chunk.project_id == project_id,
                Project.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        return int(result.scalar() or 0)

    async def delete_user_project_chunks(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int,
    ) -> int:
        """Delete chunks for a user-owned project and return deleted count."""
        ownership_stmt = select(Project.id).where(
            Project.id == project_id,
            Project.user_id == user_id,
        )
        ownership = await db.execute(ownership_stmt)
        if ownership.scalar_one_or_none() is None:
            return 0

        stmt = delete(Chunk).where(Chunk.project_id == project_id)
        result = await db.execute(stmt)
        await db.commit()
        return int(result.rowcount or 0)
