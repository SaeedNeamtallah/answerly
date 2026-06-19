## 13. Project Ownership Isolation

### Explanation

Project access is consistently scoped by the owner derived from the JWT-authenticated user. The system does not trust client-supplied owner IDs. Project create, list, get, update, delete, indexing, and stats operations are owner-scoped. Unauthorized project access is logged as `AUTHZ_DENIED`.

### Path

`backend/controllers/project_controller.py`

```python
async def get_project(
    self,
    db: AsyncSession,
    project_id: int,
    owner_id: int,
) -> Optional[Project]:
    stmt = select(Project).where(
        Project.id == project_id,
        Project.owner_id == owner_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

```python
async def list_projects(
    self,
    db: AsyncSession,
    owner_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Project]:
    stmt = (
        select(Project)
        .where(Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

---
