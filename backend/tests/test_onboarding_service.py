"""
Unit tests for OnboardingService

Tests the core functionality of the OnboardingService class including:
- Getting onboarding status
- Updating onboarding progress
- Marking onboarding as completed
- Marking onboarding as skipped
- Resetting onboarding state
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import DatabaseError, ServiceError
from app.repositories.user_preferences import UserPreferences, UserPreferencesRepository
from app.schemas.onboarding import OnboardingStatus
from app.services.onboarding_service import OnboardingService


@pytest.fixture
def mock_user_preferences_repo():
    """Create a mock UserPreferencesRepository"""
    return AsyncMock(spec=UserPreferencesRepository)


@pytest.fixture
def onboarding_service(mock_user_preferences_repo):
    """Create an OnboardingService instance with mock repository"""
    return OnboardingService(mock_user_preferences_repo)


class TestGetOnboardingStatus:
    """Tests for get_onboarding_status method"""

    @pytest.mark.asyncio
    async def test_get_status_existing_user(self, onboarding_service, mock_user_preferences_repo):
        """Test getting status for user with existing preferences"""
        user_id = uuid4()

        # Mock repository response
        from app.repositories.user_preferences import UserPreferences

        mock_prefs = UserPreferences(
            user_id=user_id,
            onboarding_completed=False,
            onboarding_step="welcome",
            onboarding_skipped=False,
            tooltip_tour_completed=False,
        )
        mock_user_preferences_repo.get_by_user_id.return_value = mock_prefs

        # Execute
        status = await onboarding_service.get_onboarding_status(user_id)

        # Verify
        assert isinstance(status, OnboardingStatus)
        assert status.onboarding_completed is False
        assert status.onboarding_step == "welcome"
        assert status.onboarding_skipped is False
        assert status.tooltip_tour_completed is False

    @pytest.mark.asyncio
    async def test_get_status_new_user_creates_default(
        self, onboarding_service, mock_user_preferences_repo
    ):
        """Test getting status for new user creates default preferences"""
        user_id = uuid4()

        # Mock repository to return None (no preferences exist)
        mock_user_preferences_repo.get_by_user_id.return_value = None
        mock_user_preferences_repo.create.return_value = None

        # Execute
        status = await onboarding_service.get_onboarding_status(user_id)

        # Verify default status returned
        assert isinstance(status, OnboardingStatus)
        assert status.onboarding_completed is False
        assert status.onboarding_step is None
        assert status.onboarding_skipped is False
        assert status.tooltip_tour_completed is False

        # Verify create was called
        mock_user_preferences_repo.create.assert_called_once()


class TestUpdateOnboardingProgress:
    """Tests for update_onboarding_progress method"""

    @pytest.mark.asyncio
    async def test_update_progress_success(self, onboarding_service, mock_user_preferences_repo):
        """Test successfully updating onboarding progress"""
        user_id = uuid4()
        step = "recommendations"

        # Mock existing preferences
        mock_prefs = UserPreferences(
            user_id=user_id,
            onboarding_started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_user_preferences_repo.get_by_user_id.return_value = mock_prefs
        mock_user_preferences_repo.update_by_user_id.return_value = mock_prefs

        # Execute
        await onboarding_service.update_onboarding_progress(user_id, step, True)

        # Verify update was called
        mock_user_preferences_repo.update_by_user_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_progress_sets_started_at_for_first_step(
        self, onboarding_service, mock_user_preferences_repo
    ):
        """Test that first step update sets onboarding_started_at"""
        user_id = uuid4()

        # Mock existing preferences without started_at
        mock_prefs = UserPreferences(
            user_id=user_id,
            onboarding_started_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_user_preferences_repo.get_by_user_id.return_value = mock_prefs
        mock_user_preferences_repo.update_by_user_id.return_value = mock_prefs

        # Execute
        await onboarding_service.update_onboarding_progress(user_id, "welcome", True)

        # Verify update was called
        mock_user_preferences_repo.update_by_user_id.assert_called_once()


class TestMarkOnboardingCompleted:
    """Tests for mark_onboarding_completed method"""

    @pytest.mark.asyncio
    async def test_mark_completed_success(self, onboarding_service, mock_user_preferences_repo):
        """Test successfully marking onboarding as completed"""
        user_id = uuid4()

        # Mock existing preferences
        mock_prefs = UserPreferences(
            user_id=user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_user_preferences_repo.get_by_user_id.return_value = mock_prefs
        mock_user_preferences_repo.update_by_user_id.return_value = mock_prefs

        # Execute
        await onboarding_service.mark_onboarding_completed(user_id)

        # Verify update was called
        mock_user_preferences_repo.update_by_user_id.assert_called_once()


class TestMarkOnboardingSkipped:
    """Tests for mark_onboarding_skipped method"""

    @pytest.mark.asyncio
    async def test_mark_skipped_success(self, onboarding_service, mock_user_preferences_repo):
        """Test successfully marking onboarding as skipped"""
        user_id = uuid4()

        # Mock existing preferences
        mock_prefs = UserPreferences(
            user_id=user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_user_preferences_repo.get_by_user_id.return_value = mock_prefs
        mock_user_preferences_repo.update_by_user_id.return_value = mock_prefs

        # Execute
        await onboarding_service.mark_onboarding_skipped(user_id)

        # Verify update was called
        mock_user_preferences_repo.update_by_user_id.assert_called_once()


class TestResetOnboarding:
    """Tests for reset_onboarding method"""

    @pytest.mark.asyncio
    async def test_reset_onboarding_success(self, onboarding_service, mock_user_preferences_repo):
        """Test successfully resetting onboarding state"""
        user_id = uuid4()

        # Mock existing preferences
        mock_prefs = UserPreferences(
            user_id=user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_user_preferences_repo.get_by_user_id.return_value = mock_prefs
        mock_user_preferences_repo.update_by_user_id.return_value = mock_prefs

        # Execute
        await onboarding_service.reset_onboarding(user_id)

        # Verify update was called
        mock_user_preferences_repo.update_by_user_id.assert_called_once()


class TestErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_get_status_database_error(self, onboarding_service, mock_user_preferences_repo):
        """Test error handling when database query fails"""
        user_id = uuid4()

        # Mock database error
        mock_user_preferences_repo.get_by_user_id.side_effect = DatabaseError("Database error")

        # Execute and verify exception
        with pytest.raises((ServiceError, DatabaseError)):
            await onboarding_service.get_onboarding_status(user_id)

    @pytest.mark.asyncio
    async def test_update_progress_database_error(
        self, onboarding_service, mock_user_preferences_repo
    ):
        """Test error handling when update fails"""
        user_id = uuid4()

        # Mock database error
        mock_user_preferences_repo.get_by_user_id.side_effect = DatabaseError("Database error")

        # Execute and verify exception
        with pytest.raises((ServiceError, DatabaseError)):
            await onboarding_service.update_onboarding_progress(user_id, "welcome", True)
