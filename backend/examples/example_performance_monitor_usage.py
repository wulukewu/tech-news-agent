"""
Example Usage: Performance Monitor

This example demonstrates how to use the PerformanceMonitor for tracking
response times, managing query queues, and monitoring system performance.

Requirements: 6.1, 6.2, 6.3, 6.5
"""

import asyncio
import logging

from .performance_monitor import PerformanceMonitor, get_performance_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_basic_tracking():
    """Example 1: Basic operation tracking."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Operation Tracking")
    print("=" * 60)

    monitor = PerformanceMonitor()

    # Track a simple operation
    async def search_operation():
        await asyncio.sleep(0.3)  # Simulate 300ms search
        return ["article1", "article2", "article3"]

    results = await monitor.track_operation(
        operation="semantic_search",
        func=search_operation,
        user_id="user123",
        metadata={"query": "machine learning", "limit": 10},
    )

    print(f"Search results: {results}")

    # Get operation stats
    stats = monitor.get_operation_stats("semantic_search")
    print("\nOperation stats:")
    print(f"  - Count: {stats['count']}")
    print(f"  - Avg duration: {stats['avg_duration_ms']:.2f}ms")
    print(f"  - Success rate: {stats['success_rate']:.1%}")


async def example_slow_query_detection():
    """Example 2: Slow query detection."""
    print("\n" + "=" * 60)
    print("Example 2: Slow Query Detection")
    print("=" * 60)

    monitor = PerformanceMonitor(slow_query_threshold_ms=500.0)

    # Register alert callback
    async def alert_handler(alert_type, metric):
        print(f"\n⚠️  ALERT: {alert_type}")
        print(f"   Operation: {metric.operation}")
        print(f"   Duration: {metric.duration_ms:.2f}ms")
        print(f"   User: {metric.user_id}")

    monitor.register_alert_callback(alert_handler)

    # Fast operation (no alert)
    async def fast_search():
        await asyncio.sleep(0.2)  # 200ms
        return "fast_results"

    print("\nExecuting fast search (200ms)...")
    await monitor.track_operation("fast_search", fast_search, user_id="user1")

    # Slow operation (triggers alert)
    async def slow_search():
        await asyncio.sleep(0.7)  # 700ms - exceeds threshold
        return "slow_results"

    print("\nExecuting slow search (700ms)...")
    await monitor.track_operation("slow_search", slow_search, user_id="user2")

    # Wait for alert to be processed
    await asyncio.sleep(0.1)

    # Get slow queries
    slow_queries = monitor.get_slow_queries(limit=5)
    print(f"\nSlow queries detected: {len(slow_queries)}")
    for query in slow_queries:
        print(f"  - {query['operation']}: {query['duration_ms']:.2f}ms")


async def example_concurrency_limiting():
    """Example 3: Concurrency limiting for 50+ users."""
    print("\n" + "=" * 60)
    print("Example 3: Concurrency Limiting (50+ Users)")
    print("=" * 60)

    monitor = PerformanceMonitor(max_concurrent_queries=50)

    async def user_query():
        await asyncio.sleep(0.1)  # Simulate query processing
        return "result"

    # Simulate 60 concurrent users
    print("\nSimulating 60 concurrent users...")
    tasks = []
    for i in range(60):
        task = asyncio.create_task(
            monitor.execute_with_concurrency_limit(
                func=user_query,
                user_id=f"user{i}",
                operation="user_query",
            )
        )
        tasks.append(task)

    # Check concurrency while running
    await asyncio.sleep(0.05)
    stats = monitor.get_concurrency_stats()
    print("\nConcurrency stats (mid-execution):")
    print(f"  - Current concurrent: {stats['current_concurrent']}")
    print(f"  - Max allowed: {stats['max_concurrent']}")
    print(f"  - Utilization: {stats['utilization']:.1%}")

    # Wait for all to complete
    results = await asyncio.gather(*tasks)
    print(f"\nAll {len(results)} queries completed successfully")

    # Final stats
    final_stats = monitor.get_concurrency_stats()
    print("\nFinal stats:")
    print(f"  - Peak concurrent: {final_stats['peak_concurrent']}")
    print(f"  - Total processed: {len(results)}")


async def example_query_queuing():
    """Example 4: Query queuing for high load."""
    print("\n" + "=" * 60)
    print("Example 4: Query Queuing for High Load")
    print("=" * 60)

    monitor = PerformanceMonitor(
        max_concurrent_queries=5,
        queue_size=20,
    )

    # Start queue workers
    await monitor.start_queue_workers(num_workers=3)

    try:
        # Enqueue multiple queries
        print("\nEnqueuing 15 queries...")
        query_ids = []
        for i in range(15):
            query_id = await monitor.enqueue_query(
                user_id=f"user{i}",
                query=f"What is machine learning? (query {i})",
                priority=i % 3,  # Vary priority
            )
            query_ids.append(query_id)
            print(f"  Enqueued query {i}: {query_id[:8]}...")

        # Check queue status
        status = monitor.get_queue_status()
        print("\nQueue status:")
        print(f"  - Queue size: {status['queue_size']}")
        print(f"  - Active queries: {status['active_queries']}")
        print(f"  - Workers running: {status['workers_running']}")
        print(f"  - Utilization: {status['queue_utilization']:.1%}")

        # Wait for processing
        print("\nWaiting for queue to process...")
        await asyncio.sleep(2.0)

        # Final status
        final_status = monitor.get_queue_status()
        print("\nFinal queue status:")
        print(f"  - Queue size: {final_status['queue_size']}")
        print(f"  - Completed: {final_status['completed_queries']}")

    finally:
        await monitor.stop_queue_workers()


async def example_performance_summary():
    """Example 5: Comprehensive performance summary."""
    print("\n" + "=" * 60)
    print("Example 5: Performance Summary and Reporting")
    print("=" * 60)

    monitor = PerformanceMonitor()

    # Simulate various operations
    async def search(duration: float):
        await asyncio.sleep(duration)
        return "results"

    async def generate_response(duration: float):
        await asyncio.sleep(duration)
        return "response"

    print("\nExecuting various operations...")

    # Fast searches
    for i in range(5):
        await monitor.track_operation(
            "search",
            search,
            0.2,  # 200ms
            user_id=f"user{i}",
        )

    # Slow searches
    for i in range(2):
        await monitor.track_operation(
            "search",
            search,
            0.6,  # 600ms
            user_id=f"user{i+5}",
        )

    # Response generation
    for i in range(3):
        await monitor.track_operation(
            "generate_response",
            generate_response,
            1.5,  # 1.5s
            user_id=f"user{i}",
        )

    # Get comprehensive summary
    summary = monitor.get_performance_summary()

    print(f"\n{'='*60}")
    print("PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    print("\nOverall Statistics:")
    print(f"  - Total operations: {summary['total_operations']}")
    print(f"  - Successful: {summary['successful_operations']}")
    print(f"  - Failed: {summary['failed_operations']}")
    print(f"  - Success rate: {summary['success_rate']:.1%}")

    print("\nDuration Statistics:")
    stats = summary["duration_stats"]
    print(f"  - Average: {stats['avg_ms']:.2f}ms")
    print(f"  - Min: {stats['min_ms']:.2f}ms")
    print(f"  - Max: {stats['max_ms']:.2f}ms")
    print(f"  - P50 (median): {stats['p50_ms']:.2f}ms")
    print(f"  - P95: {stats['p95_ms']:.2f}ms")
    print(f"  - P99: {stats['p99_ms']:.2f}ms")

    print("\nSlow Queries:")
    slow = summary["slow_queries"]
    print(f"  - Count: {slow['count']}")
    print(f"  - Percentage: {slow['percentage']:.1f}%")
    print(f"  - Threshold: {slow['threshold_ms']}ms")

    print("\nOperation Breakdown:")
    for op_name, op_stats in summary["operation_breakdown"].items():
        print(f"\n  {op_name}:")
        print(f"    - Count: {op_stats['count']}")
        print(f"    - Avg duration: {op_stats['avg_duration_ms']:.2f}ms")
        print(f"    - Success rate: {op_stats['success_rate']:.1%}")


async def example_performance_requirements():
    """Example 6: Validating performance requirements."""
    print("\n" + "=" * 60)
    print("Example 6: Performance Requirements Validation")
    print("=" * 60)

    monitor = PerformanceMonitor(slow_query_threshold_ms=500.0)

    # Requirement 6.1: Search < 500ms
    print("\nRequirement 6.1: Search response time < 500ms")

    async def search_operation():
        await asyncio.sleep(0.3)  # 300ms
        return "search_results"

    await monitor.track_operation("search", search_operation)
    search_metric = monitor._metrics[-1]

    requirement_met = search_metric.duration_ms < 500.0
    print(f"  Duration: {search_metric.duration_ms:.2f}ms")
    print(f"  Requirement met: {'✅ YES' if requirement_met else '❌ NO'}")

    # Requirement 6.2: Complete response < 3 seconds
    print("\nRequirement 6.2: Complete response generation < 3 seconds")

    async def full_response():
        await asyncio.sleep(2.0)  # 2 seconds
        return "full_response"

    await monitor.track_operation("full_response", full_response)
    response_metric = monitor._metrics[-1]

    requirement_met = response_metric.duration_ms < 3000.0
    print(f"  Duration: {response_metric.duration_ms:.2f}ms")
    print(f"  Requirement met: {'✅ YES' if requirement_met else '❌ NO'}")

    # Requirement 6.3: Support 50+ concurrent users
    print("\nRequirement 6.3: Support 50+ concurrent users")
    high_concurrency_monitor = PerformanceMonitor(max_concurrent_queries=50)

    async def user_query():
        await asyncio.sleep(0.05)
        return "result"

    tasks = [
        asyncio.create_task(
            high_concurrency_monitor.execute_with_concurrency_limit(
                func=user_query,
                operation="concurrent_test",
            )
        )
        for _ in range(50)
    ]

    results = await asyncio.gather(*tasks)
    requirement_met = len(results) == 50

    print(f"  Concurrent users served: {len(results)}")
    print(f"  Requirement met: {'✅ YES' if requirement_met else '❌ NO'}")

    # Requirement 6.5: Query queuing for high load
    print("\nRequirement 6.5: Query queuing for high load")
    queue_monitor = PerformanceMonitor(queue_size=200)

    # Enqueue queries
    for i in range(10):
        await queue_monitor.enqueue_query(
            user_id=f"user{i}",
            query=f"query {i}",
        )

    status = queue_monitor.get_queue_status()
    requirement_met = status["max_queue_size"] >= 50

    print(f"  Queue capacity: {status['max_queue_size']}")
    print(f"  Queries enqueued: {status['queue_size']}")
    print(f"  Requirement met: {'✅ YES' if requirement_met else '❌ NO'}")


async def example_global_instance():
    """Example 7: Using global performance monitor instance."""
    print("\n" + "=" * 60)
    print("Example 7: Global Performance Monitor Instance")
    print("=" * 60)

    # Get global instance
    monitor = get_performance_monitor()

    # Use it across different parts of the application
    async def operation1():
        await asyncio.sleep(0.1)
        return "result1"

    async def operation2():
        await asyncio.sleep(0.1)
        return "result2"

    print("\nUsing global monitor instance...")
    await monitor.track_operation("op1", operation1)
    await monitor.track_operation("op2", operation2)

    # Get summary from global instance
    summary = monitor.get_performance_summary()
    print(f"\nGlobal monitor tracked {summary['total_operations']} operations")

    # The same instance is returned
    monitor2 = get_performance_monitor()
    assert monitor is monitor2
    print("✅ Same instance confirmed")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PERFORMANCE MONITOR EXAMPLES")
    print("=" * 60)

    try:
        await example_basic_tracking()
        await example_slow_query_detection()
        await example_concurrency_limiting()
        await example_query_queuing()
        await example_performance_summary()
        await example_performance_requirements()
        await example_global_instance()

        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
