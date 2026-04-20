"""
Property-based test for Atomic Notification Locking
Task 3.4

This module tests Property 6: Atomic Notification Locking
For any notification attempt across multiple backend instances, the system SHALL use
atomic database operations to create locks, prevent duplicate notifications, update
completion status, and handle lock expiration to prevent deadlocks.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
"""

import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from app.services.lock_manager import LockManager, NotificationLock


# Test data generators
@st.composite
def notification_data(draw):
    """Generate valid notification data for testing."""
    return {
        "user_id": draw(st.uuids()),
        "notification_type": draw(
            st.sampled_from(
                [
                    "weekly_digest",
                    "daily_summary",
                    "monthly_report",
                    "breaking_news",
                    "custom_alert",
                    "system_notification",
                ]
            )
        ),
        "scheduled_time": draw(
            st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2025, 12, 31))
        ),
        "ttl_minutes": draw(st.integers(min_value=1, max_value=120)),
    }


@st.composite
def instance_ids(draw):
    """Generate realistic backend instance IDs."""
    return draw(
        st.one_of(
            st.text(
                min_size=5,
                max_size=50,
                alphabet=st.characters(
                    min_codepoint=48, max_codepoint=122, blacklist_characters=" \n\r\t"
                ),
            ),
            st.builds(lambda: f"instance_{os.getpid()}_{int(datetime.now().timestamp())}"),
        )
    )


class MockSupabaseClient:
    """Mock Supabase client for testing atomic operations."""

    def __init__(self):
        self.locks_storage = {}  # Simulates database storage
        self.operation_count = 0
        self.insert_failures = []  # Track which operations should fail

    def table(self, table_name):
        """Return a mock table interface."""
        return MockTable(self, table_name)

    def reset(self):
        """Reset mock state."""
        self.locks_storage.clear()
        self.operation_count = 0
        self.insert_failures.clear()

    def simulate_concurrent_insert_failure(self, operation_number):
        """Simulate a concurrent insert failure at specific operation."""
        self.insert_failures.append(operation_number)


class MockTable:
    """Mock table interface for database operations."""

    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self._insert_data = None
        self._update_data = None
        self._delete_conditions = []
        self._select_fields = "*"
        self._where_conditions = []

    def insert(self, data):
        """Mock insert operation."""
        self._insert_data = data
        return self

    def update(self, data):
        """Mock update operation."""
        self._update_data = data
        return self

    def delete(self):
        """Mock delete operation."""
        return self

    def select(self, fields):
        """Mock select operation."""
        self._select_fields = fields
        return self

    def eq(self, field, value):
        """Mock equality condition."""
        self._where_conditions.append((field, "eq", value))
        return self

    def lt(self, field, value):
        """Mock less than condition."""
        self._where_conditions.append((field, "lt", value))
        return self

    def execute(self):
        """Execute the mocked operation."""
        self.client.operation_count += 1

        if self._insert_data:
            return self._execute_insert()
        elif self._update_data:
            return self._execute_update()
        elif self._delete_conditions or any(cond[1] == "lt" for cond in self._where_conditions):
            return self._execute_delete()
        else:
            return self._execute_select()

    def _execute_insert(self):
        """Execute insert operation with atomic behavior simulation."""
        # Simulate unique constraint violation for concurrent inserts
        if self.client.operation_count in self.client.insert_failures:
            raise Exception("duplicate key value violates unique constraint")

        # Create unique key for lock
        user_id = self._insert_data["user_id"]
        notification_type = self._insert_data["notification_type"]
        scheduled_time = self._insert_data["scheduled_time"]
        lock_key = f"{user_id}_{notification_type}_{scheduled_time}"

        # Check if lock already exists (atomic check)
        if lock_key in self.client.locks_storage:
            raise Exception("duplicate key value violates unique constraint")

        # Store the lock
        self.client.locks_storage[lock_key] = self._insert_data.copy()

        return Mock(data=[self._insert_data])

    def _execute_update(self):
        """Execute update operation."""
        updated_records = []
        for key, lock_data in self.client.locks_storage.items():
            # Check all where conditions
            matches = True
            for field, op, value in self._where_conditions:
                if op == "eq" and str(lock_data.get(field)) != str(value):
                    matches = False
                    break

            if matches:
                lock_data.update(self._update_data)
                updated_records.append(lock_data.copy())

        return Mock(data=updated_records)

    def _execute_delete(self):
        """Execute delete operation."""
        deleted_records = []
        keys_to_delete = []

        for key, lock_data in self.client.locks_storage.items():
            should_delete = True

            # Check where conditions
            for field, op, value in self._where_conditions:
                if op == "eq" and str(lock_data.get(field)) != str(value):
                    should_delete = False
                    break
                elif op == "lt":
                    # For expires_at comparison
                    if field == "expires_at":
                        lock_expires = datetime.fromisoformat(
                            lock_data[field].replace("Z", "+00:00")
                        )
                        compare_time = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        if lock_expires.replace(tzinfo=None) >= compare_time.replace(tzinfo=None):
                            should_delete = False
                            break

            if should_delete:
                deleted_records.append(lock_data.copy())
                keys_to_delete.append(key)

        # Remove deleted records
        for key in keys_to_delete:
            del self.client.locks_storage[key]

        return Mock(data=deleted_records)

    def _execute_select(self):
        """Execute select operation."""
        matching_records = []

        for lock_data in self.client.locks_storage.values():
            matches = True
            for field, op, value in self._where_conditions:
                if op == "eq" and str(lock_data.get(field)) != str(value):
                    matches = False
                    break

            if matches:
                matching_records.append(lock_data.copy())

        return Mock(data=matching_records)


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for testing."""
    return MockSupabaseClient()


@pytest.fixture
def lock_manager(mock_supabase_client):
    """Create a LockManager with mock client."""
    with patch.dict(os.environ, {"INSTANCE_ID": "test_instance_123"}):
        return LockManager(mock_supabase_client)


# Feature: personalized-notification-frequency, Property 6: Atomic Notification Locking
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=notification_data())
@pytest.mark.asyncio
async def test_atomic_lock_acquisition_property(lock_manager, mock_supabase_client, data):
    """
    **Validates: Requirements 10.1, 10.2**

    Property 6: For any notification attempt, the system SHALL use atomic database
    operations to create locks and prevent duplicate notifications.

    This property ensures that:
    1. Lock acquisition is atomic (either succeeds completely or fails completely)
    2. Duplicate lock attempts for the same notification are prevented
    3. Lock data is stored correctly with all required fields
    4. Instance ID is properly tracked for multi-instance coordination
    """
    user_id = data["user_id"]
    notification_type = data["notification_type"]
    scheduled_time = data["scheduled_time"]
    ttl_minutes = data["ttl_minutes"]

    # Reset mock state
    mock_supabase_client.reset()

    # Test atomic lock acquisition
    lock = await lock_manager.acquire_notification_lock(
        user_id=user_id,
        notification_type=notification_type,
        scheduled_time=scheduled_time,
        ttl_minutes=ttl_minutes,
    )

    # Verify lock was created successfully
    assert lock is not None, "Lock should be acquired successfully"
    assert isinstance(lock, NotificationLock), "Should return NotificationLock instance"

    # Verify lock properties
    assert (
        lock.user_id == user_id
    ), f"Lock user_id should match: expected {user_id}, got {lock.user_id}"
    assert (
        lock.notification_type == notification_type
    ), f"Lock notification_type should match: expected {notification_type}, got {lock.notification_type}"
    assert (
        lock.scheduled_time == scheduled_time
    ), f"Lock scheduled_time should match: expected {scheduled_time}, got {lock.scheduled_time}"
    assert lock.status == "pending", f"Lock status should be 'pending', got {lock.status}"
    assert (
        lock.instance_id == "test_instance_123"
    ), f"Lock instance_id should match, got {lock.instance_id}"

    # Verify expiration time is set correctly
    expected_expires_at = lock.created_at + timedelta(minutes=ttl_minutes)
    time_diff = abs((lock.expires_at - expected_expires_at).total_seconds())
    assert time_diff < 1, "Lock expiration should be set correctly within 1 second tolerance"

    # Verify lock is stored in mock database
    lock_key = f"{user_id}_{notification_type}_{scheduled_time.isoformat()}"
    assert lock_key in mock_supabase_client.locks_storage, "Lock should be stored in database"

    stored_lock = mock_supabase_client.locks_storage[lock_key]
    assert stored_lock["user_id"] == str(user_id), "Stored lock should have correct user_id"
    assert (
        stored_lock["notification_type"] == notification_type
    ), "Stored lock should have correct notification_type"
    assert stored_lock["status"] == "pending", "Stored lock should have pending status"


# Feature: personalized-notification-frequency, Property 6: Atomic Notification Locking (Duplicate Prevention)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=notification_data())
@pytest.mark.asyncio
async def test_atomic_duplicate_prevention_property(lock_manager, mock_supabase_client, data):
    """
    **Validates: Requirements 10.2, 10.4**

    Property 6: For any notification attempt, if another backend instance attempts
    to send the same notification, the system SHALL detect the existing lock and
    skip duplicate processing.

    This property ensures that:
    1. Duplicate lock acquisition attempts return None
    2. Original lock remains unchanged
    3. Atomic operations prevent race conditions
    4. Multiple instances coordinate correctly
    """
    user_id = data["user_id"]
    notification_type = data["notification_type"]
    scheduled_time = data["scheduled_time"]
    ttl_minutes = data["ttl_minutes"]

    # Reset mock state
    mock_supabase_client.reset()

    # First instance acquires lock
    first_lock = await lock_manager.acquire_notification_lock(
        user_id=user_id,
        notification_type=notification_type,
        scheduled_time=scheduled_time,
        ttl_minutes=ttl_minutes,
    )

    assert first_lock is not None, "First lock acquisition should succeed"

    # Create second lock manager (simulating different instance)
    with patch.dict(os.environ, {"INSTANCE_ID": "test_instance_456"}):
        second_lock_manager = LockManager(mock_supabase_client)

        # Second instance attempts to acquire same lock
        second_lock = await second_lock_manager.acquire_notification_lock(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
            ttl_minutes=ttl_minutes,
        )

        # Verify duplicate is prevented
        assert second_lock is None, "Second lock acquisition should fail (duplicate prevention)"

    # Verify original lock is unchanged
    lock_key = f"{user_id}_{notification_type}_{scheduled_time.isoformat()}"
    stored_lock = mock_supabase_client.locks_storage[lock_key]
    assert (
        stored_lock["instance_id"] == "test_instance_123"
    ), "Original lock should retain first instance ID"
    assert stored_lock["status"] == "pending", "Original lock status should remain unchanged"

    # Verify only one lock exists in storage
    assert len(mock_supabase_client.locks_storage) == 1, "Only one lock should exist in storage"


# Feature: personalized-notification-frequency, Property 6: Atomic Notification Locking (Status Updates)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=notification_data(), final_status=st.sampled_from(["completed", "failed"]))
@pytest.mark.asyncio
async def test_atomic_status_update_property(
    lock_manager, mock_supabase_client, data, final_status
):
    """
    **Validates: Requirements 10.3**

    Property 6: When notification processing completes, the system SHALL update
    the notification status atomically to reflect completion or failure.

    This property ensures that:
    1. Lock status can be updated atomically
    2. Only the owning instance can update the lock
    3. Status updates are properly validated
    4. Lock state transitions are consistent
    """
    user_id = data["user_id"]
    notification_type = data["notification_type"]
    scheduled_time = data["scheduled_time"]
    ttl_minutes = data["ttl_minutes"]

    # Reset mock state
    mock_supabase_client.reset()

    # Acquire lock
    lock = await lock_manager.acquire_notification_lock(
        user_id=user_id,
        notification_type=notification_type,
        scheduled_time=scheduled_time,
        ttl_minutes=ttl_minutes,
    )

    assert lock is not None, "Lock should be acquired successfully"

    # Update lock status
    await lock_manager.release_lock(lock.id, status=final_status)

    # Verify status was updated in storage
    lock_key = f"{user_id}_{notification_type}_{scheduled_time.isoformat()}"
    stored_lock = mock_supabase_client.locks_storage[lock_key]
    assert stored_lock["status"] == final_status, f"Lock status should be updated to {final_status}"

    # Verify updated_at timestamp was set
    assert "updated_at" in stored_lock, "Lock should have updated_at timestamp"

    # Test that different instance cannot update the lock
    with patch.dict(os.environ, {"INSTANCE_ID": "different_instance_789"}):
        different_lock_manager = LockManager(mock_supabase_client)

        # Attempt to update from different instance should not affect the lock
        await different_lock_manager.release_lock(lock.id, status="failed")

        # Verify lock status remains unchanged (only owning instance can update)
        updated_stored_lock = mock_supabase_client.locks_storage[lock_key]
        assert (
            updated_stored_lock["status"] == final_status
        ), "Lock status should not change from different instance"


# Feature: personalized-notification-frequency, Property 6: Atomic Notification Locking (Expiration Handling)
@hypothesis_settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=notification_data(), expired_locks_count=st.integers(min_value=1, max_value=10))
@pytest.mark.asyncio
async def test_atomic_lock_expiration_property(
    lock_manager, mock_supabase_client, data, expired_locks_count
):
    """
    **Validates: Requirements 10.5**

    Property 6: The system SHALL set notification lock expiration times and
    provide cleanup mechanisms to prevent deadlocks.

    This property ensures that:
    1. Locks have proper expiration times
    2. Expired locks can be cleaned up atomically
    3. Cleanup operations remove only expired locks
    4. Active locks are preserved during cleanup
    """
    user_id = data["user_id"]
    notification_type = data["notification_type"]
    scheduled_time = data["scheduled_time"]

    # Reset mock state
    mock_supabase_client.reset()

    # Create multiple locks with different expiration times
    active_locks = []
    expired_locks = []

    # Create expired locks (TTL of 0 minutes = immediate expiration)
    for i in range(expired_locks_count):
        expired_user_id = uuid4()
        expired_lock = await lock_manager.acquire_notification_lock(
            user_id=expired_user_id,
            notification_type=f"{notification_type}_expired_{i}",
            scheduled_time=scheduled_time,
            ttl_minutes=0,  # Immediate expiration
        )
        if expired_lock:
            expired_locks.append(expired_lock)

    # Create active locks (longer TTL)
    for i in range(2):
        active_user_id = uuid4()
        active_lock = await lock_manager.acquire_notification_lock(
            user_id=active_user_id,
            notification_type=f"{notification_type}_active_{i}",
            scheduled_time=scheduled_time,
            ttl_minutes=60,  # 1 hour TTL
        )
        if active_lock:
            active_locks.append(active_lock)

    # Verify locks were created
    total_expected = expired_locks_count + 2
    assert (
        len(mock_supabase_client.locks_storage) == total_expected
    ), f"Should have {total_expected} locks in storage"

    # Wait a moment to ensure expired locks are actually expired
    await asyncio.sleep(0.1)

    # Cleanup expired locks
    cleaned_count = await lock_manager.cleanup_expired_locks()

    # Verify cleanup results
    assert (
        cleaned_count == expired_locks_count
    ), f"Should clean up {expired_locks_count} expired locks, got {cleaned_count}"

    # Verify only active locks remain
    remaining_locks = len(mock_supabase_client.locks_storage)
    assert remaining_locks == 2, f"Should have 2 active locks remaining, got {remaining_locks}"

    # Verify active locks are still present and valid
    for active_lock in active_locks:
        lock_key = f"{active_lock.user_id}_{active_lock.notification_type}_{active_lock.scheduled_time.isoformat()}"
        assert (
            lock_key in mock_supabase_client.locks_storage
        ), f"Active lock {lock_key} should still exist"

        stored_lock = mock_supabase_client.locks_storage[lock_key]
        assert stored_lock["status"] == "pending", "Active lock should maintain pending status"


# Feature: personalized-notification-frequency, Property 6: Atomic Notification Locking (Concurrent Operations)
@hypothesis_settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=notification_data(), concurrent_instances=st.integers(min_value=2, max_value=5))
@pytest.mark.asyncio
async def test_atomic_concurrent_operations_property(
    mock_supabase_client, data, concurrent_instances
):
    """
    **Validates: Requirements 10.1, 10.2, 10.4**

    Property 6: For any notification attempt with multiple concurrent backend
    instances, atomic operations SHALL ensure only one instance successfully
    acquires the lock while others are properly rejected.

    This property ensures that:
    1. Concurrent lock attempts are handled atomically
    2. Only one instance succeeds in acquiring the lock
    3. Race conditions are prevented through database constraints
    4. All instances receive appropriate responses
    """
    user_id = data["user_id"]
    notification_type = data["notification_type"]
    scheduled_time = data["scheduled_time"]
    ttl_minutes = data["ttl_minutes"]

    # Reset mock state
    mock_supabase_client.reset()

    # Simulate concurrent insert failures for all but the first operation
    for i in range(2, concurrent_instances + 1):
        mock_supabase_client.simulate_concurrent_insert_failure(i)

    # Create multiple lock managers (simulating different instances)
    lock_managers = []
    for i in range(concurrent_instances):
        with patch.dict(os.environ, {"INSTANCE_ID": f"concurrent_instance_{i}"}):
            manager = LockManager(mock_supabase_client)
            lock_managers.append(manager)

    # Attempt concurrent lock acquisition
    tasks = []
    for manager in lock_managers:
        task = manager.acquire_notification_lock(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
            ttl_minutes=ttl_minutes,
        )
        tasks.append(task)

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Analyze results
    successful_locks = [r for r in results if isinstance(r, NotificationLock)]
    failed_attempts = [r for r in results if r is None]
    exceptions = [r for r in results if isinstance(r, Exception)]

    # Verify exactly one lock succeeded
    assert (
        len(successful_locks) == 1
    ), f"Exactly one lock should succeed, got {len(successful_locks)} successful locks"

    # Verify other attempts were properly rejected
    expected_failures = concurrent_instances - 1
    actual_failures = len(failed_attempts) + len(exceptions)
    assert (
        actual_failures == expected_failures
    ), f"Expected {expected_failures} failures, got {actual_failures}"

    # Verify the successful lock has correct properties
    successful_lock = successful_locks[0]
    assert successful_lock.user_id == user_id, "Successful lock should have correct user_id"
    assert (
        successful_lock.notification_type == notification_type
    ), "Successful lock should have correct notification_type"
    assert (
        successful_lock.scheduled_time == scheduled_time
    ), "Successful lock should have correct scheduled_time"
    assert successful_lock.status == "pending", "Successful lock should have pending status"

    # Verify only one lock exists in storage
    assert (
        len(mock_supabase_client.locks_storage) == 1
    ), "Only one lock should exist in storage after concurrent attempts"


# Feature: personalized-notification-frequency, Property 6: Atomic Notification Locking (Lock Statistics)
@hypothesis_settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    locks_data=st.lists(notification_data(), min_size=1, max_size=10),
    status_distribution=st.lists(
        st.sampled_from(["pending", "completed", "failed"]), min_size=1, max_size=10
    ),
)
@pytest.mark.asyncio
async def test_atomic_lock_statistics_property(
    lock_manager, mock_supabase_client, locks_data, status_distribution
):
    """
    **Validates: Requirements 10.1, 10.2, 10.3, 10.5**

    Property 6: The system SHALL provide accurate statistics about notification
    locks including counts by status, expiration tracking, and instance coordination.

    This property ensures that:
    1. Lock statistics accurately reflect database state
    2. Status counts are correctly calculated
    3. Expiration tracking works properly
    4. Statistics include instance identification
    """
    # Reset mock state
    mock_supabase_client.reset()

    # Create locks with various statuses
    created_locks = []
    expected_status_counts = {}

    for i, (lock_data, status) in enumerate(zip(locks_data, status_distribution)):
        # Create unique notification type to avoid conflicts
        unique_notification_type = f"{lock_data['notification_type']}_{i}"

        # Acquire lock
        lock = await lock_manager.acquire_notification_lock(
            user_id=lock_data["user_id"],
            notification_type=unique_notification_type,
            scheduled_time=lock_data["scheduled_time"],
            ttl_minutes=lock_data["ttl_minutes"],
        )

        if lock:
            created_locks.append(lock)

            # Update status if not pending
            if status != "pending":
                await lock_manager.release_lock(lock.id, status=status)

            # Track expected counts
            expected_status_counts[status] = expected_status_counts.get(status, 0) + 1

    # Get lock statistics
    stats = await lock_manager.get_lock_statistics()

    # Verify statistics structure
    assert isinstance(stats, dict), "Statistics should be a dictionary"
    assert "total_locks" in stats, "Statistics should include total_locks"
    assert "by_status" in stats, "Statistics should include by_status breakdown"
    assert "expired_locks" in stats, "Statistics should include expired_locks count"
    assert "active_locks" in stats, "Statistics should include active_locks count"
    assert "instance_id" in stats, "Statistics should include instance_id"

    # Verify total count
    assert stats["total_locks"] == len(
        created_locks
    ), f"Total locks should be {len(created_locks)}, got {stats['total_locks']}"

    # Verify status counts
    for status, expected_count in expected_status_counts.items():
        actual_count = stats["by_status"].get(status, 0)
        assert (
            actual_count == expected_count
        ), f"Status '{status}' should have {expected_count} locks, got {actual_count}"

    # Verify instance ID
    assert (
        stats["instance_id"] == "test_instance_123"
    ), f"Instance ID should match, got {stats['instance_id']}"

    # Verify expired vs active counts sum to total
    total_by_expiration = stats["expired_locks"] + stats["active_locks"]
    assert (
        total_by_expiration == stats["total_locks"]
    ), f"Expired + active should equal total: {total_by_expiration} != {stats['total_locks']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
