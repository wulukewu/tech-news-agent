"""
Example: Performance Monitor Integration with QA Agent Controller

This example demonstrates how to integrate the PerformanceMonitor with the
existing QA Agent Controller to track and optimize performance across all
system components.

Requirements: 6.1, 6.2, 6.3, 6.5
"""

import asyncio
import logging
from typing import Optional
from uuid import uuid4

from .performance_monitor import PerformanceMonitor, get_performance_monitor
from .models import UserProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceOptimizedQAController:
    """
    Example QA Controller with integrated performance monitoring.

    This demonstrates how to wrap existing QA Agent Controller methods
    with performance tracking to ensure requirements are met.
    """

    def __init__(self):
        """Initialize controller with performance monitoring."""
        # Get global performance monitor
        self.performance_monitor = get_performance_monitor()

        # Configure for production load
        self.performance_monitor.max_concurrent_queries = 50
        self.performance_monitor.slow_query_threshold_ms = 500.0

        # Register alert handlers
        self.performance_monitor.register_alert_callback(self._handle_performance_alert)

        logger.info("Performance-optimized QA Controller initialized")

    async def _handle_performance_alert(self, alert_type: str, metric) -> None:
        """Handle performance alerts."""
        if alert_type == "slow_query":
            logger.warning(
                f"⚠️  Slow query detected: {metric.operation} took {metric.duration_ms:.2f}ms "
                f"(user: {metric.user_id}, threshold: {self.performance_monitor.slow_query_threshold_ms}ms)"
            )

            # In production, you might:
            # - Send notification to monitoring system
            # - Trigger auto-scaling
            # - Log to analytics platform

    async def process_query(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        user_profile: Optional[UserProfile] = None,
    ):
        """
        Process a user query with comprehensive performance tracking.

        This method demonstrates wrapping the entire query processing pipeline
        with performance monitoring to ensure < 3 second response time (Requirement 6.2).
        """
        # Use concurrency limiting to support 50+ users (Requirement 6.3)
        return await self.performance_monitor.execute_with_concurrency_limit(
            func=self._process_query_internal,
            operation="process_query",
            user_id=user_id,
            metadata={
                "query_length": len(query),
                "has_conversation": conversation_id is not None,
                "has_profile": user_profile is not None,
            },
            # Pass through arguments
            user_id=user_id,
            query=query,
            conversation_id=conversation_id,
            user_profile=user_profile,
        )

    async def _process_query_internal(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str],
        user_profile: Optional[UserProfile],
    ):
        """Internal query processing with component-level tracking."""

        # Step 1: Query validation (fast operation)
        validation_result = await self.performance_monitor.track_operation(
            operation="validate_query",
            func=self._validate_query,
            user_id=user_id,
            query=query,
        )

        if not validation_result["is_valid"]:
            return {
                "error": validation_result["error"],
                "suggestions": validation_result["suggestions"],
            }

        # Step 2: Generate embedding (should be fast)
        query_vector = await self.performance_monitor.track_operation(
            operation="generate_embedding",
            func=self._generate_embedding,
            user_id=user_id,
            metadata={"query_length": len(query)},
            query=query,
        )

        # Step 3: Semantic search (Requirement 6.1: < 500ms)
        articles = await self.performance_monitor.track_operation(
            operation="semantic_search",
            func=self._semantic_search,
            user_id=user_id,
            metadata={"has_vector": len(query_vector) > 0},
            query_vector=query_vector,
            user_id=user_id,
            limit=10,
        )

        # Step 4: Generate response (should complete within remaining time budget)
        response = await self.performance_monitor.track_operation(
            operation="generate_response",
            func=self._generate_response,
            user_id=user_id,
            metadata={"article_count": len(articles)},
            query=query,
            articles=articles,
            user_profile=user_profile,
        )

        return response

    async def _validate_query(self, query: str):
        """Simulate query validation."""
        await asyncio.sleep(0.05)  # 50ms

        if not query or len(query) < 3:
            return {
                "is_valid": False,
                "error": "Query too short",
                "suggestions": ["Please provide a more detailed question"],
            }

        return {"is_valid": True}

    async def _generate_embedding(self, query: str):
        """Simulate embedding generation."""
        await asyncio.sleep(0.2)  # 200ms
        return [0.1] * 1536  # Simulated embedding vector

    async def _semantic_search(self, query_vector, user_id: str, limit: int):
        """
        Simulate semantic search.

        This operation must complete in < 500ms (Requirement 6.1).
        """
        await asyncio.sleep(0.3)  # 300ms - within requirement

        # Simulated search results
        return [
            {"id": f"article_{i}", "title": f"Article {i}", "score": 0.9 - i * 0.1}
            for i in range(min(limit, 5))
        ]

    async def _generate_response(self, query: str, articles, user_profile):
        """Simulate response generation."""
        await asyncio.sleep(1.5)  # 1.5s

        return {
            "query": query,
            "articles": articles,
            "insights": ["Insight 1", "Insight 2"],
            "recommendations": ["Read article 1", "Explore topic X"],
        }

    async def get_performance_report(self):
        """Get comprehensive performance report."""
        summary = self.performance_monitor.get_performance_summary()

        report = {
            "overall": {
                "total_queries": summary["total_operations"],
                "success_rate": f"{summary['success_rate']:.1%}",
                "avg_response_time": f"{summary['duration_stats']['avg_ms']:.2f}ms",
            },
            "requirements_compliance": {
                "search_under_500ms": (
                    summary["duration_stats"]["p95_ms"] < 500
                    if "semantic_search" in summary["operation_breakdown"]
                    else None
                ),
                "response_under_3s": summary["duration_stats"]["p95_ms"] < 3000,
                "concurrent_users_supported": summary["concurrency"]["max_concurrent"],
                "queue_available": summary["queue"]["max_queue_size"] > 0,
            },
            "performance_details": {
                "p50_response_time": f"{summary['duration_stats']['p50_ms']:.2f}ms",
                "p95_response_time": f"{summary['duration_stats']['p95_ms']:.2f}ms",
                "p99_response_time": f"{summary['duration_stats']['p99_ms']:.2f}ms",
                "slow_queries": summary["slow_queries"]["count"],
                "slow_query_percentage": f"{summary['slow_queries']['percentage']:.1f}%",
            },
            "concurrency": {
                "current": summary["concurrency"]["current_concurrent"],
                "peak": summary["concurrency"]["peak_concurrent"],
                "utilization": f"{summary['concurrency']['utilization']:.1%}",
            },
            "queue": {
                "size": summary["queue"]["queue_size"],
                "utilization": f"{summary['queue']['queue_utilization']:.1%}",
            },
            "operation_breakdown": summary["operation_breakdown"],
        }

        return report


async def example_basic_integration():
    """Example 1: Basic integration with performance tracking."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Integration")
    print("=" * 60)

    controller = PerformanceOptimizedQAController()

    # Process a single query
    print("\nProcessing query...")
    result = await controller.process_query(
        user_id="user123",
        query="What is machine learning?",
    )

    print(f"Result: {result}")

    # Get performance report
    report = await controller.get_performance_report()
    print(f"\nPerformance Report:")
    print(f"  Total queries: {report['overall']['total_queries']}")
    print(f"  Success rate: {report['overall']['success_rate']}")
    print(f"  Avg response time: {report['overall']['avg_response_time']}")


async def example_concurrent_load():
    """Example 2: Handling concurrent load (Requirement 6.3)."""
    print("\n" + "=" * 60)
    print("Example 2: Concurrent Load (50+ Users)")
    print("=" * 60)

    controller = PerformanceOptimizedQAController()

    # Simulate 50 concurrent users
    print("\nSimulating 50 concurrent users...")
    tasks = []
    for i in range(50):
        task = asyncio.create_task(
            controller.process_query(
                user_id=f"user{i}",
                query=f"Query from user {i}",
            )
        )
        tasks.append(task)

    # Wait for all queries to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = sum(1 for r in results if not isinstance(r, Exception))
    print(f"\nCompleted: {successful}/{len(results)} queries")

    # Get performance report
    report = await controller.get_performance_report()
    print(f"\nConcurrency Stats:")
    print(f"  Peak concurrent: {report['concurrency']['peak']}")
    print(f"  Max supported: {report['requirements_compliance']['concurrent_users_supported']}")
    print(f"  Utilization: {report['concurrency']['utilization']}")


async def example_performance_validation():
    """Example 3: Validating performance requirements."""
    print("\n" + "=" * 60)
    print("Example 3: Performance Requirements Validation")
    print("=" * 60)

    controller = PerformanceOptimizedQAController()

    # Process multiple queries to get meaningful statistics
    print("\nProcessing 20 queries for performance analysis...")
    for i in range(20):
        await controller.process_query(
            user_id=f"user{i}",
            query=f"Test query {i}",
        )

    # Get comprehensive report
    report = await controller.get_performance_report()

    print(f"\n{'='*60}")
    print("PERFORMANCE REQUIREMENTS VALIDATION")
    print(f"{'='*60}")

    # Requirement 6.1: Search < 500ms
    print(f"\nRequirement 6.1: Search response time < 500ms")
    if "semantic_search" in report["operation_breakdown"]:
        search_stats = report["operation_breakdown"]["semantic_search"]
        search_compliant = search_stats["avg_duration_ms"] < 500
        print(f"  Avg search time: {search_stats['avg_duration_ms']:.2f}ms")
        print(f"  Status: {'✅ PASS' if search_compliant else '❌ FAIL'}")

    # Requirement 6.2: Complete response < 3s
    print(f"\nRequirement 6.2: Complete response generation < 3 seconds")
    if "process_query" in report["operation_breakdown"]:
        query_stats = report["operation_breakdown"]["process_query"]
        response_compliant = query_stats["avg_duration_ms"] < 3000
        print(f"  Avg response time: {query_stats['avg_duration_ms']:.2f}ms")
        print(f"  P95 response time: {report['performance_details']['p95_response_time']}")
        print(f"  Status: {'✅ PASS' if response_compliant else '❌ FAIL'}")

    # Requirement 6.3: Support 50+ concurrent users
    print(f"\nRequirement 6.3: Support 50+ concurrent users")
    concurrent_compliant = report["requirements_compliance"]["concurrent_users_supported"] >= 50
    print(f"  Max concurrent: {report['requirements_compliance']['concurrent_users_supported']}")
    print(f"  Status: {'✅ PASS' if concurrent_compliant else '❌ FAIL'}")

    # Requirement 6.5: Query queuing
    print(f"\nRequirement 6.5: Query queuing for high load")
    queue_compliant = report["requirements_compliance"]["queue_available"]
    print(f"  Queue available: {queue_compliant}")
    print(f"  Status: {'✅ PASS' if queue_compliant else '❌ FAIL'}")

    # Overall performance summary
    print(f"\n{'='*60}")
    print("OVERALL PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    print(f"  Total queries processed: {report['overall']['total_queries']}")
    print(f"  Success rate: {report['overall']['success_rate']}")
    print(f"  Average response time: {report['overall']['avg_response_time']}")
    print(f"  P50 response time: {report['performance_details']['p50_response_time']}")
    print(f"  P95 response time: {report['performance_details']['p95_response_time']}")
    print(f"  P99 response time: {report['performance_details']['p99_response_time']}")
    print(
        f"  Slow queries: {report['performance_details']['slow_queries']} ({report['performance_details']['slow_query_percentage']})"
    )


async def example_high_load_with_queuing():
    """Example 4: High load scenario with query queuing (Requirement 6.5)."""
    print("\n" + "=" * 60)
    print("Example 4: High Load with Query Queuing")
    print("=" * 60)

    controller = PerformanceOptimizedQAController()

    # Start queue workers
    await controller.performance_monitor.start_queue_workers(num_workers=5)

    try:
        # Simulate burst of 100 queries
        print("\nSimulating burst of 100 queries...")
        tasks = []
        for i in range(100):
            # Some queries go through normal processing
            if i < 50:
                task = asyncio.create_task(
                    controller.process_query(
                        user_id=f"user{i}",
                        query=f"Query {i}",
                    )
                )
                tasks.append(task)
            # Others are queued
            else:
                await controller.performance_monitor.enqueue_query(
                    user_id=f"user{i}",
                    query=f"Queued query {i}",
                    priority=i % 3,
                )

        # Check queue status during processing
        await asyncio.sleep(0.5)
        queue_status = controller.performance_monitor.get_queue_status()
        print(f"\nQueue Status (mid-processing):")
        print(f"  Queue size: {queue_status['queue_size']}")
        print(f"  Active queries: {queue_status['active_queries']}")
        print(f"  Utilization: {queue_status['queue_utilization']:.1%}")

        # Wait for direct queries to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        print(f"\nDirect queries completed: {len(results)}")

        # Wait for queued queries to process
        await asyncio.sleep(2.0)

        # Final status
        final_status = controller.performance_monitor.get_queue_status()
        print(f"\nFinal Queue Status:")
        print(f"  Queue size: {final_status['queue_size']}")
        print(f"  Completed: {final_status['completed_queries']}")

    finally:
        await controller.performance_monitor.stop_queue_workers()


async def main():
    """Run all integration examples."""
    print("\n" + "=" * 60)
    print("PERFORMANCE MONITOR INTEGRATION EXAMPLES")
    print("=" * 60)

    try:
        await example_basic_integration()
        await example_concurrent_load()
        await example_performance_validation()
        await example_high_load_with_queuing()

        print("\n" + "=" * 60)
        print("ALL INTEGRATION EXAMPLES COMPLETED")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Integration example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
