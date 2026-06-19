## 12. File Upload Security

### Explanation

File upload validation is one of the strongest security areas in the project. The system rejects empty files, enforces a maximum file size, blocks dangerous extensions such as `.php`, `.exe`, `.js`, and `.sh`, checks all suffixes to catch double-extension attacks, allows only supported document types, validates MIME/content type, and optionally validates magic bytes to confirm the real file format.

### Path

`backend/services/file_service.py`

```python
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
```

```python
def _validate_magic_signature(self, extension: str, file_content: bytes) -> tuple[bool, Optional[str]]:
    if not settings.security_upload_validate_magic:
        return True, None

    sample = file_content[: self.magic_scan_bytes]

    if extension == ".pdf":
        if not sample.startswith(b"%PDF-"):
            return False, "File content does not match PDF format"

    if extension == ".docx":
        if not sample.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            return False, "File content does not match DOCX format"

    if extension == ".txt":
        if b"\x00" in sample:
            return False, "Text file appears to contain binary content"

    return True, None
```

```python
blocked_match = sorted(file_suffixes.intersection(self.blocked_extensions))
if blocked_match:
    _log_blocked(f"blocked_extension:{blocked_match[0]}")
    return False, f"Blocked file extension detected: {blocked_match[0]}"

if file_size > self.max_size_bytes:
    _log_blocked("file_too_large")
    return False, f"File too large. Maximum size is {settings.max_file_size_mb}MB"

if file_content is not None:
    valid_signature, signature_error = self._validate_magic_signature(file_ext, file_content)
    if not valid_signature:
        _log_blocked("invalid_file_signature")
        return False, signature_error
```

---
