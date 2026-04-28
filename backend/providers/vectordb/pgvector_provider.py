"""
PGVector Provider Implementation.
Uses PostgreSQL with pgvector extension for vector storage.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.providers.vectordb.interface import VectorDBInterface
from backend.database.models import Chunk, Project
from backend.database.connection import async_session_maker
import logging

logger = logging.getLogger(__name__)


class PGVectorProvider(VectorDBInterface):
    """PostgreSQL pgvector implementation."""
    
    def __init__(self):
        """Initialize PGVector provider."""
        logger.info("PGVector provider initialized")
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        **kwargs
    ) -> bool:
        """
        Create collection (for pgvector, this is handled by table creation).
        
        Args:
            collection_name: Not used (using chunks table)
            dimension: Vector dimension
            
        Returns:
            True (table already exists from migrations)
        """
        # With pgvector, collections are handled by the chunks table
        # The vector column is already defined in the model
        logger.info(f"Collection '{collection_name}' ready (using chunks table)")
        return True
    
    async def add_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        ids: List[Any],
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> bool:
        """
        Add/update vectors in chunks table.
        
        Args:
            collection_name: Project name or identifier
            vectors: List of embeddings
            ids: List of chunk IDs
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            from sqlalchemy import update as sa_update
            async with async_session_maker() as session:
                for i, (chunk_id, vector) in enumerate(zip(ids, vectors)):
                    await session.execute(
                        sa_update(Chunk)
                        .where(Chunk.id == chunk_id)
                        .values(embedding=vector)
                    )
                    if (i + 1) % 500 == 0:
                        await session.flush()
                await session.commit()
                logger.info(f"Added {len(vectors)} vectors to collection '{collection_name}'")
                return True
                
        except Exception as e:
            logger.error(f"Error adding vectors: {str(e)}")
            raise
    
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
        Falls back to Python-based similarity if pgvector is not available.
        """
        try:
            async with async_session_maker() as session:
                # Build query to get relevant chunks and calculate distance natively
                query = select(
                    Chunk.id,
                    Chunk.content,
                    Chunk.extra_metadata,
                    Chunk.asset_id,
                    Chunk.embedding.cosine_distance(query_vector).label('distance')
                ).where(
                    Chunk.embedding.isnot(None)
                )
                
                # Apply filters
                if filter_dict:
                    if 'project_id' in filter_dict:
                        query = query.where(Chunk.project_id == filter_dict['project_id'])
                    if 'asset_id' in filter_dict:
                        query = query.where(Chunk.asset_id == filter_dict['asset_id'])
                
                # Offload vector similarity to database
                query = query.order_by('distance').limit(top_k)
                result = await session.execute(query)
                rows = result.all()

                if not rows:
                    return []

                results = [
                    (
                        r.id,
                        1.0 - float(r.distance), # convert distance to similarity
                        {
                            'content': r.content,
                            'metadata': r.extra_metadata,
                            'asset_id': r.asset_id,
                        }
                    )
                    for r in rows
                ]

                logger.info(f"Found {len(results)} similar chunks (pgvector cosine)")
                return results
                
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise
    
    async def delete_collection(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        """
        Delete all chunks for a project.
        
        Args:
            collection_name: Project ID or identifier
            
        Returns:
            True if successful
        """
        try:
            async with async_session_maker() as session:
                project_id = kwargs.get('project_id')
                if project_id:
                    stmt = delete(Chunk).where(Chunk.project_id == project_id)
                    await session.execute(stmt)
                    await session.commit()
                    logger.info(f"Deleted collection '{collection_name}'")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise
    
    async def collection_exists(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        """
        Check if project exists.
        
        Args:
            collection_name: Project name
            
        Returns:
            True if exists
        """
        try:
            async with async_session_maker() as session:
                project_id = kwargs.get('project_id')
                if project_id:
                    stmt = select(Project).where(Project.id == project_id)
                    result = await session.execute(stmt)
                    return result.scalar_one_or_none() is not None
                return False
                
        except Exception as e:
            logger.error(f"Error checking collection: {str(e)}")
            return False
