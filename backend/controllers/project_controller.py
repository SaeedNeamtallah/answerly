"""
Project Controller.
Business logic for project management.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Project, Asset, Chunk
from backend.services.file_service import FileService
from datetime import datetime
from fastapi import Depends
import logging

logger = logging.getLogger(__name__)


class ProjectController:
    """Controller for project operations."""
    
    def __init__(self, file_service: FileService = Depends(FileService)):
        """Initialize project controller."""
        self.file_service = file_service
    
    async def create_project_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a new project.
        
        Args:
            db: Database session
            user_id: Owner user ID
            name: Project name
            description: Optional description
            metadata: Optional metadata
            
        Returns:
            Created project
        """
        try:
            project = Project(
                user_id=user_id,
                name=name,
                description=description,
                extra_metadata=metadata or {}
            )
            
            db.add(project)
            await db.commit()
            await db.refresh(project)
            
            logger.info(f"Created project: {project.id} - {project.name} (user_id={user_id})")
            return project
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating project: {str(e)}")
            raise
    
    async def get_user_project(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int
    ) -> Optional[Project]:
        """
        Get project by ID.
        
        Args:
            db: Database session
            user_id: Owner user ID
            project_id: Project ID
            
        Returns:
            Project or None
        """
        try:
            stmt = select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
            result = await db.execute(stmt)
            project = result.scalar_one_or_none()
            
            return project
            
        except Exception as e:
            logger.error(f"Error getting project: {str(e)}")
            raise
    
    async def get_user_projects(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        List all projects.
        
        Args:
            db: Database session
            user_id: Owner user ID
            skip: Number of projects to skip
            limit: Maximum number of projects to return
            
        Returns:
            List of projects
        """
        try:
            from sqlalchemy import func
            count_stmt = select(func.count()).select_from(Project).where(Project.user_id == user_id)
            count_result = await db.execute(count_stmt)
            total_count = count_result.scalar()
            
            stmt = (
                select(Project)
                .where(Project.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(Project.created_at.desc())
            )
            result = await db.execute(stmt)
            projects = result.scalars().all()
            
            return list(projects), total_count
            
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            raise
    
    async def update_user_project(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Project]:
        """
        Update project.
        
        Args:
            db: Database session
            user_id: Owner user ID
            project_id: Project ID
            name: Optional new name
            description: Optional new description
            metadata: Optional new metadata
            
        Returns:
            Updated project or None
        """
        try:
            project = await self.get_user_project(db, user_id, project_id)
            if not project:
                return None
            
            if name is not None:
                project.name = name
            if description is not None:
                project.description = description
            if metadata is not None:
                project.extra_metadata = metadata
            
            project.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(project)
            
            logger.info(f"Updated project: {project_id} (user_id={user_id})")
            return project
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating project: {str(e)}")
            raise
    
    async def delete_user_project(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int
    ) -> bool:
        """
        Delete project and all associated data.
        
        Args:
            db: Database session
            user_id: Owner user ID
            project_id: Project ID
            
        Returns:
            True if deleted successfully
        """
        try:
            # Delete files from storage
            await self.file_service.delete_project_files(project_id)
            
            # Delete only user-owned project (cascade handles assets/chunks)
            stmt = delete(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
            result = await db.execute(stmt)
            await db.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted project: {project_id} (user_id={user_id})")
            
            return deleted
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting project: {str(e)}")
            raise
    
    async def get_user_project_stats(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Get project statistics.
        
        Args:
            db: Database session
            user_id: Owner user ID
            project_id: Project ID
            
        Returns:
            Statistics dictionary
        """
        try:
            project = await self.get_user_project(db=db, user_id=user_id, project_id=project_id)
            if not project:
                return {
                    'asset_count': 0,
                    'chunk_count': 0,
                    'total_size': 0,
                    'completed_assets': 0,
                    'processing_assets': 0,
                    'failed_assets': 0,
                }

            # Get asset count scoped to user-owned project
            asset_stmt = (
                select(Asset)
                .join(Project, Project.id == Asset.project_id)
                .where(
                    Asset.project_id == project_id,
                    Project.user_id == user_id,
                )
            )
            asset_result = await db.execute(asset_stmt)
            assets = asset_result.scalars().all()
            
            # Get chunk count scoped to user-owned project
            chunk_stmt = (
                select(Chunk)
                .join(Project, Project.id == Chunk.project_id)
                .where(
                    Chunk.project_id == project_id,
                    Project.user_id == user_id,
                )
            )
            chunk_result = await db.execute(chunk_stmt)
            chunks = chunk_result.scalars().all()
            
            return {
                'asset_count': len(assets),
                'chunk_count': len(chunks),
                'total_size': sum(a.file_size for a in assets),
                'completed_assets': sum(1 for a in assets if a.status == 'completed'),
                'processing_assets': sum(1 for a in assets if a.status == 'processing'),
                'failed_assets': sum(1 for a in assets if a.status == 'failed')
            }
            
        except Exception as e:
            logger.error(f"Error getting project stats: {str(e)}")
            raise

    # Deprecated compatibility methods.
    async def create_project(
        self,
        db: AsyncSession,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> Project:
        if user_id is None:
            raise ValueError("user_id is required. Use create_project_for_user")
        return await self.create_project_for_user(db, user_id, name, description, metadata)

    async def get_project(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[Project]:
        if user_id is None:
            raise ValueError("user_id is required. Use get_user_project")
        return await self.get_user_project(db, user_id, project_id)

    async def list_projects(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
    ) -> List[Project]:
        if user_id is None:
            raise ValueError("user_id is required. Use get_user_projects")
        return await self.get_user_projects(db, user_id, skip, limit)

    async def update_project(
        self,
        db: AsyncSession,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> Optional[Project]:
        if user_id is None:
            raise ValueError("user_id is required. Use update_user_project")
        return await self.update_user_project(db, user_id, project_id, name, description, metadata)

    async def delete_project(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        if user_id is None:
            raise ValueError("user_id is required. Use delete_user_project")
        return await self.delete_user_project(db, user_id, project_id)

    async def get_project_stats(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        if user_id is None:
            raise ValueError("user_id is required. Use get_user_project_stats")
        return await self.get_user_project_stats(db, user_id, project_id)
