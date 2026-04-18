"""
Integration Tests for Service Layer

Task 5.4: Write integration tests for service layer

These tests verify that services work correctly with real repository implementations,
testing:
- Service methods with real repository implementations
- Error handling and logging integration
- Transaction boundaries
- Cross-repository operations

Requirements: 3.3, 4.4, 5.3
"""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from supabase import Client

from app.core.errors import DatabaseError, ServiceError
from app.repositories.analytics_event import AnalyticsEventRepository
from app.repositories.feed import FeedRepository
from app.repositories.user_preferences import UserPreferencesRepository
from app.repositories.user_subscription import UserSubscriptionRepository
from app.services.analytics_service import AnalyticsService
from app.services.onboarding_service import OnboardingService
from app.services.subscription_service import SubscriptionService

# Skip all tests if database is not available
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or "dummy" in os.getenv("SUPABASE_URL", "").lower(),
    reason="Database not available for integration tests",
)


class TestSubscriptionServiceIntegration:
    """
    Integration tests for SubscriptionService with real repositories.

    Tests service methods with actual database operations to verify:
    - Correct repository usage
    - Error handling
    - Logging integration
    - Business logic execution
    """

    @pytest.fixture
    def subscription_service(self, test_supabase_client: Client):
        """Create SubscriptionService with real repositories."""
        feed_repo = FeedRepository(test_supabase_client)
        user_subscription_repo = UserSubscriptionRepository(test_supabase_client)
        return SubscriptionService(feed_repo, user_subscription_repo)

    @pytest.mark.asyncio
    async def test_batch_subscribe_success(
        self, subscription_service, test_supabase_client, test_user, test_feed
    ):
        """
        Test successful batch subscription with real repositories.

        Validates: Requirements 3.3 (service calls repository methods)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        feed_ids = [UUID(test_feed["id"])]

        # Act
        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        # Assert
        assert result.subscribed_count == 1
        assert result.failed_count == 0
        assert len(result.errors) == 0

        # Verify subscription was created in database
        response = (
            test_supabase_client.table("user_subscriptions")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("feed_id", str(feed_ids[0]))
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["user_id"] == str(user_id)
        assert response.data[0]["feed_id"] == str(feed_ids[0])

    @pytest.mark.asyncio
    async def test_batch_subscribe_idempotent(
        self, subscription_service, test_supabase_client, test_user, test_feed
    ):
        """
        Test that batch_subscribe is idempotent (subscribing twice succeeds).

        Validates: Requirements 3.3 (service handles business logic correctly)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        feed_ids = [UUID(test_feed["id"])]

        # Act - Subscribe twice
        result1 = await subscription_service.batch_subscribe(user_id, feed_ids)
        result2 = await subscription_service.batch_subscribe(user_id, feed_ids)

        # Assert - Both should succeed
        assert result1.subscribed_count == 1
        assert result2.subscribed_count == 1

        # Verify only one subscription exists
        response = (
            test_supabase_client.table("user_subscriptions")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("feed_id", str(feed_ids[0]))
            .execute()
        )

        assert len(response.data) == 1

    @pytest.mark.asyncio
    async def test_batch_subscribe_partial_failure(
        self, subscription_service, test_supabase_client, test_user, test_feed
    ):
        """
        Test batch_subscribe with partial failures (some feeds don't exist).

        Validates: Requirements 3.3, 4.4 (error handling in services)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        valid_feed_id = UUID(test_feed["id"])
        invalid_feed_id = uuid4()  # Non-existent feed
        feed_ids = [valid_feed_id, invalid_feed_id]

        # Act
        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        # Assert
        assert result.subscribed_count == 1  # Only valid feed subscribed
        assert result.failed_count == 1  # Invalid feed failed
        assert len(result.errors) == 1
        assert str(invalid_feed_id) in result.errors[0]

    @pytest.mark.asyncio
    async def test_batch_subscribe_empty_list(self, subscription_service, test_user):
        """
        Test batch_subscribe with empty feed list.

        Validates: Requirements 3.3 (service handles edge cases)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        feed_ids = []

        # Act
        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        # Assert
        assert result.subscribed_count == 0
        assert result.failed_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_batch_subscribe_logging(self, subscription_service, test_user, test_feed):
        """
        Test that batch_subscribe logs operations correctly.

        Validates: Requirements 5.3 (logging in backend services)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        feed_ids = [UUID(test_feed["id"])]

        # Act - Patch logger to capture log calls
        with patch.object(subscription_service.logger, "info") as mock_info:
            await subscription_service.batch_subscribe(user_id, feed_ids)

            # Assert - Verify logging occurred
            assert mock_info.call_count >= 2  # Start and completion logs

            # Check that logs include context
            calls = [str(call) for call in mock_info.call_args_list]
            log_output = " ".join(calls)
            assert "batch subscription" in log_output.lower()


class TestOnboardingServiceIntegration:
    """
    Integration tests for OnboardingService with real repositories.

    Tests service methods with actual database operations.
    """

    @pytest.fixture
    def onboarding_service(self, test_supabase_client: Client):
        """Create OnboardingService with real repository."""
        user_preferences_repo = UserPreferencesRepository(test_supabase_client)
        return OnboardingService(user_preferences_repo)

    @pytest.mark.asyncio
    async def test_get_onboarding_status_creates_default(
        self, onboarding_service, test_supabase_client, test_user
    ):
        """
        Test that get_onboarding_status creates default preferences if none exist.

        Validates: Requirements 3.3 (service orchestrates repository operations)
        """
        # Arrange
        user_id = UUID(test_user["id"])

        # Act
        status = await onboarding_service.get_onboarding_status(user_id)

        # Assert
        assert status.onboarding_completed is False
        assert status.onboarding_step is None
        assert status.onboarding_skipped is False
        assert status.should_show_onboarding is True

        # Verify preferences were created in database
        response = (
            test_supabase_client.table("user_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["user_id"] == str(user_id)

    @pytest.mark.asyncio
    async def test_update_onboarding_progress(
        self, onboarding_service, test_supabase_client, test_user
    ):
        """
        Test updating onboarding progress updates database correctly.

        Validates: Requirements 3.3 (service calls repository methods)
        """
        # Arrange
        user_id = UUID(test_user["id"])

        # Create initial preferences
        await onboarding_service.get_onboarding_status(user_id)

        # Act
        await onboarding_service.update_onboarding_progress(user_id, "welcome", True)

        # Assert - Verify database was updated
        response = (
            test_supabase_client.table("user_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["onboarding_step"] == "welcome"
        assert response.data[0]["onboarding_started_at"] is not None

    @pytest.mark.asyncio
    async def test_mark_onboarding_completed(
        self, onboarding_service, test_supabase_client, test_user
    ):
        """
        Test marking onboarding as completed.

        Validates: Requirements 3.3 (service handles business logic)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        await onboarding_service.get_onboarding_status(user_id)

        # Act
        await onboarding_service.mark_onboarding_completed(user_id)

        # Assert
        response = (
            test_supabase_client.table("user_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["onboarding_completed"] is True
        assert response.data[0]["onboarding_step"] == "complete"
        assert response.data[0]["onboarding_completed_at"] is not None

    @pytest.mark.asyncio
    async def test_mark_onboarding_skipped(
        self, onboarding_service, test_supabase_client, test_user
    ):
        """
        Test marking onboarding as skipped.

        Validates: Requirements 3.3 (service handles business logic)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        await onboarding_service.get_onboarding_status(user_id)

        # Act
        await onboarding_service.mark_onboarding_skipped(user_id)

        # Assert
        response = (
            test_supabase_client.table("user_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(response.data) == 1
        assert response.data[0]["onboarding_skipped"] is True

    @pytest.mark.asyncio
    async def test_reset_onboarding(self, onboarding_service, test_supabase_client, test_user):
        """
        Test resetting onboarding state.

        Validates: Requirements 3.3 (service orchestrates complex operations)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        await onboarding_service.get_onboarding_status(user_id)
        await onboarding_service.mark_onboarding_completed(user_id)

        # Act
        await onboarding_service.reset_onboarding(user_id)

        # Assert
        response = (
            test_supabase_client.table("user_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(response.data) == 1
        prefs = response.data[0]
        assert prefs["onboarding_completed"] is False
        assert prefs["onboarding_step"] is None
        assert prefs["onboarding_skipped"] is False
        assert prefs["onboarding_started_at"] is None
        assert prefs["onboarding_completed_at"] is None

    @pytest.mark.asyncio
    async def test_onboarding_service_error_handling(
        self, onboarding_service, test_supabase_client
    ):
        """
        Test error handling when database operations fail.

        Validates: Requirements 4.4 (error handler logs errors with severity)
        """
        # Arrange - Use invalid user_id that will cause database error
        invalid_user_id = uuid4()

        # Create preferences first
        test_supabase_client.table("user_preferences").insert(
            {"user_id": str(invalid_user_id)}
        ).execute()

        # Act & Assert - Patch repository to simulate database error
        with patch.object(
            onboarding_service.user_preferences_repo,
            "update_by_user_id",
            side_effect=DatabaseError(
                "Database connection failed", error_code="DB_CONNECTION_FAILED"
            ),
        ):
            with pytest.raises(ServiceError) as exc_info:
                await onboarding_service.mark_onboarding_completed(invalid_user_id)

            # Verify error was wrapped correctly
            assert "Failed to mark onboarding as completed" in str(exc_info.value)

        # Cleanup
        test_supabase_client.table("user_preferences").delete().eq(
            "user_id", str(invalid_user_id)
        ).execute()

    @pytest.mark.asyncio
    async def test_onboarding_service_logging_with_context(self, onboarding_service, test_user):
        """
        Test that service logs include request context.

        Validates: Requirements 5.3 (logger includes request context)
        """
        # Arrange
        user_id = UUID(test_user["id"])

        # Act - Patch logger to capture log calls
        with patch.object(onboarding_service.logger, "info") as mock_info:
            await onboarding_service.get_onboarding_status(user_id)

            # Assert - Verify logging includes user_id context
            assert mock_info.call_count >= 1

            # Check that logs include user_id
            for call in mock_info.call_args_list:
                args, kwargs = call
                if "user_id" in kwargs:
                    assert kwargs["user_id"] == str(user_id)
                    break
            else:
                pytest.fail("No log call included user_id context")


class TestAnalyticsServiceIntegration:
    """
    Integration tests for AnalyticsService with real repositories.

    Tests service methods with actual database operations.
    """

    @pytest.fixture
    def analytics_service(self, test_supabase_client: Client):
        """Create AnalyticsService with real repository."""
        analytics_event_repo = AnalyticsEventRepository(test_supabase_client)
        return AnalyticsService(analytics_event_repo)

    @pytest.mark.asyncio
    async def test_log_event(self, analytics_service, test_supabase_client, test_user):
        """
        Test logging analytics events to database.

        Validates: Requirements 3.3 (service calls repository methods)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        event_type = "onboarding_started"
        event_data = {"step": "welcome"}

        # Act
        await analytics_service.log_event(user_id, event_type, event_data)

        # Assert - Verify event was created in database
        response = (
            test_supabase_client.table("analytics_events")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("event_type", event_type)
            .execute()
        )

        assert len(response.data) >= 1
        event = response.data[0]
        assert event["user_id"] == str(user_id)
        assert event["event_type"] == event_type
        assert event["event_data"] == event_data

        # Cleanup
        test_supabase_client.table("analytics_events").delete().eq("id", event["id"]).execute()

    @pytest.mark.asyncio
    async def test_get_onboarding_completion_rate(
        self, analytics_service, test_supabase_client, test_user
    ):
        """
        Test calculating onboarding completion rate.

        Validates: Requirements 3.3 (service orchestrates repository operations)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        start_date = datetime.now(UTC) - timedelta(days=1)
        end_date = datetime.now(UTC) + timedelta(days=1)

        # Create test events
        await analytics_service.log_event(user_id, "onboarding_started", {})
        await analytics_service.log_event(user_id, "onboarding_finished", {})

        # Act
        result = await analytics_service.get_onboarding_completion_rate(start_date, end_date)

        # Assert
        assert result.total_users >= 1
        assert result.completed_users >= 1
        assert result.completion_rate > 0

        # Cleanup
        test_supabase_client.table("analytics_events").delete().eq(
            "user_id", str(user_id)
        ).execute()

    @pytest.mark.asyncio
    async def test_get_drop_off_rates(self, analytics_service, test_supabase_client, test_user):
        """
        Test calculating drop-off rates by step.

        Validates: Requirements 3.3 (service handles complex queries)
        """
        # Arrange
        user_id = UUID(test_user["id"])

        # Create test events
        await analytics_service.log_event(user_id, "onboarding_started", {})
        await analytics_service.log_event(user_id, "step_completed", {"step": "welcome"})

        # Act
        result = await analytics_service.get_drop_off_rates()

        # Assert
        assert result.total_started >= 1
        assert isinstance(result.drop_off_by_step, dict)

        # Cleanup
        test_supabase_client.table("analytics_events").delete().eq(
            "user_id", str(user_id)
        ).execute()

    @pytest.mark.asyncio
    async def test_get_average_time_per_step(
        self, analytics_service, test_supabase_client, test_user
    ):
        """
        Test calculating average time per step.

        Validates: Requirements 3.3 (service aggregates data correctly)
        """
        # Arrange
        user_id = UUID(test_user["id"])

        # Create test events with time data
        await analytics_service.log_event(
            user_id, "step_completed", {"step": "welcome", "time_spent_seconds": 30}
        )
        await analytics_service.log_event(
            user_id, "step_completed", {"step": "welcome", "time_spent_seconds": 40}
        )

        # Act
        result = await analytics_service.get_average_time_per_step()

        # Assert
        assert result.total_completions >= 2
        assert isinstance(result.average_time_by_step, dict)
        if "welcome" in result.average_time_by_step:
            assert result.average_time_by_step["welcome"] > 0

        # Cleanup
        test_supabase_client.table("analytics_events").delete().eq(
            "user_id", str(user_id)
        ).execute()

    @pytest.mark.asyncio
    async def test_analytics_service_error_handling(self, analytics_service, test_user):
        """
        Test error handling in analytics service.

        Validates: Requirements 4.4 (error handler logs errors)
        """
        # Arrange
        user_id = UUID(test_user["id"])

        # Act & Assert - Patch repository to simulate database error
        with patch.object(
            analytics_service.analytics_event_repo,
            "create",
            side_effect=DatabaseError("Database write failed", error_code="DB_WRITE_FAILED"),
        ):
            with pytest.raises(ServiceError) as exc_info:
                await analytics_service.log_event(user_id, "test_event", {})

            # Verify error was wrapped correctly
            assert "Failed to log analytics event" in str(exc_info.value)


class TestServiceLayerTransactionBoundaries:
    """
    Tests for transaction boundaries and cross-repository operations.

    These tests verify that services correctly handle operations that span
    multiple repositories and maintain data consistency.
    """

    @pytest.fixture
    def subscription_service(self, test_supabase_client: Client):
        """Create SubscriptionService with real repositories."""
        feed_repo = FeedRepository(test_supabase_client)
        user_subscription_repo = UserSubscriptionRepository(test_supabase_client)
        return SubscriptionService(feed_repo, user_subscription_repo)

    @pytest.mark.asyncio
    async def test_batch_subscribe_transaction_consistency(
        self, subscription_service, test_supabase_client, test_user, test_feed
    ):
        """
        Test that batch_subscribe maintains consistency across operations.

        Validates: Requirements 3.3 (service handles transaction boundaries)
        """
        # Arrange
        user_id = UUID(test_user["id"])
        feed_ids = [UUID(test_feed["id"])]

        # Act - Subscribe
        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        # Assert - Verify consistency
        assert result.subscribed_count == 1

        # Verify subscription exists
        sub_response = (
            test_supabase_client.table("user_subscriptions")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(sub_response.data) == 1

        # Verify feed still exists and is unchanged
        feed_response = (
            test_supabase_client.table("feeds").select("*").eq("id", str(feed_ids[0])).execute()
        )

        assert len(feed_response.data) == 1

    @pytest.mark.asyncio
    async def test_service_operations_are_isolated(self, test_supabase_client, test_user):
        """
        Test that service operations don't interfere with each other.

        Validates: Requirements 3.3 (services maintain isolation)
        """
        # Arrange
        user_id = UUID(test_user["id"])

        onboarding_service = OnboardingService(UserPreferencesRepository(test_supabase_client))
        analytics_service = AnalyticsService(AnalyticsEventRepository(test_supabase_client))

        # Act - Perform operations in both services
        await onboarding_service.get_onboarding_status(user_id)
        await analytics_service.log_event(user_id, "test_event", {})

        # Assert - Verify both operations succeeded independently
        prefs_response = (
            test_supabase_client.table("user_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        events_response = (
            test_supabase_client.table("analytics_events")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(prefs_response.data) == 1
        assert len(events_response.data) >= 1

        # Cleanup
        test_supabase_client.table("analytics_events").delete().eq(
            "user_id", str(user_id)
        ).execute()


class TestServiceLayerLoggingIntegration:
    """
    Tests for logging integration across service layer.

    Validates that services properly integrate with centralized logging
    and include appropriate context in log messages.
    """

    @pytest.mark.asyncio
    async def test_service_logs_include_operation_context(
        self, test_supabase_client, test_user, test_feed
    ):
        """
        Test that service logs include operation context.

        Validates: Requirements 5.3 (logger includes request context)
        """
        # Arrange
        subscription_service = SubscriptionService(
            FeedRepository(test_supabase_client), UserSubscriptionRepository(test_supabase_client)
        )
        user_id = UUID(test_user["id"])
        feed_ids = [UUID(test_feed["id"])]

        # Act - Patch logger to capture log calls
        with (
            patch.object(subscription_service.logger, "info") as mock_info,
            patch.object(subscription_service.logger, "debug") as mock_debug,
        ):
            await subscription_service.batch_subscribe(user_id, feed_ids)

            # Assert - Verify logs include context
            all_calls = mock_info.call_args_list + mock_debug.call_args_list

            # Check that at least one log includes user_id
            found_user_context = False
            for call in all_calls:
                args, kwargs = call
                if "user_id" in kwargs:
                    assert kwargs["user_id"] == str(user_id)
                    found_user_context = True
                    break

            assert found_user_context, "No log call included user_id context"

    @pytest.mark.asyncio
    async def test_service_logs_errors_with_severity(self, test_supabase_client, test_user):
        """
        Test that service logs errors with appropriate severity.

        Validates: Requirements 4.4 (error handler logs errors with severity)
        """
        # Arrange
        onboarding_service = OnboardingService(UserPreferencesRepository(test_supabase_client))
        user_id = UUID(test_user["id"])

        # Act - Patch repository to cause error and capture logs
        with (
            patch.object(
                onboarding_service.user_preferences_repo,
                "get_by_user_id",
                side_effect=DatabaseError("Database error", error_code="DB_ERROR"),
            ),
            patch.object(onboarding_service.logger, "error") as mock_error,
        ):
            with pytest.raises(ServiceError):
                await onboarding_service.get_onboarding_status(user_id)

            # Assert - Verify error was logged
            assert mock_error.call_count >= 1

            # Check that error log includes context
            call_args, call_kwargs = mock_error.call_args
            assert "exc_info" in call_kwargs
            assert call_kwargs["exc_info"] is True
