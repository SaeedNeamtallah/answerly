## 14. Document Ownership Isolation

### Explanation

Document routes enforce ownership isolation. Uploading requires an owned project, and listing, reading, processing, indexing, deleting documents, and checking task status all require ownership verification. Unauthorized document or task access is rejected and logged.

### Path

`backend/controllers/document_controller.py`

```python
# SECURITY RULE: all user-facing document queries must be scoped by JWT owner_id.

async def upload_document(
    self,
    db: AsyncSession,
    owner_id: int,
    project_id: int,
    file_content: bytes,
    filename: str,
    file_size: int,
    content_type: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Asset:
    project_stmt = select(Project).where(
        Project.id == project_id,
        Project.owner_id == owner_id,
    )
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if not project:
        raise ValueError("Forbidden")
```

---
