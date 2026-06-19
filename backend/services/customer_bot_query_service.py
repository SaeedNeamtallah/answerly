"""Customer-safe Telegram answer generation over the existing RAG stack."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.controllers.query_controller import QueryController
from backend.database.models import BotIntegration
from backend.runtime_config import get_runtime_value
from backend.security.sanitization import sanitize_text


class CustomerBotQueryService:
    """Reuse QueryController while stripping customer-facing debug/source data by default."""

    def __init__(self, query_controller: QueryController | None = None):
        self.query_controller = query_controller or QueryController()

    async def answer(
        self,
        db: AsyncSession,
        *,
        integration: BotIntegration,
        query: str,
        language: str = "ar",
    ) -> dict[str, Any]:
        clean_query = sanitize_text(query, max_length=4000, strip_html=True, allow_newlines=True)
        query_kwargs = {
            "db": db,
            "owner_id": integration.owner_id,
            "project_id": integration.project_id,
            "query": clean_query,
            "top_k": max(
                1,
                min(
                    int(get_runtime_value("retrieval_top_k", settings.retrieval_top_k)),
                    settings.retrieval_top_k_max,
                ),
            ),
            "language": language,
        }
        if integration.system_prompt:
            query_kwargs["custom_system_prompt"] = integration.system_prompt

        result = await self.query_controller.answer_query(**query_kwargs)
        sources = result.get("sources") or []
        customer_answer = str(result.get("answer") or "").strip()
        if integration.show_sources_to_customer and sources:
            source_names = []
            for source in sources:
                document_name = sanitize_text(source.get("document_name"), max_length=120, strip_html=True, allow_newlines=False)
                if document_name and document_name not in source_names:
                    source_names.append(document_name)
            if source_names:
                customer_answer = f"{customer_answer}\n\nSources: {', '.join(source_names[:5])}"

        return {
            "customer_answer": customer_answer,
            "internal_sources": sources,
            "context_used": int(result.get("context_used") or 0),
        }

