"""
Google Gemini 2.5 Flash LLM Provider Implementation.
Uses the Google GenAI SDK for text generation and embeddings.
"""
import asyncio
from typing import Any, List, Optional, AsyncIterator
from google import genai
from google.genai import types
from backend.providers.llm.interface import LLMInterface
from backend.providers.llm.exceptions import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class GeminiProvider(LLMInterface):
    """Google Gemini LLM provider implementation."""

    _EMBED_MODEL_DIMENSIONS = {
        "models/gemini-embedding-001": 3072,
        "models/text-embedding-004": 768,
    }

    @staticmethod
    def _get_attr_or_key(obj: Any, name: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _extract_text_from_candidate(self, candidate: Any) -> str:
        content = self._get_attr_or_key(candidate, "content")
        if content is None:
            return ""

        parts = self._get_attr_or_key(content, "parts", []) or []
        chunks: List[str] = []
        for part in parts:
            text = self._get_attr_or_key(part, "text")
            if text:
                chunks.append(str(text))

        return "".join(chunks)

    def _extract_text_from_response(self, response: Any) -> str:
        # Fast path: if quick accessor is valid, use it.
        try:
            quick_text = self._get_attr_or_key(response, "text")
            if quick_text:
                return str(quick_text)
        except Exception:
            pass

        # Safe path: parse candidates/content/parts manually.
        candidates = self._get_attr_or_key(response, "candidates", []) or []
        for candidate in candidates:
            text = self._extract_text_from_candidate(candidate)
            if text:
                return text

        return ""

    def _extract_finish_reason(self, response: Any) -> str:
        candidates = self._get_attr_or_key(response, "candidates", []) or []
        if not candidates:
            return "unknown"
        reason = self._get_attr_or_key(candidates[0], "finish_reason", "unknown")
        return str(reason)
    
    def __init__(self, api_key: str = None, model_name: str = None):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Gemini API key (defaults to settings)
            model_name: Model name (defaults to settings)
        """
        self.api_key = api_key or settings.gemini_api_key
        # Support both flash and lite-flash
        if model_name:
            self.model_name = model_name
        else:
            import backend.runtime_config as rc
            runtime_model = rc.get_runtime_value("gemini_model")
            if runtime_model:
                self.model_name = runtime_model
            else:
                # Use special model if provider is gemini-2.5-lite-flash
                provider = rc.get_runtime_value("llm_provider", settings.llm_provider)
                if provider == "gemini-2.5-lite-flash":
                    self.model_name = getattr(settings, "gemini_lite_model", "gemini-2.5-lite-flash")
                else:
                    self.model_name = settings.gemini_model
        self.client = genai.Client(api_key=self.api_key)
        self.embedding_model = settings.gemini_embed_model
        self._detected_embedding_dimension: Optional[int] = None
        logger.info(f"Gemini provider initialized with model: {self.model_name}")

    def _infer_embedding_dimension_from_model(self) -> int:
        model_key = (self.embedding_model or "").strip().lower()
        if model_key in self._EMBED_MODEL_DIMENSIONS:
            return self._EMBED_MODEL_DIMENSIONS[model_key]

        # Conservative fallback for unknown Gemini embedding models.
        if "embedding-001" in model_key:
            return 3072
        if "text-embedding" in model_key:
            return 768
        return 3072

    @staticmethod
    def _classify_provider_exception(exc: BaseException, *, provider: str) -> BaseException:
        text = str(exc).lower()
        name = exc.__class__.__name__.lower()

        if isinstance(exc, asyncio.TimeoutError) or "timeout" in text or "deadline" in text:
            return ProviderTimeoutError(provider=provider)
        if any(token in text for token in ("unauthorized", "forbidden", "api key", "permission", "401", "403")):
            return ProviderAuthError(provider=provider)
        if any(token in text for token in ("rate limit", "quota", "429", "resource exhausted")):
            return ProviderRateLimitError(provider=provider)
        if any(
            token in text or token in name
            for token in (
                "cannot connect",
                "connection",
                "connecterror",
                "network",
                "service unavailable",
                "temporarily unavailable",
                "503",
                "502",
                "500",
                "unavailable",
            )
        ):
            return ProviderUnavailableError(provider=provider)
        return exc

    async def _run_with_retries(self, operation, *, provider: str, max_attempts: int = 3):
        last_error: BaseException | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                return await asyncio.wait_for(operation(), timeout=30)
            except Exception as exc:
                classified = self._classify_provider_exception(exc, provider=provider)
                if isinstance(classified, (ProviderUnavailableError, ProviderTimeoutError, ProviderRateLimitError)):
                    last_error = classified
                    if attempt < max_attempts:
                        await asyncio.sleep(min(2 ** (attempt - 1), 4))
                        continue
                raise classified from exc
        if last_error:
            raise last_error
        raise ProviderUnavailableError(provider=provider)
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            
        Returns:
            Generated text
        """
        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            generation_config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens or 2048,
            )

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt if system_prompt else full_prompt,
                config=generation_config,
            )

            text = self._extract_text_from_response(response)
            if not text:
                logger.warning(
                    "Gemini returned an empty response (finish_reason=%s)",
                    self._extract_finish_reason(response)
                )
            return text
            
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {str(e)}")
            raise

    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream text token-by-token using Gemini SDK."""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            generation_config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens or 2048,
            )

            emitted_any = False
            last_finish_reason = "unknown"
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt if system_prompt else full_prompt,
                config=generation_config,
            )
            async for chunk in stream:
                last_finish_reason = self._extract_finish_reason(chunk)
                text = self._extract_text_from_response(chunk)
                if text:
                    emitted_any = True
                    yield text

            if not emitted_any:
                logger.warning(
                    "Gemini stream returned no tokens (finish_reason=%s)",
                    last_finish_reason,
                )

        except Exception as e:
            logger.error(f"Error streaming text with Gemini: {str(e)}")
            raise
    
    async def generate_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings using Gemini.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = await self._run_with_retries(
                lambda: self.client.aio.models.embed_content(
                    model=self.embedding_model,
                    contents=texts,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
                ),
                provider="gemini",
            )
            embeddings = []
            for item in response.embeddings or []:
                values = self._get_attr_or_key(item, "values")
                if values is None:
                    values = self._get_attr_or_key(item, "embedding", [])
                embeddings.append(list(values or []))

            if embeddings and embeddings[0]:
                self._detected_embedding_dimension = len(embeddings[0])
            
            return list(embeddings)
            
        except Exception as e:
            classified = self._classify_provider_exception(e, provider="gemini")
            logger.warning("Gemini embedding request failed: %s", classified)
            raise classified from e

    async def health_check(self) -> bool:
        """Run a minimal embedding request to verify active Gemini embedding access."""
        embeddings = await self.generate_embeddings(["health check"], batch_size=1)
        return bool(embeddings and embeddings[0])
    
    def get_model_name(self) -> str:
        """Get model name."""
        return self.model_name
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension for Gemini embedding model."""
        if self._detected_embedding_dimension:
            return int(self._detected_embedding_dimension)
        return self._infer_embedding_dimension_from_model()
