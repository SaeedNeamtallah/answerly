"""
File Management Service.
Handles file storage with project-based organization.
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from backend.config import settings
import logging
import aiofiles

logger = logging.getLogger(__name__)


class FileService:
    """Service for managing uploaded files."""
    
    def __init__(self):
        """Initialize file service."""
        self.upload_dir = Path(settings.upload_dir)
        self.max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"File service initialized (upload_dir={self.upload_dir})")
    
    def get_project_dir(self, project_id: int) -> Path:
        """
        Get directory path for project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Path to project directory
        """
        project_dir = self.upload_dir / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate unique filename while preserving extension.
        
        Args:
            original_filename: Original file name
            
        Returns:
            Unique filename
        """
        file_ext = Path(original_filename).suffix
        unique_id = uuid.uuid4().hex[:12]
        safe_name = Path(original_filename).stem[:50]  # Limit length
        return f"{safe_name}_{unique_id}{file_ext}"
    
    async def save_upload_file(
        self,
        file_content: bytes,
        filename: str,
        project_id: int
    ) -> tuple[str, str]:
        """
        Save uploaded file to project directory.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            project_id: Project ID
            
        Returns:
            Tuple of (unique_filename, file_path)
            
        Raises:
            ValueError: If file is too large
        """
        # Check file size
        if len(file_content) > self.max_size_bytes:
            raise ValueError(
                f"File too large ({len(file_content)} bytes). "
                f"Maximum size is {settings.max_file_size_mb}MB"
            )
        
        # Generate unique filename
        unique_filename = self.generate_unique_filename(filename)
        
        # Get project directory
        project_dir = self.get_project_dir(project_id)
        file_path = project_dir / unique_filename
        
        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"Saved file: {file_path} ({len(file_content)} bytes)")
        
        return unique_filename, str(file_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted successfully
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            raise
    
    async def delete_project_files(self, project_id: int) -> bool:
        """
        Delete all files for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if deleted successfully
        """
        try:
            project_dir = self.get_project_dir(project_id)
            if project_dir.exists():
                shutil.rmtree(project_dir)
                logger.info(f"Deleted project directory: {project_dir}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting project files: {str(e)}")
            raise
    
    def validate_file(self, filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate file before upload.
        
        Args:
            filename: File name
            file_size: File size in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        from backend.services.document_loader import DocumentLoaderService
        if not DocumentLoaderService.is_supported_file(filename):
            return False, f"Unsupported file type. Supported: {DocumentLoaderService.get_supported_extensions()}"
        
        # Check file size
        if file_size > self.max_size_bytes:
            return False, f"File too large. Maximum size is {settings.max_file_size_mb}MB"
        
        return True, None
