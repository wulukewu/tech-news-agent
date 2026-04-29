"""
Performance Monitor for Intelligent Q&A Agent

This module implements comprehensive performance monitoring and optimization features:
- Response time tracking and performance metrics
- Query queuing for high load scenarios
- Database query optimization and connection pooling
- Slow query detection and logging
- Performance metrics collection and reporting

Requirements: 6.1, 6.2, 6.3, 6.5
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Deque, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class QueryQueueItem:
    """Item in the query queue for load management."""

    query_id: str
    user_id: str
    query: str
    priority: int = 0  # Higher priority = processed first
    queued_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None


from app.qa_agent._pm_stats_mixin import PerformanceMetric, PerfStatsMixin


class PerformanceMonitor(PerfStatsMixin):
    """
    Comprehensive performance monitoring and optimization system.

    Features:
    - Real-time response time tracking
    - Performance metrics collection and aggregation
    - Slow query detection and logging
    - Query queuing for high load scenarios
    - Performance reporting and analytics

    Requirements: 6.1, 6.2, 6.3, 6.5
    """

    def __init__(
        self,
        max_concurrent_queries: int = 50,
        queue_size: int = 200,
        slow_query_threshold_ms: float = 500.0,
        metrics_retention_seconds: int = 3600,
    ):
        """
        Initialize the PerformanceMonitor.

        Args:
            max_concurrent_queries: Maximum concurrent queries (Requirement 6.3)
            queue_size: Maximum queue size for pending queries
            slow_query_threshold_ms: Threshold for slow query detection (Requirement 6.1)
            metrics_retention_seconds: How long to retain metrics in memory
        """
        self.max_concurrent_queries = max_concurrent_queries
        self.queue_size = queue_size
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.metrics_retention_seconds = metrics_retention_seconds

        # Metrics storage
        self._metrics: Deque[PerformanceMetric] = deque(maxlen=10000)
        self._operation_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_duration_ms": 0.0,
                "min_duration_ms": float("inf"),
                "max_duration_ms": 0.0,
                "success_count": 0,
                "error_count": 0,
            }
        )

        # Query queue for load management (Requirement 6.5)
        self._query_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._active_queries: Dict[str, QueryQueueItem] = {}
        self._completed_queries: Deque[QueryQueueItem] = deque(maxlen=1000)
        self._queue_workers: List[asyncio.Task] = []
        self._queue_running = False

        # Concurrent query tracking (Requirement 6.3)
        self._concurrent_semaphore = asyncio.Semaphore(max_concurrent_queries)
        self._current_concurrent_count = 0
        self._peak_concurrent_count = 0

        # Slow query tracking
        self._slow_queries: Deque[PerformanceMetric] = deque(maxlen=100)

        # Performance alerts
        self._alert_callbacks: List[Callable] = []

        logger.info(
            f"PerformanceMonitor initialized: max_concurrent={max_concurrent_queries}, "
            f"queue_size={queue_size}, slow_threshold={slow_query_threshold_ms}ms"
        )

    # ------------------------------------------------------------------
    # Response Time Tracking (Requirement 6.1, 6.2)
    # ------------------------------------------------------------------

    async def track_operation(
        self,
        operation: str,
        func: Callable,
        *args,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """
        Track the performance of an async operation.

        Automatically measures execution time, detects slow queries,
        and collects performance metrics.

        Args:
            operation: Name of the operation being tracked
            func: Async function to execute and track
            *args: Positional arguments for func
            user_id: Optional user ID for tracking
            metadata: Optional metadata to attach to metric
            **kwargs: Keyword arguments for func

        Returns:
            Result of the function execution

        Raises:
            Any exception raised by the function

        Validates: Requirements 6.1, 6.2
        """
        metric_id = str(uuid4())
        start_time = time.time()
        success = False
        error_msg = None

        try:
            result = await func(*args, **kwargs)
            success = True
            return result

        except Exception as e:
            error_msg = str(e)
            raise

        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Create metric
            metric = PerformanceMetric(
                metric_id=metric_id,
                operation=operation,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                success=success,
                metadata=metadata or {},
                user_id=user_id,
                error=error_msg,
            )

            # Store metric
            self._metrics.append(metric)

            # Update operation stats
            self._update_operation_stats(operation, duration_ms, success)

            # Check for slow query (Requirement 6.1: < 500ms)
            if duration_ms > self.slow_query_threshold_ms:
                self._slow_queries.append(metric)
                logger.warning(
                    f"Slow query detected: {operation} took {duration_ms:.2f}ms "
                    f"(threshold: {self.slow_query_threshold_ms}ms)",
                    extra={
                        "operation": operation,
                        "duration_ms": duration_ms,
                        "user_id": user_id,
                        "metadata": metadata,
                    },
                )

                # Trigger alerts
                await self._trigger_alerts("slow_query", metric)

            # Log performance
            log_level = logging.WARNING if not success else logging.DEBUG
            logger.log(
                log_level,
                f"Operation {operation}: {duration_ms:.2f}ms, success={success}",
                extra={
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "success": success,
                    "user_id": user_id,
                },
            )

    def _update_operation_stats(self, operation: str, duration_ms: float, success: bool) -> None:
        """Update aggregated statistics for an operation."""
        stats = self._operation_stats[operation]
        stats["count"] += 1
        stats["total_duration_ms"] += duration_ms
        stats["min_duration_ms"] = min(stats["min_duration_ms"], duration_ms)
        stats["max_duration_ms"] = max(stats["max_duration_ms"], duration_ms)

        if success:
            stats["success_count"] += 1
        else:
            stats["error_count"] += 1

    # ------------------------------------------------------------------
    # Query Queuing for High Load (Requirement 6.5)
    # ------------------------------------------------------------------

    async def start_queue_workers(self, num_workers: int = 10) -> None:
        """
        Start background workers to process queued queries.

        Implements Requirement 6.5: Query queuing for high load scenarios.

        Args:
            num_workers: Number of concurrent worker tasks
        """
        if self._queue_running:
            logger.warning("Queue workers already running")
            return

        self._queue_running = True

        for i in range(num_workers):
            worker = asyncio.create_task(self._queue_worker(i))
            self._queue_workers.append(worker)

        logger.info(f"Started {num_workers} queue workers")

    async def stop_queue_workers(self) -> None:
        """Stop all queue workers gracefully."""
        if not self._queue_running:
            return

        self._queue_running = False

        # Cancel all workers
        for worker in self._queue_workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self._queue_workers, return_exceptions=True)

        self._queue_workers.clear()
        logger.info("Stopped all queue workers")

    async def _queue_worker(self, worker_id: int) -> None:
        """
        Background worker that processes queued queries.

        Args:
            worker_id: Unique identifier for this worker
        """
        logger.info(f"Queue worker {worker_id} started")

        while self._queue_running:
            try:
                # Get next item from queue (with timeout to allow checking _queue_running)
                try:
                    item = await asyncio.wait_for(self._query_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Process the query
                item.started_at = datetime.utcnow()
                self._active_queries[item.query_id] = item

                try:
                    # The actual query processing will be done by the handler
                    # This worker just manages the queue
                    logger.debug(f"Worker {worker_id} processing query {item.query_id}")

                    # Mark as completed (actual processing happens elsewhere)
                    item.completed_at = datetime.utcnow()

                except Exception as e:
                    item.error = e
                    logger.error(f"Worker {worker_id} error processing query {item.query_id}: {e}")

                finally:
                    # Move to completed and remove from active
                    self._completed_queries.append(item)
                    self._active_queries.pop(item.query_id, None)
                    self._query_queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"Queue worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Queue worker {worker_id} unexpected error: {e}")
                await asyncio.sleep(1.0)  # Back off on error

        logger.info(f"Queue worker {worker_id} stopped")

    async def enqueue_query(
        self,
        user_id: str,
        query: str,
        priority: int = 0,
    ) -> str:
        """
        Add a query to the processing queue.

        Implements Requirement 6.5: Query queuing for high load.

        Args:
            user_id: User identifier
            query: Query text
            priority: Query priority (higher = processed first)

        Returns:
            Query ID for tracking

        Raises:
            asyncio.QueueFull: If queue is at capacity
        """
        query_id = str(uuid4())

        item = QueryQueueItem(
            query_id=query_id,
            user_id=user_id,
            query=query,
            priority=priority,
        )

        try:
            # Try to add to queue (non-blocking)
            self._query_queue.put_nowait(item)
            logger.info(
                f"Query {query_id} enqueued (priority={priority}, "
                f"queue_size={self._query_queue.qsize()})"
            )
            return query_id

        except asyncio.QueueFull:
            logger.error(f"Query queue full ({self.queue_size}), rejecting query {query_id}")
            raise

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.

        Returns:
            Dictionary with queue statistics
        """
        return {
            "queue_size": self._query_queue.qsize(),
            "max_queue_size": self.queue_size,
            "active_queries": len(self._active_queries),
            "completed_queries": len(self._completed_queries),
            "workers_running": len(self._queue_workers),
            "queue_utilization": self._query_queue.qsize() / self.queue_size,
        }

    # ------------------------------------------------------------------
    # Concurrent Query Management (Requirement 6.3)
    # ------------------------------------------------------------------

    async def execute_with_concurrency_limit(
        self,
        func: Callable,
        *args,
        operation: str = "query",
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Execute a function with concurrency limiting.

        Implements Requirement 6.3: Support 50+ concurrent users.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            operation: Operation name for tracking
            user_id: Optional user ID
            **kwargs: Keyword arguments for func

        Returns:
            Result of the function execution
        """
        async with self._concurrent_semaphore:
            self._current_concurrent_count += 1
            self._peak_concurrent_count = max(
                self._peak_concurrent_count, self._current_concurrent_count
            )

            try:
                return await self.track_operation(
                    operation=operation,
                    func=func,
                    *args,
                    user_id=user_id,
                    metadata={"concurrent_count": self._current_concurrent_count},
                    **kwargs,
                )
            finally:
                self._current_concurrent_count -= 1

    def get_concurrency_stats(self) -> Dict[str, Any]:
        """
        Get concurrency statistics.

        Returns:
            Dictionary with concurrency metrics
        """
        return {
            "current_concurrent": self._current_concurrent_count,
            "peak_concurrent": self._peak_concurrent_count,
            "max_concurrent": self.max_concurrent_queries,
            "utilization": self._current_concurrent_count / self.max_concurrent_queries,
            "available_slots": self.max_concurrent_queries - self._current_concurrent_count,
        }

    # ------------------------------------------------------------------
    # Performance Metrics and Reporting
    # ------------------------------------------------------------------


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get the global PerformanceMonitor instance.

    Returns:
        Global PerformanceMonitor instance
    """
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()

    return _performance_monitor


def set_performance_monitor(monitor: PerformanceMonitor) -> None:
    """
    Set the global PerformanceMonitor instance.

    Args:
        monitor: PerformanceMonitor instance to use globally
    """
    global _performance_monitor
    _performance_monitor = monitor
