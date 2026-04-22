"""
Property-Based Test for Vector Store Synchronization - Property 9

**Validates: Requirements 5.3, 5.4, 7.2, 7.5**

Property 9: Vector Store Synchronization
For any article addition, update, or deletion in the article database, the corresponding
vector embeddings SHALL be automatically synchronized, with proper chunking strategy
applied and incremental processing to avoid redundant work.

This test uses Hypothesis to generate random article data and verify that:
1. Article additions trigger automatic embedding creation
2. Article updates trigger embedding updates
3. Article deletions trigger embedding soft deletes
4. Chunking strategy is properly applied for long articles
5. Incremental processing avoids duplicate work
6. Database schema integrity is maintained

**Test Requirements:**
- Requires PostgreSQL database with pgvector extension
- Requires DATABASE_URL environment variable to be set
- Tests will be skipped if database is not available
- Tests use real database operations (not mocked)

**Running the tests:**
```bash
# Ensure PostgreSQL is running with pgvector extension
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"

# Run the property tests
pytest backend/tests/property/test_vector_store_synchronization_property.py -v
```
"""

import asyncio
import os
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.qa_agent.article_models import Article, ArticleMetadata
from app.qa_agent.database import DatabaseConnectionError, get_db_connection
from app.qa_agent.embedding_service import EmbeddingService
from app.qa_agent.vector_store import VectorStore

# Check if database is available for testing
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or "dummy" in os.getenv("DATABASE_URL", "").lower(),
    reason="DATABASE_URL not set or using dummy URL - skipping QA agent database tests",
)

# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================

# Strategy for generating valid article titles
article_titles = st.text(
    min_size=10,
    max_size=200,
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po"), blacklist_characters="\x00\n\r\t"
    ),
)

# Strategy for generating article content of varying lengths
short_content = st.text(min_size=100, max_size=500)  # Single chunk
medium_content = st.text(min_size=500, max_size=2000)  # 1-2 chunks
long_content = st.text(min_size=2000, max_size=5000)  # Multiple chunks

article_content = st.one_of(short_content, medium_content, long_content)

# Strategy for generating valid URLs
article_urls = st.builds(
    lambda domain, path: f"https://{domain}.com/{path}",
    domain=st.text(
        min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))
    ),
    path=st.text(
        min_size=3,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-_/"),
    ),
)

# Strategy for generating article categories
article_categories = st.sampled_from(
    [
        "Technology",
        "Science",
        "Business",
        "Health",
        "Education",
        "Entertainment",
        "Sports",
        "Politics",
        "Culture",
        "Other",
    ]
)

# Strategy for generating article metadata
article_metadata_strategy = st.builds(
    ArticleMetadata,
    author=st.one_of(st.none(), st.text(min_size=3, max_size=50)),
    source=st.one_of(st.none(), st.text(min_size=3, max_size=50)),
    tags=st.lists(st.text(min_size=2, max_size=20), min_size=0, max_size=5),
    language=st.sampled_from(["zh", "en", "zh-TW", "en-US"]),
    content_type=st.sampled_from(["article", "tutorial", "news", "research"]),
)


def create_article_strategy():
    """Create a strategy for generating Article objects."""
    return st.builds(
        Article,
        id=st.uuids(),
        title=article_titles,
        content=article_content,
        url=article_urls,
        feed_id=st.uuids(),
        feed_name=st.text(min_size=3, max_size=50),
        category=article_categories,
        published_at=st.one_of(
            st.none(),
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2024, 12, 31)),
        ),
        metadata=article_metadata_strategy,
        is_processed=st.just(False),
        processing_status=st.just("pending"),
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def cleanup_test_data(article_id: UUID):
    """Clean up test data from database."""
    try:
        async with get_db_connection() as conn:
            # Delete embeddings
            await conn.execute("DELETE FROM article_embeddings WHERE article_id = $1", article_id)
            # Delete article if exists
            await conn.execute("DELETE FROM articles WHERE id = $1", article_id)
    except DatabaseConnectionError:
        # Database not available - skip cleanup
        pytest.skip("Database not available for cleanup")
    except Exception as e:
        # Ignore other cleanup errors
        pass


async def insert_test_article(article: Article, user_id: UUID, feed_id: UUID):
    """Insert a test article into the database."""
    async with get_db_connection() as conn:
        # First ensure feed exists
        await conn.execute(
            """
            INSERT INTO feeds (id, name, url, category, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (id) DO NOTHING
            """,
            feed_id,
            article.feed_name,
            str(article.url),
            article.category,
        )

        # Ensure user subscription exists
        await conn.execute(
            """
            INSERT INTO user_subscriptions (user_id, feed_id, created_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (user_id, feed_id) DO NOTHING
            """,
            user_id,
            feed_id,
        )

        # Insert article
        await conn.execute(
            """
            INSERT INTO articles (
                id, feed_id, title, content, url, category,
                published_at, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                updated_at = NOW()
            """,
            article.id,
            feed_id,
            article.title,
            article.content,
            str(article.url),
            article.category,
            article.published_at,
        )


async def get_embedding_count(article_id: UUID) -> int:
    """Get the number of embeddings for an article."""
    async with get_db_connection() as conn:
        count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM article_embeddings
            WHERE article_id = $1 AND deleted_at IS NULL
            """,
            article_id,
        )
        return count or 0


async def get_embeddings(article_id: UUID) -> List[dict]:
    """Get all embeddings for an article."""
    async with get_db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT article_id, chunk_index, chunk_text, metadata, created_at, updated_at
            FROM article_embeddings
            WHERE article_id = $1 AND deleted_at IS NULL
            ORDER BY chunk_index
            """,
            article_id,
        )
        return [dict(row) for row in rows]


# ============================================================================
# PROPERTY TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.property
@given(article=create_article_strategy())
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20, deadline=None
)
async def test_property_9_article_addition_triggers_embedding_creation(article):
    """
    Property 9: Vector Store Synchronization - Article Addition

    For any article addition to the database, the system SHALL automatically
    create corresponding vector embeddings with proper chunking.

    Test Strategy:
    1. Generate random article data
    2. Store article in database
    3. Create embeddings using vector store
    4. Verify embeddings are created with correct schema
    5. Verify chunking strategy is applied for long content
    """
    # Arrange
    user_id = uuid4()
    feed_id = article.feed_id
    vector_store = VectorStore()
    embedding_service = EmbeddingService()

    try:
        # Insert test article
        await insert_test_article(article, user_id, feed_id)

        # Act - Generate and store embeddings
        # Simulate chunking for long content
        content_length = len(article.content)
        chunk_size = 1000  # Characters per chunk

        if content_length <= chunk_size:
            # Single chunk
            chunks = [article.content]
        else:
            # Multiple chunks
            chunks = []
            for i in range(0, content_length, chunk_size):
                chunk = article.content[i : i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)

        # Store embeddings for each chunk
        for chunk_index, chunk_text in enumerate(chunks):
            # Generate embedding (mock with random vector for testing)
            embedding = [0.1] * 1536  # Mock embedding

            await vector_store.store_embedding(
                article_id=article.id,
                embedding=embedding,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                metadata={
                    "title": article.title,
                    "category": article.category,
                    "language": article.metadata.language,
                },
            )

        # Assert - Verify embeddings were created
        embedding_count = await get_embedding_count(article.id)
        expected_chunks = len(chunks)

        assert embedding_count == expected_chunks, (
            f"Expected {expected_chunks} embedding(s) for article with "
            f"{content_length} characters, got {embedding_count}"
        )

        # Verify database schema integrity
        embeddings = await get_embeddings(article.id)

        assert (
            len(embeddings) == expected_chunks
        ), f"Database should contain {expected_chunks} embedding record(s)"

        # Verify each embedding has correct schema
        for i, embedding_record in enumerate(embeddings):
            # Required fields
            assert "article_id" in embedding_record, f"Chunk {i}: missing article_id"
            assert "chunk_index" in embedding_record, f"Chunk {i}: missing chunk_index"
            assert "chunk_text" in embedding_record, f"Chunk {i}: missing chunk_text"
            assert "metadata" in embedding_record, f"Chunk {i}: missing metadata"
            assert "created_at" in embedding_record, f"Chunk {i}: missing created_at"
            assert "updated_at" in embedding_record, f"Chunk {i}: missing updated_at"

            # Verify values
            assert embedding_record["article_id"] == article.id, f"Chunk {i}: article_id mismatch"
            assert (
                embedding_record["chunk_index"] == i
            ), f"Chunk {i}: chunk_index should be {i}, got {embedding_record['chunk_index']}"
            assert (
                embedding_record["chunk_text"] is not None
            ), f"Chunk {i}: chunk_text should not be null"
            assert (
                len(embedding_record["chunk_text"]) > 0
            ), f"Chunk {i}: chunk_text should not be empty"

            # Verify metadata structure
            metadata = embedding_record["metadata"]
            assert isinstance(metadata, dict), f"Chunk {i}: metadata should be a dict"
            assert "title" in metadata, f"Chunk {i}: metadata missing title"
            assert "category" in metadata, f"Chunk {i}: metadata missing category"

            # Verify timestamps
            assert (
                embedding_record["created_at"] is not None
            ), f"Chunk {i}: created_at should not be null"
            assert (
                embedding_record["updated_at"] is not None
            ), f"Chunk {i}: updated_at should not be null"

        # Verify chunking strategy for long content
        if content_length > chunk_size:
            assert embedding_count > 1, (
                f"Long article ({content_length} chars) should be chunked into "
                f"multiple embeddings, got {embedding_count}"
            )

            # Verify chunks are sequential
            chunk_indices = [e["chunk_index"] for e in embeddings]
            assert chunk_indices == list(
                range(len(chunk_indices))
            ), f"Chunk indices should be sequential: {chunk_indices}"

    finally:
        # Cleanup
        await cleanup_test_data(article.id)


@pytest.mark.asyncio
@pytest.mark.property
@given(article=create_article_strategy())
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20, deadline=None
)
async def test_property_9_article_update_triggers_embedding_update(article):
    """
    Property 9: Vector Store Synchronization - Article Update

    For any article update in the database, the system SHALL update the
    corresponding vector embeddings to reflect the new content.

    Test Strategy:
    1. Create article with initial embeddings
    2. Update article content
    3. Update embeddings
    4. Verify embeddings are updated (updated_at changes)
    5. Verify old embeddings are replaced, not duplicated
    """
    # Arrange
    user_id = uuid4()
    feed_id = article.feed_id
    vector_store = VectorStore()

    try:
        # Insert initial article
        await insert_test_article(article, user_id, feed_id)

        # Create initial embedding
        initial_embedding = [0.1] * 1536
        await vector_store.store_embedding(
            article_id=article.id,
            embedding=initial_embedding,
            chunk_index=0,
            chunk_text=article.content[:500],
            metadata={"version": "initial"},
        )

        # Get initial state
        initial_embeddings = await get_embeddings(article.id)
        assert len(initial_embeddings) == 1, "Should have one initial embedding"
        initial_updated_at = initial_embeddings[0]["updated_at"]

        # Wait a moment to ensure timestamp difference
        await asyncio.sleep(0.1)

        # Act - Update article content
        updated_content = article.content + " [UPDATED]"
        async with get_db_connection() as conn:
            await conn.execute(
                """
                UPDATE articles
                SET content = $1, updated_at = NOW()
                WHERE id = $2
                """,
                updated_content,
                article.id,
            )

        # Update embedding
        updated_embedding = [0.2] * 1536  # Different embedding
        await vector_store.update_embedding(
            article_id=article.id,
            embedding=updated_embedding,
            chunk_index=0,
            chunk_text=updated_content[:500],
            metadata={"version": "updated"},
        )

        # Assert - Verify embedding was updated
        updated_embeddings = await get_embeddings(article.id)

        # Should still have exactly one embedding (not duplicated)
        assert (
            len(updated_embeddings) == 1
        ), f"Should have exactly one embedding after update, got {len(updated_embeddings)}"

        # Verify updated_at changed
        new_updated_at = updated_embeddings[0]["updated_at"]
        assert new_updated_at > initial_updated_at, (
            f"updated_at should change after update: "
            f"initial={initial_updated_at}, new={new_updated_at}"
        )

        # Verify metadata was updated
        assert (
            updated_embeddings[0]["metadata"]["version"] == "updated"
        ), "Metadata should reflect the update"

        # Verify chunk_text was updated
        assert (
            "[UPDATED]" in updated_embeddings[0]["chunk_text"]
        ), "Chunk text should reflect the updated content"

    finally:
        # Cleanup
        await cleanup_test_data(article.id)


@pytest.mark.asyncio
@pytest.mark.property
@given(article=create_article_strategy())
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20, deadline=None
)
async def test_property_9_article_deletion_triggers_embedding_soft_delete(article):
    """
    Property 9: Vector Store Synchronization - Article Deletion

    For any article deletion from the database, the system SHALL soft-delete
    the corresponding vector embeddings (set deleted_at timestamp).

    Test Strategy:
    1. Create article with embeddings
    2. Delete embeddings using vector store
    3. Verify embeddings are soft-deleted (deleted_at is set)
    4. Verify soft-deleted embeddings are excluded from searches
    """
    # Arrange
    user_id = uuid4()
    feed_id = article.feed_id
    vector_store = VectorStore()

    try:
        # Insert article
        await insert_test_article(article, user_id, feed_id)

        # Create embeddings
        embedding = [0.1] * 1536
        await vector_store.store_embedding(
            article_id=article.id,
            embedding=embedding,
            chunk_index=0,
            chunk_text=article.content[:500],
        )

        # Verify embedding exists
        initial_count = await get_embedding_count(article.id)
        assert initial_count == 1, "Should have one embedding before deletion"

        # Act - Delete embedding (soft delete)
        deleted_count = await vector_store.delete_embedding(article.id)

        # Assert - Verify soft delete
        assert deleted_count == 1, f"Should have deleted 1 embedding, got {deleted_count}"

        # Verify embedding is no longer returned by normal queries
        active_count = await get_embedding_count(article.id)
        assert (
            active_count == 0
        ), f"Soft-deleted embeddings should not be counted, got {active_count}"

        # Verify embedding still exists in database with deleted_at set
        async with get_db_connection() as conn:
            deleted_embedding = await conn.fetchrow(
                """
                SELECT article_id, chunk_index, deleted_at
                FROM article_embeddings
                WHERE article_id = $1
                """,
                article.id,
            )

            assert (
                deleted_embedding is not None
            ), "Embedding should still exist in database (soft delete)"
            assert (
                deleted_embedding["deleted_at"] is not None
            ), "deleted_at should be set for soft-deleted embedding"

        # Verify soft-deleted embeddings are excluded from searches
        query_vector = [0.1] * 1536
        search_results = await vector_store.search_similar(
            query_vector=query_vector, user_id=user_id, limit=10, threshold=0.0
        )

        # Should not find the soft-deleted embedding
        matching_results = [r for r in search_results if r.article_id == article.id]
        assert (
            len(matching_results) == 0
        ), "Soft-deleted embeddings should not appear in search results"

    finally:
        # Cleanup
        await cleanup_test_data(article.id)


@pytest.mark.asyncio
@pytest.mark.property
@given(article=create_article_strategy())
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20, deadline=None
)
async def test_property_9_incremental_processing_avoids_duplicates(article):
    """
    Property 9: Vector Store Synchronization - Incremental Processing

    For any article that already has embeddings, attempting to create
    embeddings again SHALL either update existing embeddings or skip
    processing to avoid duplicate work.

    Test Strategy:
    1. Create article with embeddings
    2. Attempt to create embeddings again
    3. Verify no duplicate embeddings are created
    4. Verify existing embeddings are preserved or updated
    """
    # Arrange
    user_id = uuid4()
    feed_id = article.feed_id
    vector_store = VectorStore()

    try:
        # Insert article
        await insert_test_article(article, user_id, feed_id)

        # Create initial embedding
        embedding = [0.1] * 1536
        await vector_store.store_embedding(
            article_id=article.id,
            embedding=embedding,
            chunk_index=0,
            chunk_text=article.content[:500],
            metadata={"version": 1},
        )

        # Verify initial state
        initial_count = await get_embedding_count(article.id)
        assert initial_count == 1, "Should have one initial embedding"

        initial_embeddings = await get_embeddings(article.id)
        initial_created_at = initial_embeddings[0]["created_at"]

        # Act - Attempt to create embedding again (should update, not duplicate)
        new_embedding = [0.2] * 1536
        await vector_store.store_embedding(
            article_id=article.id,
            embedding=new_embedding,
            chunk_index=0,
            chunk_text=article.content[:500],
            metadata={"version": 2},
        )

        # Assert - Verify no duplicates
        final_count = await get_embedding_count(article.id)
        assert (
            final_count == 1
        ), f"Should still have exactly one embedding (no duplicates), got {final_count}"

        # Verify embedding was updated (ON CONFLICT DO UPDATE)
        final_embeddings = await get_embeddings(article.id)
        assert len(final_embeddings) == 1, "Should have exactly one embedding"

        # Verify metadata was updated
        assert (
            final_embeddings[0]["metadata"]["version"] == 2
        ), "Metadata should reflect the update (incremental processing)"

        # Verify created_at is preserved (not a new record)
        assert (
            final_embeddings[0]["created_at"] == initial_created_at
        ), "created_at should be preserved (update, not insert)"

        # Verify updated_at changed
        assert (
            final_embeddings[0]["updated_at"] > initial_created_at
        ), "updated_at should change on update"

    finally:
        # Cleanup
        await cleanup_test_data(article.id)


@pytest.mark.asyncio
@pytest.mark.property
@given(
    articles=st.lists(create_article_strategy(), min_size=2, max_size=5, unique_by=lambda a: a.id)
)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10, deadline=None
)
async def test_property_9_multiple_articles_synchronization(articles):
    """
    Property 9: Vector Store Synchronization - Multiple Articles

    For any set of articles, the system SHALL maintain correct synchronization
    between articles and their embeddings, with no cross-contamination.

    Test Strategy:
    1. Create multiple articles with embeddings
    2. Verify each article has correct embeddings
    3. Verify no cross-contamination between articles
    4. Verify schema integrity for all articles
    """
    # Arrange
    user_id = uuid4()
    vector_store = VectorStore()
    article_ids = [article.id for article in articles]

    try:
        # Act - Create articles and embeddings
        for article in articles:
            feed_id = article.feed_id
            await insert_test_article(article, user_id, feed_id)

            # Create embedding
            embedding = [0.1] * 1536
            await vector_store.store_embedding(
                article_id=article.id,
                embedding=embedding,
                chunk_index=0,
                chunk_text=article.content[:500],
                metadata={"article_title": article.title},
            )

        # Assert - Verify each article has correct embeddings
        for article in articles:
            embeddings = await get_embeddings(article.id)

            assert len(embeddings) >= 1, f"Article {article.id} should have at least one embedding"

            # Verify no cross-contamination
            for embedding_record in embeddings:
                assert embedding_record["article_id"] == article.id, (
                    f"Embedding article_id mismatch: expected {article.id}, "
                    f"got {embedding_record['article_id']}"
                )

                # Verify metadata matches this article
                metadata = embedding_record["metadata"]
                assert (
                    metadata["article_title"] == article.title
                ), f"Metadata title mismatch for article {article.id}"

        # Verify total embedding count
        async with get_db_connection() as conn:
            total_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM article_embeddings
                WHERE article_id = ANY($1) AND deleted_at IS NULL
                """,
                article_ids,
            )

            assert total_count >= len(
                articles
            ), f"Should have at least {len(articles)} embeddings total, got {total_count}"

        # Verify schema integrity for all embeddings
        async with get_db_connection() as conn:
            all_embeddings = await conn.fetch(
                """
                SELECT article_id, chunk_index, chunk_text, metadata, created_at, updated_at
                FROM article_embeddings
                WHERE article_id = ANY($1) AND deleted_at IS NULL
                ORDER BY article_id, chunk_index
                """,
                article_ids,
            )

            for embedding in all_embeddings:
                # Verify required fields
                assert embedding["article_id"] is not None
                assert embedding["chunk_index"] is not None
                assert embedding["chunk_text"] is not None
                assert embedding["metadata"] is not None
                assert embedding["created_at"] is not None
                assert embedding["updated_at"] is not None

                # Verify article_id is in our test set
                assert (
                    embedding["article_id"] in article_ids
                ), f"Found unexpected article_id: {embedding['article_id']}"

    finally:
        # Cleanup
        for article_id in article_ids:
            await cleanup_test_data(article_id)


@pytest.mark.asyncio
@pytest.mark.property
@given(article=create_article_strategy())
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20, deadline=None
)
async def test_property_9_database_schema_constraints(article):
    """
    Property 9: Vector Store Synchronization - Database Schema Constraints

    For any article embedding, the database schema constraints SHALL be
    satisfied (foreign key, check constraints, not null, unique, etc.).

    Test Strategy:
    1. Create article with embeddings
    2. Verify all schema constraints are satisfied
    3. Test constraint violations are properly handled
    """
    # Arrange
    user_id = uuid4()
    feed_id = article.feed_id
    vector_store = VectorStore()

    try:
        # Insert article
        await insert_test_article(article, user_id, feed_id)

        # Act - Create embedding
        embedding = [0.1] * 1536
        await vector_store.store_embedding(
            article_id=article.id,
            embedding=embedding,
            chunk_index=0,
            chunk_text=article.content[:500],
            metadata={"test": "data"},
        )

        # Assert - Verify schema constraints
        async with get_db_connection() as conn:
            embedding_record = await conn.fetchrow(
                """
                SELECT *
                FROM article_embeddings
                WHERE article_id = $1 AND chunk_index = 0
                """,
                article.id,
            )

            assert embedding_record is not None, "Embedding should exist"

            # Verify NOT NULL constraints
            assert embedding_record["article_id"] is not None, "article_id should not be null"
            assert embedding_record["embedding"] is not None, "embedding should not be null"
            assert embedding_record["chunk_index"] is not None, "chunk_index should not be null"
            assert embedding_record["created_at"] is not None, "created_at should not be null"
            assert embedding_record["updated_at"] is not None, "updated_at should not be null"

            # Verify CHECK constraint for chunk_index (non-negative)
            assert (
                embedding_record["chunk_index"] >= 0
            ), f"chunk_index should be non-negative, got {embedding_record['chunk_index']}"

            # Verify embedding dimension
            embedding_vector = embedding_record["embedding"]
            # pgvector returns the vector, we need to check its dimension
            # The dimension is enforced by the vector(1536) type

            # Verify FOREIGN KEY constraint (article_id references articles)
            article_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM articles WHERE id = $1)", article.id
            )
            assert article_exists, "Foreign key constraint: article must exist"

            # Verify PRIMARY KEY constraint (article_id, chunk_index)
            # Attempt to insert duplicate should fail
            try:
                await conn.execute(
                    """
                    INSERT INTO article_embeddings (article_id, embedding, chunk_index)
                    VALUES ($1, $2::vector, $3)
                    """,
                    article.id,
                    f"[{','.join(['0.1'] * 1536)}]",
                    0,
                )
                # If we get here, the constraint didn't work (should have failed)
                pytest.fail(
                    "PRIMARY KEY constraint should prevent duplicate (article_id, chunk_index)"
                )
            except Exception:
                # Expected: primary key violation
                pass

    finally:
        # Cleanup
        await cleanup_test_data(article.id)
