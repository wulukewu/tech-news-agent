"""
Unit tests for LockManager service.

Tests the atomic notification locking functionality including lock acquisition,
release, and cleanup mechanisms.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import ServiceError
from app.services.lock_manager import LockManager, NotificationLock


class TestNotificationLock:
    """Test cases for NotificationLock class."""

    def test_create_lock(self):
        """Test creating a new notification lock."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()
        instance_id = "test_instance"
        ttl_minutes = 30

        lock = NotificationLock.create(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
            instance_id=instance_id,
            ttl_minutes=ttl_minutes,
        )

        assert lock.user_id == user_id
        assert lock.notification_type == notification_type
        assert lock.scheduled_time == scheduled_time
        assert lock.instance_id == instance_id
        assert lock.status == "pending"
        assert lock.expires_at is not None
        assert lock.expires_at > datetime.utcnow()

    def test_is_expired_false(self):
        """Test lock is not expired when within TTL."""
        lock = NotificationLock(
            id=uuid4(),
            user_id=uuid4(),
            notification_type="test",
            scheduled_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        assert not lock.is_expired()

    def test_is_expired_true(self):
        """Test lock is expired when past TTL."""
        lock = NotificationLock(
            id=uuid4(),
            user_id=uuid4(),
            notification_type="test",
            scheduled_time=datetime.utcnow(),
            expires_at=datetime.utcnow() - timedelta(minutes=10),
        )

        assert lock.is_expired()

    def test_is_expired_no_expiry(self):
        """Test lock without expiry time is not expired."""
        lock = NotificationLock(
            id=uuid4(),
            user_id=uuid4(),
            notification_type="test",
            scheduled_time=datetime.utcnow(),
            expires_at=None,
        )

        assert not lock.is_expired()

    def test_can_process_valid(self):
        """Test lock can be processed by correct instance."""
        instance_id = "test_instance"
        lock = NotificationLock(
            id=uuid4(),
            user_id=uuid4(),
            notification_type="test",
            scheduled_time=datetime.utcnow(),
            status="pending",
            instance_id=instance_id,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        assert lock.can_process(instance_id)

    def test_can_process_wrong_instance(self):
        """Test lock cannot be processed by wrong instance."""
        lock = NotificationLock(
            id=uuid4(),
            user_id=uuid4(),
            notification_type="test",
            scheduled_time=datetime.utcnow(),
            status="pending",
            instance_id="instance_1",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        assert not lock.can_process("instance_2")

    def test_can_process_wrong_status(self):
        """Test lock cannot be processed with wrong status."""
        instance_id = "test_instance"
        lock = NotificationLock(
            id=uuid4(),
            user_id=uuid4(),
            notification_type="test",
            scheduled_time=datetime.utcnow(),
            status="completed",
            instance_id=instance_id,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        assert not lock.can_process(instance_id)

    def test_can_process_expired(self):
        """Test expired lock cannot be processed."""
        instance_id = "test_instance"
        lock = NotificationLock(
            id=uuid4(),
            user_id=uuid4(),
            notification_type="test",
            scheduled_time=datetime.utcnow(),
            status="pending",
            instance_id=instance_id,
            expires_at=datetime.utcnow() - timedelta(minutes=10),
        )

        assert not lock.can_process(instance_id)


class TestLockManager:
    """Test cases for LockManager service."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Supabase client."""
        client = MagicMock()
        client.table.return_value = client
        return client

    @pytest.fixture
    def lock_manager(self, mock_client):
        """Create a LockManager instance with mocked client."""
        with patch.dict("os.environ", {"INSTANCE_ID": "test_instance"}):
            return LockManager(mock_client)

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, lock_manager, mock_client):
        """Test successful lock acquisition."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        # Mock successful database insert
        mock_response = MagicMock()
        mock_response.data = [{"id": str(uuid4())}]
        mock_client.insert.return_value.execute.return_value = mock_response

        lock = await lock_manager.acquire_notification_lock(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
        )

        assert lock is not None
        assert lock.user_id == user_id
        assert lock.notification_type == notification_type
        assert lock.scheduled_time == scheduled_time
        assert lock.instance_id == "test_instance"

        # Verify database call
        mock_client.table.assert_called_with("notification_locks")
        mock_client.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_lock_already_exists(self, lock_manager, mock_client):
        """Test lock acquisition when lock already exists."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        # Mock unique constraint violation
        mock_client.insert.return_value.execute.side_effect = Exception(
            "unique constraint violation"
        )

        lock = await lock_manager.acquire_notification_lock(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
        )

        assert lock is None

    @pytest.mark.asyncio
    async def test_acquire_lock_database_error(self, lock_manager, mock_client):
        """Test lock acquisition with database error."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        # Mock database error
        mock_client.insert.return_value.execute.side_effect = Exception(
            "database connection failed"
        )

        with pytest.raises(ServiceError):
            await lock_manager.acquire_notification_lock(
                user_id=user_id,
                notification_type=notification_type,
                scheduled_time=scheduled_time,
            )

    @pytest.mark.asyncio
    async def test_release_lock_success(self, lock_manager, mock_client):
        """Test successful lock release."""
        lock_id = uuid4()
        status = "completed"

        # Mock successful database update
        mock_response = MagicMock()
        mock_response.data = [{"id": str(lock_id)}]
        mock_client.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        await lock_manager.release_lock(lock_id, status)

        # Verify database call
        mock_client.table.assert_called_with("notification_locks")
        mock_client.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_release_lock_invalid_status(self, lock_manager, mock_client):
        """Test lock release with invalid status."""
        lock_id = uuid4()
        invalid_status = "invalid"

        with pytest.raises(ValueError, match="Invalid status"):
            await lock_manager.release_lock(lock_id, invalid_status)

    @pytest.mark.asyncio
    async def test_release_lock_not_found(self, lock_manager, mock_client):
        """Test lock release when lock not found."""
        lock_id = uuid4()
        status = "completed"

        # Mock no data returned (lock not found)
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Should not raise error, just log warning
        await lock_manager.release_lock(lock_id, status)

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks_success(self, lock_manager, mock_client):
        """Test successful cleanup of expired locks."""
        # Mock successful database delete
        mock_response = MagicMock()
        mock_response.data = [{"id": "lock1"}, {"id": "lock2"}]

        # Set up the mock chain properly
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_response
        mock_client.delete.return_value.lt.return_value = mock_query

        cleaned_count = await lock_manager.cleanup_expired_locks()

        assert cleaned_count == 2

        # Verify database call
        mock_client.table.assert_called_with("notification_locks")
        mock_client.delete.assert_called_once()
        mock_client.delete.return_value.lt.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks_none_found(self, lock_manager, mock_client):
        """Test cleanup when no expired locks found."""
        # Mock no data returned
        mock_response = MagicMock()
        mock_response.data = []

        # Set up the mock chain properly
        mock_query = MagicMock()
        mock_query.execute.return_value = mock_response
        mock_client.delete.return_value.lt.return_value = mock_query

        cleaned_count = await lock_manager.cleanup_expired_locks()

        assert cleaned_count == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks_database_error(self, lock_manager, mock_client):
        """Test cleanup with database error."""
        # Mock database error
        mock_query = MagicMock()
        mock_query.execute.side_effect = Exception("database error")
        mock_client.delete.return_value.lt.return_value = mock_query

        with pytest.raises(ServiceError):
            await lock_manager.cleanup_expired_locks()

    @pytest.mark.asyncio
    async def test_get_lock_status_found(self, lock_manager, mock_client):
        """Test getting lock status when lock exists."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        # Mock database response
        lock_data = {
            "id": str(uuid4()),
            "status": "pending",
            "instance_id": "test_instance",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        }
        mock_response = MagicMock()
        mock_response.data = [lock_data]
        mock_client.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        status = await lock_manager.get_lock_status(user_id, notification_type, scheduled_time)

        assert status is not None
        assert status["id"] == lock_data["id"]
        assert status["status"] == lock_data["status"]
        assert status["is_expired"] is False

    @pytest.mark.asyncio
    async def test_get_lock_status_not_found(self, lock_manager, mock_client):
        """Test getting lock status when lock doesn't exist."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        # Mock no data returned
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        status = await lock_manager.get_lock_status(user_id, notification_type, scheduled_time)

        assert status is None

    @pytest.mark.asyncio
    async def test_force_release_lock_success(self, lock_manager, mock_client):
        """Test successful force release of lock."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        # Mock successful database delete
        mock_response = MagicMock()
        mock_response.data = [{"id": str(uuid4())}]
        mock_client.delete.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        released = await lock_manager.force_release_lock(user_id, notification_type, scheduled_time)

        assert released is True

        # Verify database call
        mock_client.table.assert_called_with("notification_locks")
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_release_lock_not_found(self, lock_manager, mock_client):
        """Test force release when lock not found."""
        user_id = uuid4()
        notification_type = "weekly_digest"
        scheduled_time = datetime.utcnow()

        # Mock no data returned
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.delete.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        released = await lock_manager.force_release_lock(user_id, notification_type, scheduled_time)

        assert released is False

    @pytest.mark.asyncio
    async def test_get_lock_statistics_success(self, lock_manager, mock_client):
        """Test getting lock statistics."""
        # Mock database response with various lock statuses
        locks_data = [
            {
                "status": "pending",
                "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "status": "completed",
                "expires_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "status": "pending",
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            },
        ]
        mock_response = MagicMock()
        mock_response.data = locks_data
        mock_client.select.return_value.execute.return_value = mock_response

        stats = await lock_manager.get_lock_statistics()

        assert stats["total_locks"] == 3
        assert stats["by_status"]["pending"] == 2
        assert stats["by_status"]["completed"] == 1
        assert stats["expired_locks"] == 1
        assert stats["active_locks"] == 2
        assert stats["instance_id"] == "test_instance"

    @pytest.mark.asyncio
    async def test_get_lock_statistics_empty(self, lock_manager, mock_client):
        """Test getting lock statistics when no locks exist."""
        # Mock empty database response
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.select.return_value.execute.return_value = mock_response

        stats = await lock_manager.get_lock_statistics()

        assert stats["total_locks"] == 0
        assert stats["by_status"] == {}
        assert stats["expired_locks"] == 0
        assert stats["active_locks"] == 0

    def test_get_instance_id_from_env(self):
        """Test getting instance ID from environment variable."""
        with patch.dict("os.environ", {"INSTANCE_ID": "custom_instance"}):
            mock_client = MagicMock()
            manager = LockManager(mock_client)
            assert manager.instance_id == "custom_instance"

    def test_get_instance_id_generated(self):
        """Test generating instance ID when not in environment."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("os.getpid", return_value=12345):
                with patch("time.time", return_value=1234567890):
                    mock_client = MagicMock()
                    manager = LockManager(mock_client)
                    assert manager.instance_id == "instance_12345_1234567890"
