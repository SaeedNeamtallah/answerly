"""
VectorDB Provider Factory.
Creates vector database provider instances using a registry-based Factory Pattern.
"""
import logging
from typing import Callable, Dict, List

from backend.config import settings
from backend.providers.vectordb.enums import VectorDBProvider
from backend.providers.vectordb.interface import VectorDBInterface
from backend.providers.vectordb.pgvector_provider import PGVectorProvider
from backend.providers.vectordb.qdrant_provider import QdrantProvider
from backend.runtime_config import get_runtime_value

logger = logging.getLogger(__name__)


class VectorDBProviderFactory:
    """Factory for creating VectorDB provider instances."""

    _instances: Dict[str, VectorDBInterface] = {}
    _registry: Dict[str, Callable[[], VectorDBInterface]] = {}
    _initialized = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        if cls._initialized:
            return

        cls.register_provider(VectorDBProvider.PGVECTOR.value, cls._build_pgvector_provider)
        cls.register_provider(VectorDBProvider.QDRANT.value, cls._build_qdrant_provider)
        cls._initialized = True

    @classmethod
    def register_provider(cls, provider_name: str, builder: Callable[[], VectorDBInterface]) -> None:
        """Register or override a vector DB provider builder."""
        cls._registry[provider_name.lower()] = builder

    @staticmethod
    def _build_pgvector_provider() -> VectorDBInterface:
        return PGVectorProvider()

    @staticmethod
    def _build_qdrant_provider() -> VectorDBInterface:
        return QdrantProvider(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
    
    @classmethod
    def create_provider(cls, provider_name: str = None) -> VectorDBInterface:
        """
        Create or return existing VectorDB provider instance (Singleton).
        
        Args:
            provider_name: Name of provider ('pgvector', 'qdrant', etc.)
                          Defaults to settings.vector_db_provider
        
        Returns:
            VectorDB provider instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        cls._ensure_initialized()

        provider_name = provider_name or get_runtime_value("vector_db_provider", settings.vector_db_provider)
        provider_name = provider_name.lower()

        if provider_name in cls._instances:
            return cls._instances[provider_name]

        builder = cls._registry.get(provider_name)
        if not builder:
            available = ", ".join(cls.get_available_providers())
            raise ValueError(f"Unsupported VectorDB provider: {provider_name}. Available: {available}")

        logger.info("Creating VectorDB provider: %s", provider_name)
        instance = builder()
        cls._instances[provider_name] = instance
        return instance

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider names."""
        cls._ensure_initialized()
        return list(cls._registry.keys())
