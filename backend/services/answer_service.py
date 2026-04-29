"""
Answer Generation Service.
Handles generating AI-powered answers using LLM.
"""
from typing import List, Dict, Any, Optional
from backend.providers.llm.factory import LLMProviderFactory
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class AnswerService:
    """Service for generating answers from context."""

    @staticmethod
    def _fallback_answer(language: str) -> str:
        if language == "ar":
            return "تعذر توليد إجابة واضحة الآن. حاول إعادة صياغة السؤال بشكل أدق."
        return "Could not generate a clear answer right now. Please try rephrasing your question."
    
    def __init__(self):
        """Initialize answer service."""
        self.llm_provider = LLMProviderFactory.create_provider()
        logger.info("Answer service initialized")
    
    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        language: str = "ar",  # Default to Arabic
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Generate answer from query and context.
        
        Args:
            query: User question
            context_chunks: List of relevant chunks
            language: Response language ('ar' or 'en')
            include_sources: Whether to include source references
            
        Returns:
            Dict with 'answer' and optional 'sources'
        """
        try:
            # Build context from chunks
            context = self._build_context(context_chunks)
            
            # Build system + user prompts
            system_prompt = self._build_system_prompt(language)
            prompt = self._build_prompt(query, context, language)
            
            # Generate answer
            answer = await self.llm_provider.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=25000
            )

            answer = (answer or "").strip()
            if not answer:
                logger.warning("LLM returned empty answer, using fallback")
                answer = self._fallback_answer(language)
            
            # Format response
            response = {
                'answer': answer,
                'context_used': len(context_chunks)
            }
            
            if include_sources:
                response['sources'] = self._extract_sources(context_chunks)
            
            logger.info(f"Generated answer (length={len(answer)})")
            return response
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build context string from chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Formatted context string
        """
        def _estimate_tokens(text: str) -> int:
            return max(1, len(text) // 4)

        budget = max(500, int(settings.context_token_budget))
        token_count = 0

        context_parts: list[str] = []
        seen_parents = set()
        seen_text_keys: set[str] = set()

        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            doc_name = metadata.get('document_name', 'Unknown')
            parent_content = metadata.get('parent_content')
            parent_key = None

            if parent_content:
                parent_key = (metadata.get('asset_id'), metadata.get('parent_index'))
                if parent_key in seen_parents:
                    continue
                seen_parents.add(parent_key)
                content = parent_content
            else:
                content = chunk.get('content', '')

            clean_content = str(content or "").strip()
            if not clean_content:
                continue

            text_key = clean_content[:500]
            if text_key in seen_text_keys:
                continue
            seen_text_keys.add(text_key)

            source_index = len(context_parts) + 1
            part = f"[مصدر {source_index} - {doc_name}]\n{clean_content}"
            estimated = _estimate_tokens(part)

            if estimated > budget and not context_parts:
                truncated = clean_content[: budget * 4]
                context_parts.append(f"[مصدر {source_index} - {doc_name}]\n{truncated}")
                break

            if token_count + estimated > budget:
                break

            context_parts.append(part)
            token_count += estimated
        
        return "\n\n".join(context_parts)
    
    def _build_system_prompt(self, language: str) -> str:
        """
        Build system instruction for LLM.

        Args:
            language: Response language

        Returns:
            System instruction text
        """
        if language == "ar":
            return """أنت مساعد احترافي على مستوى الشركات للإجابة بدقة اعتمادًا على سياق المستندات فقط.
اتّبع القواعد التالية بدقة:
1) اعتمد فقط على السياق المقدم. إذا لم تجد الإجابة في السياق، قل ذلك بوضوح.
2) قدّم إجابة مباشرة ومختصرة أولاً، ثم أضف تفاصيل داعمة عند الحاجة.
3) اربط كل معلومة بمرجع داخل النص باستخدام (مصدر 1) أو (مصدر 2) بعد الجملة ذات الصلة.
4) لا تخمّن ولا تضف معلومات من خارج السياق.
5) إذا كان المصدر دينيًّا، فأدرج الأحاديث الواردة أو القريبة في هذا الباب فقط إن كانت موجودة صراحة في السياق.
6) استخدم العربية الفصحى وتجنّب الحشو.

الإخراج:
- فقرة إجابة واضحة.
- عند اللزوم، قائمة نقاط موجزة مع الاستشهادات."""

        return """You are an enterprise-grade assistant answering strictly from the provided document context.
Follow these rules:
1) Use only the given context. If the answer is not in the context, state that clearly.
2) Provide a concise direct answer first, then add supporting detail if needed.
3) Cite sources inline using (Source 1) or (Source 2) after each relevant statement.
4) Do not guess or add external knowledge.
5) If the source is religious, include relevant hadiths only when they explicitly appear in the context.
6) Keep the response clear and professional.

Output:
- One clear answer paragraph.
- If helpful, a short bullet list with citations."""

    def _build_prompt(self, query: str, context: str, language: str) -> str:
        """
        Build user prompt for LLM.
        
        Args:
            query: User question
            context: Context text
            language: Response language
            
        Returns:
            Formatted user prompt
        """
        if language == "ar":
            prompt = f"""السياق:
{context}

السؤال: {query}

الإجابة:"""
        else:
            prompt = f"""Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract unique source information from chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of unique source information
        """
        seen = set()
        sources = []

        for chunk in chunks:
            metadata = chunk.get('metadata', {}) or {}
            asset_id = chunk.get('asset_id')
            chunk_index = metadata.get('chunk_index', 0)

            key = (asset_id, chunk_index)
            if key in seen:
                continue

            seen.add(key)

            sources.append({
                'document_name': metadata.get('document_name', 'Unknown'),
                'chunk_index': chunk_index,
                'similarity': chunk.get('similarity', 0.0),
                'asset_id': asset_id
            })
        
        return sources
