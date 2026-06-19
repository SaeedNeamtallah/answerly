## 10. Input Sanitization

### Explanation

The project uses centralized input sanitization. It is applied to usernames, project names, descriptions, query text, metadata, filenames, incident notes, reasons, bot profile names, and runtime configuration values. Sanitization removes control characters, script blocks, and HTML tags, normalizes line endings, trims and truncates text, collapses excessive whitespace, and limits metadata sizes.

### Path

`backend/security/sanitization.py`

```python
def sanitize_text(
    value: Any,
    *,
    max_length: int = 4000,
    strip_html: bool = True,
    allow_newlines: bool = True,
) -> str:
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

    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text[:max_length]
```

---
