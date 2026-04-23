"""
Performance Monitoring and Metrics for Chat Persistence System

Provides:
  - ``PerformanceTracker`` — lightweight in-process metrics collector
    (response times, throughput, error rates) with no external dependencies.
  - ``timed`` async context-manager / decorator for measuring operation
    latency and recording it automatically.
  - ``HealthStatus`` dataclass returned by the ``/health`` endpoint.
  - ``check_system_health`` — aggregates DB, cache, and service health.

For production deployments the metrics can be exported to Prometheus or
another time-series backend by replacing the in-memory store with a proper
client library.  The interface is intentionally kept simple so that swap-out
is straightforward.

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Any, AsyncIterator, Callable, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class OperationMetric:
    """Aggregated metrics for a named operation.

    Attributes:
        name: Operation identifier (e.g. ``"list_conversations"``).
        call_count: Total number of calls recorded.
        error_count: Number of calls that raised an exception.
        total_duration_ms: Cumulative duration in milliseconds.
        min_duration_ms: Minimum observed duration.
        max_duration_ms: Maximum observed duration.
        recent_durations_ms: Ring-buffer of the last 100 durations for
            percentile calculations.
    """

    name: str
    call_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    recent_durations_ms: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def avg_duration_ms(self) -> float:
        """Average duration across all recorded calls."""
        if self.call_count == 0:
            return 0.0
        return round(self.total_duration_ms / self.call_count, 2)

    @property
    def error_rate(self) -> float:
        """Error rate as a fraction in [0, 1]."""
        if self.call_count == 0:
            return 0.0
        return round(self.error_count / self.call_count, 4)

    @property
    def p95_duration_ms(self) -> float:
        """95th-percentile duration from the recent sample window."""
        if not self.recent_durations_ms:
            return 0.0
        sorted_durations = sorted(self.recent_durations_ms)
        idx = max(0, int(len(sorted_durations) * 0.95) - 1)
        return round(sorted_durations[idx], 2)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary for JSON responses."""
        return {
            "name": self.name,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "min_duration_ms": (
                round(self.min_duration_ms, 2) if self.min_duration_ms != float("inf") else 0.0
            ),
            "max_duration_ms": round(self.max_duration_ms, 2),
            "p95_duration_ms": self.p95_duration_ms,
        }


@dataclass
class HealthStatus:
    """Aggregated health status for the chat persistence system.

    Attributes:
        healthy: ``True`` when all critical components are operational.
        components: Per-component health results.
        checked_at: UTC timestamp of the check.
        version: Application version string (optional).
    """

    healthy: bool
    components: dict[str, dict[str, Any]] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary for JSON responses."""
        return {
            "healthy": self.healthy,
            "components": self.components,
            "checked_at": self.checked_at.isoformat(),
            "version": self.version,
        }


# ---------------------------------------------------------------------------
# PerformanceTracker
# ---------------------------------------------------------------------------


class PerformanceTracker:
    """In-process performance metrics collector.

    Thread-safe for asyncio workloads (single event-loop).  For multi-process
    deployments use a shared backend (Redis, Prometheus push-gateway, etc.).

    Usage::

        tracker = PerformanceTracker()

        # As a context manager
        async with tracker.measure("list_conversations"):
            result = await repo.list_conversations(user_id)

        # As a decorator
        @tracker.track("generate_title")
        async def generate_title(...):
            ...

        # Read metrics
        metrics = tracker.get_all_metrics()
    """

    def __init__(self) -> None:
        self._metrics: dict[str, OperationMetric] = defaultdict(
            lambda: OperationMetric(name="unknown")
        )
        self._lock = asyncio.Lock()

    def _get_or_create(self, name: str) -> OperationMetric:
        if name not in self._metrics:
            self._metrics[name] = OperationMetric(name=name)
        return self._metrics[name]

    async def record(
        self,
        name: str,
        duration_ms: float,
        *,
        error: bool = False,
    ) -> None:
        """Record a single operation measurement.

        Args:
            name: Operation identifier.
            duration_ms: Duration in milliseconds.
            error: ``True`` if the operation raised an exception.
        """
        async with self._lock:
            metric = self._get_or_create(name)
            metric.call_count += 1
            metric.total_duration_ms += duration_ms
            metric.recent_durations_ms.append(duration_ms)
            if error:
                metric.error_count += 1
            if duration_ms < metric.min_duration_ms:
                metric.min_duration_ms = duration_ms
            if duration_ms > metric.max_duration_ms:
                metric.max_duration_ms = duration_ms

        # Warn when SLA thresholds are breached
        _check_sla(name, duration_ms)

    @asynccontextmanager
    async def measure(self, name: str) -> AsyncIterator[None]:
        """Async context manager that measures the enclosed block.

        Args:
            name: Operation identifier.

        Yields:
            Nothing — used purely for timing.

        Example::

            async with tracker.measure("get_conversation"):
                conv = await repo.get_conversation(id, user_id)
        """
        start = time.perf_counter()
        error = False
        try:
            yield
        except Exception:
            error = True
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            await self.record(name, duration_ms, error=error)

    def track(self, name: str) -> Callable:
        """Decorator that wraps an async function with performance tracking.

        Args:
            name: Operation identifier.

        Returns:
            Decorator function.

        Example::

            @tracker.track("generate_summary")
            async def generate_summary(self, ...):
                ...
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with self.measure(name):
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def get_metric(self, name: str) -> Optional[OperationMetric]:
        """Return the metric for a specific operation, or ``None``.

        Args:
            name: Operation identifier.

        Returns:
            :class:`OperationMetric` or ``None`` if not yet recorded.
        """
        return self._metrics.get(name)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Return all recorded metrics as a serialisable dictionary.

        Returns:
            Mapping of operation name → metric dict.
        """
        return {name: metric.to_dict() for name, metric in self._metrics.items()}

    async def reset(self, name: Optional[str] = None) -> None:
        """Reset metrics for one operation or all operations.

        Args:
            name: Operation to reset.  When ``None`` all metrics are cleared.
        """
        async with self._lock:
            if name is not None:
                self._metrics.pop(name, None)
            else:
                self._metrics.clear()


# ---------------------------------------------------------------------------
# SLA thresholds (Requirements 7.2, 7.3, 7.4)
# ---------------------------------------------------------------------------

#: Operations and their maximum acceptable latency in milliseconds.
_SLA_THRESHOLDS_MS: dict[str, float] = {
    # Requirement 7.2 — message store: 100 ms
    "add_message": 100.0,
    "add_messages_batch": 200.0,
    # Requirement 7.3 — conversation list: 500 ms
    "list_conversations": 500.0,
    "search_conversations": 500.0,
    # Requirement 7.4 — cross-platform sync: 200 ms
    "cross_platform_sync": 200.0,
    # Smart conversation LLM calls — soft warning only
    "generate_title": 5000.0,
    "generate_summary": 10000.0,
    "analyse_conversations": 15000.0,
}


def _check_sla(name: str, duration_ms: float) -> None:
    """Log a warning when an operation exceeds its SLA threshold.

    Args:
        name: Operation identifier.
        duration_ms: Observed duration in milliseconds.
    """
    threshold = _SLA_THRESHOLDS_MS.get(name)
    if threshold is not None and duration_ms > threshold:
        logger.warning(
            "SLA breach detected",
            operation=name,
            duration_ms=round(duration_ms, 2),
            threshold_ms=threshold,
            overage_ms=round(duration_ms - threshold, 2),
        )


# ---------------------------------------------------------------------------
# Global tracker instance
# ---------------------------------------------------------------------------

#: Module-level singleton — import and use directly in services / routers.
tracker = PerformanceTracker()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


async def check_system_health(
    supabase_client: Any,
    *,
    check_tables: Optional[list[str]] = None,
) -> HealthStatus:
    """Run a lightweight health check across all critical components.

    Checks:
    - Database connectivity (Supabase table accessibility)
    - Performance metrics summary (error rates)

    Args:
        supabase_client: Initialised Supabase ``Client`` instance.
        check_tables: List of table names to probe.  Defaults to the four
            chat-persistence tables.

    Returns:
        :class:`HealthStatus` with per-component results.
    """
    if check_tables is None:
        check_tables = [
            "conversations",
            "conversation_messages",
            "user_platform_links",
            "conversation_tags",
        ]

    components: dict[str, dict[str, Any]] = {}
    all_healthy = True

    # ---- Database check --------------------------------------------------
    db_healthy = True
    db_details: dict[str, Any] = {}
    for table in check_tables:
        start = time.perf_counter()
        try:
            supabase_client.table(table).select("*", count="exact").limit(0).execute()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            db_details[table] = {"accessible": True, "latency_ms": latency_ms}
        except Exception as exc:
            db_details[table] = {"accessible": False, "error": str(exc)}
            db_healthy = False
            all_healthy = False

    components["database"] = {
        "healthy": db_healthy,
        "tables": db_details,
    }

    # ---- Metrics summary -------------------------------------------------
    all_metrics = tracker.get_all_metrics()
    high_error_ops = [
        name
        for name, m in all_metrics.items()
        if m.get("error_rate", 0) > 0.1 and m.get("call_count", 0) >= 10
    ]
    metrics_healthy = len(high_error_ops) == 0
    if not metrics_healthy:
        all_healthy = False

    components["metrics"] = {
        "healthy": metrics_healthy,
        "high_error_operations": high_error_ops,
        "total_operations_tracked": len(all_metrics),
    }

    status = HealthStatus(
        healthy=all_healthy,
        components=components,
    )

    log_fn = logger.info if all_healthy else logger.warning
    log_fn(
        "System health check complete",
        healthy=all_healthy,
        db_healthy=db_healthy,
        metrics_healthy=metrics_healthy,
    )

    return status
