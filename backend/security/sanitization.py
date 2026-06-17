"""Input sanitization helpers for API request payloads."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, Optional


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_SCRIPT_TAG_RE = re.compile(r"(?is)<\s*script[^>]*>.*?<\s*/\s*script\s*>")
_HTML_TAG_RE = re.compile(r"(?is)<[^>]+>")
_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._ -]+")

_SUSPICIOUS_PATTERNS = [
    re.compile(r"(?is)<script[^>]*>.*?</script>"),
    re.compile(r"(?i)javascript:"),
    re.compile(r"(?i)\b(onload|onerror|onmouseover|alert)\s*="),
    re.compile(r"(?i)\bUNION\s+ALL\s+SELECT\b"),
    re.compile(r"(?i)\bDROP\s+(TABLE|DATABASE)\b"),
    re.compile(r"(?i)\bOR\s+1\s*=\s*1\b"),
]

def contains_suspicious_input(value: Any) -> bool:
    """Check if the given payload matches common XSS/SQLi patterns."""
    if not isinstance(value, str):
        return False
    for pattern in _SUSPICIOUS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def sanitize_text(
    value: Any,
    *,
    max_length: int = 4000,
    strip_html: bool = True,
    allow_newlines: bool = True,
) -> str:
    """Normalize text payloads while keeping user intent intact."""
    if value is None:
        return ""

    text = str(value)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if strip_html:
        text = _SCRIPT_TAG_RE.sub("", text)
        text = _HTML_TAG_RE.sub("", text)

    if not allow_newlines:
        text = text.replace("\n", " ")

    text = _MULTI_SPACE_RE.sub(" ", text)
    text = text.strip()

    if max_length > 0 and len(text) > max_length:
        text = text[:max_length]

    if contains_suspicious_input(text):
        try:
            from backend.security.event_service import log_event
            from backend.security.security_event import SecurityEventType
            log_event({
                "event_type": SecurityEventType.SUSPICIOUS_INPUT,
                "severity": "HIGH",
                "message": "Suspicious input pattern detected during sanitization",
                "metadata": {"snippet": text[:100]}
            })
        except Exception:
            pass

    return text


def sanitize_project_name(name: str) -> str:
    """Sanitize project name without changing semantic meaning."""
    return sanitize_text(name, max_length=255, strip_html=True, allow_newlines=False)


def sanitize_optional_text(value: Optional[str], max_length: int = 4000) -> Optional[str]:
    """Sanitize optional text and preserve None values."""
    if value is None:
        return None
    return sanitize_text(value, max_length=max_length, strip_html=True, allow_newlines=True)


def sanitize_metadata(
    metadata: Optional[Dict[str, Any]],
    *,
    max_items: int = 32,
) -> Optional[Dict[str, Any]]:
    """Bound metadata keys/values to safe, compact text."""
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        return {}

    sanitized: Dict[str, Any] = {}
    for idx, (key, value) in enumerate(metadata.items()):
        if idx >= max_items:
            break

        clean_key = sanitize_text(key, max_length=64, strip_html=True, allow_newlines=False)
        if not clean_key:
            continue

        clean_value = sanitize_text(value, max_length=400, strip_html=True, allow_newlines=True)
        sanitized[clean_key] = clean_value

    return sanitized


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
