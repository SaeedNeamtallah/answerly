import asyncio
import os
import traceback
from typing import Any, Dict, List

from backend.providers.llm.factory import LLMProviderFactory
from backend.providers.vectordb.factory import VectorDBProviderFactory


def safe_repr(value: Any) -> str:
    try:
        return str(value)
    except Exception:
        return repr(value)


async def run_llm_provider_checks() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "available_llm": [],
        "available_embedding": [],
        "llm_create": [],
        "embedding_create": [],
        "active_llm_generate_text": None,
        "active_embedding_generate_embeddings": None,
    }

    available_llm = LLMProviderFactory.get_available_providers()
    available_embedding = LLMProviderFactory.get_available_embedding_providers()
    report["available_llm"] = available_llm
    report["available_embedding"] = available_embedding

    for name in available_llm:
        entry = {"provider": name, "status": "unknown", "class": None, "model": None, "error": None}
        try:
            instance = LLMProviderFactory.create_provider(name)
            entry["status"] = "ok"
            entry["class"] = instance.__class__.__name__
            try:
                entry["model"] = safe_repr(instance.get_model_name())
            except Exception as model_exc:
                entry["model"] = f"<model-error: {model_exc}>"
        except Exception as exc:
            entry["status"] = "error"
            entry["error"] = safe_repr(exc)
        report["llm_create"].append(entry)

    for name in available_embedding:
        entry = {"provider": name, "status": "unknown", "class": None, "dimension": None, "error": None}
        try:
            instance = LLMProviderFactory.create_embedding_provider(name)
            entry["status"] = "ok"
            entry["class"] = instance.__class__.__name__
            try:
                entry["dimension"] = int(instance.get_embedding_dimension())
            except Exception as dim_exc:
                entry["dimension"] = f"<dimension-error: {dim_exc}>"
        except Exception as exc:
            entry["status"] = "error"
            entry["error"] = safe_repr(exc)
        report["embedding_create"].append(entry)

    # Active provider behavior checks (network-dependent, best effort)
    try:
        active_llm = LLMProviderFactory.create_provider()
        text = await asyncio.wait_for(
            active_llm.generate_text("Reply with one short token: ok"),
            timeout=90,
        )
        report["active_llm_generate_text"] = {
            "status": "ok",
            "class": active_llm.__class__.__name__,
            "sample": (text or "")[:120],
        }
    except Exception as exc:
        report["active_llm_generate_text"] = {
            "status": "error",
            "error": safe_repr(exc),
        }

    try:
        active_embedding = LLMProviderFactory.create_embedding_provider()
        vectors = await asyncio.wait_for(
            active_embedding.generate_embeddings(["RAGMind provider intensive test sentence."]),
            timeout=120,
        )
        dim = len(vectors[0]) if vectors and vectors[0] else 0
        report["active_embedding_generate_embeddings"] = {
            "status": "ok",
            "class": active_embedding.__class__.__name__,
            "vectors": len(vectors),
            "dimension": dim,
        }
    except Exception as exc:
        report["active_embedding_generate_embeddings"] = {
            "status": "error",
            "error": safe_repr(exc),
        }

    return report


async def run_vectordb_provider_checks() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "available_vectordb": [],
        "create": [],
        "owner_filter_guard": [],
        "collection_exists_checks": [],
    }

    available = VectorDBProviderFactory.get_available_providers()
    report["available_vectordb"] = available

    for name in available:
        entry = {"provider": name, "status": "unknown", "class": None, "error": None}
        instance = None
        try:
            instance = VectorDBProviderFactory.create_provider(name)
            entry["status"] = "ok"
            entry["class"] = instance.__class__.__name__
        except Exception as exc:
            entry["status"] = "error"
            entry["error"] = safe_repr(exc)
        report["create"].append(entry)

        if instance is None:
            continue

        # Guard check: search should reject calls without owner_id filter.
        guard_entry = {"provider": name, "status": "unknown", "error": None}
        try:
            await instance.search(
                collection_name="intensive_guard_check",
                query_vector=[0.1, 0.2, 0.3],
                top_k=1,
                filter_dict={},
            )
            guard_entry["status"] = "unexpected_ok"
        except Exception as exc:
            msg = safe_repr(exc)
            if "owner_id" in msg:
                guard_entry["status"] = "ok"
            else:
                guard_entry["status"] = "error"
            guard_entry["error"] = msg
        report["owner_filter_guard"].append(guard_entry)

        exists_entry = {"provider": name, "status": "unknown", "result": None, "error": None}
        try:
            if name == "pgvector":
                result = await instance.collection_exists("intensive_collection", project_id=-1, owner_id=-1)
            else:
                result = await instance.collection_exists("intensive_collection")
            exists_entry["status"] = "ok"
            exists_entry["result"] = bool(result)
        except Exception as exc:
            exists_entry["status"] = "error"
            exists_entry["error"] = safe_repr(exc)
        report["collection_exists_checks"].append(exists_entry)

    return report


async def main() -> None:
    print("[INFO] Provider factory intensive checks started")
    llm_report = await run_llm_provider_checks()
    vector_report = await run_vectordb_provider_checks()

    print("\n[RESULT] LLM provider checks")
    print(llm_report)

    print("\n[RESULT] Vector DB provider checks")
    print(vector_report)

    print("\n[OK] Provider factory intensive checks completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
        raise
