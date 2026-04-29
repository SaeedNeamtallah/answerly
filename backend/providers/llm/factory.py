"""
LLM Provider Factory.
Creates LLM and embedding provider instances using a registry-based Factory Pattern.
"""
import logging
from typing import Callable, Dict, List

from backend.config import settings
from backend.providers.llm.enums import EmbeddingProvider, LLMProvider
from backend.providers.llm.gemini_provider import GeminiProvider
from backend.providers.llm.interface import LLMInterface
from backend.providers.llm.openai_compat_provider import OpenAICompatProvider
from backend.runtime_config import get_runtime_value

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM and embedding provider instances."""

    _llm_registry: Dict[str, Callable[[], LLMInterface]] = {}
    _embedding_registry: Dict[str, Callable[[], LLMInterface]] = {}
    _initialized = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        if cls._initialized:
            return

        cls.register_provider(LLMProvider.GEMINI.value, cls._build_gemini_provider)
        cls.register_provider(LLMProvider.GEMINI_2_5_LITE_FLASH.value, cls._build_gemini_lite_provider)
        cls.register_provider(LLMProvider.OPENROUTER_GEMINI_2_0_FLASH.value, cls._build_openrouter_gemini_2_flash_provider)
        cls.register_provider(LLMProvider.OPENROUTER_FREE.value, cls._build_openrouter_free_provider)
        cls.register_provider(LLMProvider.OPENROUTER_GEMMA_4_26B_A4B.value, cls._build_openrouter_gemma_4_26b_a4b_provider)
        cls.register_provider(LLMProvider.GROQ_LLAMA_3_3_70B_VERSATILE.value, cls._build_groq_llama_3_3_70b_versatile_provider)
        cls.register_provider(LLMProvider.CEREBRAS_LLAMA_3_1_8B.value, cls._build_cerebras_llama_3_1_8b_provider)

        cls.register_embedding_provider(EmbeddingProvider.GEMINI.value, cls._build_gemini_provider)
        cls.register_embedding_provider(EmbeddingProvider.COHERE.value, cls._build_cohere_provider)

        cls._initialized = True

    @classmethod
    def register_provider(cls, provider_name: str, builder: Callable[[], LLMInterface]) -> None:
        """Register or override an LLM provider builder."""
        key = provider_name.lower()
        cls._llm_registry[key] = builder

    @classmethod
    def register_embedding_provider(cls, provider_name: str, builder: Callable[[], LLMInterface]) -> None:
        """Register or override an embedding provider builder."""
        key = provider_name.lower()
        cls._embedding_registry[key] = builder

    @staticmethod
    def _build_openrouter_headers() -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if settings.openrouter_site_url:
            headers["HTTP-Referer"] = settings.openrouter_site_url
        if settings.openrouter_app_name:
            headers["X-Title"] = settings.openrouter_app_name
        return headers

    @staticmethod
    def _build_gemini_provider() -> LLMInterface:
        return GeminiProvider()

    @staticmethod
    def _build_gemini_lite_provider() -> LLMInterface:
        return GeminiProvider(model_name=settings.gemini_lite_model)

    @classmethod
    def _build_openrouter_gemini_2_flash_provider(cls) -> LLMInterface:
        return OpenAICompatProvider(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model_name=settings.openrouter_gemini_2_flash_model,
            provider_label="OpenRouter",
            extra_headers=cls._build_openrouter_headers(),
        )

    @classmethod
    def _build_openrouter_free_provider(cls) -> LLMInterface:
        return OpenAICompatProvider(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model_name=settings.openrouter_free_model,
            provider_label="OpenRouter",
            extra_headers=cls._build_openrouter_headers(),
        )

    @classmethod
    def _build_openrouter_gemma_4_26b_a4b_provider(cls) -> LLMInterface:
        return OpenAICompatProvider(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model_name=settings.openrouter_gemma_4_26b_a4b_model,
            provider_label="OpenRouter",
            extra_headers=cls._build_openrouter_headers(),
        )

    @staticmethod
    def _build_groq_llama_3_3_70b_versatile_provider() -> LLMInterface:
        return OpenAICompatProvider(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            model_name=settings.groq_llama_3_3_70b_versatile_model,
            provider_label="Groq",
        )

    @staticmethod
    def _build_cerebras_llama_3_1_8b_provider() -> LLMInterface:
        return OpenAICompatProvider(
            api_key=settings.cerebras_api_key,
            base_url=settings.cerebras_base_url,
            model_name=settings.cerebras_llama_3_1_8b_model,
            provider_label="Cerebras",
        )

    @staticmethod
    def _build_cohere_provider() -> LLMInterface:
        from backend.providers.llm.cohere_provider import CohereProvider

        return CohereProvider()

    @classmethod
    def create_provider(cls, provider_name: str = None) -> LLMInterface:
        """
        Create LLM provider instance.
        
        Args:
            provider_name: Name of provider ('gemini', 'openai', etc.)
                          Defaults to settings.llm_provider
        
        Returns:
            LLM provider instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        cls._ensure_initialized()

        provider_name = provider_name or get_runtime_value("llm_provider", settings.llm_provider)
        provider_name = provider_name.lower()

        builder = cls._llm_registry.get(provider_name)
        if not builder:
            available = ", ".join(cls.get_available_providers())
            raise ValueError(f"Unsupported LLM provider: {provider_name}. Available: {available}")

        logger.info("Creating LLM provider: %s", provider_name)
        return builder()

    @classmethod
    def create_embedding_provider(cls, provider_name: str = None) -> LLMInterface:
        """
        Create embedding provider instance.

        Args:
            provider_name: Name of provider ('gemini', 'cohere', etc.)
                          Defaults to settings.embedding_provider

        Returns:
            LLM provider instance
        """
        cls._ensure_initialized()

        provider_name = provider_name or get_runtime_value("embedding_provider", settings.embedding_provider)
        provider_name = provider_name.lower()

        builder = cls._embedding_registry.get(provider_name)
        if not builder:
            available = ", ".join(cls.get_available_embedding_providers())
            raise ValueError(f"Unsupported embedding provider: {provider_name}. Available: {available}")

        logger.info("Creating embedding provider: %s", provider_name)
        return builder()

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider names."""
        cls._ensure_initialized()
        return list(cls._llm_registry.keys())

    @classmethod
    def get_available_embedding_providers(cls) -> List[str]:
        """Get list of available embedding provider names."""
        cls._ensure_initialized()
        return list(cls._embedding_registry.keys())
