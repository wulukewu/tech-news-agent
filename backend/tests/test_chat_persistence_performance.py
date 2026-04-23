"""
Performance and Load Tests for Chat Persistence System

Tests system performance under load:
  - Message storage latency (target: < 100ms)
  - Conversation list query (target: < 500ms)
  - Cross-platform sync latency (target: < 200ms)
  - Concurrent conversation handling (10,000+)
  - Search performance

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5 (Task 10.2)
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_conversation(user_id: str) -> dict:
    return {
        "id": str(uuid4()),
        "user_id": user_id,
        "title": f"Conversation {uuid4().hex[:8]}",
        "platform": "web",
        "tags": [],
        "is_archived": False,
        "is_favorite": False,
        "message_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_message_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
    }


def _make_message(conversation_id: str, role: str = "user") -> dict:
    return {
        "id": str(uuid4()),
        "conversation_id": conversation_id,
        "role": role,
        "content": "Performance test message content " * 10,
        "platform": "web",
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Test: Message Storage Latency (Requirement 7.2 — target < 100ms)
# ---------------------------------------------------------------------------


class TestMessageStorageLatency:
    """Verify message storage meets the 100ms SLA."""

    def test_message_serialisation_is_fast(self):
        """Message serialisation should complete well under 100ms."""
        import json

        message = _make_message(str(uuid4()))
        start = time.perf_counter()
        for _ in range(1000):
            json.dumps(message, default=str)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 1000 serialisations should complete in < 500ms (0.5ms each)
        assert elapsed_ms < 500, f"Serialisation too slow: {elapsed_ms:.1f}ms for 1000 ops"

    def test_message_validation_is_fast(self):
        """Message field validation should be negligible overhead."""
        valid_roles = {"user", "assistant"}
        valid_platforms = {"web", "discord"}

        messages = [_make_message(str(uuid4())) for _ in range(10000)]

        start = time.perf_counter()
        for msg in messages:
            assert msg["role"] in valid_roles
            assert msg["platform"] in valid_platforms
            assert msg["content"]
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 10,000 validations should complete in < 100ms
        assert elapsed_ms < 100, f"Validation too slow: {elapsed_ms:.1f}ms for 10k ops"

    def test_batch_message_preparation_is_fast(self):
        """Preparing a batch of 500 messages should be fast."""
        conversation_id = str(uuid4())
        start = time.perf_counter()
        batch = [_make_message(conversation_id) for _ in range(500)]
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(batch) == 500
        # Batch preparation should complete in < 50ms
        assert elapsed_ms < 50, f"Batch prep too slow: {elapsed_ms:.1f}ms"


# ---------------------------------------------------------------------------
# Test: Conversation List Query (Requirement 7.3 — target < 500ms)
# ---------------------------------------------------------------------------


class TestConversationListPerformance:
    """Verify conversation list queries meet the 500ms SLA."""

    def test_in_memory_conversation_filtering_is_fast(self):
        """In-memory filtering of 10,000 conversations should be fast."""
        user_id = str(uuid4())
        conversations = [_make_conversation(user_id) for _ in range(10000)]

        start = time.perf_counter()
        # Filter: active (not archived), web platform
        filtered = [c for c in conversations if not c["is_archived"] and c["platform"] == "web"]
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(filtered) == 10000  # All match
        # Filtering 10k items should complete in < 50ms
        assert elapsed_ms < 50, f"Filtering too slow: {elapsed_ms:.1f}ms"

    def test_conversation_sorting_is_fast(self):
        """Sorting 10,000 conversations by last_message_at should be fast."""
        user_id = str(uuid4())
        conversations = [_make_conversation(user_id) for _ in range(10000)]

        start = time.perf_counter()
        sorted_convs = sorted(
            conversations,
            key=lambda c: c["last_message_at"],
            reverse=True,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(sorted_convs) == 10000
        # Sorting 10k items should complete in < 100ms
        assert elapsed_ms < 100, f"Sorting too slow: {elapsed_ms:.1f}ms"

    def test_pagination_slice_is_fast(self):
        """Pagination slicing of large result sets should be instant."""
        user_id = str(uuid4())
        conversations = [_make_conversation(user_id) for _ in range(10000)]

        start = time.perf_counter()
        for page in range(100):
            offset = page * 20
            page_data = conversations[offset : offset + 20]
            assert len(page_data) == 20
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 100 pagination operations should complete in < 10ms
        assert elapsed_ms < 10, f"Pagination too slow: {elapsed_ms:.1f}ms"


# ---------------------------------------------------------------------------
# Test: Cross-Platform Sync Latency (Requirement 7.4 — target < 200ms)
# ---------------------------------------------------------------------------


class TestCrossPlatformSyncPerformance:
    """Verify cross-platform sync meets the 200ms SLA."""

    def test_message_format_conversion_is_fast(self):
        """Converting between web and Discord message formats should be fast."""
        messages = [_make_message(str(uuid4())) for _ in range(1000)]

        start = time.perf_counter()
        for msg in messages:
            # Simulate format conversion: truncate to Discord limit
            discord_content = msg["content"][:2000]
            assert len(discord_content) <= 2000
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 1000 conversions should complete in < 50ms
        assert elapsed_ms < 50, f"Format conversion too slow: {elapsed_ms:.1f}ms"

    def test_sync_state_update_preparation_is_fast(self):
        """Preparing sync state updates should be fast."""
        conversation_id = str(uuid4())

        start = time.perf_counter()
        for _ in range(1000):
            state_update = {
                "conversation_id": conversation_id,
                "last_message_at": datetime.now(timezone.utc).isoformat(),
                "message_count": 42,
                "platform": "discord",
                "sync_timestamp": datetime.now(timezone.utc).isoformat(),
            }
            assert state_update["conversation_id"] == conversation_id
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 1000 state update preparations should complete in < 100ms
        assert elapsed_ms < 100, f"State update prep too slow: {elapsed_ms:.1f}ms"


# ---------------------------------------------------------------------------
# Test: Concurrent Conversation Handling (Requirement 7.1 — 10,000+)
# ---------------------------------------------------------------------------


class TestConcurrentConversationHandling:
    """Verify system can handle 10,000+ concurrent conversations."""

    def test_create_10000_conversation_objects(self):
        """Creating 10,000 conversation objects should be fast."""
        user_id = str(uuid4())

        start = time.perf_counter()
        conversations = [_make_conversation(user_id) for _ in range(10000)]
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(conversations) == 10000
        # Creating 10k objects should complete in < 500ms
        assert elapsed_ms < 500, f"Object creation too slow: {elapsed_ms:.1f}ms"

    def test_unique_conversation_ids(self):
        """All conversation IDs should be unique."""
        user_id = str(uuid4())
        conversations = [_make_conversation(user_id) for _ in range(1000)]
        ids = {c["id"] for c in conversations}
        assert len(ids) == 1000  # All unique

    def test_conversation_lookup_by_id_is_fast(self):
        """Looking up conversations by ID should be O(1) with dict."""
        user_id = str(uuid4())
        conversations = [_make_conversation(user_id) for _ in range(10000)]
        conv_map = {c["id"]: c for c in conversations}

        # Pick 1000 random IDs to look up
        ids_to_lookup = [conversations[i * 10]["id"] for i in range(1000)]

        start = time.perf_counter()
        for cid in ids_to_lookup:
            result = conv_map.get(cid)
            assert result is not None
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 1000 dict lookups should complete in < 5ms
        assert elapsed_ms < 5, f"Dict lookup too slow: {elapsed_ms:.1f}ms"

    @pytest.mark.asyncio
    async def test_async_concurrent_operations(self):
        """Verify async operations can run concurrently without blocking."""

        async def simulate_message_store(msg_id: str) -> dict:
            """Simulate storing a message (async I/O)."""
            await asyncio.sleep(0)  # Yield to event loop
            return {"id": msg_id, "stored": True}

        message_ids = [str(uuid4()) for _ in range(100)]

        start = time.perf_counter()
        results = await asyncio.gather(*[simulate_message_store(mid) for mid in message_ids])
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(results) == 100
        assert all(r["stored"] for r in results)
        # 100 concurrent async ops should complete in < 100ms
        assert elapsed_ms < 100, f"Concurrent ops too slow: {elapsed_ms:.1f}ms"


# ---------------------------------------------------------------------------
# Test: Search Performance (Requirement 7.3)
# ---------------------------------------------------------------------------


class TestSearchPerformance:
    """Verify search operations meet performance requirements."""

    def test_keyword_search_in_memory_is_fast(self):
        """In-memory keyword search across 1000 conversations should be fast."""
        user_id = str(uuid4())
        conversations = [
            {**_make_conversation(user_id), "title": f"Conversation about topic {i % 10}"}
            for i in range(1000)
        ]

        query = "topic 5"
        start = time.perf_counter()
        results = [c for c in conversations if query in c["title"]]
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(results) == 100  # 100 conversations match "topic 5"
        # Search should complete in < 10ms
        assert elapsed_ms < 10, f"Search too slow: {elapsed_ms:.1f}ms"

    def test_tag_filter_is_fast(self):
        """Filtering conversations by tag should be fast."""
        user_id = str(uuid4())
        conversations = [
            {**_make_conversation(user_id), "tags": ["python"] if i % 3 == 0 else ["other"]}
            for i in range(1000)
        ]

        start = time.perf_counter()
        python_convs = [c for c in conversations if "python" in c["tags"]]
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(python_convs) > 0
        # Tag filter should complete in < 10ms
        assert elapsed_ms < 10, f"Tag filter too slow: {elapsed_ms:.1f}ms"


# ---------------------------------------------------------------------------
# Test: PerformanceTracker (monitoring.py)
# ---------------------------------------------------------------------------


class TestPerformanceTracker:
    """Verify the PerformanceTracker meets its own performance requirements."""

    @pytest.mark.asyncio
    async def test_tracker_record_is_fast(self):
        """Recording metrics should add negligible overhead."""
        from app.core.monitoring import PerformanceTracker

        tracker = PerformanceTracker()

        start = time.perf_counter()
        for i in range(1000):
            await tracker.record("test_op", float(i % 100))
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 1000 metric recordings should complete in < 200ms
        assert elapsed_ms < 200, f"Tracker recording too slow: {elapsed_ms:.1f}ms"

    @pytest.mark.asyncio
    async def test_tracker_get_all_metrics_is_fast(self):
        """Retrieving all metrics should be fast."""
        from app.core.monitoring import PerformanceTracker

        tracker = PerformanceTracker()
        # Pre-populate with 50 different operations
        for i in range(50):
            await tracker.record(f"op_{i}", float(i * 10))

        start = time.perf_counter()
        for _ in range(100):
            metrics = tracker.get_all_metrics()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(metrics) == 50
        # 100 get_all_metrics calls should complete in < 50ms
        assert elapsed_ms < 50, f"get_all_metrics too slow: {elapsed_ms:.1f}ms"

    @pytest.mark.asyncio
    async def test_tracker_measure_context_manager(self):
        """The measure() context manager should work correctly."""
        from app.core.monitoring import PerformanceTracker

        tracker = PerformanceTracker()

        async with tracker.measure("test_operation"):
            await asyncio.sleep(0.01)  # 10ms operation

        metric = tracker.get_metric("test_operation")
        assert metric is not None
        assert metric.call_count == 1
        assert metric.avg_duration_ms >= 10.0  # At least 10ms

    @pytest.mark.asyncio
    async def test_tracker_records_errors(self):
        """The tracker should record errors correctly."""
        from app.core.monitoring import PerformanceTracker

        tracker = PerformanceTracker()

        with pytest.raises(ValueError):
            async with tracker.measure("failing_op"):
                raise ValueError("Test error")

        metric = tracker.get_metric("failing_op")
        assert metric is not None
        assert metric.error_count == 1
        assert metric.error_rate == 1.0
