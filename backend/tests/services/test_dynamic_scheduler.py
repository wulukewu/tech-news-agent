"""
Tests for DynamicScheduler Service

This module contains unit tests for the DynamicScheduler class, testing
job scheduling, cancellation, rescheduling, and lifecycle management.

Requirements: 5.1, 5.2, 5.4, 5.5
"""

from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.repositories.user_notification_preferences import UserNotificationPreferences
from app.services.dynamic_scheduler import DynamicScheduler


@pytest.fixture
def mock_scheduler():
    """Create a mock APScheduler instance."""
    scheduler = MagicMock(spec=AsyncIOScheduler)
    scheduler.running = True
    scheduler.state = "running"
    return scheduler


@pytest.fixture
def dynamic_scheduler(mock_scheduler):
    """Create a DynamicScheduler instance with mocked dependencies."""
    return DynamicScheduler(scheduler=mock_scheduler)


@pytest.fixture
def sample_user_id():
    """Create a sample user ID."""
    return uuid4()


@pytest.fixture
def sample_preferences():
    """Create sample user notification preferences."""
    return UserNotificationPreferences(
        id=uuid4(),
        user_id=uuid4(),
        frequency="weekly",
        notification_time=time(18, 0),
        timezone="Asia/Taipei",
        dm_enabled=True,
        email_enabled=False,
    )


@pytest.fixture
def disabled_preferences():
    """Create disabled user notification preferences."""
    return UserNotificationPreferences(
        id=uuid4(),
        user_id=uuid4(),
        frequency="disabled",
        notification_time=time(18, 0),
        timezone="Asia/Taipei",
        dm_enabled=False,
        email_enabled=False,
    )


class TestDynamicScheduler:
    """Test cases for DynamicScheduler class."""

    @pytest.mark.asyncio
    async def test_schedule_user_notification_success(
        self, dynamic_scheduler, mock_scheduler, sample_user_id, sample_preferences
    ):
        """Test successful scheduling of user notification."""
        # Mock the get_next_notification_time method
        next_time = datetime(2024, 1, 5, 18, 0)  # Friday 6 PM
        with patch.object(dynamic_scheduler, "get_next_notification_time", return_value=next_time):
            # Mock scheduler methods
            mock_scheduler.get_job.return_value = None
            mock_scheduler.add_job = MagicMock()

            # Call the method
            await dynamic_scheduler.schedule_user_notification(sample_user_id, sample_preferences)

            # Verify scheduler interactions
            job_id = f"user_notification_{sample_user_id}"
            mock_scheduler.get_job.assert_called_once_with(job_id)
            mock_scheduler.add_job.assert_called_once()

            # Verify job parameters
            call_args = mock_scheduler.add_job.call_args
            assert call_args[1]["id"] == job_id
            assert call_args[1]["name"] == f"User Notification - {sample_user_id}"
            assert call_args[1]["args"] == [sample_user_id, sample_preferences]

    @pytest.mark.asyncio
    async def test_schedule_user_notification_disabled(
        self, dynamic_scheduler, mock_scheduler, sample_user_id, disabled_preferences
    ):
        """Test scheduling skipped for disabled notifications."""
        # Call the method with disabled preferences
        await dynamic_scheduler.schedule_user_notification(sample_user_id, disabled_preferences)

        # Verify no scheduler interactions
        mock_scheduler.get_job.assert_not_called()
        mock_scheduler.add_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_schedule_user_notification_replaces_existing(
        self, dynamic_scheduler, mock_scheduler, sample_user_id, sample_preferences
    ):
        """Test scheduling replaces existing job."""
        # Mock existing job
        existing_job = MagicMock()
        mock_scheduler.get_job.return_value = existing_job
        mock_scheduler.remove_job = MagicMock()
        mock_scheduler.add_job = MagicMock()

        # Mock the get_next_notification_time method
        next_time = datetime(2024, 1, 5, 18, 0)
        with patch.object(dynamic_scheduler, "get_next_notification_time", return_value=next_time):
            # Call the method
            await dynamic_scheduler.schedule_user_notification(sample_user_id, sample_preferences)

            # Verify existing job was removed
            job_id = f"user_notification_{sample_user_id}"
            mock_scheduler.remove_job.assert_called_once_with(job_id)
            mock_scheduler.add_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_user_notification_success(
        self, dynamic_scheduler, mock_scheduler, sample_user_id
    ):
        """Test successful cancellation of user notification."""
        # Mock existing job
        existing_job = MagicMock()
        mock_scheduler.get_job.return_value = existing_job
        mock_scheduler.remove_job = MagicMock()

        # Call the method
        await dynamic_scheduler.cancel_user_notification(sample_user_id)

        # Verify scheduler interactions
        job_id = f"user_notification_{sample_user_id}"
        mock_scheduler.get_job.assert_called_once_with(job_id)
        mock_scheduler.remove_job.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_cancel_user_notification_no_job(
        self, dynamic_scheduler, mock_scheduler, sample_user_id
    ):
        """Test cancellation when no job exists."""
        # Mock no existing job
        mock_scheduler.get_job.return_value = None
        mock_scheduler.remove_job = MagicMock()

        # Call the method
        await dynamic_scheduler.cancel_user_notification(sample_user_id)

        # Verify scheduler interactions
        job_id = f"user_notification_{sample_user_id}"
        mock_scheduler.get_job.assert_called_once_with(job_id)
        mock_scheduler.remove_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_reschedule_user_notification_success(
        self, dynamic_scheduler, sample_user_id, sample_preferences
    ):
        """Test successful rescheduling of user notification."""
        # Mock the cancel and schedule methods
        with (
            patch.object(dynamic_scheduler, "cancel_user_notification") as mock_cancel,
            patch.object(dynamic_scheduler, "schedule_user_notification") as mock_schedule,
        ):
            # Call the method
            await dynamic_scheduler.reschedule_user_notification(sample_user_id, sample_preferences)

            # Verify both methods were called
            mock_cancel.assert_called_once_with(sample_user_id)
            mock_schedule.assert_called_once_with(sample_user_id, sample_preferences)

    def test_get_next_notification_time_weekly(self, dynamic_scheduler, sample_preferences):
        """Test calculation of next notification time for weekly frequency."""
        with patch(
            "app.services.dynamic_scheduler.TimezoneConverter.get_next_notification_time"
        ) as mock_converter:
            expected_time = datetime(2024, 1, 5, 18, 0)
            mock_converter.return_value = expected_time

            # Call the method
            result = dynamic_scheduler.get_next_notification_time(sample_preferences)

            # Verify result
            assert result == expected_time
            mock_converter.assert_called_once_with(
                frequency="weekly", notification_time="18:00", timezone="Asia/Taipei"
            )

    def test_get_next_notification_time_disabled(self, dynamic_scheduler, disabled_preferences):
        """Test calculation returns None for disabled notifications."""
        with patch(
            "app.services.dynamic_scheduler.TimezoneConverter.get_next_notification_time"
        ) as mock_converter:
            mock_converter.return_value = None

            # Call the method
            result = dynamic_scheduler.get_next_notification_time(disabled_preferences)

            # Verify result
            assert result is None

    def test_get_next_notification_time_error(self, dynamic_scheduler, sample_preferences):
        """Test handling of errors in time calculation."""
        with patch(
            "app.services.dynamic_scheduler.TimezoneConverter.get_next_notification_time"
        ) as mock_converter:
            mock_converter.side_effect = ValueError("Invalid timezone")

            # Call the method
            result = dynamic_scheduler.get_next_notification_time(sample_preferences)

            # Verify result is None on error
            assert result is None

    @pytest.mark.asyncio
    async def test_send_user_notification_success(
        self, dynamic_scheduler, sample_user_id, sample_preferences
    ):
        """Test successful sending of user notification with lock mechanism."""
        with (
            patch("app.bot.client.bot") as mock_bot,
            patch(
                "app.services.dm_notification_service.DMNotificationService"
            ) as mock_dm_service_class,
            patch("app.services.lock_manager.LockManager") as mock_lock_manager_class,
            patch.object(dynamic_scheduler, "schedule_user_notification") as mock_schedule,
        ):
            # Mock bot and DM service
            mock_bot.is_ready.return_value = True
            mock_dm_service = AsyncMock()
            mock_dm_service.send_personalized_digest.return_value = True
            mock_dm_service_class.return_value = mock_dm_service

            # Mock lock manager
            mock_lock_manager = AsyncMock()
            mock_lock = MagicMock()
            mock_lock.id = uuid4()
            mock_lock_manager.acquire_notification_lock.return_value = mock_lock
            mock_lock_manager.release_lock = AsyncMock()
            mock_lock_manager.instance_id = "test_instance"
            mock_lock_manager_class.return_value = mock_lock_manager

            # Mock repository and preferences
            with (
                patch(
                    "app.repositories.user_notification_preferences.UserNotificationPreferencesRepository"
                ) as mock_repo_class,
                patch("app.services.supabase_service.SupabaseService") as mock_supabase_class,
            ):
                mock_repo = AsyncMock()
                mock_repo.get_by_user_id.return_value = sample_preferences
                mock_repo_class.return_value = mock_repo

                mock_supabase = MagicMock()
                mock_supabase_class.return_value = mock_supabase

                # Call the method
                await dynamic_scheduler._send_user_notification(sample_user_id, sample_preferences)

                # Verify lock was acquired
                mock_lock_manager.acquire_notification_lock.assert_called_once()

                # Verify DM service was called
                mock_dm_service.send_personalized_digest.assert_called_once_with(
                    str(sample_user_id)
                )

                # Verify lock was released as completed
                mock_lock_manager.release_lock.assert_called_once_with(mock_lock.id, "completed")

                # Verify rescheduling was attempted
                mock_schedule.assert_called_once_with(sample_user_id, sample_preferences)

    @pytest.mark.asyncio
    async def test_send_user_notification_lock_already_exists(
        self, dynamic_scheduler, sample_user_id, sample_preferences
    ):
        """Test notification skipped when lock already exists (duplicate prevention)."""
        with (
            patch("app.bot.client.bot") as mock_bot,
            patch(
                "app.services.dm_notification_service.DMNotificationService"
            ) as mock_dm_service_class,
            patch("app.services.lock_manager.LockManager") as mock_lock_manager_class,
            patch("app.services.supabase_service.SupabaseService") as mock_supabase_class,
        ):
            # Mock lock manager to return None (lock already exists)
            mock_lock_manager = AsyncMock()
            mock_lock_manager.acquire_notification_lock.return_value = None
            mock_lock_manager_class.return_value = mock_lock_manager

            mock_supabase = MagicMock()
            mock_supabase_class.return_value = mock_supabase

            # Mock DM service
            mock_dm_service = AsyncMock()
            mock_dm_service_class.return_value = mock_dm_service

            # Call the method
            await dynamic_scheduler._send_user_notification(sample_user_id, sample_preferences)

            # Verify lock acquisition was attempted
            mock_lock_manager.acquire_notification_lock.assert_called_once()

            # Verify DM service was NOT called (duplicate prevented)
            mock_dm_service.send_personalized_digest.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_user_notification_failure_releases_lock(
        self, dynamic_scheduler, sample_user_id, sample_preferences
    ):
        """Test lock is released as failed when notification sending fails."""
        with (
            patch("app.bot.client.bot") as mock_bot,
            patch(
                "app.services.dm_notification_service.DMNotificationService"
            ) as mock_dm_service_class,
            patch("app.services.lock_manager.LockManager") as mock_lock_manager_class,
            patch("app.services.supabase_service.SupabaseService") as mock_supabase_class,
        ):
            # Mock bot and DM service
            mock_bot.is_ready.return_value = True
            mock_dm_service = AsyncMock()
            mock_dm_service.send_personalized_digest.return_value = False  # Failure
            mock_dm_service_class.return_value = mock_dm_service

            # Mock lock manager
            mock_lock_manager = AsyncMock()
            mock_lock = MagicMock()
            mock_lock.id = uuid4()
            mock_lock_manager.acquire_notification_lock.return_value = mock_lock
            mock_lock_manager.release_lock = AsyncMock()
            mock_lock_manager.instance_id = "test_instance"
            mock_lock_manager_class.return_value = mock_lock_manager

            mock_supabase = MagicMock()
            mock_supabase_class.return_value = mock_supabase

            # Mock repository
            with patch(
                "app.repositories.user_notification_preferences.UserNotificationPreferencesRepository"
            ) as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_by_user_id.return_value = sample_preferences
                mock_repo_class.return_value = mock_repo

                # Call the method
                await dynamic_scheduler._send_user_notification(sample_user_id, sample_preferences)

                # Verify lock was acquired
                mock_lock_manager.acquire_notification_lock.assert_called_once()

                # Verify DM service was called
                mock_dm_service.send_personalized_digest.assert_called_once()

                # Verify lock was released as failed
                mock_lock_manager.release_lock.assert_called_once_with(mock_lock.id, "failed")

    @pytest.mark.asyncio
    async def test_send_user_notification_bot_not_ready(
        self, dynamic_scheduler, sample_user_id, sample_preferences
    ):
        """Test handling when bot is not ready."""
        with (
            patch("app.bot.client.bot") as mock_bot,
            patch("app.services.lock_manager.LockManager") as mock_lock_manager_class,
            patch("app.services.supabase_service.SupabaseService") as mock_supabase_class,
        ):
            mock_bot.is_ready.return_value = False

            # Mock lock manager
            mock_lock_manager = AsyncMock()
            mock_lock = MagicMock()
            mock_lock.id = uuid4()
            mock_lock_manager.acquire_notification_lock.return_value = mock_lock
            mock_lock_manager.release_lock = AsyncMock()
            mock_lock_manager_class.return_value = mock_lock_manager

            mock_supabase = MagicMock()
            mock_supabase_class.return_value = mock_supabase

            # Call the method
            await dynamic_scheduler._send_user_notification(sample_user_id, sample_preferences)

            # Verify lock was released as failed
            mock_lock_manager.release_lock.assert_called_once_with(mock_lock.id, "failed")

    @pytest.mark.asyncio
    async def test_get_user_job_info_exists(
        self, dynamic_scheduler, mock_scheduler, sample_user_id
    ):
        """Test getting job info when job exists."""
        # Mock existing job
        mock_job = MagicMock()
        mock_job.id = f"user_notification_{sample_user_id}"
        mock_job.name = f"User Notification - {sample_user_id}"
        mock_job.next_run_time = datetime(2024, 1, 5, 18, 0)
        mock_job.trigger = "DateTrigger"

        mock_scheduler.get_job.return_value = mock_job

        # Call the method
        result = await dynamic_scheduler.get_user_job_info(sample_user_id)

        # Verify result
        assert result is not None
        assert result["job_id"] == mock_job.id
        assert result["name"] == mock_job.name
        assert result["next_run_time"] == mock_job.next_run_time.isoformat()

    @pytest.mark.asyncio
    async def test_get_user_job_info_not_exists(
        self, dynamic_scheduler, mock_scheduler, sample_user_id
    ):
        """Test getting job info when job doesn't exist."""
        mock_scheduler.get_job.return_value = None

        # Call the method
        result = await dynamic_scheduler.get_user_job_info(sample_user_id)

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_jobs(self, dynamic_scheduler, mock_scheduler):
        """Test cleanup of expired notification jobs."""
        # Mock jobs
        user_job_1 = MagicMock()
        user_job_1.id = f"user_notification_{uuid4()}"

        user_job_2 = MagicMock()
        user_job_2.id = f"user_notification_{uuid4()}"

        other_job = MagicMock()
        other_job.id = "background_fetch"

        mock_scheduler.get_jobs.return_value = [user_job_1, user_job_2, other_job]
        mock_scheduler.remove_job = MagicMock()

        # Mock repository to return no preferences (expired jobs)
        with (
            patch(
                "app.repositories.user_notification_preferences.UserNotificationPreferencesRepository"
            ) as mock_repo_class,
            patch("app.services.supabase_service.SupabaseService") as mock_supabase_class,
        ):
            mock_repo = AsyncMock()
            mock_repo.get_by_user_id.return_value = None  # No preferences = expired
            mock_repo_class.return_value = mock_repo

            mock_supabase = MagicMock()
            mock_supabase_class.return_value = mock_supabase

            # Call the method
            result = await dynamic_scheduler.cleanup_expired_jobs()

            # Verify cleanup
            assert result == 2  # Two user jobs should be cleaned up
            assert mock_scheduler.remove_job.call_count == 2

    @pytest.mark.asyncio
    async def test_get_scheduler_stats(self, dynamic_scheduler, mock_scheduler):
        """Test getting scheduler statistics."""
        # Mock jobs
        user_job = MagicMock()
        user_job.id = f"user_notification_{uuid4()}"

        other_job = MagicMock()
        other_job.id = "background_fetch"

        mock_scheduler.get_jobs.return_value = [user_job, other_job]
        mock_scheduler.running = True
        mock_scheduler.state = "running"

        # Call the method
        result = await dynamic_scheduler.get_scheduler_stats()

        # Verify stats
        assert result["total_jobs"] == 2
        assert result["user_notification_jobs"] == 1
        assert result["scheduler_running"] is True
        assert result["scheduler_state"] == "running"


class TestDynamicSchedulerIntegration:
    """Integration tests for DynamicScheduler with real APScheduler."""

    @pytest.fixture
    def real_scheduler(self):
        """Create a real APScheduler instance for integration tests."""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        scheduler = AsyncIOScheduler(event_loop=loop)
        scheduler.start()
        yield scheduler
        scheduler.shutdown()
        loop.close()

    @pytest.fixture
    def integration_scheduler(self, real_scheduler):
        """Create a DynamicScheduler with real APScheduler."""
        return DynamicScheduler(scheduler=real_scheduler)

    @pytest.mark.asyncio
    async def test_real_scheduler_integration(
        self, integration_scheduler, sample_user_id, sample_preferences
    ):
        """Test integration with real APScheduler."""
        # Mock the get_next_notification_time to return a near-future time
        future_time = datetime.now().replace(microsecond=0)
        future_time = future_time.replace(second=future_time.second + 2)  # 2 seconds from now

        with patch.object(
            integration_scheduler, "get_next_notification_time", return_value=future_time
        ):
            # Schedule a notification
            await integration_scheduler.schedule_user_notification(
                sample_user_id, sample_preferences
            )

            # Verify job was created
            job_info = await integration_scheduler.get_user_job_info(sample_user_id)
            assert job_info is not None
            assert job_info["job_id"] == f"user_notification_{sample_user_id}"

            # Cancel the notification
            await integration_scheduler.cancel_user_notification(sample_user_id)

            # Verify job was removed
            job_info = await integration_scheduler.get_user_job_info(sample_user_id)
            assert job_info is None
