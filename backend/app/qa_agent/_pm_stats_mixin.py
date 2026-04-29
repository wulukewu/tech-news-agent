"""Performance stats mixin for PerformanceMonitor."""
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data point."""

    operation: str
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerfStatsMixin:
    def get_performance_summary(self, time_window_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.

        Args:
            time_window_seconds: Optional time window for metrics (None = all time)

        Returns:
            Dictionary with performance statistics
        """
        # Filter metrics by time window if specified
        if time_window_seconds:
            cutoff_time = datetime.utcnow() - timedelta(seconds=time_window_seconds)
            metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]
        else:
            metrics = list(self._metrics)

        if not metrics:
            return {
                "total_operations": 0,
                "time_window_seconds": time_window_seconds,
                "message": "No metrics available",
            }

        # Calculate overall statistics
        total_ops = len(metrics)
        successful_ops = sum(1 for m in metrics if m.success)
        failed_ops = total_ops - successful_ops

        durations = [m.duration_ms for m in metrics]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        # Calculate percentiles
        sorted_durations = sorted(durations)
        p50 = sorted_durations[len(sorted_durations) // 2]
        p95 = sorted_durations[int(len(sorted_durations) * 0.95)]
        p99 = sorted_durations[int(len(sorted_durations) * 0.99)]

        # Slow query statistics
        slow_queries = [m for m in metrics if m.duration_ms > self.slow_query_threshold_ms]

        # Operation breakdown
        operation_breakdown = {}
        for op, stats in self._operation_stats.items():
            if stats["count"] > 0:
                operation_breakdown[op] = {
                    "count": stats["count"],
                    "avg_duration_ms": stats["total_duration_ms"] / stats["count"],
                    "min_duration_ms": stats["min_duration_ms"],
                    "max_duration_ms": stats["max_duration_ms"],
                    "success_rate": stats["success_count"] / stats["count"],
                    "error_count": stats["error_count"],
                }

        return {
            "time_window_seconds": time_window_seconds,
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0.0,
            "duration_stats": {
                "avg_ms": avg_duration,
                "min_ms": min_duration,
                "max_ms": max_duration,
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
            },
            "slow_queries": {
                "count": len(slow_queries),
                "percentage": len(slow_queries) / total_ops * 100 if total_ops > 0 else 0.0,
                "threshold_ms": self.slow_query_threshold_ms,
            },
            "operation_breakdown": operation_breakdown,
            "concurrency": self.get_concurrency_stats(),
            "queue": self.get_queue_status(),
        }

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent slow queries.

        Args:
            limit: Maximum number of slow queries to return

        Returns:
            List of slow query details
        """
        slow_queries = list(self._slow_queries)[-limit:]

        return [
            {
                "metric_id": m.metric_id,
                "operation": m.operation,
                "duration_ms": m.duration_ms,
                "timestamp": m.timestamp.isoformat(),
                "user_id": m.user_id,
                "metadata": m.metadata,
                "error": m.error,
            }
            for m in slow_queries
        ]

    def get_operation_stats(self, operation: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific operation.

        Args:
            operation: Operation name

        Returns:
            Operation statistics or None if not found
        """
        if operation not in self._operation_stats:
            return None

        stats = self._operation_stats[operation]

        if stats["count"] == 0:
            return None

        return {
            "operation": operation,
            "count": stats["count"],
            "avg_duration_ms": stats["total_duration_ms"] / stats["count"],
            "min_duration_ms": stats["min_duration_ms"],
            "max_duration_ms": stats["max_duration_ms"],
            "success_count": stats["success_count"],
            "error_count": stats["error_count"],
            "success_rate": stats["success_count"] / stats["count"],
        }

    # ------------------------------------------------------------------
    # Performance Alerts
    # ------------------------------------------------------------------

    def register_alert_callback(self, callback: Callable) -> None:
        """
        Register a callback for performance alerts.

        Args:
            callback: Async function to call on alerts
        """
        self._alert_callbacks.append(callback)
        logger.info(f"Registered alert callback: {callback.__name__}")

    async def _trigger_alerts(self, alert_type: str, metric: PerformanceMetric) -> None:
        """
        Trigger registered alert callbacks.

        Args:
            alert_type: Type of alert
            metric: Performance metric that triggered the alert
        """
        for callback in self._alert_callbacks:
            try:
                await callback(alert_type, metric)
            except Exception as e:
                logger.error(f"Error in alert callback {callback.__name__}: {e}")

    # ------------------------------------------------------------------
    # Cleanup and Maintenance
    # ------------------------------------------------------------------

    def cleanup_old_metrics(self) -> int:
        """
        Remove metrics older than retention period.

        Returns:
            Number of metrics removed
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.metrics_retention_seconds)

        original_count = len(self._metrics)

        # Filter out old metrics
        self._metrics = deque(
            (m for m in self._metrics if m.timestamp >= cutoff_time), maxlen=self._metrics.maxlen
        )

        removed_count = original_count - len(self._metrics)

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old metrics")

        return removed_count

    def reset_stats(self) -> None:
        """Reset all performance statistics."""
        self._metrics.clear()
        self._operation_stats.clear()
        self._slow_queries.clear()
        self._completed_queries.clear()
        self._peak_concurrent_count = 0

        logger.info("Performance statistics reset")
