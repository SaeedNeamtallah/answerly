"""
Abstract VectorDB Provider Interface.
Defines the contract for vector database providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class VectorDBInterface(ABC):
    """Abstract base class for vector database providers."""
    
    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        **kwargs
    ) -> bool:
        """
        Create a collection/index for storing vectors.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension size
            **kwargs: Provider-specific parameters
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def add_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        ids: List[Any],
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> bool:
        """
        Add vectors to collection.
        
        Args:
            collection_name: Collection name
            vectors: List of vector embeddings
            ids: List of unique identifiers
            metadata: Optional metadata for each vector
            **kwargs: Provider-specific parameters
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[Any, float, Dict[str, Any]]]:
        """
        Search for similar vectors.
        
        Args:
            collection_name: Collection name
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            **kwargs: Provider-specific parameters
            
        Returns:
            List of tuples: (id, similarity_score, metadata)
        """
        pass
    
    @abstractmethod
    async def delete_collection(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Collection name
            **kwargs: Provider-specific parameters
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def collection_exists(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        """
        Check if collection exists.
        
        Args:
            collection_name: Collection name
            **kwargs: Provider-specific parameters
            
        Returns:
            True if exists
        """
        pass
