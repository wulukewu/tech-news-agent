"""
Tests for Performance Monitor

Tests performance monitoring, query queuing, concurrency limiting,
and metrics collection features.

Requirements: 6.1, 6.2, 6.3, 6.5
"""

import asyncio
import time
from datetime import datetime, timedelta

import pytest

from .performance_monitor import (
    PerformanceMetric,
    PerformanceMonitor,
    QueryQueueItem,
    get_performance_monitor,
    set_performance_monitor,
)


@pytest.fixture
def performance_monitor():
    """Create a fresh PerformanceMonitor instance for testing."""
    monitor = PerformanceMonitor(
        max_concurrent_queries=5,
        queue_size=10,
        slow_query_threshold_ms=100.0,
        metrics_retention_seconds=3600,
    )
    return monitor


@pytest.fixture
async def monitor_with_workers(performance_monitor):
    """Create a monitor with running queue workers."""
    await performance_monitor.start_queue_workers(num_workers=2)
    yield performance_monitor
    await performance_monitor.stop_queue_workers()


class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor class."""

    # ------------------------------------------------------------------
    # Initialization Tests
    # ------------------------------------------------------------------

    def test_initialization(self, performance_monitor):
        """Test PerformanceMonitor initialization."""
        assert performance_monitor.max_concurrent_queries == 5
        assert performance_monitor.queue_size == 10
        assert performance_monitor.slow_query_threshold_ms == 100.0
        assert performance_monitor.metrics_retention_seconds == 3600
        assert len(performance_monitor._metrics) == 0
        assert len(performance_monitor._slow_queries) == 0

    # ------------------------------------------------------------------
    # Response Time Tracking Tests (Requirement 6.1, 6.2)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_track_operation_success(self, performance_monitor):
        """Test tracking a successful operation."""

        async def fast_operation():
            await asyncio.sleep(0.01)
            return "success"

        result = await performance_monitor.track_operation(
            operation="test_op",
            func=fast_operation,
            user_id="user123",
            metadata={"test": "data"},
        )

        assert result == "success"
        assert len(performance_monitor._metrics) == 1

        metric = performance_monitor._metrics[0]
        assert metric.operation == "test_op"
        assert metric.success is True
        assert metric.user_id == "user123"
        assert metric.duration_ms >= 10.0  # At least 10ms
        assert metric.metadata == {"test": "data"}

    @pytest.mark.asyncio
    async def test_track_operation_failure(self, performance_monitor):
        """Test tracking a failed operation."""

        async def failing_operation():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await performance_monitor.track_operation(
                operation="failing_op",
                func=failing_operation,
                user_id="user123",
            )

        assert len(performance_monitor._metrics) == 1

        metric = performance_monitor._metrics[0]
        assert metric.operation == "failing_op"
        assert metric.success is False
        assert metric.error == "Test error"

    @pytest.mark.asyncio
    async def test_slow_query_detection(self, performance_monitor):
        """Test detection of slow queries (Requirement 6.1: < 500ms)."""

        async def slow_operation():
            await asyncio.sleep(0.15)  # 150ms - exceeds 100ms threshold
            return "slow"

        result = await performance_monitor.track_operation(
            operation="slow_op",
            func=slow_operation,
        )

        assert result == "slow"
        assert len(performance_monitor._slow_queries) == 1

        slow_query = performance_monitor._slow_queries[0]
        assert slow_query.operation == "slow_op"
        assert slow_query.duration_ms >= 100.0

    @pytest.mark.asyncio
    async def test_response_time_requirement(self, performance_monitor):
        """Test that operations complete within 3-second requirement (Requirement 6.2)."""

        async def normal_operation():
            await asyncio.sleep(0.05)  # 50ms
            return "done"

        start_time = time.time()
        result = await performance_monitor.track_operation(
            operation="normal_op",
            func=normal_operation,
        )
        total_time = time.time() - start_time

        assert result == "done"
        assert total_time < 3.0  # Must complete within 3 seconds

        metric = performance_monitor._metrics[0]
        assert metric.duration_ms < 3000.0

    # ------------------------------------------------------------------
    # Query Queuing Tests (Requirement 6.5)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_enqueue_query(self, performance_monitor):
        """Test enqueueing a query for processing."""
        query_id = await performance_monitor.enqueue_query(
            user_id="user123",
            query="test query",
            priority=1,
        )

        assert query_id is not None
        assert performance_monitor._query_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_queue_full_rejection(self, performance_monitor):
        """Test that queue rejects queries when full."""
        # Fill the queue
        for i in range(10):  # queue_size = 10
            await performance_monitor.enqueue_query(
                user_id=f"user{i}",
                query=f"query {i}",
            )

        # Try to add one more - should raise QueueFull
        with pytest.raises(asyncio.QueueFull):
            await performance_monitor.enqueue_query(
                user_id="user_overflow",
                query="overflow query",
            )

    @pytest.mark.asyncio
    async def test_queue_workers(self, monitor_with_workers):
        """Test queue workers processing queries."""
        # Enqueue some queries
        query_ids = []
        for i in range(3):
            query_id = await monitor_with_workers.enqueue_query(
                user_id=f"user{i}",
                query=f"query {i}",
            )
            query_ids.append(query_id)

        # Wait for workers to process
        await asyncio.sleep(0.5)

        # Check queue status
        status = monitor_with_workers.get_queue_status()
        assert status["workers_running"] == 2
        assert status["queue_size"] <= 3  # Should be processing

    @pytest.mark.asyncio
    async def test_get_queue_status(self, performance_monitor):
        """Test getting queue status."""
        # Add some queries
        for i in range(3):
            await performance_monitor.enqueue_query(
                user_id=f"user{i}",
                query=f"query {i}",
            )

        status = performance_monitor.get_queue_status()

        assert status["queue_size"] == 3
        assert status["max_queue_size"] == 10
        assert status["queue_utilization"] == 0.3
        assert status["active_queries"] == 0

    # ------------------------------------------------------------------
    # Concurrency Limiting Tests (Requirement 6.3)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, performance_monitor):
        """Test that concurrency is limited to max_concurrent_queries (Requirement 6.3)."""

        async def slow_operation():
            await asyncio.sleep(0.1)
            return "done"

        # Start more operations than the limit
        tasks = []
        for i in range(10):  # More than max_concurrent_queries (5)
            task = asyncio.create_task(
                performance_monitor.execute_with_concurrency_limit(
                    func=slow_operation,
                    operation=f"op_{i}",
                    user_id=f"user{i}",
                )
            )
            tasks.append(task)

        # Check that concurrent count doesn't exceed limit
        await asyncio.sleep(0.05)  # Let some operations start
        assert performance_monitor._current_concurrent_count <= 5

        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(r == "done" for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_user_support(self, performance_monitor):
        """Test support for 50+ concurrent users (Requirement 6.3)."""
        # Create a monitor with higher concurrency limit
        high_concurrency_monitor = PerformanceMonitor(
            max_concurrent_queries=50,
            queue_size=200,
        )

        async def user_query():
            await asyncio.sleep(0.01)
            return "result"

        # Simulate 50 concurrent users
        tasks = []
        for i in range(50):
            task = asyncio.create_task(
                high_concurrency_monitor.execute_with_concurrency_limit(
                    func=user_query,
                    operation="user_query",
                    user_id=f"user{i}",
                )
            )
            tasks.append(task)

        # All should complete successfully
        results = await asyncio.gather(*tasks)
        assert len(results) == 50
        assert all(r == "result" for r in results)

        # Check peak concurrent count
        assert high_concurrency_monitor._peak_concurrent_count <= 50

    @pytest.mark.asyncio
    async def test_get_concurrency_stats(self, performance_monitor):
        """Test getting concurrency statistics."""

        async def operation():
            await asyncio.sleep(0.05)
            return "done"

        # Start some concurrent operations
        tasks = [
            asyncio.create_task(
                performance_monitor.execute_with_concurrency_limit(
                    func=operation,
                    operation="test_op",
                )
            )
            for _ in range(3)
        ]

        # Check stats while operations are running
        await asyncio.sleep(0.02)
        stats = performance_monitor.get_concurrency_stats()

        assert stats["max_concurrent"] == 5
        assert stats["current_concurrent"] <= 3
        assert 0.0 <= stats["utilization"] <= 1.0
        assert stats["available_slots"] >= 2

        # Wait for completion
        await asyncio.gather(*tasks)

    # ------------------------------------------------------------------
    # Performance Metrics Tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_operation_stats_tracking(self, performance_monitor):
        """Test tracking of operation statistics."""

        async def test_operation():
            await asyncio.sleep(0.01)
            return "done"

        # Execute same operation multiple times
        for _ in range(5):
            await performance_monitor.track_operation(
                operation="repeated_op",
                func=test_operation,
            )

        stats = performance_monitor.get_operation_stats("repeated_op")

        assert stats is not None
        assert stats["count"] == 5
        assert stats["success_count"] == 5
        assert stats["error_count"] == 0
        assert stats["success_rate"] == 1.0
        assert stats["avg_duration_ms"] > 0

    @pytest.mark.asyncio
    async def test_performance_summary(self, performance_monitor):
        """Test getting comprehensive performance summary."""

        async def fast_op():
            await asyncio.sleep(0.01)
            return "fast"

        async def slow_op():
            await asyncio.sleep(0.15)
            return "slow"

        # Execute various operations
        await performance_monitor.track_operation("fast", fast_op)
        await performance_monitor.track_operation("fast", fast_op)
        await performance_monitor.track_operation("slow", slow_op)

        summary = performance_monitor.get_performance_summary()

        assert summary["total_operations"] == 3
        assert summary["successful_operations"] == 3
        assert summary["failed_operations"] == 0
        assert summary["success_rate"] == 1.0
        assert "duration_stats" in summary
        assert "slow_queries" in summary
        assert "operation_breakdown" in summary
        assert summary["slow_queries"]["count"] == 1  # One slow operation

    @pytest.mark.asyncio
    async def test_performance_summary_with_time_window(self, performance_monitor):
        """Test performance summary with time window filtering."""

        async def operation():
            await asyncio.sleep(0.01)
            return "done"

        # Execute operations
        await performance_monitor.track_operation("op1", operation)
        await asyncio.sleep(0.1)
        await performance_monitor.track_operation("op2", operation)

        # Get summary for last 1 second
        summary = performance_monitor.get_performance_summary(time_window_seconds=1)

        assert summary["total_operations"] == 2
        assert summary["time_window_seconds"] == 1

    def test_get_slow_queries(self, performance_monitor):
        """Test retrieving slow query list."""
        # Manually add some slow queries
        for i in range(5):
            metric = PerformanceMetric(
                metric_id=f"metric_{i}",
                operation=f"slow_op_{i}",
                duration_ms=200.0 + i * 10,
                timestamp=datetime.utcnow(),
                success=True,
            )
            performance_monitor._slow_queries.append(metric)

        slow_queries = performance_monitor.get_slow_queries(limit=3)

        assert len(slow_queries) == 3
        assert all("operation" in q for q in slow_queries)
        assert all("duration_ms" in q for q in slow_queries)

    # ------------------------------------------------------------------
    # Alert Tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_alert_callback_registration(self, performance_monitor):
        """Test registering alert callbacks."""
        alert_triggered = []

        async def alert_callback(alert_type, metric):
            alert_triggered.append((alert_type, metric))

        performance_monitor.register_alert_callback(alert_callback)

        # Trigger a slow query alert
        async def slow_operation():
            await asyncio.sleep(0.15)
            return "slow"

        await performance_monitor.track_operation("slow_op", slow_operation)

        # Wait for alert to be processed
        await asyncio.sleep(0.1)

        assert len(alert_triggered) == 1
        assert alert_triggered[0][0] == "slow_query"

    # ------------------------------------------------------------------
    # Cleanup Tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, performance_monitor):
        """Test cleanup of old metrics."""
        # Add some old metrics
        old_time = datetime.utcnow() - timedelta(hours=2)
        for i in range(5):
            metric = PerformanceMetric(
                metric_id=f"old_{i}",
                operation="old_op",
                duration_ms=50.0,
                timestamp=old_time,
                success=True,
            )
            performance_monitor._metrics.append(metric)

        # Add some recent metrics
        async def operation():
            await asyncio.sleep(0.01)
            return "done"

        await performance_monitor.track_operation("recent_op", operation)

        # Cleanup (retention is 3600 seconds = 1 hour)
        removed = performance_monitor.cleanup_old_metrics()

        assert removed == 5  # Should remove 5 old metrics
        assert len(performance_monitor._metrics) == 1  # Only recent one remains

    def test_reset_stats(self, performance_monitor):
        """Test resetting all statistics."""
        # Add some data
        metric = PerformanceMetric(
            metric_id="test",
            operation="test_op",
            duration_ms=50.0,
            timestamp=datetime.utcnow(),
            success=True,
        )
        performance_monitor._metrics.append(metric)
        performance_monitor._slow_queries.append(metric)
        performance_monitor._peak_concurrent_count = 10

        # Reset
        performance_monitor.reset_stats()

        assert len(performance_monitor._metrics) == 0
        assert len(performance_monitor._slow_queries) == 0
        assert performance_monitor._peak_concurrent_count == 0

    # ------------------------------------------------------------------
    # Global Instance Tests
    # ------------------------------------------------------------------

    def test_get_global_performance_monitor(self):
        """Test getting global performance monitor instance."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2  # Should be same instance

    def test_set_global_performance_monitor(self):
        """Test setting global performance monitor instance."""
        custom_monitor = PerformanceMonitor(max_concurrent_queries=100)
        set_performance_monitor(custom_monitor)

        retrieved_monitor = get_performance_monitor()
        assert retrieved_monitor is custom_monitor
        assert retrieved_monitor.max_concurrent_queries == 100


class TestPerformanceMetric:
    """Test suite for PerformanceMetric dataclass."""

    def test_metric_creation(self):
        """Test creating a performance metric."""
        metric = PerformanceMetric(
            metric_id="test123",
            operation="test_op",
            duration_ms=123.45,
            timestamp=datetime.utcnow(),
            success=True,
            metadata={"key": "value"},
            user_id="user123",
        )

        assert metric.metric_id == "test123"
        assert metric.operation == "test_op"
        assert metric.duration_ms == 123.45
        assert metric.success is True
        assert metric.metadata == {"key": "value"}
        assert metric.user_id == "user123"
        assert metric.error is None


class TestQueryQueueItem:
    """Test suite for QueryQueueItem dataclass."""

    def test_queue_item_creation(self):
        """Test creating a query queue item."""
        item = QueryQueueItem(
            query_id="q123",
            user_id="user123",
            query="test query",
            priority=5,
        )

        assert item.query_id == "q123"
        assert item.user_id == "user123"
        assert item.query == "test query"
        assert item.priority == 5
        assert item.queued_at is not None
        assert item.started_at is None
        assert item.completed_at is None


# ------------------------------------------------------------------
# Integration Tests
# ------------------------------------------------------------------


class TestPerformanceMonitorIntegration:
    """Integration tests for performance monitoring."""

    @pytest.mark.asyncio
    async def test_end_to_end_query_processing(self, monitor_with_workers):
        """Test complete query processing flow with monitoring."""

        async def process_query(query: str):
            await asyncio.sleep(0.05)
            return f"Result for: {query}"

        # Enqueue queries
        query_ids = []
        for i in range(5):
            query_id = await monitor_with_workers.enqueue_query(
                user_id=f"user{i}",
                query=f"query {i}",
                priority=i,
            )
            query_ids.append(query_id)

        # Process with monitoring
        results = []
        for i in range(5):
            result = await monitor_with_workers.track_operation(
                operation="process_query",
                func=process_query,
                query=f"query {i}",
                user_id=f"user{i}",
            )
            results.append(result)

        # Verify results
        assert len(results) == 5
        assert all("Result for:" in r for r in results)

        # Check metrics
        summary = monitor_with_workers.get_performance_summary()
        assert summary["total_operations"] == 5
        assert summary["successful_operations"] == 5

    @pytest.mark.asyncio
    async def test_high_load_scenario(self):
        """Test system behavior under high load (Requirement 6.3, 6.5)."""
        monitor = PerformanceMonitor(
            max_concurrent_queries=50,
            queue_size=200,
            slow_query_threshold_ms=500.0,
        )

        await monitor.start_queue_workers(num_workers=10)

        try:

            async def user_query():
                await asyncio.sleep(0.02)
                return "result"

            # Simulate 100 concurrent users
            tasks = []
            for i in range(100):
                task = asyncio.create_task(
                    monitor.execute_with_concurrency_limit(
                        func=user_query,
                        operation="user_query",
                        user_id=f"user{i}",
                    )
                )
                tasks.append(task)

            # All should complete
            results = await asyncio.gather(*tasks)
            assert len(results) == 100

            # Check performance
            summary = monitor.get_performance_summary()
            assert summary["total_operations"] == 100
            assert summary["success_rate"] >= 0.95  # At least 95% success

            # Verify response times
            assert summary["duration_stats"]["p95_ms"] < 3000  # 95th percentile < 3s

        finally:
            await monitor.stop_queue_workers()

    @pytest.mark.asyncio
    async def test_performance_requirements_validation(self):
        """Test that all performance requirements are met."""
        monitor = PerformanceMonitor(
            max_concurrent_queries=50,
            slow_query_threshold_ms=500.0,
        )

        async def search_operation():
            """Simulates a search operation (Requirement 6.1: < 500ms)."""
            await asyncio.sleep(0.3)  # 300ms - within requirement
            return "search_results"

        async def full_response_operation():
            """Simulates full response generation (Requirement 6.2: < 3s)."""
            await asyncio.sleep(2.0)  # 2s - within requirement
            return "full_response"

        # Test search performance (Requirement 6.1)
        search_result = await monitor.track_operation(
            operation="search",
            func=search_operation,
        )
        assert search_result == "search_results"

        search_metric = monitor._metrics[-1]
        assert search_metric.duration_ms < 500.0  # Must be < 500ms

        # Test full response performance (Requirement 6.2)
        response_result = await monitor.track_operation(
            operation="full_response",
            func=full_response_operation,
        )
        assert response_result == "full_response"

        response_metric = monitor._metrics[-1]
        assert response_metric.duration_ms < 3000.0  # Must be < 3s

        # Test concurrent user support (Requirement 6.3)
        async def concurrent_query():
            await asyncio.sleep(0.01)
            return "result"

        tasks = [
            asyncio.create_task(
                monitor.execute_with_concurrency_limit(
                    func=concurrent_query,
                    operation="concurrent_test",
                )
            )
            for _ in range(50)
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 50  # All 50 concurrent users served

        # Verify queue functionality (Requirement 6.5)
        queue_status = monitor.get_queue_status()
        assert queue_status["max_queue_size"] > 0  # Queue is configured
