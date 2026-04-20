"""
Integration tests for LockManager service.

Tests the LockManager with real database operations to ensure atomic locking
works correctly in multi-instance scenarios.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import asyncio
import os
from datetime import datetime
from uuid import uuid4

import pytest

from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService


# Check if notification_locks table exists
def check_notification_locks_table_exists():
    """Check if notification_locks table exists in the database."""
    try:
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key or "dummy" in url.lower():
            return False

        client = create_client(url, key)
        client.table("notification_locks").select("id").limit(1).execute()
        return True
    except Exception:
        return False


# Skip all tests if notification_locks table doesn't exist
pytestmark = pytest.mark.skipif(
    not check_notification_locks_table_exists(),
    reason="notification_locks table not found. Apply migration 006_create_notification_locks_table.sql first.",
)


class TestLockManagerIntegration:
    """Integration tests for LockManager with real database operations."""

    @pytest.fixture
    async def lock_manager(self):
        """Create a LockManager instance with real Supabase client."""
        supabase_service = SupabaseService()
        return LockManager(supabase_service.client)

    @pytest.fixture
    async def second_lock_manager(self):
        """Create a second LockManager instance to simulate multi-instance scenario."""
        supabase_service = SupabaseService()
        # Override instance ID to simulate different instance
        manager = LockManager(supabase_service.client)
        manager.instance_id = "test_instance_2"
        return manager

    @pytest.mark.asyncio
    async def test_acquire_and_release_lock_integration(self, lock_manager):
        """Test acquiring and releasing a lock with real database operations."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        try:
            # Acquire lock
            lock = await lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock is not None
            assert lock.user_id == user_id
            assert lock.notification_type == notification_type
            assert lock.status == "pending"

            # Verify lock exists in database
            lock_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock_status is not None
            assert lock_status["status"] == "pending"
            assert lock_status["instance_id"] == lock_manager.instance_id

            # Release lock
            await lock_manager.release_lock(lock.id, "completed")

            # Verify lock status updated
            updated_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert updated_status is not None
            assert updated_status["status"] == "completed"

        finally:
            # Cleanup - force release any remaining locks
            await lock_manager.force_release_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

    @pytest.mark.asyncio
    async def test_duplicate_lock_prevention_integration(self, lock_manager, second_lock_manager):
        """Test that duplicate locks are prevented across multiple instances."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        try:
            # First instance acquires lock
            lock1 = await lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock1 is not None

            # Second instance tries to acquire same lock - should fail
            lock2 = await second_lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock2 is None

            # Verify only one lock exists
            lock_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock_status is not None
            assert lock_status["instance_id"] == lock_manager.instance_id

        finally:
            # Cleanup
            await lock_manager.force_release_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

    @pytest.mark.asyncio
    async def test_concurrent_lock_acquisition_integration(self, lock_manager, second_lock_manager):
        """Test concurrent lock acquisition attempts from multiple instances."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        async def acquire_lock(manager, instance_name):
            """Helper function to acquire lock and return result."""
            try:
                lock = await manager.acquire_notification_lock(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
                return instance_name, lock is not None
            except Exception as e:
                return instance_name, False

        try:
            # Attempt concurrent lock acquisition
            results = await asyncio.gather(
                acquire_lock(lock_manager, "instance_1"),
                acquire_lock(second_lock_manager, "instance_2"),
                return_exceptions=True,
            )

            # Exactly one should succeed
            successful_acquisitions = sum(1 for _, success in results if success)
            assert (
                successful_acquisitions == 1
            ), f"Expected 1 successful acquisition, got {successful_acquisitions}"

            # Verify lock exists
            lock_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock_status is not None
            assert lock_status["status"] == "pending"

        finally:
            # Cleanup
            await lock_manager.force_release_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

    @pytest.mark.asyncio
    async def test_lock_expiration_cleanup_integration(self, lock_manager):
        """Test cleanup of expired locks with real database operations."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        try:
            # Acquire lock with very short TTL
            lock = await lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
                ttl_minutes=0,  # Expires immediately
            )

            assert lock is not None

            # Wait a moment to ensure expiration
            await asyncio.sleep(0.1)

            # Run cleanup
            cleaned_count = await lock_manager.cleanup_expired_locks()

            assert cleaned_count >= 1

            # Verify lock was cleaned up
            lock_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock_status is None

        finally:
            # Cleanup any remaining locks
            await lock_manager.force_release_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

    @pytest.mark.asyncio
    async def test_lock_statistics_integration(self, lock_manager):
        """Test getting lock statistics with real database operations."""
        user_ids = [uuid4() for _ in range(3)]
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        acquired_locks = []

        try:
            # Acquire multiple locks
            for user_id in user_ids:
                lock = await lock_manager.acquire_notification_lock(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
                if lock:
                    acquired_locks.append(lock)

            # Release one lock as completed
            if acquired_locks:
                await lock_manager.release_lock(acquired_locks[0].id, "completed")

            # Get statistics
            stats = await lock_manager.get_lock_statistics()

            assert stats["total_locks"] >= len(acquired_locks)
            assert "by_status" in stats
            assert "expired_locks" in stats
            assert "active_locks" in stats
            assert stats["instance_id"] == lock_manager.instance_id

            # Should have at least one completed lock
            if "completed" in stats["by_status"]:
                assert stats["by_status"]["completed"] >= 1

        finally:
            # Cleanup all locks
            for user_id in user_ids:
                await lock_manager.force_release_lock(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )

    @pytest.mark.asyncio
    async def test_different_notification_types_integration(self, lock_manager):
        """Test that different notification types can have separate locks."""
        user_id = uuid4()
        scheduled_time = datetime.utcnow()
        notification_types = ["weekly_digest", "daily_summary", "monthly_report"]

        acquired_locks = []

        try:
            # Acquire locks for different notification types
            for notification_type in notification_types:
                lock = await lock_manager.acquire_notification_lock(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
                assert lock is not None
                acquired_locks.append((lock, notification_type))

            # Verify all locks exist independently
            for lock, notification_type in acquired_locks:
                lock_status = await lock_manager.get_lock_status(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
                assert lock_status is not None
                assert lock_status["status"] == "pending"

        finally:
            # Cleanup all locks
            for notification_type in notification_types:
                await lock_manager.force_release_lock(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )

    @pytest.mark.asyncio
    async def test_lock_ownership_enforcement_integration(self, lock_manager, second_lock_manager):
        """Test that only the owning instance can release a lock."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        try:
            # First instance acquires lock
            lock = await lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock is not None

            # Second instance tries to release the lock - should not affect it
            await second_lock_manager.release_lock(lock.id, "completed")

            # Verify lock is still pending (not released by wrong instance)
            lock_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock_status is not None
            assert lock_status["status"] == "pending"  # Should still be pending

            # First instance releases the lock - should succeed
            await lock_manager.release_lock(lock.id, "completed")

            # Verify lock is now completed
            updated_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert updated_status is not None
            assert updated_status["status"] == "completed"

        finally:
            # Cleanup
            await lock_manager.force_release_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

    @pytest.mark.asyncio
    async def test_force_release_lock_integration(self, lock_manager):
        """Test force releasing a lock (admin operation)."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        try:
            # Acquire lock
            lock = await lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock is not None

            # Verify lock exists
            lock_status = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock_status is not None

            # Force release lock
            released = await lock_manager.force_release_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert released is True

            # Verify lock is gone
            lock_status_after = await lock_manager.get_lock_status(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

            assert lock_status_after is None

        finally:
            # Cleanup (should be no-op since lock was force released)
            await lock_manager.force_release_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

    @pytest.mark.asyncio
    async def test_multiple_users_separate_locks_integration(self, lock_manager):
        """Test that different users can have separate locks for the same notification type."""
        user_ids = [uuid4() for _ in range(3)]
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        acquired_locks = []

        try:
            # Acquire locks for different users
            for user_id in user_ids:
                lock = await lock_manager.acquire_notification_lock(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
                assert lock is not None
                acquired_locks.append((lock, user_id))

            # Verify all locks exist independently
            for lock, user_id in acquired_locks:
                lock_status = await lock_manager.get_lock_status(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
                assert lock_status is not None
                assert lock_status["status"] == "pending"

            # Release one user's lock
            first_lock, first_user_id = acquired_locks[0]
            await lock_manager.release_lock(first_lock.id, "completed")

            # Verify only that user's lock was affected
            first_status = await lock_manager.get_lock_status(
                user_id=first_user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )
            assert first_status["status"] == "completed"

            # Other users' locks should still be pending
            for _, user_id in acquired_locks[1:]:
                lock_status = await lock_manager.get_lock_status(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
                assert lock_status["status"] == "pending"

        finally:
            # Cleanup all locks
            for _, user_id in acquired_locks:
                await lock_manager.force_release_lock(
                    user_id=user_id,
                    notification_type=notification_type,
                    scheduled_time=scheduled_time,
                )
