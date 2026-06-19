## 15. Query/RAG Access Control

### Explanation

The query/RAG pipeline is protected against cross-user data leakage. The query endpoint requires authentication, verifies that the project belongs to the current user, sanitizes query text, bounds retrieval parameters, passes `owner_id` to the query service, and scopes vector retrieval by `owner_id`, `project_id`, and optionally `asset_id`.

### Paths

`backend/routes/query.py`

```python
@router.post("/projects/{project_id}/query", response_model=QueryResponse)
async def query_project(
    project_id: int,
    query_data: QueryRequest,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_query_scope(
        db=db,
        project_id=project_id,
        current_user=current_user,
        project_controller=project_controller,
        document_controller=document_controller,
        asset_id=query_data.asset_id,
    )

    clean_query = sanitize_text(query_data.query, max_length=4000, strip_html=True, allow_newlines=True)

    result = await query_controller.answer_query(
        db=db,
        owner_id=current_user.id,
        project_id=project_id,
        query=clean_query,
        asset_id=query_data.asset_id,
    )
```

`backend/services/query_service.py`

```python
filter_dict = {
    'owner_id': owner_id,
    'project_id': project_id,
}
if asset_id:
    filter_dict['asset_id'] = asset_id

results = await vector_db.search(
    collection_name=f"project_{project_id}",
    query_vector=query_embedding,
    top_k=candidate_k,
    filter_dict=filter_dict
)
```

---
