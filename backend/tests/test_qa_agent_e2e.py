"""
End-to-End System Tests for Intelligent Q&A Agent

Tests complete user journeys, multi-turn conversations, personalization,
error recovery, concurrent users, and system health.

Requirements covered:
- Complete system validation
- Multi-turn conversation flows with context preservation
- System behavior under various load conditions
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import pytest

from app.qa_agent.embedding_service import EmbeddingError
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
from app.qa_agent.query_processor import QueryValidationResult
from app.qa_agent.response_generator import ResponseGeneratorError
from app.qa_agent.retrieval_engine import RetrievalEngineError
from app.qa_agent.vector_store import VectorMatch

# ===========================================================================
# Mock Components
# ===========================================================================


def _make_article_match(
    title: str = "Test Article",
    similarity_score: float = 0.85,
    category: str = "Technology",
) -> ArticleMatch:
    """Create a mock ArticleMatch for testing."""
    return ArticleMatch(
        article_id=uuid4(),
        title=title,
        content_preview="This is a test article content preview for end-to-end testing.",
        similarity_score=similarity_score,
        url="https://example.com/article",
        published_at=datetime.utcnow(),
        feed_name="Test Feed",
        category=category,
    )


def _make_article_summary(article: ArticleMatch) -> ArticleSummary:
    """Create a mock ArticleSummary from an ArticleMatch."""
    return ArticleSummary(
        article_id=article.article_id,
        title=article.title,
        summary=(
            "This is the first sentence of the article summary. "
            "This is the second sentence providing more detail."
        ),
        url=article.url,
        relevance_score=article.similarity_score,
        reading_time=3,
        published_at=article.published_at,
        category=article.category,
    )


class MockQueryProcessor:
    """Mock QueryProcessor for E2E tests."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def validate_query(self, query: str) -> QueryValidationResult:
        if self.should_fail:
            raise Exception("MockQueryProcessor.validate_query failure")
        if not query.strip():
            return QueryValidationResult(is_valid=False, error_message="Query cannot be empty")
        return QueryValidationResult(is_valid=True)

    async def parse_query(
        self,
        query: str,
        language: str = "auto",
        context: Optional[ConversationContext] = None,
    ) -> ParsedQuery:
        if self.should_fail:
            raise Exception("MockQueryProcessor.parse_query failure")
        return ParsedQuery(
            original_query=query,
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=query.split()[:5],
            confidence=0.8,
        )

    async def expand_query(self, query: str, context: ConversationContext) -> str:
        return query


class MockEmbeddingService:
    """Mock EmbeddingService for E2E tests."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def generate_embedding(self, text: str) -> List[float]:
        if self.should_fail:
            raise EmbeddingError("MockEmbeddingService failure")
        return [0.1] * 1536


class MockRetrievalEngine:
    """Mock RetrievalEngine for E2E tests."""

    def __init__(
        self,
        should_fail: bool = False,
        articles: Optional[List[ArticleMatch]] = None,
    ):
        self.should_fail = should_fail
        self._articles = articles or [_make_article_match()]

    async def intelligent_search(
        self,
        query: str,
        query_vector: List[float],
        user_id: str,
        user_profile: Optional[UserProfile] = None,
        **kwargs,
    ) -> dict:
        if self.should_fail:
            raise RetrievalEngineError("MockRetrievalEngine.intelligent_search failure")
        return {
            "results": self._articles,
            "expanded": False,
            "personalized": bool(user_profile),
            "search_time": 0.05,
        }

    async def semantic_search(
        self,
        query_vector: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = 0.5,
        **kwargs,
    ) -> List[ArticleMatch]:
        if self.should_fail:
            raise RetrievalEngineError("MockRetrievalEngine.semantic_search failure")
        return self._articles

    async def _expand_by_keywords(
        self,
        query_text: str,
        user_uuid: UUID,
        existing_ids: set,
        limit: int = 5,
    ) -> List[ArticleMatch]:
        return []


class MockResponseGenerator:
    """Mock ResponseGenerator for E2E tests."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def generate_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> StructuredResponse:
        if self.should_fail:
            raise ResponseGeneratorError("MockResponseGenerator failure")
        summaries = [_make_article_summary(a) for a in articles[:3]]
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
    """Mock ConversationManager for E2E tests."""

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
        context = self._conversations.get(conversation_id)
        if context:
            context.turns = []
            context.current_topic = new_topic

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


class MockVectorStore:
    """Mock VectorStore for E2E tests."""

    def __init__(self):
        pass

    async def search_similar(self, **kwargs) -> List:
        return []


class InMemoryVectorStore:
    """In-memory vector store for testing vectorization scenarios."""

    def __init__(self):
        self._embeddings: Dict[tuple, List[float]] = {}  # (article_id, chunk_index) -> embedding

    async def store_embedding(
        self,
        article_id: UUID,
        embedding: List[float],
        chunk_index: int = 0,
    ) -> None:
        """Store or update an embedding."""
        key = (str(article_id), chunk_index)
        self._embeddings[key] = embedding

    async def search_similar(
        self,
        query_vector: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = 0.5,
    ) -> List[VectorMatch]:
        """Search for similar embeddings (simple mock implementation)."""
        matches = []
        for (article_id_str, chunk_index), embedding in self._embeddings.items():
            # Simple similarity: just check if vectors exist
            similarity = 0.85  # Mock similarity score
            if similarity >= threshold:
                matches.append(
                    VectorMatch(
                        article_id=UUID(article_id_str),
                        similarity_score=similarity,
                        metadata={},
                        chunk_index=chunk_index,
                    )
                )
        return matches[:limit]

    async def delete_embedding(self, article_id: UUID) -> int:
        """Delete all chunks for an article."""
        article_id_str = str(article_id)
        keys_to_delete = [k for k in self._embeddings.keys() if k[0] == article_id_str]
        for key in keys_to_delete:
            del self._embeddings[key]
        return len(keys_to_delete)


def _make_controller(
    query_processor=None,
    retrieval_engine=None,
    response_generator=None,
    conversation_manager=None,
    embedding_service=None,
    vector_store=None,
) -> QAAgentController:
    """Create a QAAgentController with mock components."""
    return QAAgentController(
        query_processor=query_processor or MockQueryProcessor(),
        retrieval_engine=retrieval_engine or MockRetrievalEngine(),
        response_generator=response_generator or MockResponseGenerator(),
        conversation_manager=conversation_manager or MockConversationManager(),
        embedding_service=embedding_service or MockEmbeddingService(),
        vector_store=vector_store or MockVectorStore(),
    )


# ===========================================================================
# Scenario 1: Complete User Journey (5 steps)
# ===========================================================================


class TestCompleteUserJourney:
    """Test complete user journey from query to response."""

    @pytest.mark.asyncio
    async def test_complete_user_journey_five_steps(self):
        """
        Complete user journey:
        1. User submits query → structured response with articles
        2. User asks follow-up → uses conversation context
        3. User asks another follow-up → context preserved across 3 turns
        4. User deletes conversation → history is gone
        5. Verify deleted conversation cannot be retrieved
        """
        ctrl = _make_controller()
        user_id = str(uuid4())

        # Step 1: User submits a query
        response1 = await ctrl.process_query(
            user_id=user_id,
            query="What are the latest developments in AI?",
        )
        assert isinstance(response1, StructuredResponse)
        assert response1.response_type == ResponseType.STRUCTURED
        assert len(response1.articles) > 0
        conversation_id = str(response1.conversation_id)

        # Step 2: User asks a follow-up question
        response2 = await ctrl.continue_conversation(
            user_id=user_id,
            query="Tell me more about neural networks",
            conversation_id=conversation_id,
        )
        assert isinstance(response2, StructuredResponse)
        assert response2.conversation_id == response1.conversation_id

        # Step 3: User asks another follow-up
        response3 = await ctrl.continue_conversation(
            user_id=user_id,
            query="What about deep learning applications?",
            conversation_id=conversation_id,
        )
        assert isinstance(response3, StructuredResponse)
        assert response3.conversation_id == response1.conversation_id

        # Verify context preserved across 3 turns
        context = await ctrl.get_conversation_history(user_id, conversation_id)
        assert context is not None
        assert len(context.turns) == 3

        # Step 4: User deletes conversation
        deleted = await ctrl.delete_conversation(user_id, conversation_id)
        assert deleted is True

        # Step 5: Verify deleted conversation cannot be retrieved
        context_after_delete = await ctrl.get_conversation_history(user_id, conversation_id)
        assert context_after_delete is None


# ===========================================================================
# Scenario 2: Multi-turn Conversation with Context Preservation (10-turn limit)
# ===========================================================================


class TestMultiTurnConversationContextPreservation:
    """Test multi-turn conversation with 10-turn limit."""

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_ten_turn_limit(self):
        """
        Multi-turn conversation with 10-turn limit:
        1. Create conversation with 5 turns
        2. Verify all 5 turns are stored
        3. Add 6 more turns (total 11) → only 10 are kept
        4. Verify oldest turn was dropped
        5. Verify turn numbers are sequential (1-10)
        """
        ctrl = _make_controller()
        user_id = str(uuid4())

        # Step 1: Create conversation with 5 turns
        response1 = await ctrl.process_query(user_id=user_id, query="Query 1")
        conversation_id = str(response1.conversation_id)

        for i in range(2, 6):
            await ctrl.continue_conversation(
                user_id=user_id,
                query=f"Query {i}",
                conversation_id=conversation_id,
            )

        # Step 2: Verify all 5 turns are stored
        context = await ctrl.get_conversation_history(user_id, conversation_id)
        assert context is not None
        assert len(context.turns) == 5

        # Step 3: Add 6 more turns (total 11)
        for i in range(6, 12):
            await ctrl.continue_conversation(
                user_id=user_id,
                query=f"Query {i}",
                conversation_id=conversation_id,
            )

        # Step 4: Verify only 10 turns are kept (most recent)
        context = await ctrl.get_conversation_history(user_id, conversation_id)
        assert context is not None
        assert len(context.turns) == 10

        # Step 5: Verify oldest turn was dropped and turn numbers are sequential
        turn_numbers = [turn.turn_number for turn in context.turns]
        assert turn_numbers == list(range(1, 11))

        # Verify the queries are the most recent 10
        queries = [turn.query for turn in context.turns]
        expected_queries = [f"Query {i}" for i in range(2, 12)]
        assert queries == expected_queries


# ===========================================================================
# Scenario 3: Personalized User Journey
# ===========================================================================


class TestPersonalizedUserJourney:
    """Test personalized user journey with user profile."""

    @pytest.mark.asyncio
    async def test_personalized_user_journey(self):
        """
        Personalized user journey:
        1. Create user profile with preferred topics
        2. Submit 3 queries with user profile
        3. Verify all 3 responses are valid StructuredResponse objects
        4. Verify each response has a conversation_id
        """
        ctrl = _make_controller()
        user_id = uuid4()

        # Step 1: Create user profile with preferred topics
        user_profile = UserProfile(
            user_id=user_id,
            preferred_topics=["AI", "Machine Learning", "Deep Learning"],
            language_preference=QueryLanguage.ENGLISH,
        )

        # Step 2: Submit 3 queries with user profile
        queries = [
            "What are the latest AI developments?",
            "Tell me about machine learning applications",
            "How does deep learning work?",
        ]

        responses = []
        for query in queries:
            response = await ctrl.process_query(
                user_id=str(user_id),
                query=query,
                user_profile=user_profile,
            )
            responses.append(response)

        # Step 3: Verify all 3 responses are valid StructuredResponse objects
        assert len(responses) == 3
        for response in responses:
            assert isinstance(response, StructuredResponse)
            assert response.response_type == ResponseType.STRUCTURED

        # Step 4: Verify each response has a conversation_id
        for response in responses:
            assert response.conversation_id is not None
            assert isinstance(response.conversation_id, UUID)


# ===========================================================================
# Scenario 4: Error Recovery Journey
# ===========================================================================


class TestErrorRecoveryJourney:
    """Test error recovery and fallback mechanisms."""

    @pytest.mark.asyncio
    async def test_error_recovery_journey(self):
        """
        Error recovery journey:
        1. Submit query when retrieval engine fails → get fallback response
        2. Submit query when response generator fails → get search results fallback
        3. Submit empty query → get error response with helpful message
        4. Submit valid query after errors → system recovers
        """
        user_id = str(uuid4())

        # Step 1: Retrieval engine fails → fallback response
        ctrl1 = _make_controller(retrieval_engine=MockRetrievalEngine(should_fail=True))
        response1 = await ctrl1.process_query(user_id=user_id, query="Test query 1")
        assert isinstance(response1, StructuredResponse)
        # Should not crash, should return some response type

        # Step 2: Response generator fails → search results fallback
        ctrl2 = _make_controller(response_generator=MockResponseGenerator(should_fail=True))
        response2 = await ctrl2.process_query(user_id=user_id, query="Test query 2")
        assert isinstance(response2, StructuredResponse)
        assert response2.response_type in (
            ResponseType.SEARCH_RESULTS,
            ResponseType.ERROR,
            ResponseType.PARTIAL,
        )

        # Step 3: Empty query → error response
        ctrl3 = _make_controller()
        response3 = await ctrl3.process_query(user_id=user_id, query="")
        assert isinstance(response3, StructuredResponse)
        assert response3.response_type == ResponseType.ERROR
        assert len(response3.insights) > 0

        # Step 4: Valid query after errors → system recovers
        ctrl4 = _make_controller()
        response4 = await ctrl4.process_query(user_id=user_id, query="Valid query")
        assert isinstance(response4, StructuredResponse)
        assert response4.response_type == ResponseType.STRUCTURED
        assert len(response4.articles) > 0


# ===========================================================================
# Scenario 5: Load Scenario (concurrent users)
# ===========================================================================


class TestLoadScenarioConcurrentUsers:
    """Test system behavior under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_users_load_scenario(self):
        """
        Load scenario:
        1. 10 users each submit 3 queries sequentially (30 total, 10 concurrent)
        2. All 30 responses must be valid StructuredResponse objects
        3. Each user's conversation_id must be consistent across their 3 queries
        4. No cross-user data leakage
        """
        ctrl = _make_controller()

        # Step 1: 10 users each submit 3 queries sequentially
        async def user_session(user_index: int):
            user_id = str(uuid4())
            responses = []

            # First query
            response1 = await ctrl.process_query(
                user_id=user_id,
                query=f"User {user_index} query 1",
            )
            responses.append(response1)
            conversation_id = str(response1.conversation_id)

            # Second query (continue conversation)
            response2 = await ctrl.continue_conversation(
                user_id=user_id,
                query=f"User {user_index} query 2",
                conversation_id=conversation_id,
            )
            responses.append(response2)

            # Third query (continue conversation)
            response3 = await ctrl.continue_conversation(
                user_id=user_id,
                query=f"User {user_index} query 3",
                conversation_id=conversation_id,
            )
            responses.append(response3)

            return user_id, responses

        # Run 10 user sessions concurrently
        tasks = [user_session(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Step 2: All 30 responses must be valid StructuredResponse objects
        all_responses = []
        for user_id, responses in results:
            all_responses.extend(responses)

        assert len(all_responses) == 30
        for response in all_responses:
            assert isinstance(response, StructuredResponse)

        # Step 3: Each user's conversation_id must be consistent
        for user_id, responses in results:
            conversation_ids = [str(r.conversation_id) for r in responses]
            assert len(set(conversation_ids)) == 1, "User's conversation_id should be consistent"

        # Step 4: No cross-user data leakage
        all_conversation_ids = [
            str(r.conversation_id) for _, responses in results for r in responses
        ]
        unique_conversation_ids = set(all_conversation_ids)
        assert len(unique_conversation_ids) == 10, "Each user should have unique conversation"


# ===========================================================================
# Scenario 6: System Health Journey
# ===========================================================================


class TestSystemHealthJourney:
    """Test system health monitoring and reporting."""

    @pytest.mark.asyncio
    async def test_system_health_journey(self):
        """
        System health journey:
        1. Check system health → all components healthy
        2. Verify health check includes required fields
        3. Verify error_handling_features are advertised
        """
        ctrl = _make_controller()

        # Step 1: Check system health
        health = await ctrl.get_system_health()

        # Step 2: Verify health check includes required fields
        required_fields = {"overall_health", "status", "components", "timestamp"}
        assert required_fields.issubset(health.keys())

        # Verify overall_health is a valid score
        assert isinstance(health["overall_health"], (int, float))
        assert 0.0 <= health["overall_health"] <= 1.0

        # Verify status is valid
        assert health["status"] in ("healthy", "degraded", "unhealthy")

        # Verify components is a dict
        assert isinstance(health["components"], dict)

        # Verify timestamp is present
        assert "timestamp" in health

        # Step 3: Verify error_handling_features are advertised
        assert "error_handling_features" in health
        features = health["error_handling_features"]

        assert features.get("keyword_search_fallback") is True
        assert features.get("search_results_fallback") is True
        assert features.get("partial_results_on_timeout") is True
        assert features.get("retry_mechanisms") is True
        assert features.get("circuit_breakers") is True
        assert features.get("comprehensive_error_logging") is True

    @pytest.mark.asyncio
    async def test_system_health_with_all_components_healthy(self):
        """When all components are healthy, overall_health should be >= 0.8."""
        ctrl = _make_controller()
        health = await ctrl.get_system_health()

        assert health["overall_health"] >= 0.8
        assert health["status"] == "healthy"
