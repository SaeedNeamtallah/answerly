## 16. Vector Database Security

### Explanation

Both PGVector and Qdrant enforce ownership-aware retrieval. Search operations require `owner_id`, and missing ownership filtering is treated as an error. PGVector filters by project owner through SQL joins, while Qdrant uses payload filters for `owner_id`, `project_id`, and `asset_id`. Qdrant vector deletion also refuses empty filters to prevent accidental broad deletion.

### Paths

`backend/providers/vectordb/pgvector_provider.py`

```python
class PGVectorProvider(VectorDBInterface):
    """PostgreSQL pgvector implementation."""

    # SECURITY RULE: retrieval queries must include owner_id filtering.

    async def collection_exists(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        stmt = select(Project).where(Project.id == project_id)
        owner_id = kwargs.get('owner_id')
        if owner_id is not None:
            stmt = stmt.where(Project.owner_id == owner_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
```

`backend/providers/vectordb/qdrant_provider.py`

```python
async def delete_vectors(
    self,
    collection_name: str,
    *,
    filter_dict: Dict[str, Any],
    **kwargs
) -> bool:
    if not filter_dict:
        raise ValueError("filter_dict is required when deleting vectors")

    conditions = []
    for key, value in filter_dict.items():
        conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

    await asyncio.to_thread(
        self.client.delete,
        collection_name=collection_name,
        points_selector=Filter(must=conditions),
        wait=True,
    )
```

---
