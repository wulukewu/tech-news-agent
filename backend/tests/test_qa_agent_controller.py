"""
Test suite for QAAgentController

Tests the main orchestration functionality including:
- Query processing pipeline
- Component coordination
- Error handling and fallback mechanisms
- Performance requirements (3-second response time)
- Multi-turn conversation support
"""

import asyncio
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytest

from .models import (
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
from .qa_agent_controller import QAAgentController
from .query_processor import QueryValidationResult

# Mock components for testing


class MockQueryProcessor:
    """Mock QueryProcessor for testing."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay

    async def validate_query(self, query: str) -> QueryValidationResult:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock query processor failure")

        if not query.strip():
            return QueryValidationResult(is_valid=False, error_message="Query cannot be empty")

        return QueryValidationResult(is_valid=True)

    async def parse_query(
        self, query: str, language: str = "auto", context: Optional[ConversationContext] = None
    ) -> ParsedQuery:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock query processor failure")

        return ParsedQuery(
            original_query=query,
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=query.split()[:5],
            confidence=0.8,
        )

    async def expand_query(self, query: str, context: ConversationContext) -> str:
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return query  # No expansion in mock


class MockEmbeddingService:
    """Mock EmbeddingService for testing."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay

    async def generate_embedding(self, text: str) -> List[float]:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock embedding service failure")

        # Return a dummy embedding vector
        return [0.1] * 1536


class MockRetrievalEngine:
    """Mock RetrievalEngine for testing."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0, return_empty: bool = False):
        self.should_fail = should_fail
        self.delay = delay
        self.return_empty = return_empty

    async def intelligent_search(
        self,
        query: str,
        query_vector: List[float],
        user_id: str,
        user_profile: Optional[UserProfile] = None,
        **kwargs,
    ) -> dict:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock retrieval engine failure")

        if self.return_empty:
            return {"results": [], "expanded": False, "personalized": False}

        # Return mock articles
        mock_article = ArticleMatch(
            article_id=uuid4(),
            title="Mock Article Title",
            content_preview="This is a mock article content preview for testing purposes.",
            similarity_score=0.85,
            url="https://example.com/mock-article",
            published_at=datetime.utcnow(),
            feed_name="Mock Feed",
            category="Technology",
        )

        return {
            "results": [mock_article],
            "expanded": False,
            "personalized": bool(user_profile),
            "search_time": 0.1,
        }

    async def semantic_search(
        self,
        query_vector: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = 0.5,
        **kwargs,
    ) -> List[ArticleMatch]:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock retrieval engine failure")

        if self.return_empty:
            return []

        # Return mock articles
        mock_article = ArticleMatch(
            article_id=uuid4(),
            title="Mock Semantic Search Article",
            content_preview="This is a mock article from semantic search.",
            similarity_score=0.75,
            url="https://example.com/semantic-article",
            published_at=datetime.utcnow(),
            feed_name="Mock Feed",
            category="Technology",
        )

        return [mock_article]


class MockResponseGenerator:
    """Mock ResponseGenerator for testing."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay

    async def generate_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> StructuredResponse:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock response generator failure")

        # Create mock article summaries
        summaries = []
        for article in articles[:3]:  # Limit to 3
            summary = ArticleSummary(
                article_id=article.article_id,
                title=article.title,
                summary="This is a mock summary of the article content. It provides detailed information about the topic discussed.",  # Two sentences for validation
                url=article.url,
                relevance_score=article.similarity_score,
                reading_time=5,
                published_at=article.published_at,
                category=article.category,
            )
            summaries.append(summary)

        return StructuredResponse(
            query=query,
            response_type=ResponseType.STRUCTURED,
            articles=summaries,
            insights=["Mock insight about the query results"],
            recommendations=["Try searching for related topics"],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,  # Will be set by controller
            confidence=0.8,
        )


class MockConversationManager:
    """Mock ConversationManager for testing."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay
        self._conversations = {}

    async def create_conversation(self, user_id: UUID) -> str:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock conversation manager failure")

        conversation_id = str(uuid4())
        context = ConversationContext(
            conversation_id=UUID(conversation_id),
            user_id=user_id,
        )
        self._conversations[conversation_id] = context
        return conversation_id

    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock conversation manager failure")

        return self._conversations.get(conversation_id)

    async def should_reset_context(self, conversation_id: str, new_query: str) -> bool:
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return False  # Don't reset in mock

    async def reset_context(self, conversation_id: str, new_topic: Optional[str] = None) -> None:
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        pass  # No-op in mock

    async def add_turn(
        self,
        conversation_id: str,
        query: str,
        parsed_query: Optional[ParsedQuery] = None,
        response: Optional[StructuredResponse] = None,
    ) -> None:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock conversation manager failure")

        # Update mock conversation
        context = self._conversations.get(conversation_id)
        if context:
            context.add_turn(query, parsed_query, response)

    async def delete_conversation(self, conversation_id: str) -> bool:
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False


class MockVectorStore:
    """Mock VectorStore for testing."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def search_similar(self, **kwargs) -> List:
        if self.should_fail:
            raise Exception("Mock vector store failure")
        return []  # Return empty for health checks


# Test fixtures


@pytest.fixture
def mock_user_profile():
    """Create a mock user profile for testing."""
    return UserProfile(
        user_id=uuid4(),
        preferred_topics=["AI", "Machine Learning", "Technology"],
        language_preference=QueryLanguage.ENGLISH,
    )


@pytest.fixture
def qa_controller():
    """Create a QAAgentController with mock components."""
    return QAAgentController(
        query_processor=MockQueryProcessor(),
        retrieval_engine=MockRetrievalEngine(),
        response_generator=MockResponseGenerator(),
        conversation_manager=MockConversationManager(),
        embedding_service=MockEmbeddingService(),
        vector_store=MockVectorStore(),
    )


# Test cases


@pytest.mark.asyncio
async def test_process_query_success(qa_controller, mock_user_profile):
    """Test successful query processing."""
    user_id = str(uuid4())
    query = "What are the latest developments in AI?"

    response = await qa_controller.process_query(
        user_id=user_id,
        query=query,
        user_profile=mock_user_profile,
    )

    assert isinstance(response, StructuredResponse)
    assert response.query == query
    assert response.response_type == ResponseType.STRUCTURED
    assert len(response.articles) > 0
    assert len(response.insights) > 0
    assert response.response_time > 0
    assert response.confidence > 0


@pytest.mark.asyncio
async def test_process_query_empty_query(qa_controller):
    """Test processing empty query."""
    user_id = str(uuid4())
    query = ""

    response = await qa_controller.process_query(
        user_id=user_id,
        query=query,
    )

    assert response.response_type == ResponseType.ERROR
    assert "empty" in response.insights[0].lower()


@pytest.mark.asyncio
async def test_process_query_with_conversation(qa_controller, mock_user_profile):
    """Test query processing with existing conversation."""
    user_id = str(uuid4())

    # First query to create conversation
    response1 = await qa_controller.process_query(
        user_id=user_id,
        query="Tell me about machine learning",
        user_profile=mock_user_profile,
    )

    conversation_id = str(response1.conversation_id)

    # Follow-up query
    response2 = await qa_controller.process_query(
        user_id=user_id,
        query="What about deep learning?",
        conversation_id=conversation_id,
        user_profile=mock_user_profile,
    )

    assert response2.conversation_id == response1.conversation_id
    assert response2.response_type == ResponseType.STRUCTURED


@pytest.mark.asyncio
async def test_continue_conversation(qa_controller, mock_user_profile):
    """Test continue_conversation method."""
    user_id = str(uuid4())

    # Create initial conversation
    response1 = await qa_controller.process_query(
        user_id=user_id,
        query="What is artificial intelligence?",
        user_profile=mock_user_profile,
    )

    conversation_id = str(response1.conversation_id)

    # Continue conversation
    response2 = await qa_controller.continue_conversation(
        user_id=user_id,
        query="Tell me more about neural networks",
        conversation_id=conversation_id,
        user_profile=mock_user_profile,
    )

    assert response2.conversation_id == response1.conversation_id
    assert response2.response_type == ResponseType.STRUCTURED


@pytest.mark.asyncio
async def test_performance_requirement(qa_controller):
    """Test that responses are generated within 3 seconds."""
    user_id = str(uuid4())
    query = "What are the latest AI trends?"

    start_time = time.time()
    response = await qa_controller.process_query(
        user_id=user_id,
        query=query,
    )
    end_time = time.time()

    total_time = end_time - start_time

    # Should complete within 3 seconds (requirement 6.2)
    assert total_time <= 3.5  # Allow small buffer for test overhead
    assert response.response_time <= 3.5


@pytest.mark.asyncio
async def test_component_failure_fallback():
    """Test fallback behavior when components fail."""
    # Create controller with failing components
    qa_controller = QAAgentController(
        query_processor=MockQueryProcessor(should_fail=False),  # Keep this working
        retrieval_engine=MockRetrievalEngine(should_fail=True),  # This fails
        response_generator=MockResponseGenerator(should_fail=False),
        conversation_manager=MockConversationManager(should_fail=False),
        embedding_service=MockEmbeddingService(should_fail=False),
        vector_store=MockVectorStore(should_fail=False),
    )

    user_id = str(uuid4())
    query = "Test query with failing retrieval"

    response = await qa_controller.process_query(
        user_id=user_id,
        query=query,
    )

    # Should still return a response (fallback behavior)
    assert isinstance(response, StructuredResponse)
    # May be an error response or simplified response
    assert response.query == query


@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling for slow components."""
    # Create controller with slow components
    qa_controller = QAAgentController(
        query_processor=MockQueryProcessor(delay=0.1),
        retrieval_engine=MockRetrievalEngine(delay=2.0),  # Slow retrieval
        response_generator=MockResponseGenerator(delay=0.1),
        conversation_manager=MockConversationManager(delay=0.1),
        embedding_service=MockEmbeddingService(delay=0.1),
        vector_store=MockVectorStore(),
    )

    user_id = str(uuid4())
    query = "Test query with slow retrieval"

    start_time = time.time()
    response = await qa_controller.process_query(
        user_id=user_id,
        query=query,
    )
    end_time = time.time()

    # Should still complete reasonably quickly due to timeout handling
    assert end_time - start_time <= 4.0  # Allow some buffer
    assert isinstance(response, StructuredResponse)


@pytest.mark.asyncio
async def test_no_articles_found(qa_controller):
    """Test behavior when no articles are found."""
    # Create controller that returns no articles
    qa_controller_empty = QAAgentController(
        query_processor=MockQueryProcessor(),
        retrieval_engine=MockRetrievalEngine(return_empty=True),
        response_generator=MockResponseGenerator(),
        conversation_manager=MockConversationManager(),
        embedding_service=MockEmbeddingService(),
        vector_store=MockVectorStore(),
    )

    user_id = str(uuid4())
    query = "Very specific query that returns no results"

    response = await qa_controller_empty.process_query(
        user_id=user_id,
        query=query,
    )

    assert isinstance(response, StructuredResponse)
    # Should handle empty results gracefully
    assert len(response.articles) == 0 or response.response_type in [
        ResponseType.ERROR,
        ResponseType.SIMPLE,
    ]


@pytest.mark.asyncio
async def test_get_conversation_history(qa_controller):
    """Test getting conversation history."""
    user_id = str(uuid4())

    # Create a conversation
    response = await qa_controller.process_query(
        user_id=user_id,
        query="Initial query",
    )

    conversation_id = str(response.conversation_id)

    # Get conversation history
    history = await qa_controller.get_conversation_history(user_id, conversation_id)

    assert history is not None
    assert history.conversation_id == response.conversation_id
    assert str(history.user_id) == user_id


@pytest.mark.asyncio
async def test_delete_conversation(qa_controller):
    """Test deleting a conversation."""
    user_id = str(uuid4())

    # Create a conversation
    response = await qa_controller.process_query(
        user_id=user_id,
        query="Test query",
    )

    conversation_id = str(response.conversation_id)

    # Delete the conversation
    deleted = await qa_controller.delete_conversation(user_id, conversation_id)

    assert deleted is True

    # Verify it's deleted
    history = await qa_controller.get_conversation_history(user_id, conversation_id)
    assert history is None


@pytest.mark.asyncio
async def test_user_access_control(qa_controller):
    """Test that users can only access their own conversations."""
    user1_id = str(uuid4())
    user2_id = str(uuid4())

    # User 1 creates a conversation
    response = await qa_controller.process_query(
        user_id=user1_id,
        query="User 1 query",
    )

    conversation_id = str(response.conversation_id)

    # User 2 tries to access User 1's conversation
    history = await qa_controller.get_conversation_history(user2_id, conversation_id)
    assert history is None

    # User 2 tries to delete User 1's conversation
    deleted = await qa_controller.delete_conversation(user2_id, conversation_id)
    assert deleted is False


@pytest.mark.asyncio
async def test_system_health_check(qa_controller):
    """Test system health check functionality."""
    health = await qa_controller.get_system_health()

    assert isinstance(health, dict)
    assert "overall_health" in health
    assert "status" in health
    assert "components" in health
    assert "timestamp" in health

    # Should be healthy with mock components
    assert health["overall_health"] >= 0.8
    assert health["status"] == "healthy"


@pytest.mark.asyncio
async def test_system_health_with_failures():
    """Test system health check with component failures."""
    qa_controller = QAAgentController(
        query_processor=MockQueryProcessor(should_fail=True),  # Failing component
        retrieval_engine=MockRetrievalEngine(),
        response_generator=MockResponseGenerator(),
        conversation_manager=MockConversationManager(),
        embedding_service=MockEmbeddingService(),
        vector_store=MockVectorStore(should_fail=True),  # Another failing component
    )

    health = await qa_controller.get_system_health()

    assert isinstance(health, dict)
    assert health["overall_health"] < 1.0  # Should be degraded
    assert health["status"] in ["degraded", "unhealthy"]

    # Check specific component failures
    assert health["components"]["query_processor"] is False
    assert health["components"]["vector_store"] is False


# Integration test


@pytest.mark.asyncio
async def test_full_conversation_flow(qa_controller, mock_user_profile):
    """Test a complete conversation flow with multiple turns."""
    user_id = str(uuid4())

    # Turn 1: Initial query
    response1 = await qa_controller.process_query(
        user_id=user_id,
        query="What is machine learning?",
        user_profile=mock_user_profile,
    )

    assert response1.response_type == ResponseType.STRUCTURED
    conversation_id = str(response1.conversation_id)

    # Turn 2: Follow-up question
    response2 = await qa_controller.continue_conversation(
        user_id=user_id,
        query="What are the main types?",
        conversation_id=conversation_id,
        user_profile=mock_user_profile,
    )

    assert response2.conversation_id == response1.conversation_id
    assert response2.response_type == ResponseType.STRUCTURED

    # Turn 3: Another follow-up
    response3 = await qa_controller.continue_conversation(
        user_id=user_id,
        query="Tell me more about supervised learning",
        conversation_id=conversation_id,
        user_profile=mock_user_profile,
    )

    assert response3.conversation_id == response1.conversation_id
    assert response3.response_type == ResponseType.STRUCTURED

    # Verify conversation history
    history = await qa_controller.get_conversation_history(user_id, conversation_id)
    assert history is not None
    assert len(history.turns) >= 1  # Should have conversation turns


if __name__ == "__main__":
    # Run a simple test
    async def main():
        print("Running QAAgentController tests...")

        # Create controller with mock components
        controller = QAAgentController(
            query_processor=MockQueryProcessor(),
            retrieval_engine=MockRetrievalEngine(),
            response_generator=MockResponseGenerator(),
            conversation_manager=MockConversationManager(),
            embedding_service=MockEmbeddingService(),
            vector_store=MockVectorStore(),
        )

        # Test basic query processing
        user_id = str(uuid4())
        query = "What are the latest AI developments?"

        print(f"Processing query: {query}")
        start_time = time.time()

        response = await controller.process_query(
            user_id=user_id,
            query=query,
        )

        end_time = time.time()

        print(f"Response generated in {end_time - start_time:.2f} seconds")
        print(f"Response type: {response.response_type}")
        print(f"Number of articles: {len(response.articles)}")
        print(f"Number of insights: {len(response.insights)}")
        print(f"Confidence: {response.confidence}")

        # Test health check
        print("\nChecking system health...")
        health = await controller.get_system_health()
        print(f"Overall health: {health['overall_health']:.2f}")
        print(f"Status: {health['status']}")

        print("\nAll tests completed successfully!")

    asyncio.run(main())
