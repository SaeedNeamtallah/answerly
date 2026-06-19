## 17. Background Task Security

### Explanation

Celery background workflows include ownership protection. Task ownership is persisted, task status access verifies ownership, processing and indexing tasks include owner metadata, and vector metadata includes `owner_id`, `project_id`, `asset_id`, and chunk/document metadata. Failed processing also cleans stale chunks and vectors.

### Paths

`backend/utils/task_tracking.py`

```python
async def record_task_owner(
    db: AsyncSession,
    *,
    task_id: str,
    owner_id: int,
    task_name: str,
    task_args: dict[str, Any] | None,
) -> None:
    _TASK_OWNER_MAP[task_id] = owner_id

    payload_args = dict(task_args or {})
    payload_args["owner_id"] = owner_id

    manager = IdempotencyManager()
    await manager.upsert_task_record(
        db=db,
        task_name=task_name,
        task_args=payload_args,
        celery_task_id=task_id,
        status="PENDING",
    )
```

`backend/tasks/data_indexing.py`

```python
vector_metadata = [
    {
        "owner_id": project.owner_id,
        "asset_id": chunk.asset_id,
        "project_id": chunk.project_id,
        "chunk_index": chunk.chunk_index,
    }
    for chunk in chunks
]

await vector_db.add_vectors(
    collection_name=collection_name,
    vectors=embeddings,
    ids=chunk_ids,
    metadata=vector_metadata,
    session_maker=session_maker,
)
```

---
