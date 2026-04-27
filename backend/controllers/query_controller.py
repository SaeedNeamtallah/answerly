"""
Query Controller.
Business logic for query processing and answer generation.
"""
from typing import Dict, Any, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.database.models import Asset, Project

logger = logging.getLogger(__name__)


class QueryInfrastructureError(RuntimeError):
    """Raised when query infrastructure dependencies are unavailable."""


class QueryController:
    """Controller for query operations."""

    # SECURITY RULE: retrieval must be scoped to owner_id from JWT.

    @staticmethod
    def _fallback_answer(language: str) -> str:
        if language == "ar":
            return "تعذر توليد إجابة واضحة الآن. حاول إعادة صياغة السؤال بشكل أدق."
        return "Could not generate a clear answer right now. Please try rephrasing your question."

    @staticmethod
    def _no_context_answer(
        language: str,
        *,
        total_docs: int,
        completed_docs: int,
        active_docs: int,
        failed_docs: int,
    ) -> str:
        if language == "ar":
            if total_docs <= 0:
                return "لا توجد مستندات في هذا المشروع بعد. ارفع مستندًا أولًا ثم أعد المحاولة."
            if completed_docs <= 0 and active_docs > 0:
                return "المستندات ما زالت قيد المعالجة. انتظر حتى تكتمل المعالجة ثم جرّب مرة أخرى."
            if completed_docs <= 0 and failed_docs > 0:
                return "فشلت معالجة المستندات الحالية. ارفع ملفًا صالحًا (PDF/TXT/DOCX) ثم أعد المحاولة."
            return "لم أتمكن من العثور على معلومات ذات صلة في المستندات."

        if total_docs <= 0:
            return "No documents were uploaded to this project yet. Upload a document first, then try again."
        if completed_docs <= 0 and active_docs > 0:
            return "Documents are still processing. Please wait for processing to complete, then try again."
        if completed_docs <= 0 and failed_docs > 0:
            return "Current documents failed to process. Upload a valid PDF/TXT/DOCX file, then try again."
        return "Could not find relevant information in the documents."
    
    def __init__(self):
        """Initialize query controller."""
        # Lazy imports keep startup fast and avoid circular-import pitfalls.
        from backend.services.query_service import QueryService
        from backend.services.answer_service import AnswerService

        self.query_service = QueryService()
        self.answer_service = AnswerService()
    
    async def answer_query(
        self,
        db: AsyncSession,
        owner_id: int,
        project_id: int,
        query: str,
        top_k: int = 5,
        language: str = "ar",
        asset_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process query and generate answer.
        
        Args:
            db: Database session
            owner_id: Owner user ID
            project_id: Project ID to search in
            query: User question
            top_k: Number of chunks to retrieve
            language: Response language ('ar' or 'en')
            asset_id: Optional specific document to search
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            # Search for relevant chunks
            logger.info(f"Processing query for project {project_id}: {query[:50]}...")
            
            similar_chunks = await self.query_service.search_similar_chunks(
                query=query,
                owner_id=owner_id,
                project_id=project_id,
                top_k=top_k,
                asset_id=asset_id
            )
            
            if not similar_chunks:
                total_docs = 0
                completed_docs = 0
                active_docs = 0
                failed_docs = 0
                try:
                    base_scope = (
                        select(Asset.id)
                        .join(Project, Project.id == Asset.project_id)
                        .where(
                            Asset.project_id == project_id,
                            Project.owner_id == owner_id,
                        )
                    )

                    total_docs = int((await db.execute(
                        select(func.count()).select_from(base_scope.subquery())
                    )).scalar_one() or 0)

                    completed_docs = int((await db.execute(
                        select(func.count()).select_from(
                            base_scope.where(Asset.status == "completed").subquery()
                        )
                    )).scalar_one() or 0)

                    active_docs = int((await db.execute(
                        select(func.count()).select_from(
                            base_scope.where(Asset.status.in_(("uploaded", "queued", "pending", "processing"))).subquery()
                        )
                    )).scalar_one() or 0)

                    failed_docs = int((await db.execute(
                        select(func.count()).select_from(
                            base_scope.where(Asset.status == "failed").subquery()
                        )
                    )).scalar_one() or 0)
                except Exception:
                    logger.debug("Could not derive document readiness stats for query fallback", exc_info=True)

                return {
                    'answer': self._no_context_answer(
                        language,
                        total_docs=total_docs,
                        completed_docs=completed_docs,
                        active_docs=active_docs,
                        failed_docs=failed_docs,
                    ),
                    'sources': [],
                    'context_used': 0
                }
            
            # Generate answer
            result = await self.answer_service.generate_answer(
                query=query,
                context_chunks=similar_chunks,
                language=language,
                include_sources=True
            )
            
            logger.info(f"Generated answer for query (used {result['context_used']} chunks)")
            return result
            
        except Exception as e:
            logger.exception("Error processing query infrastructure")
            raise QueryInfrastructureError("Query infrastructure failure") from e
