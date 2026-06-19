## 11. Filename Sanitization

### Explanation

Uploaded filenames are hardened before storage. The system uses only the basename, removes control characters, replaces unsafe characters, strips leading/trailing spaces and dots, preserves the extension when possible, and falls back to `upload.bin` if the filename becomes empty. This helps prevent path traversal and unsafe filename handling.

### Path

`backend/security/sanitization.py`

```python
def sanitize_filename(filename: str, *, max_length: int = 255) -> str:
    """Sanitize user-supplied filenames to prevent path/control abuse."""
    base_name = Path(str(filename or "")).name
    base_name = _CONTROL_CHARS_RE.sub("", base_name)
    base_name = base_name.replace("\n", "").replace("\r", "").strip()
    base_name = _SAFE_FILENAME_RE.sub("_", base_name)
    base_name = _MULTI_SPACE_RE.sub(" ", base_name).strip(" .")

    if not base_name:
        return "upload.bin"

    if len(base_name) <= max_length:
        return base_name

    suffix = Path(base_name).suffix
    stem = Path(base_name).stem
    max_stem_len = max(1, max_length - len(suffix))
    return f"{stem[:max_stem_len]}{suffix}"
```

---
