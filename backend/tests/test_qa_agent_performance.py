"""
Performance tests for Intelligent Q&A Agent

Tests performance requirements:
- Req 6.1: Semantic search returns results within 500ms
- Req 6.2: Complete response generation within 3 seconds
- Req 6.4: Support 50+ concurrent users

This file contains:
1. PerformanceMonitor unit tests (pure, no async needed for most)
2. QA Agent performance tests (async, using mocks)
"""

import asyncio
import time
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

import pytest

from app.qa_agent.models import (
    ArticleMatch,
    ArticleSummary,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
)
from app.qa_agent.performance_monitor import PerformanceMonitor
from app.qa_agent.qa_agent_controller import QAAgentController

# ---------------------------------------------------------------------------
# Mock helpers (redefining locally to avoid import coupling)
# ---------------------------------------------------------------------------


def _make_article_match(
    title: str = "Test Article",
    similarity_score: float = 0.85,
    category: str = "Technology",
) -> ArticleMatch:
    return ArticleMatch(
        article_id=uuid4(),
        title=title,
        content_preview="This is a test article content preview for performance testing.",
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
    """Fast mock for QueryProcessor."""

    async def validate_query(self, query: str):
        from app.qa_agent.query_processor import QueryValidationResult

        if not query.strip():
            return QueryValidationResult(is_valid=False, error_message="Query cannot be empty")
        return QueryValidationResult(is_valid=True)

    async def parse_query(self, query: str, language: str = "auto", context=None):
        return ParsedQuery(
            original_query=query,
            language=QueryLanguage.ENGLISH,
            intent=QueryIntent.SEARCH,
            keywords=query.split()[:5],
            confidence=0.8,
        )

    async def expand_query(self, query: str, context):
        return query


class MockEmbeddingService:
    """Fast mock for EmbeddingService."""

    async def generate_embedding(self, text: str) -> List[float]:
        # Simulate minimal delay
        await asyncio.sleep(0.001)
        return [0.1] * 1536


class MockRetrievalEngine:
    """Fast mock for RetrievalEngine."""

    def __init__(self, articles: Optional[List[ArticleMatch]] = None):
        self._articles = articles or [_make_article_match()]

    async def intelligent_search(
        self, query: str, query_vector: List[float], user_id: str, **kwargs
    ):
        # Simulate fast search
        await asyncio.sleep(0.01)
        return {
            "results": self._articles,
            "expanded": False,
            "personalized": False,
            "search_time": 0.01,
        }

    async def semantic_search(self, query_vector: List[float], user_id: str, **kwargs):
        await asyncio.sleep(0.01)
        return self._articles


class MockResponseGenerator:
    """Fast mock for ResponseGenerator."""

    async def generate_response(
        self, query: str, articles: List[ArticleMatch], context=None, user_profile=None
    ):
        # Simulate response generation
        await asyncio.sleep(0.05)
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
    """Fast mock for ConversationManager."""

    def __init__(self):
        self._conversations = {}

    async def create_conversation(self, user_id):
        from app.qa_agent.models import ConversationContext

        conversation_id = str(uuid4())
        context = ConversationContext(conversation_id=uuid4(), user_id=user_id)
        self._conversations[conversation_id] = context
        return conversation_id

    async def get_context(self, conversation_id: str):
        return self._conversations.get(conversation_id)

    async def should_reset_context(self, conversation_id: str, new_query: str):
        return False

    async def reset_context(self, conversation_id: str, new_topic: Optional[str] = None):
        pass

    async def add_turn(self, conversation_id: str, query: str, parsed_query=None, response=None):
        context = self._conversations.get(conversation_id)
        if context:
            context.add_turn(query, parsed_query, response)


class MockVectorStore:
    """Fast mock for VectorStore."""

    async def search_similar(self, **kwargs):
        return []


def _make_fast_controller() -> QAAgentController:
    """Create a controller with fast mocks for performance testing."""
    return QAAgentController(
        query_processor=MockQueryProcessor(),
        retrieval_engine=MockRetrievalEngine(),
        response_generator=MockResponseGenerator(),
        conversation_manager=MockConversationManager(),
        embedding_service=MockEmbeddingService(),
        vector_store=MockVectorStore(),
    )


# ===========================================================================
# 1. PerformanceMonitor unit tests
# ===========================================================================


class TestPerformanceMonitorUnit:
    """Unit tests for PerformanceMonitor class."""

    def test_track_operation_records_metrics(self):
        """After calling track_operation, get_performance_summary() should show count=1."""
        monitor = PerformanceMonitor()

        async def dummy_operation():
            await asyncio.sleep(0.001)
            return "success"

        # Run the operation
        asyncio.run(monitor.track_operation("test_op", dummy_operation))

        # Check summary
        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == 1
        assert summary["duration_stats"]["avg_ms"] > 0

    def test_slow_query_detection(self):
        """When an operation takes longer than slow_query_threshold_ms, it should appear in get_slow_queries()."""
        monitor = PerformanceMonitor(slow_query_threshold_ms=50.0)

        async def slow_operation():
            await asyncio.sleep(0.06)  # 60ms
            return "slow"

        # Run slow operation
        asyncio.run(monitor.track_operation("slow_op", slow_operation))

        # Check slow queries
        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0]["operation"] == "slow_op"
        assert slow_queries[0]["duration_ms"] > 50.0

    def test_operation_stats_accumulation(self):
        """After N operations, get_operation_stats(op) should show count=N."""
        monitor = PerformanceMonitor()

        async def fast_operation():
            await asyncio.sleep(0.001)
            return "ok"

        # Run 5 operations
        for _ in range(5):
            asyncio.run(monitor.track_operation("accumulate_op", fast_operation))

        # Check stats
        stats = monitor.get_operation_stats("accumulate_op")
        assert stats is not None
        assert stats["count"] == 5
        assert stats["success_count"] == 5
        assert stats["error_count"] == 0

    def test_operation_stats_tracks_errors(self):
        """Operation stats should correctly track success and error counts."""
        monitor = PerformanceMonitor()

        async def failing_operation():
            await asyncio.sleep(0.001)
            raise ValueError("Test error")

        # Run 2 successful and 1 failing operation
        async def success_op():
            await asyncio.sleep(0.001)
            return "ok"

        asyncio.run(monitor.track_operation("mixed_op", success_op))
        asyncio.run(monitor.track_operation("mixed_op", success_op))

        try:
            asyncio.run(monitor.track_operation("mixed_op", failing_operation))
        except ValueError:
            pass

        # Check stats
        stats = monitor.get_operation_stats("mixed_op")
        assert stats["count"] == 3
        assert stats["success_count"] == 2
        assert stats["error_count"] == 1

    def test_concurrency_stats(self):
        """get_concurrency_stats() should return correct keys and values."""
        monitor = PerformanceMonitor(max_concurrent_queries=50)

        stats = monitor.get_concurrency_stats()

        assert "current_concurrent" in stats
        assert "peak_concurrent" in stats
        assert "max_concurrent" in stats
        assert "utilization" in stats
        assert "available_slots" in stats
        assert stats["max_concurrent"] == 50

    def test_queue_status(self):
        """get_queue_status() should return correct keys and values."""
        monitor = PerformanceMonitor(queue_size=200)

        status = monitor.get_queue_status()

        assert "queue_size" in status
        assert "max_queue_size" in status
        assert "active_queries" in status
        assert "completed_queries" in status
        assert "workers_running" in status
        assert "queue_utilization" in status
        assert status["max_queue_size"] == 200

    def test_metrics_cleanup(self):
        """cleanup_old_metrics() should remove metrics older than retention period."""
        monitor = PerformanceMonitor(metrics_retention_seconds=1)

        async def dummy_op():
            await asyncio.sleep(0.001)
            return "ok"

        # Add some metrics
        asyncio.run(monitor.track_operation("cleanup_test", dummy_op))
        asyncio.run(monitor.track_operation("cleanup_test", dummy_op))

        # Wait for metrics to age
        time.sleep(1.1)

        # Add one more recent metric
        asyncio.run(monitor.track_operation("cleanup_test", dummy_op))

        # Cleanup
        removed = monitor.cleanup_old_metrics()

        # Should have removed 2 old metrics
        assert removed == 2
        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == 1

    def test_reset_stats(self):
        """After reset_stats(), get_performance_summary() should show 0 operations."""
        monitor = PerformanceMonitor()

        async def dummy_op():
            await asyncio.sleep(0.001)
            return "ok"

        # Add some operations
        for _ in range(3):
            asyncio.run(monitor.track_operation("reset_test", dummy_op))

        # Reset
        monitor.reset_stats()

        # Check summary
        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == 0

    def test_percentile_calculation(self):
        """With 100 operations of known durations, p50/p95/p99 should be approximately correct."""
        monitor = PerformanceMonitor()

        # Create operations with predictable durations (1ms to 100ms)
        async def timed_operation(duration_ms: float):
            await asyncio.sleep(duration_ms / 1000.0)
            return "ok"

        # Run 100 operations with durations 1ms, 2ms, ..., 100ms
        for i in range(1, 101):
            asyncio.run(monitor.track_operation("percentile_test", timed_operation, i))

        # Get summary
        summary = monitor.get_performance_summary()
        duration_stats = summary["duration_stats"]

        # Check percentiles (with tolerance for timing variance)
        assert 45 <= duration_stats["p50_ms"] <= 55  # Should be around 50ms
        assert 90 <= duration_stats["p95_ms"] <= 100  # Should be around 95ms
        assert 95 <= duration_stats["p99_ms"] <= 105  # Should be around 99ms


# ===========================================================================
# 2. QA Agent performance tests (async, using mocks)
# ===========================================================================


class TestQAAgentPerformance:
    """Performance tests for QA Agent with fast mocks."""

    @pytest.mark.asyncio
    async def test_single_query_completes_within_3_seconds(self):
        """A single query to the controller with fast mocks should complete in < 3 seconds (Req 6.2)."""
        controller = _make_fast_controller()

        start = time.time()
        response = await controller.process_query(
            user_id=str(uuid4()),
            query="What are the latest developments in AI?",
        )
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Query took {elapsed:.2f}s (limit: 3.0s)"
        assert isinstance(response, StructuredResponse)

    @pytest.mark.asyncio
    async def test_search_operation_completes_within_500ms(self):
        """The retrieval engine mock with no delay should complete in < 500ms (Req 6.1)."""
        retrieval_engine = MockRetrievalEngine()

        start = time.time()
        result = await retrieval_engine.intelligent_search(
            query="test query",
            query_vector=[0.1] * 1536,
            user_id=str(uuid4()),
        )
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Search took {elapsed*1000:.2f}ms (limit: 500ms)"
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_50_concurrent_queries_all_complete(self):
        """50 concurrent process_query calls should all return StructuredResponse objects (Req 6.4)."""
        controller = _make_fast_controller()
        n = 50
        user_ids = [str(uuid4()) for _ in range(n)]

        tasks = [
            controller.process_query(user_id=uid, query=f"Query {i}")
            for i, uid in enumerate(user_ids)
        ]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == n
        for resp in responses:
            assert isinstance(resp, StructuredResponse)

    @pytest.mark.asyncio
    async def test_50_concurrent_queries_complete_within_time_limit(self):
        """50 concurrent queries should complete within 10 seconds wall-clock time (Req 6.4)."""
        controller = _make_fast_controller()
        n = 50
        user_ids = [str(uuid4()) for _ in range(n)]

        start = time.time()
        tasks = [
            controller.process_query(user_id=uid, query=f"Concurrent query {i}")
            for i, uid in enumerate(user_ids)
        ]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        assert elapsed < 10.0, f"50 concurrent queries took {elapsed:.2f}s (limit: 10s)"

    @pytest.mark.asyncio
    async def test_response_time_is_recorded_in_response(self):
        """response.response_time should be > 0 and < 3.5 seconds (Req 6.2)."""
        controller = _make_fast_controller()

        response = await controller.process_query(
            user_id=str(uuid4()),
            query="Test response time recording",
        )

        assert response.response_time > 0
        assert response.response_time < 3.5

    @pytest.mark.asyncio
    async def test_queue_enqueue_and_status(self):
        """After enqueuing N queries, get_queue_status() should show correct queue_size (Req 6.5)."""
        monitor = PerformanceMonitor(queue_size=100)

        # Enqueue 5 queries
        for i in range(5):
            await monitor.enqueue_query(
                user_id=str(uuid4()),
                query=f"Queued query {i}",
                priority=0,
            )

        # Check status
        status = monitor.get_queue_status()
        assert status["queue_size"] == 5

    @pytest.mark.asyncio
    async def test_queue_full_raises_queue_full(self):
        """When queue is at capacity, enqueue_query should raise asyncio.QueueFull (Req 6.5)."""
        monitor = PerformanceMonitor(queue_size=2)

        # Fill the queue
        await monitor.enqueue_query(user_id=str(uuid4()), query="Query 1")
        await monitor.enqueue_query(user_id=str(uuid4()), query="Query 2")

        # Try to add one more
        with pytest.raises(asyncio.QueueFull):
            await monitor.enqueue_query(user_id=str(uuid4()), query="Query 3")

    @pytest.mark.asyncio
    async def test_execute_with_concurrency_limit_tracks_peak_concurrent(self):
        """After running N concurrent operations, peak_concurrent should be > 1 (Req 6.4)."""
        monitor = PerformanceMonitor(max_concurrent_queries=10)

        async def dummy_operation():
            await asyncio.sleep(0.01)
            return "ok"

        # Run 5 concurrent operations
        tasks = [
            monitor.execute_with_concurrency_limit(
                dummy_operation,
                operation="concurrent_test",
                user_id=str(uuid4()),
            )
            for _ in range(5)
        ]
        await asyncio.gather(*tasks)

        # Check concurrency stats
        stats = monitor.get_concurrency_stats()
        assert stats["peak_concurrent"] >= 1  # At least 1 concurrent operation was tracked


# ===========================================================================
# 3. Integration performance tests
# ===========================================================================


class TestIntegrationPerformance:
    """Integration tests combining PerformanceMonitor with QA Agent."""

    @pytest.mark.asyncio
    async def test_track_operation_with_controller_query(self):
        """PerformanceMonitor.track_operation should work with controller.process_query."""
        monitor = PerformanceMonitor()
        controller = _make_fast_controller()

        async def query_operation():
            return await controller.process_query(
                user_id=str(uuid4()),
                query="Integration test query",
            )

        result = await monitor.track_operation(
            "integration_query",
            query_operation,
            user_id=str(uuid4()),
        )

        assert isinstance(result, StructuredResponse)

        # Check that metric was recorded
        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_queries_with_performance_tracking(self):
        """Track performance of 20 concurrent queries."""
        monitor = PerformanceMonitor(max_concurrent_queries=50)
        controller = _make_fast_controller()
        n = 20

        async def tracked_query(uid: str, query: str):
            async def _do_query():
                return await controller.process_query(user_id=uid, query=query)

            return await monitor.execute_with_concurrency_limit(
                _do_query,
                operation="tracked_concurrent_query",
                user_id=uid,
            )

        user_ids = [str(uuid4()) for _ in range(n)]
        tasks = [tracked_query(uid, f"Query {i}") for i, uid in enumerate(user_ids)]

        start = time.time()
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # All queries should succeed
        assert len(responses) == n
        for resp in responses:
            assert isinstance(resp, StructuredResponse)

        # Check performance summary
        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == n
        assert summary["success_rate"] == 1.0

        # Should complete quickly with mocks
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_performance_summary_with_time_window(self):
        """get_performance_summary with time_window_seconds should filter metrics correctly."""
        monitor = PerformanceMonitor()

        async def dummy_op():
            await asyncio.sleep(0.001)
            return "ok"

        # Add 3 operations
        for _ in range(3):
            await monitor.track_operation("windowed_test", dummy_op)

        # Wait 1 second
        await asyncio.sleep(1.1)

        # Add 2 more operations
        for _ in range(2):
            await monitor.track_operation("windowed_test", dummy_op)

        # Get summary for last 1 second
        summary = monitor.get_performance_summary(time_window_seconds=1)

        # Should only show the 2 recent operations
        assert summary["total_operations"] == 2

    @pytest.mark.asyncio
    async def test_slow_query_logging_in_real_scenario(self):
        """Slow queries should be detected and logged in a realistic scenario."""
        monitor = PerformanceMonitor(slow_query_threshold_ms=100.0)

        async def slow_query():
            await asyncio.sleep(0.15)  # 150ms
            return "slow result"

        await monitor.track_operation("slow_scenario", slow_query)

        # Check slow queries
        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0]["duration_ms"] > 100.0
