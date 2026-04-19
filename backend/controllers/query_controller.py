"""
Query Controller.
Business logic for query processing and answer generation.
"""
from typing import Dict, Any, Optional, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

logger = logging.getLogger(__name__)


class QueryController:
    """Controller for query operations."""

    # SECURITY RULE: retrieval must be scoped to owner_id from JWT.

    @staticmethod
    def _fallback_answer(language: str) -> str:
        if language == "ar":
            return "تعذر توليد إجابة واضحة الآن. حاول إعادة صياغة السؤال بشكل أدق."
        return "Could not generate a clear answer right now. Please try rephrasing your question."
    
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
                return {
                    'answer': 'لم أتمكن من العثور على معلومات ذات صلة في المستندات.' if language == 'ar' 
                             else 'Could not find relevant information in the documents.',
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
            logger.error(f"Error processing query: {str(e)}")
            return {
                'answer': self._fallback_answer(language),
                'sources': [],
                'context_used': 0
            }

    async def answer_query_stream(
        self,
        db: AsyncSession,
        owner_id: int,
        project_id: int,
        query: str,
        top_k: int = 5,
        language: str = "ar",
        asset_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream SSE events: first the sources, then token-by-token answer,
        then a [DONE] sentinel.
        """
        try:
            logger.info(
                f"Processing streaming query for project {project_id}: {query[:50]}..."
            )

            similar_chunks = await self.query_service.search_similar_chunks(
                query=query,
                owner_id=owner_id,
                project_id=project_id,
                top_k=top_k,
                asset_id=asset_id,
            )

            if not similar_chunks:
                no_info = (
                    "لم أتمكن من العثور على معلومات ذات صلة في المستندات."
                    if language == "ar"
                    else "Could not find relevant information in the documents."
                )
                yield f"data: {json.dumps({'type': 'sources', 'sources': [], 'context_used': 0})}\n\n"
                yield f"data: {json.dumps({'type': 'token', 'token': no_info})}\n\n"
                yield "data: [DONE]\n\n"
                return

            # Emit sources first
            sources = self.answer_service._extract_sources(similar_chunks)
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'context_used': len(similar_chunks)}, ensure_ascii=False)}\n\n"

            # Stream answer tokens
            async for token in self.answer_service.generate_answer_stream(
                query=query,
                context_chunks=similar_chunks,
                language=language,
            ):
                yield f"data: {json.dumps({'type': 'token', 'token': token}, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error streaming query: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': self._fallback_answer(language)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
