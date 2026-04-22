"""
Property-based tests for Error Recovery and Fallback (Property 13)

Feature: intelligent-qa-agent
Property 13: Error Recovery and Fallback

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

For any system failure (vector store unavailable, generation failure, timeout),
the system SHALL gracefully fall back to alternative methods (keyword search,
search results list, partial results) while providing meaningful error messages
and implementing appropriate retry mechanisms for transient errors.
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from app.qa_agent.models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
)
from app.qa_agent.qa_agent_controller import (
    CircuitBreaker,
    QAAgentController,
    RetryMechanism,
)
from app.qa_agent.query_processor import QueryValidationResult
from app.qa_agent.response_generator import ResponseGeneratorError
from app.qa_agent.retrieval_engine import RetrievalEngineError

# ============================================================================
# Mock helpers (reused from integration test pattern)
# ============================================================================


def _make_article_match(
    title: str = "Test Article",
    similarity_score: float = 0.85,
    category: str = "Technology",
) -> ArticleMatch:
    return ArticleMatch(
        article_id=uuid4(),
        title=title,
        content_preview="This is a test article content preview for property testing.",
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
        is_valid: bool = True,
        error_message: str = "Query cannot be empty",
    ):
        self.should_fail = should_fail
        self.is_valid = is_valid
        self.error_message = error_message

    async def validate_query(self, query: str) -> QueryValidationResult:
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
    """Configurable mock for EmbeddingService."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.call_count = 0

    async def generate_embedding(self, text: str) -> List[float]:
        self.call_count += 1
        if self.should_fail:
            from app.qa_agent.embedding_service import EmbeddingError

            raise EmbeddingError("MockEmbeddingService failure")
        return [0.1] * 1536


class MockRetrievalEngine:
    """Configurable mock for RetrievalEngine."""

    def __init__(
        self,
        should_fail: bool = False,
        return_empty: bool = False,
        articles: Optional[List[ArticleMatch]] = None,
        keyword_fallback_articles: Optional[List[ArticleMatch]] = None,
    ):
        self.should_fail = should_fail
        self.return_empty = return_empty
        self._articles = articles
        self._keyword_fallback_articles = keyword_fallback_articles or []
        self.intelligent_search_call_count = 0
        self.keyword_expand_call_count = 0

    async def intelligent_search(self, query, query_vector, user_id, **kwargs) -> dict:
        self.intelligent_search_call_count += 1
        if self.should_fail:
            raise RetrievalEngineError("MockRetrievalEngine.intelligent_search failure")
        if self.return_empty:
            return {"results": [], "expanded": False, "personalized": False}
        articles = self._articles or [_make_article_match()]
        return {
            "results": articles,
            "expanded": False,
            "personalized": False,
            "search_time": 0.05,
        }

    async def semantic_search(self, query_vector, user_id, limit=10, threshold=0.5, **kwargs):
        if self.should_fail:
            raise RetrievalEngineError("MockRetrievalEngine.semantic_search failure")
        if self.return_empty:
            return []
        return self._articles or [_make_article_match()]

    async def _expand_by_keywords(self, query_text, user_uuid, existing_ids, limit=5):
        self.keyword_expand_call_count += 1
        return self._keyword_fallback_articles


class MockResponseGenerator:
    """Configurable mock for ResponseGenerator."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.call_count = 0

    async def generate_response(self, query, articles, context=None, user_profile=None):
        self.call_count += 1
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

    def __init__(self):
        self._conversations: dict = {}

    async def create_conversation(self, user_id: UUID) -> str:
        conversation_id = str(uuid4())
        context = ConversationContext(conversation_id=UUID(conversation_id), user_id=user_id)
        self._conversations[conversation_id] = context
        return conversation_id

    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        return self._conversations.get(conversation_id)

    async def should_reset_context(self, conversation_id: str, new_query: str) -> bool:
        return False

    async def reset_context(self, conversation_id: str, new_topic=None) -> None:
        pass

    async def add_turn(self, conversation_id, query, parsed_query=None, response=None):
        context = self._conversations.get(conversation_id)
        if context:
            context.add_turn(query, parsed_query, response)

    async def delete_conversation(self, conversation_id: str) -> bool:
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
            from app.qa_agent.vector_store import VectorStoreError

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


# ============================================================================
# Custom Strategies
# ============================================================================


@composite
def valid_queries(draw):
    """Generate valid non-empty query strings."""
    topics = [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural networks",
        "natural language processing",
        "computer vision",
        "blockchain",
        "quantum computing",
        "data science",
        "cloud computing",
        "人工智慧",
        "機器學習",
        "深度學習",
        "自然語言處理",
    ]
    templates = [
        "What is {}?",
        "Tell me about {}",
        "How does {} work?",
        "Explain {}",
        "Latest developments in {}",
    ]
    template = draw(st.sampled_from(templates))
    topic = draw(st.sampled_from(topics))
    return template.format(topic)


@composite
def invalid_queries(draw):
    """Generate invalid queries (empty or whitespace-only)."""
    return draw(
        st.one_of(
            st.just(""),
            st.just("   "),
            st.just("\t"),
            st.just("\n"),
            st.text(alphabet=st.characters(whitelist_categories=("Zs",)), min_size=1, max_size=10),
        )
    )


# ============================================================================
# Property 13.1: RetryMechanism – transient errors are retried
# **Validates: Requirement 9.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(n_failures=st.integers(min_value=0, max_value=3))
def test_property_13_1_retry_mechanism_transient_errors_retried(n_failures):
    """
    Property 13.1: RetryMechanism – transient errors are retried

    **Validates: Requirements 9.5**

    For any number of initial failures N (0 ≤ N ≤ max_retries), if the operation
    succeeds on attempt N+1, execute_with_retry SHALL return the result.
    """
    call_count = 0

    async def flaky_operation():
        nonlocal call_count
        call_count += 1
        if call_count <= n_failures:
            raise ConnectionError(f"Transient failure #{call_count}")
        return "success"

    result = asyncio.run(
        RetryMechanism.execute_with_retry(
            flaky_operation,
            max_retries=3,
            base_delay=0.001,
            jitter=False,
        )
    )

    assert (
        result == "success"
    ), f"Expected 'success' after {n_failures} transient failures, got {result!r}"
    assert call_count == n_failures + 1, f"Expected {n_failures + 1} calls, got {call_count}"


# ============================================================================
# Property 13.2: RetryMechanism – exhausted retries raise last exception
# **Validates: Requirement 9.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(max_retries=st.integers(min_value=1, max_value=5))
def test_property_13_2_retry_mechanism_exhausted_raises(max_retries):
    """
    Property 13.2: RetryMechanism – exhausted retries raise last exception

    **Validates: Requirements 9.5**

    For any max_retries value (1–5), if the operation always fails,
    execute_with_retry SHALL raise the last exception after max_retries+1 attempts.
    """
    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ConnectionError(f"Persistent failure #{call_count}")

    with pytest.raises(ConnectionError):
        asyncio.run(
            RetryMechanism.execute_with_retry(
                always_fails,
                max_retries=max_retries,
                base_delay=0.001,
                jitter=False,
            )
        )

    assert (
        call_count == max_retries + 1
    ), f"Expected {max_retries + 1} total attempts, got {call_count}"


# ============================================================================
# Property 13.3: RetryMechanism – non-transient errors are not retried
# **Validates: Requirement 9.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(exc_type=st.sampled_from([ValueError, TypeError, KeyError, AttributeError, RuntimeError]))
def test_property_13_3_retry_mechanism_non_transient_not_retried(exc_type):
    """
    Property 13.3: RetryMechanism – non-transient errors are not retried

    **Validates: Requirements 9.5**

    For any non-transient exception (ValueError, TypeError, etc.),
    execute_with_retry SHALL raise immediately without retrying (call_count == 1).
    """
    call_count = 0

    async def non_transient():
        nonlocal call_count
        call_count += 1
        raise exc_type("Non-transient error")

    with pytest.raises(exc_type):
        asyncio.run(
            RetryMechanism.execute_with_retry(
                non_transient,
                max_retries=3,
                base_delay=0.001,
                jitter=False,
            )
        )

    assert call_count == 1, (
        f"Non-transient {exc_type.__name__} should not be retried, "
        f"but operation was called {call_count} times"
    )


# ============================================================================
# Property 13.4: CircuitBreaker – opens after threshold failures
# **Validates: Requirement 9.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(failure_threshold=st.integers(min_value=1, max_value=10))
def test_property_13_4_circuit_breaker_opens_after_threshold(failure_threshold):
    """
    Property 13.4: CircuitBreaker – opens after threshold failures

    **Validates: Requirements 9.5**

    For any failure_threshold (1–10), after exactly failure_threshold failures,
    the circuit breaker state SHALL be "OPEN".
    """
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=60.0,
        expected_exception=Exception,
    )

    async def failing_op():
        raise Exception("Service down")

    async def run_failures():
        for _ in range(failure_threshold):
            try:
                await cb.call(failing_op)
            except Exception:
                pass

    asyncio.run(run_failures())

    assert cb.state == "OPEN", (
        f"Circuit breaker should be OPEN after {failure_threshold} failures, "
        f"but state is {cb.state!r}"
    )
    assert (
        cb.failure_count >= failure_threshold
    ), f"failure_count should be >= {failure_threshold}, got {cb.failure_count}"


# ============================================================================
# Property 13.5: CircuitBreaker – rejects calls when OPEN
# **Validates: Requirement 9.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(failure_threshold=st.integers(min_value=1, max_value=5))
def test_property_13_5_circuit_breaker_rejects_when_open(failure_threshold):
    """
    Property 13.5: CircuitBreaker – rejects calls when OPEN

    **Validates: Requirements 9.5**

    When the circuit breaker is OPEN, calling cb.call(operation) SHALL raise
    an exception with "Circuit breaker is OPEN" in the message.
    """
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=60.0,
        expected_exception=Exception,
    )

    async def failing_op():
        raise Exception("Service down")

    async def run():
        # Trip the breaker
        for _ in range(failure_threshold):
            try:
                await cb.call(failing_op)
            except Exception:
                pass

        assert cb.state == "OPEN"

        # Next call should be rejected by the circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(failing_op)

    asyncio.run(run())


# ============================================================================
# Property 13.6: CircuitBreaker – resets to CLOSED on success
# **Validates: Requirement 9.5**
# ============================================================================


@settings(max_examples=50, deadline=None)
@given(initial_failure_count=st.integers(min_value=0, max_value=4))
def test_property_13_6_circuit_breaker_resets_on_success(initial_failure_count):
    """
    Property 13.6: CircuitBreaker – resets to CLOSED on success

    **Validates: Requirements 9.5**

    After a successful call, the circuit breaker SHALL reset to "CLOSED" state
    with failure_count == 0.
    """
    cb = CircuitBreaker(
        failure_threshold=10,  # High threshold so it stays CLOSED
        recovery_timeout=60.0,
        expected_exception=Exception,
    )
    # Simulate some prior failures without opening the breaker
    cb.failure_count = initial_failure_count

    async def success_op():
        return "ok"

    result = asyncio.run(cb.call(success_op))

    assert result == "ok", f"Expected 'ok', got {result!r}"
    assert cb.state == "CLOSED", f"Circuit breaker should be CLOSED after success, got {cb.state!r}"
    assert cb.failure_count == 0, f"failure_count should be 0 after success, got {cb.failure_count}"


# ============================================================================
# Property 13.7: Controller – vector store failure triggers fallback
# **Validates: Requirement 9.1**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_queries())
def test_property_13_7_vector_store_failure_triggers_fallback(query):
    """
    Property 13.7: Controller – vector store failure triggers fallback

    **Validates: Requirements 9.1**

    For any query, when the retrieval engine raises RetrievalEngineError,
    the controller SHALL return a StructuredResponse (not raise an exception).
    """
    ctrl = _make_controller(
        retrieval_engine=MockRetrievalEngine(should_fail=True),
    )

    response = asyncio.run(ctrl.process_query(user_id=str(uuid4()), query=query))

    assert isinstance(
        response, StructuredResponse
    ), f"Expected StructuredResponse when retrieval fails, got {type(response).__name__}"
    assert response.query == query, "Response query should match input query"


# ============================================================================
# Property 13.8: Controller – response generator failure returns search results
# **Validates: Requirement 9.2**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=valid_queries())
def test_property_13_8_response_generator_failure_returns_search_results(query):
    """
    Property 13.8: Controller – response generator failure returns search results

    **Validates: Requirements 9.2**

    For any query, when the response generator raises ResponseGeneratorError,
    the controller SHALL return a StructuredResponse with response_type in
    (SEARCH_RESULTS, ERROR, PARTIAL).
    """
    ctrl = _make_controller(
        response_generator=MockResponseGenerator(should_fail=True),
    )

    response = asyncio.run(ctrl.process_query(user_id=str(uuid4()), query=query))

    assert isinstance(
        response, StructuredResponse
    ), f"Expected StructuredResponse when generator fails, got {type(response).__name__}"
    assert response.response_type in (
        ResponseType.SEARCH_RESULTS,
        ResponseType.ERROR,
        ResponseType.PARTIAL,
    ), f"Expected fallback response type, got {response.response_type!r}"


# ============================================================================
# Property 13.9: Controller – error responses contain meaningful messages
# **Validates: Requirement 9.3**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(query=invalid_queries())
def test_property_13_9_error_responses_contain_meaningful_messages(query):
    """
    Property 13.9: Controller – error responses contain meaningful messages

    **Validates: Requirements 9.3**

    For any invalid query (empty, whitespace-only), the error response SHALL
    contain at least one non-empty insight string.
    """
    ctrl = _make_controller()

    response = asyncio.run(ctrl.process_query(user_id=str(uuid4()), query=query))

    assert isinstance(
        response, StructuredResponse
    ), f"Expected StructuredResponse for invalid query, got {type(response).__name__}"
    assert (
        response.response_type == ResponseType.ERROR
    ), f"Expected ERROR response type for invalid query, got {response.response_type!r}"
    assert len(response.insights) > 0, "Error response must contain at least one insight message"
    assert any(
        len(msg.strip()) > 0 for msg in response.insights
    ), "At least one insight must be a non-empty string"


# ============================================================================
# Property 13.10: Controller – all responses are StructuredResponse instances
# **Validates: Requirements 9.1, 9.2, 9.3, 9.4**
# ============================================================================


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    retrieval_fails=st.booleans(),
    generation_fails=st.booleans(),
    query=valid_queries(),
)
def test_property_13_10_all_responses_are_structured_response(
    retrieval_fails, generation_fails, query
):
    """
    Property 13.10: Controller – all responses are StructuredResponse instances

    **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

    For any combination of component failures (retrieval fails, generation fails,
    both fail), the controller SHALL always return a StructuredResponse, never
    raise an unhandled exception.
    """
    ctrl = _make_controller(
        retrieval_engine=MockRetrievalEngine(should_fail=retrieval_fails),
        response_generator=MockResponseGenerator(should_fail=generation_fails),
    )

    response = asyncio.run(ctrl.process_query(user_id=str(uuid4()), query=query))

    assert isinstance(response, StructuredResponse), (
        f"Controller must always return StructuredResponse regardless of failures "
        f"(retrieval_fails={retrieval_fails}, generation_fails={generation_fails}), "
        f"got {type(response).__name__}"
    )
    assert response.query == query, "Response must echo back the original query"
    assert response.conversation_id is not None, "Response must always have a conversation_id"
    assert response.response_type in list(
        ResponseType
    ), f"response_type must be a valid ResponseType, got {response.response_type!r}"
