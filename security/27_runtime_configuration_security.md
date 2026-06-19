## 27. Runtime Configuration Security

### Explanation

The runtime configuration update endpoint validates provider names and configuration values. Provider names are sanitized, then checked against allowed provider registries. Chunk strategy and numeric runtime values are bounded, and configuration inputs use strict Pydantic models. Protection depends on `SECURITY_REQUIRE_AUTH_FOR_MUTATIONS`; in the example environment it is enabled, but the code supports disabling it.

### Path

`backend/routes/app_config.py`

```python
@router.post("/providers")
async def update_providers(
    payload: ProviderUpdate,
    _auth: Optional[AuthUser] = Depends(require_mutation_auth_if_enabled),
) -> Dict[str, object]:
    llm_provider = sanitize_text(payload.llm_provider, max_length=64, strip_html=True, allow_newlines=False).lower()
    embedding_provider = sanitize_text(payload.embedding_provider, max_length=64, strip_html=True, allow_newlines=False).lower()

    llm_available = set(LLMProviderFactory.get_available_providers())
    embedding_available = set(LLMProviderFactory.get_available_embedding_providers())
    vector_available = set(VectorDBProviderFactory.get_available_providers())

    if llm_provider not in llm_available:
        raise HTTPException(status_code=400, detail="Unsupported LLM provider")
    if embedding_provider not in embedding_available:
        raise HTTPException(status_code=400, detail="Unsupported embedding provider")
    if vector_db_provider is not None and vector_db_provider not in vector_available:
        raise HTTPException(status_code=400, detail="Unsupported vector DB provider")
```

---
