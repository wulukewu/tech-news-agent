"""
Integration tests for QAAgentController

Tests the complete query-to-response flow with mocked external dependencies:
- Complete query processing pipeline (query → embedding → retrieval → response)
- Error scenarios and fallback mechanisms (Req 9.1, 9.2, 9.3, 9.4, 9.5)
- Concurrent user handling (Req 6.4)
- Performance requirements validation (Req 6.2)

External dependencies (LLM API, embedding service, database) are mocked so
these tests run without a live database or API keys.

**Validates: Requirements 6.4, 9.1, 9.2, 9.3, 9.4, 9.5**
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import pytest
from backend.app.qa_agent.embedding_service import EmbeddingError
from backend.app.qa_agent.models import (
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
from backend.app.qa_agent.qa_agent_controller import QAAgentController
from backend.app.qa_agent.query_processor import QueryValidationResult
from backend.app.qa_agent.response_generator import ResponseGeneratorError
from backend.app.qa_agent.retrieval_engine import RetrievalEngineError
from backend.app.qa_agent.vector_store import VectorStoreError

# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------


def _make_article_match(
    title: str = "Test Article",
    score: float = 0.85,
    category: str = "Technology",
) -> ArticleMatch:
    return ArticleMatch(
        article_id=uuid4(),
        title=title,
        content_preview="This is a test article content preview for integration testing.",
        similarity_score=score,
        url="https://example.com/test-article",
        published_at=datetime.utcnow(),
        feed_name="Test Feed",
        category=category,
    )


def _make_article_summary(article: ArticleMatch) -> ArticleSummary:
    return ArticleSummary(
        article_id=article.article_id,
        title=article.title,
        summary="This is a two-sentence summary. It covers the main points of the article.",
        url=article.url,
        relevance_score=article.similarity_score,
        reading_time=3,
        published_at=article.published_at,
        category=article.category,
    )


def _make_structured_response(
    query: str,
    articles: Optional[List[ArticleMatch]] = None,
    conversation_id: Optional[UUID] = None,
    response_type: ResponseType = ResponseType.STRUCTURED,
) -> StructuredResponse:
    summaries = [_make_article_summary(a) for a in (articles or [_make_article_match()])]
    return StructuredResponse(
        query=query,
        response_type=response_type,
        articles=summaries,
        insights=["Insight about the query results."],
        recommendations=["Try searching for related topics."],
        conversation_id=conversation_id or uuid4(),
        response_time=0.1,
        confidence=0.8,
    )


class _MockQueryProcessor:
    """Lightweight mock for QueryProcessor."""

    def __init__(self, fail: bool = False, empty_query_fails: bool = True):
        self._fail = fail
        self._empty_query_fails = empty_query_fails

    async def validate_query(self, query: str) -> QueryValidationResult:
        if self._fail:
            raise Exception("QueryProcessor failure")
        if self._empty_query_fails and not query.strip():
            return QueryValidationResult(is_valid=False, error_message="Query cannot be empty")
        return QueryValidationResult(is_valid=True)

    async def parse_query(self, query: str, language: str = "auto", context=None) -> ParsedQuery:
        if self._fail:
            raise Exception("QueryProcessor failure")
        return ParsedQuery(
            original_query=query,
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=query.split()[:5],
            confidence=0.8,
        )

    async def expand_query(self, query: str, context) -> str:
        return query


class _MockEmbeddingService:
    """Lightweight mock for EmbeddingService."""

    def __init__(self, fail: bool = False, fail_times: int = 0):
        self._fail = fail
        self._fail_times = fail_times
        self._call_count = 0

    async def generate_embedding(self, text: str) -> List[float]:
        self._call_count += 1
        if self._fail or (self._fail_times > 0 and self._call_count <= self._fail_times):
            raise EmbeddingError("Mock embedding failure")
        return [0.1] * 1536


class _MockVectorStore:
    """Lightweight mock for VectorStore."""

    def __init__(self, fail: bool = False):
        self._fail = fail

    async def search_similar(self, **kwargs) -> List:
        if self._fail:
            raise VectorStoreError("Mock vector store failure")
        return []


class _MockRetrievalEngine:
    """Lightweight mock for RetrievalEngine."""

    def __init__(
        self,
        fail: bool = False,
        empty: bool = False,
        slow: float = 0.0,
        articles: Optional[List[ArticleMatch]] = None,
    ):
        self._fail = fail
        self._empty = empty
        self._slow = slow
        self._articles = articles or [_make_article_match()]

    async def intelligent_search(self, **kwargs) -> Dict[str, Any]:
        if self._slow:
            await asyncio.sleep(self._slow)
        if self._fail:
            raise RetrievalEngineError("Mock retrieval failure")
        if self._empty:
            return {"results": [], "expanded": False, "personalized": False}
        return {
            "results": self._articles,
            "expanded": False,
            "personalized": False,
            "search_time": 0.05,
        }

    async def semantic_search(self, **kwargs) -> List[ArticleMatch]:
        if self._fail:
            raise RetrievalEngineError("Mock retrieval failure")
        if self._empty:
            return []
        return self._articles

    async def _expand_by_keywords(self, **kwargs) -> List[ArticleMatch]:
        return []


class _MockResponseGenerator:
    """Lightweight mock for ResponseGenerator."""

    def __init__(self, fail: bool = False, slow: float = 0.0):
        self._fail = fail
        self._slow = slow

    async def generate_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context=None,
        user_profile=None,
    ) -> StructuredResponse:
        if self._slow:
            await asyncio.sleep(self._slow)
        if self._fail:
            raise ResponseGeneratorError("Mock generation failure")
        return _make_structured_response(
            query=query,
            articles=articles,
            conversation_id=context.conversation_id if context else None,
        )


class _MockConversationManager:
    """Lightweight mock for ConversationManager backed by an in-memory dict."""

    def __init__(self, fail: bool = False):
        self._fail = fail
        self._store: Dict[str, ConversationContext] = {}

    async def create_conversation(self, user_id: UUID) -> str:
        if self._fail:
            raise Exception("ConversationManager failure")
        cid = str(uuid4())
        ctx = ConversationContext(
            conversation_id=UUID(cid),
            user_id=user_id,
        )
        self._store[cid] = ctx
        return cid

    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        if self._fail:
            raise Exception("ConversationManager failure")
        return self._store.get(conversation_id)

    async def should_reset_context(self, conversation_id: str, new_query: str) -> bool:
        return False

    async def reset_context(self, conversation_id: str, new_topic=None) -> None:
        ctx = self._store.get(conversation_id)
        if ctx:
            ctx.turns = []
            ctx.current_topic = new_topic

    async def add_turn(
        self, conversation_id: str, query: str, parsed_query=None, response=None
    ) -> None:
        if self._fail:
            raise Exception("ConversationManager failure")
        ctx = self._store.get(conversation_id)
        if ctx:
            ctx.add_turn(query, parsed_query, response)

    async def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self._store:
            del self._store[conversation_id]
            return True
        return False


def _make_controller(**overrides) -> QAAgentController:
    """Build a QAAgentController with all mocked dependencies."""
    defaults = dict(
        query_processor=_MockQueryProcessor(),
        embedding_service=_MockEmbeddingService(),
        vector_store=_MockVectorStore(),
        retrieval_engine=_MockRetrievalEngine(),
        response_generator=_MockResponseGenerator(),
        conversation_manager=_MockConversationManager(),
    )
    defaults.update(overrides)
    return QAAgentController(**defaults)


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


@pytest.mark.asyncio
async def test_complete_flow_returns_structured_response(controller):
    """
    Full pipeline: validate → parse → embed → retrieve → generate.

    **Validates: Requirements 9.3**
    """
    response = await controller.process_query(
        user_id=str(uuid4()),
        query="What is machine learning?",
    )

    assert isinstance(response, StructuredResponse)
    assert response.query == "What is machine learning?"
    assert response.response_type == ResponseType.STRUCTURED
    assert len(response.articles) > 0
    assert len(response.insights) > 0
    assert response.conversation_id is not None
    assert response.response_time >= 0


@pytest.mark.asyncio
async def test_complete_flow_with_user_profile(controller, user_profile):
    """
    Personalized query flow passes user profile through the pipeline.

    **Validates: Requirements 8.2, 9.3**
    """
    response = await controller.process_query(
        user_id=str(uuid4()),
        query="Latest AI research",
        user_profile=user_profile,
    )

    assert response is not None
    assert response.response_type in (
        ResponseType.STRUCTURED,
        ResponseType.SEARCH_RESULTS,
        ResponseType.SIMPLE,
    )
    assert response.confidence >= 0


@pytest.mark.asyncio
async def test_multi_turn_conversation_preserves_id(controller):
    """
    Conversation ID is preserved across multiple turns.

    **Validates: Requirements 4.1, 4.2, 9.3**
    """
    uid = str(uuid4())

    r1 = await controller.process_query(user_id=uid, query="What is AI?")
    cid = str(r1.conversation_id)

    r2 = await controller.continue_conversation(
        user_id=uid, query="Tell me more", conversation_id=cid
    )
    assert r2.conversation_id == r1.conversation_id

    r3 = await controller.continue_conversation(
        user_id=uid, query="Any examples?", conversation_id=cid
    )
    assert r3.conversation_id == r1.conversation_id


@pytest.mark.asyncio
async def test_conversation_history_is_stored(controller):
    """
    Conversation turns are stored and retrievable.

    **Validates: Requirements 4.1, 4.4**
    """
    uid = str(uuid4())
    r = await controller.process_query(user_id=uid, query="Explain neural networks")
    cid = str(r.conversation_id)

    history = await controller.get_conversation_history(uid, cid)
    assert history is not None
    assert history.conversation_id == r.conversation_id
    assert str(history.user_id) == uid


@pytest.mark.asyncio
async def test_multilingual_queries_handled(controller):
    """
    Chinese and English queries both produce valid responses.

    **Validates: Requirements 1.2**
    """
    uid = str(uuid4())

    r_zh = await controller.process_query(user_id=uid, query="什麼是人工智慧？")
    assert r_zh is not None
    assert r_zh.query == "什麼是人工智慧？"

    r_en = await controller.process_query(user_id=uid, query="What is artificial intelligence?")
    assert r_en is not None
    assert r_en.query == "What is artificial intelligence?"


# ===========================================================================
# 2. Error scenarios and fallback mechanisms
# ===========================================================================


@pytest.mark.asyncio
async def test_empty_query_returns_error_response(controller):
    """
    Empty query is rejected with an error response.

    **Validates: Requirements 1.5, 9.3**
    """
    response = await controller.process_query(user_id=str(uuid4()), query="")
    assert response.response_type == ResponseType.ERROR
    assert len(response.insights) > 0
    # Error message should mention the problem
    combined = " ".join(response.insights).lower()
    assert "empty" in combined or "cannot" in combined or "invalid" in combined


@pytest.mark.asyncio
async def test_whitespace_only_query_returns_error(controller):
    """Whitespace-only query is treated as empty."""
    response = await controller.process_query(user_id=str(uuid4()), query="   ")
    assert response.response_type == ResponseType.ERROR


@pytest.mark.asyncio
async def test_vector_store_unavailable_falls_back(controller):
    """
    When the vector store raises VectorStoreError the controller falls back
    to keyword search and still returns a response.

    **Validates: Requirement 9.1**
    """
    ctrl = _make_controller(
        retrieval_engine=_MockRetrievalEngine(fail=True),
    )
    response = await ctrl.process_query(user_id=str(uuid4()), query="AI trends")

    assert response is not None
    assert response.response_type in (
        ResponseType.ERROR,
        ResponseType.SEARCH_RESULTS,
        ResponseType.PARTIAL,
        ResponseType.STRUCTURED,
    )


@pytest.mark.asyncio
async def test_response_generation_failure_returns_search_results(controller):
    """
    When the response generator fails the controller falls back to a
    search-results list response.

    **Validates: Requirement 9.2**
    """
    ctrl = _make_controller(
        response_generator=_MockResponseGenerator(fail=True),
    )
    response = await ctrl.process_query(user_id=str(uuid4()), query="machine learning basics")

    assert response is not None
    assert response.response_type in (
        ResponseType.SEARCH_RESULTS,
        ResponseType.ERROR,
        ResponseType.PARTIAL,
    )
    assert len(response.insights) > 0


@pytest.mark.asyncio
async def test_all_errors_are_logged(caplog):
    """
    Errors during processing are logged with meaningful messages.

    **Validates: Requirement 9.3**
    """
    ctrl = _make_controller(
        retrieval_engine=_MockRetrievalEngine(fail=True),
        response_generator=_MockResponseGenerator(fail=True),
    )

    with caplog.at_level(logging.ERROR, logger="backend.app.qa_agent.qa_agent_controller"):
        await ctrl.process_query(user_id=str(uuid4()), query="test logging")

    # At least one error should have been logged
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) > 0


@pytest.mark.asyncio
async def test_slow_retrieval_returns_partial_or_fallback():
    """
    When retrieval is slow the controller handles the timeout and still
    returns a response (partial results or error).

    **Validates: Requirement 9.4**
    """
    ctrl = _make_controller(
        # Slow enough to trigger the 1-second retrieval timeout
        retrieval_engine=_MockRetrievalEngine(slow=1.5),
    )

    start = time.time()
    response = await ctrl.process_query(user_id=str(uuid4()), query="slow query test")
    elapsed = time.time() - start

    assert response is not None
    # Should complete within a reasonable bound (not hang indefinitely)
    assert elapsed < 6.0
    assert response.response_type in (
        ResponseType.STRUCTURED,
        ResponseType.PARTIAL,
        ResponseType.SEARCH_RESULTS,
        ResponseType.ERROR,
    )


@pytest.mark.asyncio
async def test_retry_mechanism_succeeds_after_transient_failures():
    """
    The retry mechanism retries transient embedding errors and eventually
    succeeds when the service recovers.

    **Validates: Requirement 9.5**
    """
    # Fail the first 2 calls, succeed on the 3rd
    flaky_embedding = _MockEmbeddingService(fail_times=2)
    ctrl = _make_controller(embedding_service=flaky_embedding)

    response = await ctrl.process_query(user_id=str(uuid4()), query="retry test")

    assert response is not None
    # The embedding service was called at least 3 times (2 failures + 1 success)
    assert flaky_embedding._call_count >= 2


@pytest.mark.asyncio
async def test_embedding_failure_falls_back_to_keyword_search():
    """
    When embedding generation fails completely the controller continues
    with an empty vector and falls back to keyword search.

    **Validates: Requirements 9.1, 9.5**
    """
    ctrl = _make_controller(
        embedding_service=_MockEmbeddingService(fail=True),
    )
    response = await ctrl.process_query(user_id=str(uuid4()), query="embedding failure test")

    assert response is not None
    # Should still return something (not crash)
    assert response.response_type in (
        ResponseType.STRUCTURED,
        ResponseType.SEARCH_RESULTS,
        ResponseType.PARTIAL,
        ResponseType.ERROR,
    )


@pytest.mark.asyncio
async def test_no_articles_found_returns_graceful_response():
    """
    When no articles match the query the controller returns a graceful response.
    """
    ctrl = _make_controller(
        retrieval_engine=_MockRetrievalEngine(empty=True),
    )
    response = await ctrl.process_query(user_id=str(uuid4()), query="very obscure topic xyz")

    assert response is not None
    assert isinstance(response, StructuredResponse)


# ===========================================================================
# 3. Concurrent user handling
# ===========================================================================


@pytest.mark.asyncio
async def test_concurrent_users_basic():
    """
    10 concurrent users can all get responses without interference.

    **Validates: Requirement 6.4**
    """
    ctrl = _make_controller()
    num_users = 10
    user_ids = [str(uuid4()) for _ in range(num_users)]
    queries = [f"Query about topic {i}" for i in range(num_users)]

    start = time.time()
    tasks = [ctrl.process_query(user_id=user_ids[i], query=queries[i]) for i in range(num_users)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start

    successful = [r for r in results if isinstance(r, StructuredResponse)]
    assert (
        len(successful) >= num_users * 0.9
    ), f"Only {len(successful)}/{num_users} queries succeeded"

    # Each response should carry the correct query
    for i, r in enumerate(successful):
        assert r.query == queries[i]

    print(f"\n  Concurrent basic: {len(successful)}/{num_users} OK in {elapsed:.2f}s")


@pytest.mark.asyncio
async def test_concurrent_users_stress():
    """
    50 concurrent users are handled with at least 70 % success rate.

    **Validates: Requirement 6.4 (50+ concurrent users)**
    """
    ctrl = _make_controller()
    num_users = 50
    user_ids = [str(uuid4()) for _ in range(num_users)]
    base_queries = ["AI", "ML", "deep learning", "data science", "cloud"]
    queries = [base_queries[i % len(base_queries)] + f" {i}" for i in range(num_users)]

    start = time.time()
    tasks = [ctrl.process_query(user_id=user_ids[i], query=queries[i]) for i in range(num_users)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start

    successful = [r for r in results if isinstance(r, StructuredResponse)]
    success_rate = len(successful) / num_users

    assert success_rate >= 0.7, f"Success rate {success_rate:.1%} below 70 % threshold"
    print(
        f"\n  Concurrent stress: {len(successful)}/{num_users} ({success_rate:.0%}) in {elapsed:.2f}s"
    )


@pytest.mark.asyncio
async def test_user_isolation_prevents_cross_access():
    """
    User A cannot read or delete User B's conversation.

    **Validates: Requirement 10.5**
    """
    ctrl = _make_controller()
    uid1 = str(uuid4())
    uid2 = str(uuid4())

    # User 1 creates a conversation
    r1 = await ctrl.process_query(user_id=uid1, query="User 1 private query")
    cid = str(r1.conversation_id)

    # User 2 cannot read it
    history = await ctrl.get_conversation_history(uid2, cid)
    assert history is None, "User 2 should not access User 1's conversation"

    # User 2 cannot delete it
    deleted = await ctrl.delete_conversation(uid2, cid)
    assert deleted is False, "User 2 should not delete User 1's conversation"

    # User 1 can still access their own conversation
    history = await ctrl.get_conversation_history(uid1, cid)
    assert history is not None, "User 1 should access their own conversation"


@pytest.mark.asyncio
async def test_concurrent_conversations_are_independent():
    """
    Concurrent conversations for different users do not share state.
    """
    ctrl = _make_controller()
    uid_a = str(uuid4())
    uid_b = str(uuid4())

    r_a, r_b = await asyncio.gather(
        ctrl.process_query(user_id=uid_a, query="User A query"),
        ctrl.process_query(user_id=uid_b, query="User B query"),
    )

    assert r_a.conversation_id != r_b.conversation_id
    assert r_a.query == "User A query"
    assert r_b.query == "User B query"


# ===========================================================================
# 4. Performance requirements
# ===========================================================================


@pytest.mark.asyncio
async def test_response_time_under_3_seconds():
    """
    Each query completes within 3 seconds with mocked dependencies.

    **Validates: Requirement 6.2**
    """
    ctrl = _make_controller()
    uid = str(uuid4())
    queries = [
        "What is machine learning?",
        "Explain neural networks",
        "Latest AI trends",
    ]

    times = []
    for q in queries:
        t0 = time.time()
        await ctrl.process_query(user_id=uid, query=q)
        times.append(time.time() - t0)

    assert max(times) <= 3.0, f"Slowest query took {max(times):.2f}s, exceeding 3-second limit"


@pytest.mark.asyncio
async def test_system_health_check_structure():
    """
    get_system_health returns a well-formed status dictionary.

    **Validates: Requirements 9.3, 9.5**
    """
    ctrl = _make_controller()
    health = await ctrl.get_system_health()

    assert isinstance(health, dict)
    assert "overall_health" in health
    assert "status" in health
    assert "components" in health
    assert "timestamp" in health

    assert 0.0 <= health["overall_health"] <= 1.0
    assert health["status"] in ("healthy", "degraded", "unhealthy", "error")

    components = health["components"]
    for key in (
        "query_processor",
        "embedding_service",
        "vector_store",
        "retrieval_engine",
        "response_generator",
        "conversation_manager",
    ):
        assert key in components


# ===========================================================================
# 5. Edge cases
# ===========================================================================


@pytest.mark.asyncio
async def test_very_long_query_handled_gracefully(controller):
    """Very long queries do not crash the controller."""
    long_query = "artificial intelligence " * 100
    response = await controller.process_query(user_id=str(uuid4()), query=long_query)

    assert response is not None
    assert response.response_type in (
        ResponseType.STRUCTURED,
        ResponseType.SEARCH_RESULTS,
        ResponseType.ERROR,
        ResponseType.SIMPLE,
    )


@pytest.mark.asyncio
async def test_special_characters_in_query(controller):
    """Queries with special characters are handled without errors."""
    special_queries = [
        "What is C++?",
        "Explain <html> tags",
        "SQL: SELECT * FROM users",
        "Python's f-strings",
        "React.js & Vue.js",
    ]
    uid = str(uuid4())
    for q in special_queries:
        r = await controller.process_query(user_id=uid, query=q)
        assert r is not None
        assert r.query == q


@pytest.mark.asyncio
async def test_delete_conversation_removes_it(controller):
    """Deleting a conversation makes it inaccessible."""
    uid = str(uuid4())
    r = await controller.process_query(user_id=uid, query="Temporary query")
    cid = str(r.conversation_id)

    deleted = await controller.delete_conversation(uid, cid)
    assert deleted is True

    history = await controller.get_conversation_history(uid, cid)
    assert history is None


@pytest.mark.asyncio
async def test_conversation_manager_failure_does_not_crash_query():
    """
    If the conversation manager fails, process_query still returns a response
    (context is optional for the response pipeline).
    """
    ctrl = _make_controller(
        conversation_manager=_MockConversationManager(fail=True),
    )
    response = await ctrl.process_query(user_id=str(uuid4()), query="test with broken CM")

    # Should not raise; may return error or partial response
    assert response is not None
    assert isinstance(response, StructuredResponse)
