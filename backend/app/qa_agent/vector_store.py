"""
Vector Store Implementation for Intelligent Q&A Agent

This module implements the VectorStore class with pgvector integration for
high-performance semantic search across article embeddings.

Validates: Requirements 2.1, 2.2, 10.3, 10.5
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.qa_agent.constants import PerformanceLimits, ScoringThresholds
from app.qa_agent.database import get_db_connection

logger = logging.getLogger(__name__)


class VectorMatch:
    """
    Represents a vector similarity search match result.

    Attributes:
        article_id: UUID of the matched article
        similarity_score: Cosine similarity score (0-1, higher is better)
        metadata: Additional metadata from the embedding record
        chunk_index: Index of the chunk if article was chunked
        chunk_text: The text chunk that was matched
    """

    def __init__(
        self,
        article_id: UUID,
        similarity_score: float,
        metadata: Dict[str, Any],
        chunk_index: int = 0,
        chunk_text: Optional[str] = None,
    ):
        self.article_id = article_id
        self.similarity_score = similarity_score
        self.metadata = metadata
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text

    def __repr__(self) -> str:
        return (
            f"VectorMatch(article_id={self.article_id}, "
            f"similarity_score={self.similarity_score:.4f}, "
            f"chunk_index={self.chunk_index})"
        )


class VectorStoreError(Exception):
    """Base exception for VectorStore operations."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class VectorStore:
    """
    High-performance vector store implementation using pgvector.

    Provides methods for storing, updating, deleting, and searching article
    embeddings with user-specific isolation and metadata filtering.

    Validates: Requirements 2.1, 2.2, 10.3, 10.5
    """

    def __init__(self):
        """Initialize the VectorStore."""
        self._embedding_dimension = PerformanceLimits.MAX_EMBEDDING_DIMENSION
        logger.info(f"VectorStore initialized with dimension {self._embedding_dimension}")

    async def store_embedding(
        self,
        article_id: UUID,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        chunk_index: int = 0,
        chunk_text: Optional[str] = None,
    ) -> None:
        """
        Store an article embedding in the vector store.

        Args:
            article_id: UUID of the article
            embedding: Vector embedding (must be 1536 dimensions for OpenAI)
            metadata: Optional metadata dictionary
            chunk_index: Index for chunked articles (default 0 for single chunk)
            chunk_text: The text chunk that was embedded

        Raises:
            VectorStoreError: If storage operation fails
            ValueError: If embedding dimension is invalid

        Validates: Requirements 2.1, 7.1
        """
        # Validate embedding
        if not embedding or len(embedding) != self._embedding_dimension:
            raise ValueError(
                f"Invalid embedding dimension. Expected {self._embedding_dimension}, "
                f"got {len(embedding) if embedding else 0}"
            )

        # Validate metadata
        metadata = metadata or {}

        try:
            async with get_db_connection() as conn:
                # Convert embedding list to pgvector format
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"

                # Insert or update embedding
                await conn.execute(
                    """
                    INSERT INTO article_embeddings (
                        article_id, embedding, chunk_index, chunk_text, metadata, created_at
                    )
                    VALUES ($1, $2::vector, $3, $4, $5, NOW())
                    ON CONFLICT (article_id, chunk_index)
                    DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        chunk_text = EXCLUDED.chunk_text,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """,
                    article_id,
                    embedding_str,
                    chunk_index,
                    chunk_text,
                    metadata,
                )

                logger.debug(f"Stored embedding for article {article_id}, chunk {chunk_index}")

        except Exception as e:
            logger.error(f"Failed to store embedding for article {article_id}: {e}", exc_info=True)
            raise VectorStoreError(f"Failed to store embedding: {e}", original_error=e)

    async def search_similar(
        self,
        query_vector: List[float],
        user_id: UUID,
        limit: int = 10,
        threshold: float = ScoringThresholds.MIN_SIMILARITY_THRESHOLD,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorMatch]:
        """
        Search for similar articles using vector similarity.

        This method performs user-specific search isolation, ensuring users
        only see results from their own article collection.

        Args:
            query_vector: Query embedding vector
            user_id: UUID of the user (for access isolation)
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0-1, default 0.3)
            metadata_filters: Optional metadata filters to apply

        Returns:
            List of VectorMatch objects sorted by similarity (highest first)

        Raises:
            VectorStoreError: If search operation fails
            ValueError: If query_vector dimension is invalid

        Validates: Requirements 2.2, 2.3, 10.5
        """
        # Validate query vector
        if not query_vector or len(query_vector) != self._embedding_dimension:
            raise ValueError(
                f"Invalid query vector dimension. Expected {self._embedding_dimension}, "
                f"got {len(query_vector) if query_vector else 0}"
            )

        # Validate threshold
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0 and 1, got {threshold}")

        # Validate limit
        limit = min(limit, PerformanceLimits.MAX_VECTOR_SEARCH_RESULTS)

        try:
            async with get_db_connection() as conn:
                # Convert query vector to pgvector format
                query_vector_str = f"[{','.join(str(x) for x in query_vector)}]"

                # Build the query with user isolation
                # Note: We use cosine distance (1 - cosine_similarity)
                # So we need to convert: similarity = 1 - distance
                query = """
                    SELECT
                        ae.article_id,
                        ae.chunk_index,
                        ae.chunk_text,
                        ae.metadata,
                        1 - (ae.embedding <=> $1::vector) AS similarity_score
                    FROM article_embeddings ae
                    INNER JOIN articles a ON ae.article_id = a.id
                    INNER JOIN user_subscriptions us ON a.feed_id = us.feed_id
                    WHERE us.user_id = $2
                        AND ae.deleted_at IS NULL
                        AND a.deleted_at IS NULL
                        AND (1 - (ae.embedding <=> $1::vector)) >= $3
                """

                params = [query_vector_str, user_id, threshold]

                # Add metadata filters if provided
                if metadata_filters:
                    for key, value in metadata_filters.items():
                        query += f" AND ae.metadata->>'{key}' = ${len(params) + 1}"
                        params.append(str(value))

                # Order by similarity and limit results
                query += """
                    ORDER BY similarity_score DESC
                    LIMIT $%d
                """ % (len(params) + 1)
                params.append(limit)

                # Execute search
                rows = await conn.fetch(query, *params)

                # Convert results to VectorMatch objects
                matches = [
                    VectorMatch(
                        article_id=row["article_id"],
                        similarity_score=float(row["similarity_score"]),
                        metadata=row["metadata"] or {},
                        chunk_index=row["chunk_index"],
                        chunk_text=row["chunk_text"],
                    )
                    for row in rows
                ]

                logger.debug(
                    f"Found {len(matches)} similar articles for user {user_id} "
                    f"with threshold {threshold}"
                )

                return matches

        except Exception as e:
            logger.error(
                f"Failed to search similar articles for user {user_id}: {e}", exc_info=True
            )
            raise VectorStoreError(f"Failed to search similar articles: {e}", original_error=e)

    async def update_embedding(
        self,
        article_id: UUID,
        embedding: List[float],
        chunk_index: int = 0,
        chunk_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update an existing article embedding.

        Args:
            article_id: UUID of the article
            embedding: New vector embedding
            chunk_index: Index of the chunk to update (default 0)
            chunk_text: Updated text chunk
            metadata: Updated metadata

        Raises:
            VectorStoreError: If update operation fails
            ValueError: If embedding dimension is invalid

        Validates: Requirements 5.3, 7.5
        """
        # Validate embedding
        if not embedding or len(embedding) != self._embedding_dimension:
            raise ValueError(
                f"Invalid embedding dimension. Expected {self._embedding_dimension}, "
                f"got {len(embedding) if embedding else 0}"
            )

        try:
            async with get_db_connection() as conn:
                # Convert embedding to pgvector format
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"

                # Build update query
                query = """
                    UPDATE article_embeddings
                    SET embedding = $1::vector,
                        updated_at = NOW()
                """
                params = [embedding_str]
                param_count = 1

                # Add optional fields
                if chunk_text is not None:
                    param_count += 1
                    query += f", chunk_text = ${param_count}"
                    params.append(chunk_text)

                if metadata is not None:
                    param_count += 1
                    query += f", metadata = ${param_count}"
                    params.append(metadata)

                # Add WHERE clause
                param_count += 1
                query += f" WHERE article_id = ${param_count}"
                params.append(article_id)

                param_count += 1
                query += f" AND chunk_index = ${param_count}"
                params.append(chunk_index)

                query += " AND deleted_at IS NULL"

                # Execute update
                result = await conn.execute(query, *params)

                # Check if any rows were updated
                rows_updated = int(result.split()[-1]) if result else 0

                if rows_updated == 0:
                    logger.warning(
                        f"No embedding found to update for article {article_id}, "
                        f"chunk {chunk_index}"
                    )
                else:
                    logger.debug(f"Updated embedding for article {article_id}, chunk {chunk_index}")

        except Exception as e:
            logger.error(f"Failed to update embedding for article {article_id}: {e}", exc_info=True)
            raise VectorStoreError(f"Failed to update embedding: {e}", original_error=e)

    async def delete_embedding(self, article_id: UUID, chunk_index: Optional[int] = None) -> int:
        """
        Delete article embedding(s) from the vector store.

        Uses soft delete to maintain audit trail. If chunk_index is None,
        deletes all chunks for the article.

        Args:
            article_id: UUID of the article
            chunk_index: Optional specific chunk to delete (None = all chunks)

        Returns:
            Number of embeddings deleted

        Raises:
            VectorStoreError: If delete operation fails

        Validates: Requirements 5.3, 10.4
        """
        try:
            async with get_db_connection() as conn:
                if chunk_index is not None:
                    # Delete specific chunk
                    result = await conn.execute(
                        """
                        UPDATE article_embeddings
                        SET deleted_at = NOW()
                        WHERE article_id = $1
                            AND chunk_index = $2
                            AND deleted_at IS NULL
                        """,
                        article_id,
                        chunk_index,
                    )
                else:
                    # Delete all chunks for the article
                    result = await conn.execute(
                        """
                        UPDATE article_embeddings
                        SET deleted_at = NOW()
                        WHERE article_id = $1
                            AND deleted_at IS NULL
                        """,
                        article_id,
                    )

                # Extract number of rows affected
                rows_deleted = int(result.split()[-1]) if result else 0

                logger.debug(
                    f"Deleted {rows_deleted} embedding(s) for article {article_id}"
                    + (f", chunk {chunk_index}" if chunk_index is not None else "")
                )

                return rows_deleted

        except Exception as e:
            logger.error(f"Failed to delete embedding for article {article_id}: {e}", exc_info=True)
            raise VectorStoreError(f"Failed to delete embedding: {e}", original_error=e)

    async def get_embedding(self, article_id: UUID, chunk_index: int = 0) -> Optional[List[float]]:
        """
        Retrieve an embedding vector for an article.

        Args:
            article_id: UUID of the article
            chunk_index: Index of the chunk (default 0)

        Returns:
            Embedding vector as list of floats, or None if not found

        Raises:
            VectorStoreError: If retrieval operation fails
        """
        try:
            async with get_db_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT embedding
                    FROM article_embeddings
                    WHERE article_id = $1
                        AND chunk_index = $2
                        AND deleted_at IS NULL
                    """,
                    article_id,
                    chunk_index,
                )

                if row and row["embedding"]:
                    # Convert pgvector to list of floats
                    return list(row["embedding"])

                return None

        except Exception as e:
            logger.error(
                f"Failed to retrieve embedding for article {article_id}: {e}", exc_info=True
            )
            raise VectorStoreError(f"Failed to retrieve embedding: {e}", original_error=e)

    async def count_embeddings(self, user_id: Optional[UUID] = None) -> int:
        """
        Count total embeddings in the store.

        Args:
            user_id: Optional user ID to count only their accessible embeddings

        Returns:
            Total number of embeddings

        Raises:
            VectorStoreError: If count operation fails
        """
        try:
            async with get_db_connection() as conn:
                if user_id:
                    # Count user-accessible embeddings
                    count = await conn.fetchval(
                        """
                        SELECT COUNT(DISTINCT ae.article_id)
                        FROM article_embeddings ae
                        INNER JOIN articles a ON ae.article_id = a.id
                        INNER JOIN user_subscriptions us ON a.feed_id = us.feed_id
                        WHERE us.user_id = $1
                            AND ae.deleted_at IS NULL
                            AND a.deleted_at IS NULL
                        """,
                        user_id,
                    )
                else:
                    # Count all embeddings
                    count = await conn.fetchval("""
                        SELECT COUNT(*)
                        FROM article_embeddings
                        WHERE deleted_at IS NULL
                        """)

                return count or 0

        except Exception as e:
            logger.error(f"Failed to count embeddings: {e}", exc_info=True)
            raise VectorStoreError(f"Failed to count embeddings: {e}", original_error=e)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the vector store.

        Returns:
            Dictionary containing health check results
        """
        health_status = {
            "healthy": False,
            "pgvector_available": False,
            "embeddings_table_exists": False,
            "total_embeddings": 0,
            "error": None,
        }

        try:
            async with get_db_connection() as conn:
                # Check pgvector extension
                pgvector_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                health_status["pgvector_available"] = pgvector_exists

                if not pgvector_exists:
                    health_status["error"] = "pgvector extension not available"
                    return health_status

                # Check table exists
                table_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'article_embeddings'
                    )
                    """)
                health_status["embeddings_table_exists"] = table_exists

                if not table_exists:
                    health_status["error"] = "article_embeddings table does not exist"
                    return health_status

                # Count embeddings
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM article_embeddings WHERE deleted_at IS NULL"
                )
                health_status["total_embeddings"] = count or 0

                # Test vector operations
                await conn.fetchval("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")

                health_status["healthy"] = True

        except Exception as e:
            health_status["error"] = str(e)
            logger.error(f"Vector store health check failed: {e}", exc_info=True)

        return health_status


# Convenience function for getting a VectorStore instance
def get_vector_store() -> VectorStore:
    """
    Get a VectorStore instance.

    Returns:
        VectorStore instance
    """
    return VectorStore()
