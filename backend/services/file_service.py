"""
File Management Service.
Handles file storage with project-based organization.
"""
import uuid
import shutil
import io
import zipfile
from pathlib import Path
from typing import Optional
from backend.config import settings
from backend.security.event_service import log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.security.sanitization import sanitize_filename
import logging
import aiofiles

logger = logging.getLogger(__name__)


class FileService:
    """Service for managing uploaded files."""
    
    def __init__(self):
        """Initialize file service."""
        self.upload_dir = Path(settings.upload_dir)
        self.max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        self.magic_scan_bytes = max(512, settings.security_upload_max_scan_bytes)
        self.blocked_extensions = {".php", ".exe", ".js", ".sh"}
        self.allowed_mime_types = {
            ".pdf": {"application/pdf"},
            ".txt": {"text/plain", "application/octet-stream"},
            ".docx": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/zip",
                "application/octet-stream",
            },
        }
        
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
        safe_name = sanitize_filename(original_filename)
        file_ext = Path(safe_name).suffix.lower()
        unique_id = uuid.uuid4().hex[:8]
        file_name = Path(safe_name).stem[:120] or "upload"
        return f"{file_name}_{unique_id}{file_ext}"

    def _validate_magic_signature(self, extension: str, file_content: bytes) -> tuple[bool, Optional[str]]:
        """Validate that file bytes look like the declared extension."""
        if not settings.security_upload_validate_magic:
            return True, None

        sample = file_content[: self.magic_scan_bytes]

        if extension == ".pdf":
            if not sample.startswith(b"%PDF-"):
                return False, "File content does not match PDF format"
            return True, None

        if extension == ".docx":
            if not sample.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
                return False, "File content does not match DOCX format"
            try:
                with zipfile.ZipFile(io.BytesIO(file_content)) as archive:
                    names = set(archive.namelist())
                    if "[Content_Types].xml" not in names:
                        return False, "Invalid DOCX structure"
                    if not any(name.startswith("word/") for name in names):
                        return False, "Invalid DOCX structure"
            except zipfile.BadZipFile:
                return False, "Invalid DOCX file"
            return True, None

        if extension == ".txt":
            if b"\x00" in sample:
                return False, "Text file appears to contain binary content"
            return True, None

        return True, None
    
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
    
    def validate_file(
        self,
        filename: str,
        file_size: int,
        file_content: Optional[bytes] = None,
        content_type: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded file.

        Args:
            filename: File name
            file_size: File size in bytes
            file_content: Optional file bytes for signature checks
            content_type: Optional MIME type from client upload

        Returns:
            Tuple of (is_valid, error_message)
        """
        from backend.services.document_loader import DocumentLoaderService

        def _log_blocked(reason: str) -> None:
            log_event(
                {
                    "event_type": SecurityEventType.FILE_UPLOAD_BLOCKED,
                    "severity": SecuritySeverity.HIGH,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "message": "Blocked malicious file upload",
                    "metadata": {
                        "filename": safe_filename,
                        "reason": reason,
                        "content_type": content_type,
                        "file_size": int(file_size or 0),
                    },
                }
            )

        safe_filename = sanitize_filename(filename)

        if file_size <= 0:
            _log_blocked("empty_file")
            return False, "File is empty"

        file_path = Path(safe_filename)
        file_ext = file_path.suffix.lower()
        file_suffixes = {suffix.lower() for suffix in file_path.suffixes}

        blocked_match = sorted(file_suffixes.intersection(self.blocked_extensions))
        if blocked_match:
            _log_blocked(f"blocked_extension:{blocked_match[0]}")
            return False, f"Blocked file extension detected: {blocked_match[0]}"

        if not DocumentLoaderService.is_supported_file(safe_filename):
            _log_blocked("unsupported_extension")
            return False, f"Unsupported file type. Supported: {DocumentLoaderService.get_supported_extensions()}"

        if file_size > self.max_size_bytes:
            _log_blocked("file_too_large")
            return False, f"File too large. Maximum size is {settings.max_file_size_mb}MB"

        normalized_type = (content_type or "").lower().split(";")[0].strip()
        if not normalized_type:
            _log_blocked("missing_content_type")
            return False, "Missing file content type"

        allowed_types = self.allowed_mime_types.get(file_ext, set())
        if allowed_types and normalized_type not in allowed_types:
            if not (file_ext == ".txt" and normalized_type.startswith("text/")):
                _log_blocked("invalid_content_type")
                return False, f"Invalid content type '{content_type}' for {file_ext}"

        if file_content is not None:
            valid_signature, signature_error = self._validate_magic_signature(file_ext, file_content)
            if not valid_signature:
                _log_blocked("invalid_file_signature")
                return False, signature_error
        
        return True, None
