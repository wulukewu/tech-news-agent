"""
Example usage of the VectorStore class.

This module demonstrates how to use the VectorStore for storing,
searching, updating, and deleting article embeddings.
"""

import asyncio
import logging
from uuid import uuid4

from app.qa_agent.vector_store import VectorStore, VectorStoreError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_store_embedding():
    """Example: Store an article embedding."""
    logger.info("=== Example: Store Embedding ===")

    vector_store = VectorStore()

    # Sample article data
    article_id = uuid4()
    # In production, this would come from an embedding service like OpenAI
    embedding = [0.1] * 1536  # Sample embedding vector
    metadata = {"category": "technology", "language": "en", "technical_depth": 3}
    chunk_text = "This is a sample article about machine learning and AI."

    try:
        await vector_store.store_embedding(
            article_id=article_id,
            embedding=embedding,
            metadata=metadata,
            chunk_index=0,
            chunk_text=chunk_text,
        )
        logger.info(f"✓ Successfully stored embedding for article {article_id}")
        return article_id
    except VectorStoreError as e:
        logger.error(f"✗ Failed to store embedding: {e}")
        return None


async def example_search_similar(user_id):
    """Example: Search for similar articles."""
    logger.info("\n=== Example: Search Similar Articles ===")

    vector_store = VectorStore()

    # Sample query vector (in production, this would be the user's query embedding)
    query_vector = [0.1] * 1536

    try:
        matches = await vector_store.search_similar(
            query_vector=query_vector, user_id=user_id, limit=5, threshold=0.7
        )

        logger.info(f"✓ Found {len(matches)} similar articles")
        for i, match in enumerate(matches, 1):
            logger.info(
                f"  {i}. Article {match.article_id} " f"(similarity: {match.similarity_score:.4f})"
            )

        return matches
    except VectorStoreError as e:
        logger.error(f"✗ Failed to search: {e}")
        return []


async def example_search_with_filters(user_id):
    """Example: Search with metadata filters."""
    logger.info("\n=== Example: Search with Metadata Filters ===")

    vector_store = VectorStore()

    query_vector = [0.1] * 1536
    metadata_filters = {"category": "technology", "language": "en"}

    try:
        matches = await vector_store.search_similar(
            query_vector=query_vector,
            user_id=user_id,
            limit=5,
            threshold=0.5,
            metadata_filters=metadata_filters,
        )

        logger.info(f"✓ Found {len(matches)} articles matching filters: {metadata_filters}")
        return matches
    except VectorStoreError as e:
        logger.error(f"✗ Failed to search with filters: {e}")
        return []


async def example_update_embedding(article_id):
    """Example: Update an existing embedding."""
    logger.info("\n=== Example: Update Embedding ===")

    vector_store = VectorStore()

    # New embedding vector
    new_embedding = [0.2] * 1536
    new_metadata = {
        "category": "technology",
        "language": "en",
        "technical_depth": 4,
        "updated": True,
    }

    try:
        await vector_store.update_embedding(
            article_id=article_id, embedding=new_embedding, chunk_index=0, metadata=new_metadata
        )
        logger.info(f"✓ Successfully updated embedding for article {article_id}")
    except VectorStoreError as e:
        logger.error(f"✗ Failed to update embedding: {e}")


async def example_get_embedding(article_id):
    """Example: Retrieve an embedding."""
    logger.info("\n=== Example: Get Embedding ===")

    vector_store = VectorStore()

    try:
        embedding = await vector_store.get_embedding(article_id=article_id, chunk_index=0)

        if embedding:
            logger.info(
                f"✓ Retrieved embedding for article {article_id} " f"(dimension: {len(embedding)})"
            )
        else:
            logger.info(f"✗ No embedding found for article {article_id}")

        return embedding
    except VectorStoreError as e:
        logger.error(f"✗ Failed to retrieve embedding: {e}")
        return None


async def example_count_embeddings(user_id=None):
    """Example: Count embeddings."""
    logger.info("\n=== Example: Count Embeddings ===")

    vector_store = VectorStore()

    try:
        if user_id:
            count = await vector_store.count_embeddings(user_id=user_id)
            logger.info(f"✓ User {user_id} has access to {count} articles")
        else:
            count = await vector_store.count_embeddings()
            logger.info(f"✓ Total embeddings in store: {count}")

        return count
    except VectorStoreError as e:
        logger.error(f"✗ Failed to count embeddings: {e}")
        return 0


async def example_delete_embedding(article_id):
    """Example: Delete an embedding."""
    logger.info("\n=== Example: Delete Embedding ===")

    vector_store = VectorStore()

    try:
        # Delete specific chunk
        deleted_count = await vector_store.delete_embedding(article_id=article_id, chunk_index=0)
        logger.info(f"✓ Deleted {deleted_count} embedding(s) for article {article_id}")

        return deleted_count
    except VectorStoreError as e:
        logger.error(f"✗ Failed to delete embedding: {e}")
        return 0


async def example_health_check():
    """Example: Perform health check."""
    logger.info("\n=== Example: Health Check ===")

    vector_store = VectorStore()

    health = await vector_store.health_check()

    logger.info("Health Status:")
    logger.info(f"  Healthy: {health['healthy']}")
    logger.info(f"  pgvector Available: {health['pgvector_available']}")
    logger.info(f"  Table Exists: {health['embeddings_table_exists']}")
    logger.info(f"  Total Embeddings: {health['total_embeddings']}")

    if health["error"]:
        logger.error(f"  Error: {health['error']}")

    return health


async def example_chunked_article():
    """Example: Store a chunked article with multiple embeddings."""
    logger.info("\n=== Example: Chunked Article ===")

    vector_store = VectorStore()

    article_id = uuid4()

    # Simulate a long article split into 3 chunks
    chunks = [
        {
            "text": "Introduction to machine learning and its applications...",
            "embedding": [0.1 + i * 0.01] * 1536,
            "metadata": {"section": "introduction", "chunk": i},
        }
        for i in range(3)
    ]

    try:
        for i, chunk in enumerate(chunks):
            await vector_store.store_embedding(
                article_id=article_id,
                embedding=chunk["embedding"],
                metadata=chunk["metadata"],
                chunk_index=i,
                chunk_text=chunk["text"],
            )

        logger.info(f"✓ Successfully stored {len(chunks)} chunks for article {article_id}")
        return article_id
    except VectorStoreError as e:
        logger.error(f"✗ Failed to store chunked article: {e}")
        return None


async def main():
    """Run all examples."""
    logger.info("Starting VectorStore Examples\n")

    # Note: These examples require a running database with pgvector
    # and the article_embeddings table created

    try:
        # Example 1: Health check
        await example_health_check()

        # Example 2: Store embedding
        article_id = await example_store_embedding()

        if article_id:
            # Example 3: Get embedding
            await example_get_embedding(article_id)

            # Example 4: Update embedding
            await example_update_embedding(article_id)

            # Example 5: Count embeddings
            await example_count_embeddings()

            # Example 6: Search similar (requires user_id)
            # user_id = uuid4()  # In production, use actual user ID
            # await example_search_similar(user_id)

            # Example 7: Delete embedding
            await example_delete_embedding(article_id)

        # Example 8: Chunked article
        chunked_article_id = await example_chunked_article()

        if chunked_article_id:
            # Delete all chunks
            vector_store = VectorStore()
            deleted = await vector_store.delete_embedding(
                article_id=chunked_article_id, chunk_index=None  # Delete all chunks
            )
            logger.info(f"\n✓ Cleaned up {deleted} chunks for chunked article")

        logger.info("\n✓ All examples completed successfully!")

    except Exception as e:
        logger.error(f"\n✗ Example execution failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
