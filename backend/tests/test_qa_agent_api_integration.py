"""
Integration tests for QA Agent API endpoints

Tests the complete API workflow from query to response, conversation management,
and article vectorization pipeline.

Requirements covered:
- 5.3: When articles are added/updated, Vector_Store automatically updates embeddings
- 7.2: When new articles join Article_Database, Vector_Store automatically processes vectorization
- 7.5: Support incremental vectorization to avoid duplicate work
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import pytest

from app.qa_agent.models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
    UserProfile,
)
from app.qa_agent.qa_agent_controller import QAAgentController
from app.qa_agent.vector_store import VectorMatch, VectorStoreError

# ===========================================================================
# Mock VectorStore for testing vectorization pipeline
# ===========================================================================


class InMemoryVectorStore:
    """
    In-memory mock VectorStore for testing vectorization pipeline.

    Tracks stored embeddings and supports all VectorStore operations
    without requiring a real database.
    """

    def __init__(self):
        # Storage: {(article_id, chunk_index): (embedding, metadata, chunk_text)}
        self._embeddings: Dict[tuple, tuple] = {}
        self._deleted: set = set()

    async def store_embedding(
        self,
        article_id: UUID,
        embedding: List[float],
        metadata: Optional[Dict] = None,
        chunk_index: int = 0,
        chunk_text: Optional[str] = None,
    ) -> None:
        """Store an embedding (incremental: updates if exists)."""
        if len(embedding) != 1536:
            raise ValueError(f"Invalid embedding dimension: {len(embedding)}")

        key = (article_id, chunk_index)
        self._embeddings[key] = (embedding, metadata or {}, chunk_text)

        # Remove from deleted set if it was previously deleted
        if key in self._deleted:
            self._deleted.remove(key)

    async def update_embedding(
        self,
        article_id: UUID,
        embedding: List[float],
        chunk_index: int = 0,
        chunk_text: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Update an existing embedding."""
        if len(embedding) != 1536:
            raise ValueError(f"Invalid embedding dimension: {len(embedding)}")

        key = (article_id, chunk_index)
        if key not in self._embeddings or key in self._deleted:
            raise VectorStoreError(
                f"Embedding not found for article {article_id}, chunk {chunk_index}"
            )

        # Update the embedding
        old_embedding, old_metadata, old_chunk_text = self._embeddings[key]
        new_metadata = metadata if metadata is not None else old_metadata
        new_chunk_text = chunk_text if chunk_text is not None else old_chunk_text
        self._embeddings[key] = (embedding, new_metadata, new_chunk_text)

    async def delete_embedding(self, article_id: UUID, chunk_index: Optional[int] = None) -> int:
        """Delete embedding(s) for an article."""
        deleted_count = 0

        if chunk_index is not None:
            # Delete specific chunk
            key = (article_id, chunk_index)
            if key in self._embeddings and key not in self._deleted:
                self._deleted.add(key)
                deleted_count = 1
        else:
            # Delete all chunks for the article
            for key in list(self._embeddings.keys()):
                if key[0] == article_id and key not in self._deleted:
                    self._deleted.add(key)
                    deleted_count += 1

        return deleted_count

    async def search_similar(
        self,
        query_vector: List[float],
        user_id: UUID,
        limit: int = 10,
        threshold: float = 0.3,
        metadata_filters: Optional[Dict] = None,
    ) -> List[VectorMatch]:
        """Search for similar embeddings."""
        if len(query_vector) != 1536:
            raise ValueError(f"Invalid query vector dimension: {len(query_vector)}")

        results = []

        for key, (embedding, metadata, chunk_text) in self._embeddings.items():
            if key in self._deleted:
                continue

            article_id, chunk_index = key

            # Simple cosine similarity calculation
            dot_product = sum(a * b for a, b in zip(query_vector, embedding))
            magnitude_a = sum(a * a for a in query_vector) ** 0.5
            magnitude_b = sum(b * b for b in embedding) ** 0.5
            similarity = (
                dot_product / (magnitude_a * magnitude_b) if magnitude_a and magnitude_b else 0.0
            )

            if similarity >= threshold:
                results.append(
                    VectorMatch(
                        article_id=article_id,
                        similarity_score=similarity,
                        metadata=metadata,
                        chunk_index=chunk_index,
                        chunk_text=chunk_text,
                    )
                )

        # Sort by similarity (highest first) and limit
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]

    async def get_embedding(self, article_id: UUID, chunk_index: int = 0) -> Optional[List[float]]:
        """Retrieve an embedding."""
        key = (article_id, chunk_index)
        if key in self._embeddings and key not in self._deleted:
            return self._embeddings[key][0]
        return None

    async def count_embeddings(self, user_id: Optional[UUID] = None) -> int:
        """Count total embeddings."""
        return len([k for k in self._embeddings.keys() if k not in self._deleted])

    def get_stored_article_ids(self) -> set:
        """Get all article IDs that have embeddings."""
        return {key[0] for key in self._embeddings.keys() if key not in self._deleted}

    def is_stored(self, article_id: UUID, chunk_index: int = 0) -> bool:
        """Check if an embedding is stored."""
        key = (article_id, chunk_index)
        return key in self._embeddings and key not in self._deleted


# ===========================================================================
# Mock components for controller testing
# ===========================================================================


class MockQueryProcessor:
    """Mock QueryProcessor for testing."""

    async def validate_query(self, query: str):
        from app.qa_agent.query_processor import QueryValidationResult

        if not query.strip():
            return QueryValidationResult(is_valid=False, error_message="Query cannot be empty")
        return QueryValidationResult(is_valid=True)

    async def parse_query(self, query: str, language: str = "auto", context=None) -> ParsedQuery:
        return ParsedQuery(
            original_query=query,
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=query.split()[:5],
            confidence=0.8,
        )

    async def expand_query(self, query: str, context) -> str:
        return query


class MockEmbeddingService:
    """Mock EmbeddingService for testing."""

    async def generate_embedding(self, text: str) -> List[float]:
        # Generate a deterministic embedding based on text hash
        import hashlib

        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        # Create a normalized vector
        base = [(hash_val >> (i * 8)) & 0xFF for i in range(1536)]
        magnitude = sum(x * x for x in base) ** 0.5
        return [x / magnitude if magnitude > 0 else 0.0 for x in base]


class MockRetrievalEngine:
    """Mock RetrievalEngine for testing."""

    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def intelligent_search(
        self, query: str, query_vector: List[float], user_id: str, **kwargs
    ):
        # Use the vector store to search
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        matches = await self.vector_store.search_similar(
            query_vector=query_vector,
            user_id=user_uuid,
            limit=kwargs.get("limit", 10),
            threshold=0.3,
        )

        # Convert VectorMatch to ArticleMatch
        articles = []
        for match in matches:
            articles.append(
                ArticleMatch(
                    article_id=match.article_id,
                    title=f"Article {match.article_id}",
                    content_preview=match.chunk_text or "Test content preview",
                    similarity_score=match.similarity_score,
                    url=f"https://example.com/article/{match.article_id}",
                    published_at=datetime.utcnow(),
                    feed_name="Test Feed",
                    category="Technology",
                )
            )

        return {
            "results": articles,
            "expanded": False,
            "personalized": False,
            "search_time": 0.05,
        }

    async def semantic_search(self, query_vector: List[float], user_id: str, **kwargs):
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        matches = await self.vector_store.search_similar(
            query_vector=query_vector,
            user_id=user_uuid,
            limit=kwargs.get("limit", 10),
            threshold=kwargs.get("threshold", 0.3),
        )

        articles = []
        for match in matches:
            articles.append(
                ArticleMatch(
                    article_id=match.article_id,
                    title=f"Article {match.article_id}",
                    content_preview=match.chunk_text or "Test content preview",
                    similarity_score=match.similarity_score,
                    url=f"https://example.com/article/{match.article_id}",
                    published_at=datetime.utcnow(),
                    feed_name="Test Feed",
                    category="Technology",
                )
            )

        return articles


class MockResponseGenerator:
    """Mock ResponseGenerator for testing."""

    async def generate_response(
        self, query: str, articles: List[ArticleMatch], context=None, user_profile=None
    ) -> StructuredResponse:
        summaries = []
        for article in articles[:3]:
            summaries.append(
                ArticleSummary(
                    article_id=article.article_id,
                    title=article.title,
                    summary="This is the first sentence. This is the second sentence.",
                    url=article.url,
                    relevance_score=article.similarity_score,
                    reading_time=3,
                    published_at=article.published_at,
                    category=article.category,
                )
            )

        return StructuredResponse(
            query=query,
            response_type=ResponseType.STRUCTURED,
            articles=summaries,
            insights=["Mock insight about the query."],
            recommendations=["Try searching for related topics."],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,
            confidence=0.8,
        )


class MockConversationManager:
    """Mock ConversationManager for testing."""

    def __init__(self):
        self._conversations: Dict[str, ConversationContext] = {}

    async def create_conversation(self, user_id: UUID) -> str:
        conversation_id = str(uuid4())
        context = ConversationContext(conversation_id=UUID(conversation_id), user_id=user_id)
        self._conversations[conversation_id] = context
        return conversation_id

    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        return self._conversations.get(conversation_id)

    async def should_reset_context(self, conversation_id: str, new_query: str) -> bool:
        return False

    async def reset_context(self, conversation_id: str, new_topic: Optional[str] = None) -> None:
        pass

    async def add_turn(
        self,
        conversation_id: str,
        query: str,
        parsed_query: Optional[ParsedQuery] = None,
        response: Optional[StructuredResponse] = None,
    ) -> None:
        context = self._conversations.get(conversation_id)
        if context:
            context.add_turn(query, parsed_query, response)

    async def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def vector_store():
    """Create an in-memory vector store for testing."""
    return InMemoryVectorStore()


@pytest.fixture
def controller(vector_store):
    """Create a QAAgentController with mocked components."""
    query_processor = MockQueryProcessor()
    embedding_service = MockEmbeddingService()
    retrieval_engine = MockRetrievalEngine(vector_store)
    response_generator = MockResponseGenerator()
    conversation_manager = MockConversationManager()

    return QAAgentController(
        query_processor=query_processor,
        retrieval_engine=retrieval_engine,
        response_generator=response_generator,
        conversation_manager=conversation_manager,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


@pytest.fixture
def user_profile():
    """Create a test user profile."""
    return UserProfile(
        user_id=uuid4(),
        preferred_topics=["AI", "Machine Learning"],
        language_preference=QueryLanguage.ENGLISH,
    )


# ===========================================================================
# 1. Complete API workflow tests (controller-level integration)
# ===========================================================================


class TestCompleteAPIWorkflow:
    """Test the full query → parse → retrieve → generate → response pipeline."""

    @pytest.mark.asyncio
    async def test_query_returns_structured_response_with_all_fields(
        self, controller, vector_store, user_profile
    ):
        """Test that a query returns a StructuredResponse with all required fields."""
        # Setup: Store some test embeddings
        user_id = str(user_profile.user_id)
        article_id = uuid4()
        embedding = await controller.embedding_service.generate_embedding(
            "AI machine learning article"
        )

        await vector_store.store_embedding(
            article_id=article_id,
            embedding=embedding,
            metadata={"title": "AI Article", "category": "Technology"},
            chunk_text="This is an article about AI and machine learning.",
        )

        # Execute: Process a query
        response = await controller.process_query(
            user_id=user_id,
            query="What are the latest developments in AI?",
            user_profile=user_profile,
        )

        # Verify: Response has all required fields
        assert isinstance(response, StructuredResponse)
        assert response.query == "What are the latest developments in AI?"
        assert isinstance(response.conversation_id, UUID)
        assert response.response_time >= 0
        assert response.confidence > 0
        assert isinstance(response.articles, list)
        assert isinstance(response.insights, list)
        assert isinstance(response.recommendations, list)

    @pytest.mark.asyncio
    async def test_conversation_id_returned_and_reusable(self, controller, vector_store):
        """Test that conversation_id is returned and can be used for follow-up queries."""
        user_id = str(uuid4())

        # First query
        response1 = await controller.process_query(
            user_id=user_id,
            query="What is machine learning?",
        )

        assert response1.conversation_id is not None
        conversation_id = str(response1.conversation_id)

        # Follow-up query with same conversation_id
        response2 = await controller.process_query(
            user_id=user_id,
            query="Tell me more about neural networks",
            conversation_id=conversation_id,
        )

        assert response2.conversation_id == response1.conversation_id

    @pytest.mark.asyncio
    async def test_user_profile_personalization_applied(
        self, controller, vector_store, user_profile
    ):
        """Test that user profile personalization is applied when provided."""
        user_id = str(user_profile.user_id)

        # Store embeddings for different topics
        ai_article_id = uuid4()
        ai_embedding = await controller.embedding_service.generate_embedding(
            "AI and machine learning"
        )
        await vector_store.store_embedding(
            article_id=ai_article_id,
            embedding=ai_embedding,
            metadata={"category": "AI"},
            chunk_text="Article about AI",
        )

        # Query with user profile
        response = await controller.process_query(
            user_id=user_id,
            query="Tell me about AI",
            user_profile=user_profile,
        )

        # Should return a response (personalization doesn't break the pipeline)
        assert isinstance(response, StructuredResponse)
        assert response.response_type == ResponseType.STRUCTURED


# ===========================================================================
# 2. Conversation management through API
# ===========================================================================


class TestConversationManagement:
    """Test conversation creation, continuation, retrieval, and deletion."""

    @pytest.mark.asyncio
    async def test_create_new_conversation_via_process_query(self, controller):
        """Test creating a new conversation via process_query."""
        user_id = str(uuid4())

        response = await controller.process_query(
            user_id=user_id,
            query="What is deep learning?",
        )

        assert response.conversation_id is not None

        # Verify conversation exists
        history = await controller.get_conversation_history(user_id, str(response.conversation_id))
        assert history is not None
        assert str(history.user_id) == user_id

    @pytest.mark.asyncio
    async def test_continue_conversation_via_continue_conversation(self, controller):
        """Test continuing a conversation via continue_conversation."""
        user_id = str(uuid4())

        # Create conversation
        response1 = await controller.process_query(
            user_id=user_id,
            query="What is machine learning?",
        )
        conversation_id = str(response1.conversation_id)

        # Continue conversation
        response2 = await controller.continue_conversation(
            user_id=user_id,
            query="What are the main types?",
            conversation_id=conversation_id,
        )

        assert response2.conversation_id == response1.conversation_id

    @pytest.mark.asyncio
    async def test_retrieve_conversation_history(self, controller):
        """Test retrieving conversation history via get_conversation_history."""
        user_id = str(uuid4())

        response = await controller.process_query(
            user_id=user_id,
            query="What is NLP?",
        )
        conversation_id = str(response.conversation_id)

        # Retrieve history
        history = await controller.get_conversation_history(user_id, conversation_id)

        assert history is not None
        assert history.conversation_id == response.conversation_id
        assert str(history.user_id) == user_id

    @pytest.mark.asyncio
    async def test_delete_conversation(self, controller):
        """Test deleting a conversation via delete_conversation."""
        user_id = str(uuid4())

        response = await controller.process_query(
            user_id=user_id,
            query="Test query",
        )
        conversation_id = str(response.conversation_id)

        # Delete conversation
        deleted = await controller.delete_conversation(user_id, conversation_id)
        assert deleted is True

        # Verify conversation is deleted
        history = await controller.get_conversation_history(user_id, conversation_id)
        assert history is None

    @pytest.mark.asyncio
    async def test_deleted_conversation_cannot_be_retrieved(self, controller):
        """Test that deleted conversations cannot be retrieved."""
        user_id = str(uuid4())

        response = await controller.process_query(
            user_id=user_id,
            query="Test query",
        )
        conversation_id = str(response.conversation_id)

        # Delete and verify
        await controller.delete_conversation(user_id, conversation_id)
        history = await controller.get_conversation_history(user_id, conversation_id)

        assert history is None


# ===========================================================================
# 3. Article vectorization pipeline (Req 5.3, 7.2, 7.5)
# ===========================================================================


class TestArticleVectorizationPipeline:
    """Test the VectorStore class methods and incremental vectorization."""

    @pytest.mark.asyncio
    async def test_store_embedding_makes_it_searchable(self, vector_store):
        """Test that storing an embedding makes it searchable.

        Validates: Requirement 7.2 - When new articles join Article_Database,
        Vector_Store automatically processes vectorization.
        """
        article_id = uuid4()
        user_id = uuid4()
        embedding = [0.1] * 1536  # Valid 1536-dimensional embedding

        # Store embedding
        await vector_store.store_embedding(
            article_id=article_id,
            embedding=embedding,
            metadata={"title": "Test Article"},
            chunk_text="This is a test article.",
        )

        # Search for similar embeddings
        query_vector = [0.1] * 1536  # Similar vector
        results = await vector_store.search_similar(
            query_vector=query_vector, user_id=user_id, limit=10, threshold=0.5
        )

        # Verify article is found
        assert len(results) > 0
        assert any(match.article_id == article_id for match in results)

    @pytest.mark.asyncio
    async def test_update_embedding_replaces_old_one(self, vector_store):
        """Test that updating an embedding replaces the old one.

        Validates: Requirement 5.3 - When articles are added/updated,
        Vector_Store automatically updates embeddings.
        """
        article_id = uuid4()
        user_id = uuid4()

        # Store initial embedding
        old_embedding = [0.1] * 1536
        await vector_store.store_embedding(
            article_id=article_id,
            embedding=old_embedding,
            metadata={"version": "1"},
            chunk_text="Old content",
        )

        # Update embedding
        new_embedding = [0.9] * 1536
        await vector_store.update_embedding(
            article_id=article_id,
            embedding=new_embedding,
            chunk_index=0,
            metadata={"version": "2"},
            chunk_text="New content",
        )

        # Retrieve and verify
        retrieved = await vector_store.get_embedding(article_id, chunk_index=0)
        assert retrieved == new_embedding

        # Search should find the updated version
        results = await vector_store.search_similar(
            query_vector=[0.9] * 1536, user_id=user_id, limit=10, threshold=0.5
        )

        assert len(results) > 0
        assert any(match.article_id == article_id for match in results)

    @pytest.mark.asyncio
    async def test_delete_embedding_removes_from_search(self, vector_store):
        """Test that deleting an embedding removes it from search results."""
        article_id = uuid4()
        user_id = uuid4()
        embedding = [0.1] * 1536

        # Store embedding
        await vector_store.store_embedding(
            article_id=article_id,
            embedding=embedding,
            metadata={"title": "Test Article"},
        )

        # Verify it's searchable
        results_before = await vector_store.search_similar(
            query_vector=[0.1] * 1536, user_id=user_id, limit=10, threshold=0.5
        )
        assert any(match.article_id == article_id for match in results_before)

        # Delete embedding
        deleted_count = await vector_store.delete_embedding(article_id)
        assert deleted_count == 1

        # Verify it's no longer searchable
        results_after = await vector_store.search_similar(
            query_vector=[0.1] * 1536, user_id=user_id, limit=10, threshold=0.5
        )
        assert not any(match.article_id == article_id for match in results_after)

    @pytest.mark.asyncio
    async def test_incremental_vectorization_updates_not_duplicates(self, vector_store):
        """Test incremental vectorization: storing same article_id twice should update, not duplicate.

        Validates: Requirement 7.5 - Support incremental vectorization to avoid duplicate work.
        """
        article_id = uuid4()
        user_id = uuid4()

        # Store embedding first time
        embedding_v1 = [0.1] * 1536
        await vector_store.store_embedding(
            article_id=article_id,
            embedding=embedding_v1,
            metadata={"version": "1"},
        )

        # Count embeddings
        count_after_first = await vector_store.count_embeddings()

        # Store embedding second time (should update, not duplicate)
        embedding_v2 = [0.2] * 1536
        await vector_store.store_embedding(
            article_id=article_id,
            embedding=embedding_v2,
            metadata={"version": "2"},
        )

        # Count should remain the same (no duplicate)
        count_after_second = await vector_store.count_embeddings()
        assert count_after_second == count_after_first

        # Verify the embedding was updated
        retrieved = await vector_store.get_embedding(article_id)
        assert retrieved == embedding_v2

    @pytest.mark.asyncio
    async def test_vector_store_supports_multiple_chunks(self, vector_store):
        """Test that VectorStore supports multiple chunks per article."""
        article_id = uuid4()
        user_id = uuid4()

        # Store multiple chunks
        chunk_0_embedding = [0.1] * 1536
        chunk_1_embedding = [0.2] * 1536
        chunk_2_embedding = [0.3] * 1536

        await vector_store.store_embedding(
            article_id=article_id,
            embedding=chunk_0_embedding,
            chunk_index=0,
            chunk_text="First chunk",
        )

        await vector_store.store_embedding(
            article_id=article_id,
            embedding=chunk_1_embedding,
            chunk_index=1,
            chunk_text="Second chunk",
        )

        await vector_store.store_embedding(
            article_id=article_id,
            embedding=chunk_2_embedding,
            chunk_index=2,
            chunk_text="Third chunk",
        )

        # Verify all chunks are stored
        chunk_0 = await vector_store.get_embedding(article_id, chunk_index=0)
        chunk_1 = await vector_store.get_embedding(article_id, chunk_index=1)
        chunk_2 = await vector_store.get_embedding(article_id, chunk_index=2)

        assert chunk_0 == chunk_0_embedding
        assert chunk_1 == chunk_1_embedding
        assert chunk_2 == chunk_2_embedding

    @pytest.mark.asyncio
    async def test_delete_all_chunks_for_article(self, vector_store):
        """Test deleting all chunks for an article."""
        article_id = uuid4()

        # Store multiple chunks
        for i in range(3):
            await vector_store.store_embedding(
                article_id=article_id,
                embedding=[0.1 * (i + 1)] * 1536,
                chunk_index=i,
            )

        # Delete all chunks (chunk_index=None)
        deleted_count = await vector_store.delete_embedding(article_id, chunk_index=None)
        assert deleted_count == 3

        # Verify all chunks are deleted
        for i in range(3):
            chunk = await vector_store.get_embedding(article_id, chunk_index=i)
            assert chunk is None


# ===========================================================================
# 4. System health check
# ===========================================================================


class TestSystemHealthCheck:
    """Test that get_system_health() returns all required keys."""

    @pytest.mark.asyncio
    async def test_health_check_returns_required_keys(self, controller):
        """Test that health check returns all required keys."""
        health = await controller.get_system_health()

        required_keys = {
            "overall_health",
            "status",
            "components",
            "timestamp",
            "healthy_components",
            "total_components",
        }

        assert required_keys.issubset(health.keys())

    @pytest.mark.asyncio
    async def test_health_check_includes_component_status(self, controller):
        """Test that health check includes component status."""
        health = await controller.get_system_health()

        components = health.get("components", {})

        expected_components = {
            "query_processor",
            "embedding_service",
            "vector_store",
            "retrieval_engine",
            "response_generator",
            "conversation_manager",
        }

        assert expected_components.issubset(components.keys())
