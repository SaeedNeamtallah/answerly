"""
Application configuration routes.
Exposes provider availability and runtime selections.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict

from backend.config import settings
from backend.database.models import User
from backend.runtime_config import get_runtime_value, load_runtime_config, update_runtime_config
from backend.providers.llm.factory import LLMProviderFactory
from backend.providers.vectordb.factory import VectorDBProviderFactory
from backend.security.auth import get_current_db_user
from backend.security.sanitization import sanitize_text

router = APIRouter(prefix="/config", tags=["App Config"])


class ProviderUpdate(BaseModel):
    llm_provider: str
    embedding_provider: str
    vector_db_provider: str | None = None
    retrieval_top_k: int | None = Field(default=None, ge=1)
    chunk_strategy: str | None = None
    chunk_size: int | None = Field(default=None, ge=100)
    chunk_overlap: int | None = Field(default=None, ge=0)
    parent_chunk_size: int | None = Field(default=None, ge=100)
    parent_chunk_overlap: int | None = Field(default=None, ge=0)
    retrieval_candidate_k: int | None = Field(default=None, ge=1)
    retrieval_hybrid_enabled: bool | None = None
    retrieval_hybrid_alpha: float | None = Field(default=None, ge=0.0, le=1.0)
    retrieval_rerank_enabled: bool | None = None
    retrieval_rerank_top_k: int | None = Field(default=None, ge=1)
    query_rewrite_enabled: bool | None = None
    retrieval_hnsw_ef_search: int | None = Field(default=None, ge=1)


def _normalize_provider_choice(raw_value: object, *, available: list[str], fallback_value: str) -> str:
    normalized_available = [str(item).strip().lower() for item in available if str(item).strip()]
    if not normalized_available:
        return str(fallback_value or "").strip().lower()

    candidate = str(raw_value or "").strip().lower()
    if candidate in normalized_available:
        return candidate

    fallback = str(fallback_value or "").strip().lower()
    if fallback in normalized_available:
        return fallback

    return normalized_available[0]


def normalize_provider_runtime_config() -> Dict[str, object]:
    """Migrate unsupported runtime provider selections to valid defaults."""
    llm_available = LLMProviderFactory.get_available_providers()
    embedding_available = LLMProviderFactory.get_available_embedding_providers()
    vector_available = VectorDBProviderFactory.get_available_providers()

    config = load_runtime_config()
    normalized = {
        "llm_provider": _normalize_provider_choice(
            config.get("llm_provider", settings.llm_provider),
            available=llm_available,
            fallback_value=settings.llm_provider,
        ),
        "embedding_provider": _normalize_provider_choice(
            config.get("embedding_provider", settings.embedding_provider),
            available=embedding_available,
            fallback_value=settings.embedding_provider,
        ),
        "vector_db_provider": _normalize_provider_choice(
            config.get("vector_db_provider", settings.vector_db_provider),
            available=vector_available,
            fallback_value=settings.vector_db_provider,
        ),
    }

    updates: Dict[str, str] = {}
    for key, value in normalized.items():
        current_value = str(config.get(key, "")).strip().lower()
        if current_value != value:
            updates[key] = value

    if updates:
        update_runtime_config(updates)

    return {
        **normalized,
        "migrated": bool(updates),
        "updated_fields": sorted(updates.keys()),
    }


@router.get("/providers")
async def get_providers(
    _current_user: User = Depends(get_current_db_user),
) -> Dict[str, object]:
    """Return available providers and current selections."""
    provider_state = normalize_provider_runtime_config()
    llm_available = LLMProviderFactory.get_available_providers()
    embedding_available = LLMProviderFactory.get_available_embedding_providers()
    vector_available = VectorDBProviderFactory.get_available_providers()

    return {
        "available": {
            "llm": llm_available,
            "embedding": embedding_available,
            "vector_db": vector_available,
        },
        "llm_provider": provider_state["llm_provider"],
        "embedding_provider": provider_state["embedding_provider"],
        "vector_db_provider": provider_state["vector_db_provider"],
        "provider_selection_migrated": provider_state["migrated"],
        "provider_selection_updated_fields": provider_state["updated_fields"],
        "retrieval_top_k": get_runtime_value("retrieval_top_k", settings.retrieval_top_k),
        "chunk_strategy": get_runtime_value("chunk_strategy", settings.chunk_strategy),
        "chunk_size": get_runtime_value("chunk_size", settings.chunk_size),
        "chunk_overlap": get_runtime_value("chunk_overlap", settings.chunk_overlap),
        "parent_chunk_size": get_runtime_value("parent_chunk_size", settings.parent_chunk_size),
        "parent_chunk_overlap": get_runtime_value("parent_chunk_overlap", settings.parent_chunk_overlap),
        "retrieval_candidate_k": get_runtime_value("retrieval_candidate_k", settings.retrieval_candidate_k),
        "retrieval_hybrid_enabled": get_runtime_value("retrieval_hybrid_enabled", settings.retrieval_hybrid_enabled),
        "retrieval_hybrid_alpha": get_runtime_value("retrieval_hybrid_alpha", settings.retrieval_hybrid_alpha),
        "retrieval_rerank_enabled": get_runtime_value("retrieval_rerank_enabled", settings.retrieval_rerank_enabled),
        "retrieval_rerank_top_k": get_runtime_value("retrieval_rerank_top_k", settings.retrieval_rerank_top_k),
        "query_rewrite_enabled": get_runtime_value("query_rewrite_enabled", settings.query_rewrite_enabled),
        "retrieval_hnsw_ef_search": get_runtime_value("retrieval_hnsw_ef_search", settings.retrieval_hnsw_ef_search),
    }


@router.post("/providers")
async def update_providers(
    payload: ProviderUpdate,
    _current_user: User = Depends(get_current_db_user),
) -> Dict[str, object]:
    """Update runtime provider selections."""
    llm_provider = sanitize_text(payload.llm_provider, max_length=64, strip_html=True, allow_newlines=False).lower()
    embedding_provider = sanitize_text(payload.embedding_provider, max_length=64, strip_html=True, allow_newlines=False).lower()
    vector_db_provider = None
    if payload.vector_db_provider is not None:
        vector_db_provider = sanitize_text(payload.vector_db_provider, max_length=64, strip_html=True, allow_newlines=False).lower()
    chunk_strategy = None
    if payload.chunk_strategy is not None:
        chunk_strategy = sanitize_text(payload.chunk_strategy, max_length=32, strip_html=True, allow_newlines=False).lower()

    if not llm_provider or not embedding_provider:
        raise HTTPException(status_code=400, detail="Provider names cannot be empty")

    llm_available = set(LLMProviderFactory.get_available_providers())
    embedding_available = set(LLMProviderFactory.get_available_embedding_providers())
    vector_available = set(VectorDBProviderFactory.get_available_providers())
    chunk_strategy_allowed = {"parent_child", "simple"}

    if llm_provider not in llm_available:
        raise HTTPException(status_code=400, detail="Unsupported LLM provider")
    if embedding_provider not in embedding_available:
        raise HTTPException(status_code=400, detail="Unsupported embedding provider")
    if vector_db_provider is not None and vector_db_provider not in vector_available:
        raise HTTPException(status_code=400, detail="Unsupported vector DB provider")
    if chunk_strategy is not None and chunk_strategy not in chunk_strategy_allowed:
        raise HTTPException(status_code=400, detail="Unsupported chunk strategy")

    updates = {
        "llm_provider": llm_provider,
        "embedding_provider": embedding_provider,
    }

    if vector_db_provider is not None:
        updates["vector_db_provider"] = vector_db_provider

    if payload.retrieval_top_k is not None:
        top_k = min(payload.retrieval_top_k, settings.retrieval_top_k_max)
        updates["retrieval_top_k"] = top_k

    if chunk_strategy is not None:
        updates["chunk_strategy"] = chunk_strategy
    if payload.chunk_size is not None:
        updates["chunk_size"] = payload.chunk_size
    if payload.chunk_overlap is not None:
        updates["chunk_overlap"] = payload.chunk_overlap
    if payload.parent_chunk_size is not None:
        updates["parent_chunk_size"] = payload.parent_chunk_size
    if payload.parent_chunk_overlap is not None:
        updates["parent_chunk_overlap"] = payload.parent_chunk_overlap
    if payload.retrieval_candidate_k is not None:
        updates["retrieval_candidate_k"] = payload.retrieval_candidate_k
    if payload.retrieval_hybrid_enabled is not None:
        updates["retrieval_hybrid_enabled"] = payload.retrieval_hybrid_enabled
    if payload.retrieval_hybrid_alpha is not None:
        updates["retrieval_hybrid_alpha"] = payload.retrieval_hybrid_alpha
    if payload.retrieval_rerank_enabled is not None:
        updates["retrieval_rerank_enabled"] = payload.retrieval_rerank_enabled
    if payload.retrieval_rerank_top_k is not None:
        updates["retrieval_rerank_top_k"] = payload.retrieval_rerank_top_k
    if payload.query_rewrite_enabled is not None:
        updates["query_rewrite_enabled"] = payload.query_rewrite_enabled
    if payload.retrieval_hnsw_ef_search is not None:
        updates["retrieval_hnsw_ef_search"] = payload.retrieval_hnsw_ef_search
    config = update_runtime_config(updates)

    return {
        "llm_provider": config.get("llm_provider", settings.llm_provider),
        "embedding_provider": config.get("embedding_provider", settings.embedding_provider),
        "vector_db_provider": config.get("vector_db_provider", settings.vector_db_provider),
        "retrieval_top_k": config.get("retrieval_top_k", settings.retrieval_top_k),
        "chunk_strategy": config.get("chunk_strategy", settings.chunk_strategy),
        "chunk_size": config.get("chunk_size", settings.chunk_size),
        "chunk_overlap": config.get("chunk_overlap", settings.chunk_overlap),
        "parent_chunk_size": config.get("parent_chunk_size", settings.parent_chunk_size),
        "parent_chunk_overlap": config.get("parent_chunk_overlap", settings.parent_chunk_overlap),
        "retrieval_candidate_k": config.get("retrieval_candidate_k", settings.retrieval_candidate_k),
        "retrieval_hybrid_enabled": config.get("retrieval_hybrid_enabled", settings.retrieval_hybrid_enabled),
        "retrieval_hybrid_alpha": config.get("retrieval_hybrid_alpha", settings.retrieval_hybrid_alpha),
        "retrieval_rerank_enabled": config.get("retrieval_rerank_enabled", settings.retrieval_rerank_enabled),
        "retrieval_rerank_top_k": config.get("retrieval_rerank_top_k", settings.retrieval_rerank_top_k),
        "query_rewrite_enabled": config.get("query_rewrite_enabled", settings.query_rewrite_enabled),
        "retrieval_hnsw_ef_search": config.get("retrieval_hnsw_ef_search", settings.retrieval_hnsw_ef_search),
    }

