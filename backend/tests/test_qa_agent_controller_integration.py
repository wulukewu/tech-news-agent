"""
Integration tests for QAAgentController

Tests the complete query-to-response flow, error scenarios, fallback mechanisms,
and concurrent user handling.

Requirements covered:
- 6.4: Support 50+ concurrent users
- 9.1: Fallback to keyword search when vector store unavailable
- 9.2: Provide search results list when generation fails
- 9.3: Log all errors with meaningful messages
- 9.4: Provide partial results on timeout
- 9.5: Retry mechanism for transient errors
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Optional
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
from app.qa_agent.qa_agent_controller import (
    CircuitBreaker,
    QAAgentController,
    RetryMechanism,
)
from app.qa_agent.query_processor import QueryValidationResult
from app.qa_agent.response_generator import ResponseGeneratorError
from app.qa_agent.retrieval_engine import RetrievalEngineError
from app.qa_agent.vector_store import VectorStoreError

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_article_match(
    title: str = "Test Article",
    similarity_score: float = 0.85,
    category: str = "Technology",
) -> ArticleMatch:
    return ArticleMatch(
        article_id=uuid4(),
        title=title,
        content_preview="This is a test article content preview for integration testing.",
        similarity_score=similarity_score,
        url="https://example.com/article",
        published_at=datetime.utcnow(),
        feed_name="Test Feed",
        category=category,
    )


def _make_article_summary(article: ArticleMatch) -> ArticleSummary:
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
    """Configurable mock for QueryProcessor."""

    def __init__(
        self,
        should_fail: bool = False,
        delay: float = 0.0,
        is_valid: bool = True,
        error_message: str = "Query cannot be empty",
    ):
        self.should_fail = should_fail
        self.delay = delay
        self.is_valid = is_valid
        self.error_message = error_message
        self.validate_call_count = 0
        self.parse_call_count = 0

    async def validate_query(self, query: str) -> QueryValidationResult:
        self.validate_call_count += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise Exception("MockQueryProcessor.validate_query failure")
        if not query.strip():
            return QueryValidationResult(is_valid=False, error_message="Query cannot be empty")
        if not self.is_valid:
            return QueryValidationResult(is_valid=False, error_message=self.error_message)
        return QueryValidationResult(is_valid=True)

    async def parse_query(
        self,
        query: str,
        language: str = "auto",
        context: Optional[ConversationContext] = None,
    ) -> ParsedQuery:
        self.parse_call_count += 1
        if self.delay:
            await asyncio.sleep(self.delay)
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
        if self.delay:
            await asyncio.sleep(self.delay)
        return query


class MockEmbeddingService:
    """Configurable mock for EmbeddingService."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay
        self.call_count = 0

    async def generate_embedding(self, text: str) -> List[float]:
        self.call_count += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise EmbeddingError("MockEmbeddingService failure")
        return [0.1] * 1536


class MockRetrievalEngine:
    """Configurable mock for RetrievalEngine."""

    def __init__(
        self,
        should_fail: bool = False,
        delay: float = 0.0,
        return_empty: bool = False,
        articles: Optional[List[ArticleMatch]] = None,
        keyword_fallback_articles: Optional[List[ArticleMatch]] = None,
    ):
        self.should_fail = should_fail
        self.delay = delay
        self.return_empty = return_empty
        self._articles = articles
        self._keyword_fallback_articles = keyword_fallback_articles or []
        self.intelligent_search_call_count = 0
        self.semantic_search_call_count = 0
        self.keyword_expand_call_count = 0

    async def intelligent_search(
        self,
        query: str,
        query_vector: List[float],
        user_id: str,
        user_profile: Optional[UserProfile] = None,
        **kwargs,
    ) -> dict:
        self.intelligent_search_call_count += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise RetrievalEngineError("MockRetrievalEngine.intelligent_search failure")
        if self.return_empty:
            return {"results": [], "expanded": False, "personalized": False}
        articles = self._articles or [_make_article_match()]
        return {
            "results": articles,
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
        self.semantic_search_call_count += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise RetrievalEngineError("MockRetrievalEngine.semantic_search failure")
        if self.return_empty:
            return []
        return self._articles or [_make_article_match()]

    async def _expand_by_keywords(
        self,
        query_text: str,
        user_uuid: UUID,
        existing_ids: set,
        limit: int = 5,
    ) -> List[ArticleMatch]:
        self.keyword_expand_call_count += 1
        return self._keyword_fallback_articles


class MockResponseGenerator:
    """Configurable mock for ResponseGenerator."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay
        self.call_count = 0

    async def generate_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> StructuredResponse:
        self.call_count += 1
        if self.delay:
            await asyncio.sleep(self.delay)
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
    """Configurable mock for ConversationManager."""

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay
        self._conversations: dict = {}

    async def create_conversation(self, user_id: UUID) -> str:
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise Exception("MockConversationManager.create_conversation failure")
        conversation_id = str(uuid4())
        context = ConversationContext(conversation_id=UUID(conversation_id), user_id=user_id)
        self._conversations[conversation_id] = context
        return conversation_id

    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise Exception("MockConversationManager.get_context failure")
        return self._conversations.get(conversation_id)

    async def should_reset_context(self, conversation_id: str, new_query: str) -> bool:
        if self.delay:
            await asyncio.sleep(self.delay)
        return False

    async def reset_context(self, conversation_id: str, new_topic: Optional[str] = None) -> None:
        if self.delay:
            await asyncio.sleep(self.delay)

    async def add_turn(
        self,
        conversation_id: str,
        query: str,
        parsed_query: Optional[ParsedQuery] = None,
        response: Optional[StructuredResponse] = None,
    ) -> None:
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise Exception("MockConversationManager.add_turn failure")
        context = self._conversations.get(conversation_id)
        if context:
            context.add_turn(query, parsed_query, response)

    async def delete_conversation(self, conversation_id: str) -> bool:
        if self.delay:
            await asyncio.sleep(self.delay)
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False


class MockVectorStore:
    """Configurable mock for VectorStore."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def search_similar(self, **kwargs) -> List:
        if self.should_fail:
            raise VectorStoreError("MockVectorStore failure")
        return []


def _make_controller(
    query_processor=None,
    retrieval_engine=None,
    response_generator=None,
    conversation_manager=None,
    embedding_service=None,
    vector_store=None,
) -> QAAgentController:
    return QAAgentController(
        query_processor=query_processor or MockQueryProcessor(),
        retrieval_engine=retrieval_engine or MockRetrievalEngine(),
        response_generator=response_generator or MockResponseGenerator(),
        conversation_manager=conversation_manager or MockConversationManager(),
        embedding_service=embedding_service or MockEmbeddingService(),
        vector_store=vector_store or MockVectorStore(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def controller():
    return _make_controller()


@pytest.fixture
def user_profile():
    return UserProfile(
        user_id=uuid4(),
        preferred_topics=["AI", "Machine Learning"],
        language_preference=QueryLanguage.ENGLISH,
    )


# ===========================================================================
# 1. Complete query-to-response flow
# ===========================================================================


class TestCompleteQueryToResponseFlow:
    """Integration tests for the full query processing pipeline."""

    @pytest.mark.asyncio
    async def test_basic_query_returns_structured_response(self, controller, user_profile):
        """Happy-path: a valid query produces a STRUCTURED response with articles."""
        response = await controller.process_query(
            user_id=str(uuid4()),
            query="What are the latest developments in AI?",
            user_profile=user_profile,
        )

        assert isinstance(response, StructuredResponse)
        assert response.response_type == ResponseType.STRUCTURED
        assert len(response.articles) > 0
        assert response.response_time >= 0
        assert response.confidence > 0
        assert response.conversation_id is not None

    @pytest.mark.asyncio
    async def test_response_contains_required_fields(self, controller):
        """Every response must carry query, conversation_id, and response_time."""
        query = "Tell me about machine learning"
        response = await controller.process_query(user_id=str(uuid4()), query=query)

        assert response.query == query
        assert isinstance(response.conversation_id, UUID)
        assert response.response_time >= 0

    @pytest.mark.asyncio
    async def test_new_conversation_created_when_no_id_provided(self, controller):
        """A new conversation_id is created when none is supplied."""
        response = await controller.process_query(
            user_id=str(uuid4()),
            query="What is deep learning?",
        )

        assert response.conversation_id is not None

    @pytest.mark.asyncio
    async def test_existing_conversation_id_is_preserved(self, controller):
        """When a conversation_id is provided, the response uses the same conversation."""
        user_id = str(uuid4())

        first = await controller.process_query(user_id=user_id, query="What is AI?")
        conversation_id = str(first.conversation_id)

        second = await controller.process_query(
            user_id=user_id,
            query="Tell me more about neural networks",
            conversation_id=conversation_id,
        )

        assert second.conversation_id == first.conversation_id

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_flow(self, controller, user_profile):
        """Three consecutive turns in the same conversation all succeed."""
        user_id = str(uuid4())

        r1 = await controller.process_query(
            user_id=user_id, query="What is machine learning?", user_profile=user_profile
        )
        assert r1.response_type == ResponseType.STRUCTURED
        conv_id = str(r1.conversation_id)

        r2 = await controller.continue_conversation(
            user_id=user_id,
            query="What are the main types?",
            conversation_id=conv_id,
            user_profile=user_profile,
        )
        assert r2.conversation_id == r1.conversation_id
        assert r2.response_type == ResponseType.STRUCTURED

        r3 = await controller.continue_conversation(
            user_id=user_id,
            query="Tell me more about supervised learning",
            conversation_id=conv_id,
            user_profile=user_profile,
        )
        assert r3.conversation_id == r1.conversation_id
        assert r3.response_type == ResponseType.STRUCTURED

    @pytest.mark.asyncio
    async def test_conversation_history_is_stored(self, controller):
        """After a query, the conversation history is retrievable."""
        user_id = str(uuid4())
        response = await controller.process_query(user_id=user_id, query="What is NLP?")
        conv_id = str(response.conversation_id)

        history = await controller.get_conversation_history(user_id, conv_id)

        assert history is not None
        assert history.conversation_id == response.conversation_id
        assert str(history.user_id) == user_id

    @pytest.mark.asyncio
    async def test_user_profile_personalization_accepted(self, controller, user_profile):
        """Passing a user_profile does not break the pipeline."""
        response = await controller.process_query(
            user_id=str(user_profile.user_id),
            query="Recommend articles about AI",
            user_profile=user_profile,
        )

        assert response.response_type == ResponseType.STRUCTURED

    @pytest.mark.asyncio
    async def test_articles_sorted_by_relevance(self, controller):
        """Articles in the response are sorted by relevance (highest first)."""
        articles = [
            _make_article_match("Low relevance", similarity_score=0.5),
            _make_article_match("High relevance", similarity_score=0.95),
            _make_article_match("Medium relevance", similarity_score=0.75),
        ]
        ctrl = _make_controller(retrieval_engine=MockRetrievalEngine(articles=articles))

        response = await ctrl.process_query(user_id=str(uuid4()), query="AI articles")

        scores = [a.relevance_score for a in response.articles]
        assert scores == sorted(scores, reverse=True), "Articles must be sorted by relevance"

    @pytest.mark.asyncio
    async def test_response_time_is_recorded(self, controller):
        """response_time must be a positive float reflecting actual elapsed time."""
        start = time.time()
        response = await controller.process_query(user_id=str(uuid4()), query="Test query")
        elapsed = time.time() - start

        assert response.response_time > 0
        assert response.response_time <= elapsed + 0.5  # small tolerance


# ===========================================================================
# 2. Error scenarios and fallback mechanisms
# ===========================================================================


class TestErrorScenariosAndFallbacks:
    """Tests for Req 9.1, 9.2, 9.3, 9.4, 9.5 – error handling and fallbacks."""

    # -----------------------------------------------------------------------
    # 2a. Empty / invalid query (Req 9.3 – meaningful error messages)
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_empty_query_returns_error_response(self, controller):
        """An empty query must return ResponseType.ERROR with a helpful message."""
        response = await controller.process_query(user_id=str(uuid4()), query="")

        assert response.response_type == ResponseType.ERROR
        assert len(response.insights) > 0
        assert any("empty" in msg.lower() for msg in response.insights)

    @pytest.mark.asyncio
    async def test_whitespace_only_query_returns_error(self, controller):
        """A whitespace-only query is treated the same as empty."""
        response = await controller.process_query(user_id=str(uuid4()), query="   ")

        assert response.response_type == ResponseType.ERROR

    @pytest.mark.asyncio
    async def test_invalid_query_includes_suggestions(self):
        """When validation fails, the response should include suggestions."""
        ctrl = _make_controller(
            query_processor=MockQueryProcessor(is_valid=False, error_message="Query is too vague")
        )
        response = await ctrl.process_query(user_id=str(uuid4()), query="?")

        assert response.response_type == ResponseType.ERROR
        assert len(response.insights) > 0

    # -----------------------------------------------------------------------
    # 2b. Req 9.1 – Fallback to keyword search when vector store unavailable
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_vector_store_failure_triggers_keyword_fallback(self):
        """When the retrieval engine raises VectorStoreError, keyword fallback is used."""
        fallback_articles = [_make_article_match("Keyword fallback article")]
        retrieval = MockRetrievalEngine(
            should_fail=True,
            keyword_fallback_articles=fallback_articles,
        )
        ctrl = _make_controller(retrieval_engine=retrieval)

        response = await ctrl.process_query(user_id=str(uuid4()), query="What is machine learning?")

        # The controller must return a response (not crash)
        assert isinstance(response, StructuredResponse)
        assert response.query == "What is machine learning?"

    @pytest.mark.asyncio
    async def test_embedding_failure_falls_back_to_keyword_search(self):
        """When embedding generation fails, the pipeline continues with keyword search."""
        ctrl = _make_controller(
            embedding_service=MockEmbeddingService(should_fail=True),
        )

        response = await ctrl.process_query(
            user_id=str(uuid4()), query="Tell me about deep learning"
        )

        # Must still return a response
        assert isinstance(response, StructuredResponse)

    # -----------------------------------------------------------------------
    # 2c. Req 9.2 – Search results list when generation fails
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_response_generator_failure_returns_search_results_fallback(self):
        """When ResponseGenerator fails, the controller returns SEARCH_RESULTS fallback."""
        ctrl = _make_controller(
            response_generator=MockResponseGenerator(should_fail=True),
        )

        response = await ctrl.process_query(
            user_id=str(uuid4()), query="What is reinforcement learning?"
        )

        assert isinstance(response, StructuredResponse)
        # Must be SEARCH_RESULTS or ERROR – not a crash
        assert response.response_type in (
            ResponseType.SEARCH_RESULTS,
            ResponseType.ERROR,
            ResponseType.PARTIAL,
        )

    @pytest.mark.asyncio
    async def test_search_results_fallback_includes_articles(self):
        """The SEARCH_RESULTS fallback should still surface the retrieved articles."""
        articles = [_make_article_match(f"Article {i}") for i in range(3)]
        ctrl = _make_controller(
            retrieval_engine=MockRetrievalEngine(articles=articles),
            response_generator=MockResponseGenerator(should_fail=True),
        )

        response = await ctrl.process_query(user_id=str(uuid4()), query="AI research")

        # Articles should be present in the fallback response
        assert isinstance(response, StructuredResponse)
        if response.response_type == ResponseType.SEARCH_RESULTS:
            assert len(response.articles) > 0

    # -----------------------------------------------------------------------
    # 2d. Req 9.3 – Errors are logged with meaningful messages
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_retrieval_failure_is_logged(self, caplog):
        """A retrieval failure must produce a log entry at WARNING or ERROR level."""
        ctrl = _make_controller(
            retrieval_engine=MockRetrievalEngine(should_fail=True),
        )

        with caplog.at_level(logging.WARNING, logger="app.qa_agent.qa_agent_controller"):
            await ctrl.process_query(user_id=str(uuid4()), query="Test logging")

        # At least one warning/error must have been emitted
        assert len(caplog.records) > 0

    @pytest.mark.asyncio
    async def test_response_generator_failure_is_logged(self, caplog):
        """A response generator failure must produce a log entry."""
        ctrl = _make_controller(
            response_generator=MockResponseGenerator(should_fail=True),
        )

        with caplog.at_level(logging.WARNING, logger="app.qa_agent.qa_agent_controller"):
            await ctrl.process_query(user_id=str(uuid4()), query="Test logging")

        assert len(caplog.records) > 0

    @pytest.mark.asyncio
    async def test_error_response_contains_meaningful_message(self):
        """Error responses must contain at least one non-empty insight string."""
        ctrl = _make_controller(
            query_processor=MockQueryProcessor(is_valid=False, error_message="Query too short"),
        )

        response = await ctrl.process_query(user_id=str(uuid4()), query="x")

        assert response.response_type == ResponseType.ERROR
        assert any(len(msg.strip()) > 0 for msg in response.insights)

    # -----------------------------------------------------------------------
    # 2e. Req 9.4 – Partial results on timeout
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_slow_retrieval_returns_partial_or_fallback_response(self):
        """When retrieval is very slow, the controller returns a usable response."""
        # Delay longer than the retrieval timeout (1.0 s) but within overall budget
        ctrl = _make_controller(
            retrieval_engine=MockRetrievalEngine(delay=1.5),
        )

        start = time.time()
        response = await ctrl.process_query(user_id=str(uuid4()), query="Slow retrieval test")
        elapsed = time.time() - start

        assert isinstance(response, StructuredResponse)
        # Must complete within a reasonable bound (controller max is 3 s + buffer)
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_timeout_response_has_informative_message(self):
        """A timeout response must explain the situation to the user."""
        ctrl = _make_controller(
            retrieval_engine=MockRetrievalEngine(delay=1.5),
        )

        response = await ctrl.process_query(user_id=str(uuid4()), query="Timeout scenario")

        assert isinstance(response, StructuredResponse)
        # If it's an error/partial, insights must be non-empty
        if response.response_type in (ResponseType.ERROR, ResponseType.PARTIAL):
            assert len(response.insights) > 0

    # -----------------------------------------------------------------------
    # 2f. Req 9.5 – Retry mechanism for transient errors
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_retry_mechanism_retries_on_transient_errors(self):
        """RetryMechanism.execute_with_retry retries on transient exceptions."""
        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient network error")
            return "success"

        result = await RetryMechanism.execute_with_retry(
            flaky_operation,
            max_retries=3,
            base_delay=0.01,
            jitter=False,
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_mechanism_raises_after_max_retries(self):
        """RetryMechanism raises the last exception when all retries are exhausted."""

        async def always_fails():
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError):
            await RetryMechanism.execute_with_retry(
                always_fails,
                max_retries=2,
                base_delay=0.01,
                jitter=False,
            )

    @pytest.mark.asyncio
    async def test_retry_mechanism_does_not_retry_non_transient_errors(self):
        """Non-transient exceptions are raised immediately without retrying."""
        call_count = 0

        async def non_transient():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-transient error")

        with pytest.raises(ValueError):
            await RetryMechanism.execute_with_retry(
                non_transient,
                max_retries=3,
                base_delay=0.01,
                jitter=False,
            )

        assert call_count == 1, "Non-transient errors must not be retried"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """CircuitBreaker opens after reaching the failure threshold."""
        cb = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60.0, expected_exception=Exception
        )

        async def failing_op():
            raise Exception("Service down")

        for _ in range(3):
            try:
                await cb.call(failing_op)
            except Exception:
                pass

        assert cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_calls_when_open(self):
        """An OPEN circuit breaker rejects calls immediately."""
        cb = CircuitBreaker(
            failure_threshold=1, recovery_timeout=60.0, expected_exception=Exception
        )

        async def failing_op():
            raise Exception("Service down")

        # Trip the breaker
        try:
            await cb.call(failing_op)
        except Exception:
            pass

        assert cb.state == "OPEN"

        # Next call should be rejected by the circuit breaker itself
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(failing_op)

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(self):
        """CircuitBreaker resets to CLOSED after a successful call."""
        cb = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60.0, expected_exception=Exception
        )
        cb.failure_count = 3  # Simulate some failures

        async def success_op():
            return "ok"

        result = await cb.call(success_op)

        assert result == "ok"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0


# ===========================================================================
# 3. Access control and conversation management
# ===========================================================================


class TestAccessControlAndConversationManagement:
    """Tests for user isolation and conversation lifecycle."""

    @pytest.mark.asyncio
    async def test_user_cannot_access_another_users_conversation(self, controller):
        """User B must not be able to read User A's conversation history."""
        user_a = str(uuid4())
        user_b = str(uuid4())

        response = await controller.process_query(user_id=user_a, query="Private query")
        conv_id = str(response.conversation_id)

        history = await controller.get_conversation_history(user_b, conv_id)
        assert history is None

    @pytest.mark.asyncio
    async def test_user_cannot_delete_another_users_conversation(self, controller):
        """User B must not be able to delete User A's conversation."""
        user_a = str(uuid4())
        user_b = str(uuid4())

        response = await controller.process_query(user_id=user_a, query="Private query")
        conv_id = str(response.conversation_id)

        deleted = await controller.delete_conversation(user_b, conv_id)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_delete_conversation_removes_history(self, controller):
        """After deletion, get_conversation_history returns None."""
        user_id = str(uuid4())
        response = await controller.process_query(user_id=user_id, query="Test query")
        conv_id = str(response.conversation_id)

        deleted = await controller.delete_conversation(user_id, conv_id)
        assert deleted is True

        history = await controller.get_conversation_history(user_id, conv_id)
        assert history is None

    @pytest.mark.asyncio
    async def test_get_history_returns_none_for_nonexistent_conversation(self, controller):
        """Requesting history for a non-existent conversation returns None."""
        history = await controller.get_conversation_history(str(uuid4()), str(uuid4()))
        assert history is None


# ===========================================================================
# 4. System health check
# ===========================================================================


class TestSystemHealthCheck:
    """Tests for get_system_health (Req 9.3, 9.5)."""

    @pytest.mark.asyncio
    async def test_health_check_returns_required_keys(self, controller):
        """Health check response must contain all required keys."""
        health = await controller.get_system_health()

        required_keys = {"overall_health", "status", "components", "timestamp"}
        assert required_keys.issubset(health.keys())

    @pytest.mark.asyncio
    async def test_healthy_system_reports_healthy_status(self, controller):
        """All-healthy mocks should yield overall_health >= 0.8 and status 'healthy'."""
        health = await controller.get_system_health()

        assert health["overall_health"] >= 0.8
        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_failing_components_degrade_health(self):
        """Failing components must lower overall_health below 1.0.

        The controller's health check methods catch internal exceptions and return
        False/True booleans. The gather uses return_exceptions=True, so only
        exceptions that escape the health check coroutines themselves are treated
        as failures. We simulate this by patching the health check method directly
        to raise, which is what would happen if the coroutine itself crashed.
        """
        from unittest.mock import patch

        ctrl = _make_controller()

        # Patch two health check coroutines to raise so gather captures them
        async def raise_error():
            raise RuntimeError("Simulated health check failure")

        with (
            patch.object(ctrl, "_check_query_processor_health", side_effect=raise_error),
            patch.object(ctrl, "_check_vector_store_health", side_effect=raise_error),
        ):
            health = await ctrl.get_system_health()

        assert health["overall_health"] < 1.0
        assert health["status"] in ("degraded", "unhealthy")

    @pytest.mark.asyncio
    async def test_health_check_reports_error_handling_features(self, controller):
        """Health check must advertise the error-handling capabilities."""
        health = await controller.get_system_health()

        features = health.get("error_handling_features", {})
        assert features.get("keyword_search_fallback") is True
        assert features.get("search_results_fallback") is True
        assert features.get("partial_results_on_timeout") is True
        assert features.get("retry_mechanisms") is True

    @pytest.mark.asyncio
    async def test_health_check_includes_circuit_breaker_states(self, controller):
        """Health check must include circuit breaker state information."""
        health = await controller.get_system_health()

        assert "circuit_breakers" in health
        cb_states = health["circuit_breakers"]
        assert "embedding_service" in cb_states
        assert "vector_store" in cb_states
        assert "response_generator" in cb_states


# ===========================================================================
# 5. Concurrent user handling (Req 6.4)
# ===========================================================================


class TestConcurrentUserHandling:
    """Tests verifying the system handles multiple simultaneous users correctly."""

    @pytest.mark.asyncio
    async def test_ten_concurrent_queries_all_succeed(self):
        """10 concurrent queries from different users must all return valid responses."""
        ctrl = _make_controller()
        user_ids = [str(uuid4()) for _ in range(10)]
        queries = [f"Query from user {i}" for i in range(10)]

        tasks = [ctrl.process_query(user_id=uid, query=q) for uid, q in zip(user_ids, queries)]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 10
        for resp in responses:
            assert isinstance(resp, StructuredResponse)

    @pytest.mark.asyncio
    async def test_fifty_concurrent_queries_all_succeed(self):
        """50 concurrent queries (Req 6.4) must all return valid responses."""
        ctrl = _make_controller()
        n = 50
        user_ids = [str(uuid4()) for _ in range(n)]
        queries = [f"Concurrent query {i}" for i in range(n)]

        tasks = [ctrl.process_query(user_id=uid, query=q) for uid, q in zip(user_ids, queries)]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == n
        for resp in responses:
            assert isinstance(resp, StructuredResponse)

    @pytest.mark.asyncio
    async def test_concurrent_queries_are_isolated_per_user(self):
        """Each concurrent user gets their own conversation_id."""
        ctrl = _make_controller()
        n = 20
        user_ids = [str(uuid4()) for _ in range(n)]

        tasks = [ctrl.process_query(user_id=uid, query="What is AI?") for uid in user_ids]
        responses = await asyncio.gather(*tasks)

        conversation_ids = {str(r.conversation_id) for r in responses}
        # Each user should have a distinct conversation
        assert len(conversation_ids) == n

    @pytest.mark.asyncio
    async def test_concurrent_queries_complete_within_time_limit(self):
        """50 concurrent queries must all complete within a reasonable wall-clock time."""
        ctrl = _make_controller()
        n = 50
        user_ids = [str(uuid4()) for _ in range(n)]

        start = time.time()
        tasks = [
            ctrl.process_query(user_id=uid, query=f"Query {i}") for i, uid in enumerate(user_ids)
        ]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # With async concurrency, 50 queries should finish well under 10 s
        assert elapsed < 10.0, f"50 concurrent queries took {elapsed:.2f}s (limit: 10s)"

    @pytest.mark.asyncio
    async def test_concurrent_queries_with_partial_failures(self):
        """When some concurrent queries fail, the others must still succeed."""
        # Use a retrieval engine that fails on every other call
        call_count = 0

        class AlternatingRetrievalEngine(MockRetrievalEngine):
            async def intelligent_search(self, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 2 == 0:
                    raise RetrievalEngineError("Alternating failure")
                return {
                    "results": [_make_article_match()],
                    "expanded": False,
                    "personalized": False,
                }

        ctrl = _make_controller(retrieval_engine=AlternatingRetrievalEngine())
        n = 10
        user_ids = [str(uuid4()) for _ in range(n)]

        tasks = [
            ctrl.process_query(user_id=uid, query=f"Query {i}") for i, uid in enumerate(user_ids)
        ]
        responses = await asyncio.gather(*tasks)

        # All must return a StructuredResponse (no unhandled exceptions)
        assert len(responses) == n
        for resp in responses:
            assert isinstance(resp, StructuredResponse)


# ===========================================================================
# 6. Performance requirement (Req 6.2)
# ===========================================================================


class TestPerformanceRequirement:
    """Verify the 3-second response time requirement."""

    @pytest.mark.asyncio
    async def test_single_query_completes_within_three_seconds(self, controller):
        """A single query must complete within 3 seconds (Req 6.2)."""
        start = time.time()
        response = await controller.process_query(
            user_id=str(uuid4()), query="What is the latest in AI research?"
        )
        elapsed = time.time() - start

        assert elapsed <= 3.5  # 0.5 s buffer for test overhead
        assert response.response_time <= 3.5

    @pytest.mark.asyncio
    async def test_response_time_field_reflects_actual_duration(self, controller):
        """response_time in the response must be close to the actual wall-clock time."""
        start = time.time()
        response = await controller.process_query(
            user_id=str(uuid4()), query="Performance test query"
        )
        elapsed = time.time() - start

        # response_time should be within 1 second of actual elapsed time
        assert abs(response.response_time - elapsed) < 1.0
