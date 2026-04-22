"""
Unit tests for VectorStore class.

Tests the vector store implementation including storage, retrieval,
search, update, and delete operations with user isolation.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.qa_agent.constants import PerformanceLimits
from app.qa_agent.vector_store import VectorMatch, VectorStore, VectorStoreError


class TestVectorStore:
    """Test suite for VectorStore class."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance for testing."""
        return VectorStore()

    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding vector."""
        return [0.1] * 1536  # OpenAI embedding dimension

    @pytest.fixture
    def sample_article_id(self):
        """Create a sample article UUID."""
        return uuid4()

    @pytest.fixture
    def sample_user_id(self):
        """Create a sample user UUID."""
        return uuid4()

    def test_vector_store_initialization(self, vector_store):
        """Test VectorStore initialization."""
        assert vector_store._embedding_dimension == 1536

    @pytest.mark.asyncio
    async def test_store_embedding_success(self, vector_store, sample_article_id, sample_embedding):
        """Test successful embedding storage."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            await vector_store.store_embedding(
                article_id=sample_article_id,
                embedding=sample_embedding,
                metadata={"category": "tech"},
                chunk_index=0,
                chunk_text="Sample text",
            )

            # Verify execute was called
            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args

            # Verify SQL contains INSERT
            assert "INSERT INTO article_embeddings" in call_args[0][0]
            assert "ON CONFLICT" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_store_embedding_invalid_dimension(self, vector_store, sample_article_id):
        """Test storing embedding with invalid dimension."""
        invalid_embedding = [0.1] * 100  # Wrong dimension

        with pytest.raises(ValueError) as exc_info:
            await vector_store.store_embedding(
                article_id=sample_article_id, embedding=invalid_embedding
            )

        assert "Invalid embedding dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_embedding_empty_vector(self, vector_store, sample_article_id):
        """Test storing empty embedding vector."""
        with pytest.raises(ValueError) as exc_info:
            await vector_store.store_embedding(article_id=sample_article_id, embedding=[])

        assert "Invalid embedding dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_embedding_database_error(
        self, vector_store, sample_article_id, sample_embedding
    ):
        """Test handling database errors during storage."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Database error"))

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            with pytest.raises(VectorStoreError) as exc_info:
                await vector_store.store_embedding(
                    article_id=sample_article_id, embedding=sample_embedding
                )

            assert "Failed to store embedding" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_similar_success(self, vector_store, sample_user_id, sample_embedding):
        """Test successful similarity search."""
        mock_conn = AsyncMock()

        # Mock search results
        mock_results = [
            {
                "article_id": uuid4(),
                "chunk_index": 0,
                "chunk_text": "Sample text 1",
                "metadata": {"category": "tech"},
                "similarity_score": 0.95,
            },
            {
                "article_id": uuid4(),
                "chunk_index": 0,
                "chunk_text": "Sample text 2",
                "metadata": {"category": "science"},
                "similarity_score": 0.85,
            },
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            matches = await vector_store.search_similar(
                query_vector=sample_embedding, user_id=sample_user_id, limit=10, threshold=0.7
            )

            # Verify results
            assert len(matches) == 2
            assert all(isinstance(m, VectorMatch) for m in matches)
            assert matches[0].similarity_score == 0.95
            assert matches[1].similarity_score == 0.85

            # Verify query was called with correct parameters
            mock_conn.fetch.assert_called_once()
            call_args = mock_conn.fetch.call_args

            # Verify SQL contains user isolation
            assert "user_subscriptions" in call_args[0][0]
            assert "us.user_id" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_similar_with_metadata_filters(
        self, vector_store, sample_user_id, sample_embedding
    ):
        """Test similarity search with metadata filters."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            await vector_store.search_similar(
                query_vector=sample_embedding,
                user_id=sample_user_id,
                limit=10,
                threshold=0.7,
                metadata_filters={"category": "tech", "language": "en"},
            )

            # Verify metadata filters were applied
            call_args = mock_conn.fetch.call_args
            sql_query = call_args[0][0]

            assert "ae.metadata->>" in sql_query

    @pytest.mark.asyncio
    async def test_search_similar_invalid_dimension(self, vector_store, sample_user_id):
        """Test search with invalid query vector dimension."""
        invalid_vector = [0.1] * 100  # Wrong dimension

        with pytest.raises(ValueError) as exc_info:
            await vector_store.search_similar(query_vector=invalid_vector, user_id=sample_user_id)

        assert "Invalid query vector dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_similar_invalid_threshold(
        self, vector_store, sample_user_id, sample_embedding
    ):
        """Test search with invalid threshold."""
        with pytest.raises(ValueError) as exc_info:
            await vector_store.search_similar(
                query_vector=sample_embedding,
                user_id=sample_user_id,
                threshold=1.5,  # Invalid threshold
            )

        assert "Threshold must be between 0 and 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_similar_respects_limit(
        self, vector_store, sample_user_id, sample_embedding
    ):
        """Test that search respects result limit."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            # Request more than max allowed
            await vector_store.search_similar(
                query_vector=sample_embedding,
                user_id=sample_user_id,
                limit=200,  # Exceeds MAX_VECTOR_SEARCH_RESULTS
            )

            # Verify limit was capped
            call_args = mock_conn.fetch.call_args
            params = call_args[0][1:]

            # Last parameter should be the limit
            assert params[-1] == PerformanceLimits.MAX_VECTOR_SEARCH_RESULTS

    @pytest.mark.asyncio
    async def test_update_embedding_success(
        self, vector_store, sample_article_id, sample_embedding
    ):
        """Test successful embedding update."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            await vector_store.update_embedding(
                article_id=sample_article_id,
                embedding=sample_embedding,
                chunk_index=0,
                chunk_text="Updated text",
                metadata={"updated": True},
            )

            # Verify update was called
            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args

            # Verify SQL contains UPDATE
            assert "UPDATE article_embeddings" in call_args[0][0]
            assert "WHERE article_id" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_embedding_not_found(
        self, vector_store, sample_article_id, sample_embedding
    ):
        """Test updating non-existent embedding."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 0")

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            # Should not raise error, just log warning
            await vector_store.update_embedding(
                article_id=sample_article_id, embedding=sample_embedding
            )

            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_embedding_invalid_dimension(self, vector_store, sample_article_id):
        """Test updating with invalid embedding dimension."""
        invalid_embedding = [0.1] * 100

        with pytest.raises(ValueError) as exc_info:
            await vector_store.update_embedding(
                article_id=sample_article_id, embedding=invalid_embedding
            )

        assert "Invalid embedding dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_embedding_single_chunk(self, vector_store, sample_article_id):
        """Test deleting a single chunk."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            deleted_count = await vector_store.delete_embedding(
                article_id=sample_article_id, chunk_index=0
            )

            assert deleted_count == 1

            # Verify soft delete was used
            call_args = mock_conn.execute.call_args
            assert "SET deleted_at = NOW()" in call_args[0][0]
            assert "chunk_index" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_embedding_all_chunks(self, vector_store, sample_article_id):
        """Test deleting all chunks for an article."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 3")

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            deleted_count = await vector_store.delete_embedding(
                article_id=sample_article_id, chunk_index=None  # Delete all chunks
            )

            assert deleted_count == 3

            # Verify soft delete was used
            call_args = mock_conn.execute.call_args
            assert "SET deleted_at = NOW()" in call_args[0][0]
            assert "chunk_index" not in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_embedding_success(self, vector_store, sample_article_id):
        """Test retrieving an embedding."""
        mock_embedding = [0.1] * 1536
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"embedding": mock_embedding})

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            embedding = await vector_store.get_embedding(
                article_id=sample_article_id, chunk_index=0
            )

            assert embedding == mock_embedding
            mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embedding_not_found(self, vector_store, sample_article_id):
        """Test retrieving non-existent embedding."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            embedding = await vector_store.get_embedding(article_id=sample_article_id)

            assert embedding is None

    @pytest.mark.asyncio
    async def test_count_embeddings_all(self, vector_store):
        """Test counting all embeddings."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1000)

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            count = await vector_store.count_embeddings()

            assert count == 1000
            mock_conn.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_embeddings_user_specific(self, vector_store, sample_user_id):
        """Test counting user-accessible embeddings."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=50)

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            count = await vector_store.count_embeddings(user_id=sample_user_id)

            assert count == 50

            # Verify user isolation was applied
            call_args = mock_conn.fetchval.call_args
            assert "user_subscriptions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, vector_store):
        """Test health check when everything is working."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(
            side_effect=[
                True,  # pgvector exists
                True,  # table exists
                1000,  # embedding count
                0.5,  # test vector operation
            ]
        )

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            health = await vector_store.health_check()

            assert health["healthy"] is True
            assert health["pgvector_available"] is True
            assert health["embeddings_table_exists"] is True
            assert health["total_embeddings"] == 1000
            assert health["error"] is None

    @pytest.mark.asyncio
    async def test_health_check_pgvector_missing(self, vector_store):
        """Test health check when pgvector is not available."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=False)  # pgvector not available

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            health = await vector_store.health_check()

            assert health["healthy"] is False
            assert health["pgvector_available"] is False
            assert "pgvector extension not available" in health["error"]

    @pytest.mark.asyncio
    async def test_health_check_table_missing(self, vector_store):
        """Test health check when table doesn't exist."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(
            side_effect=[True, False]  # pgvector exists  # table doesn't exist
        )

        with patch("app.qa_agent.vector_store.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            health = await vector_store.health_check()

            assert health["healthy"] is False
            assert health["embeddings_table_exists"] is False
            assert "article_embeddings table does not exist" in health["error"]


class TestVectorMatch:
    """Test suite for VectorMatch class."""

    def test_vector_match_initialization(self):
        """Test VectorMatch initialization."""
        article_id = uuid4()
        match = VectorMatch(
            article_id=article_id,
            similarity_score=0.95,
            metadata={"category": "tech"},
            chunk_index=0,
            chunk_text="Sample text",
        )

        assert match.article_id == article_id
        assert match.similarity_score == 0.95
        assert match.metadata == {"category": "tech"}
        assert match.chunk_index == 0
        assert match.chunk_text == "Sample text"

    def test_vector_match_repr(self):
        """Test VectorMatch string representation."""
        article_id = uuid4()
        match = VectorMatch(
            article_id=article_id, similarity_score=0.95, metadata={}, chunk_index=0
        )

        repr_str = repr(match)
        assert "VectorMatch" in repr_str
        assert str(article_id) in repr_str
        assert "0.9500" in repr_str


def test_get_vector_store():
    """Test get_vector_store convenience function."""
    from app.qa_agent.vector_store import get_vector_store

    store = get_vector_store()
    assert isinstance(store, VectorStore)
    assert store._embedding_dimension == 1536
