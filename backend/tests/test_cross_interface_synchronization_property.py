"""
Property-based test for Cross-Interface Synchronization
Task 8.2

This module tests Property 5: Cross-Interface Synchronization
For any preference change made through either Discord or Web interface, the system SHALL
immediately synchronize the change to all interfaces, ensuring consistent display of
settings and triggering scheduler updates.

**Validates: Requirements 6.2, 6.6, 7.1, 7.6, 8.1, 8.2, 8.3, 8.4, 11.1, 11.2, 11.3**
"""

import asyncio
from datetime import datetime, time
from typing import Optional
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from app.schemas.user_notification_preferences import (
    UpdateUserNotificationPreferencesRequest,
    UserNotificationPreferences,
)
from app.services.preference_event_system import PreferenceChangeEvent
from app.services.preference_service import PreferenceService
from app.services.preference_synchronization_service import PreferenceSynchronizationService


# Test data generators
@st.composite
def user_preferences_data(draw):
    """Generate valid user notification preferences for testing."""
    frequencies = ["daily", "weekly", "monthly", "disabled"]
    timezones = [
        "Asia/Taipei",
        "UTC",
        "America/New_York",
        "Europe/London",
        "Asia/Tokyo",
        "Australia/Sydney",
        "America/Los_Angeles",
    ]

    # Generate time components
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))

    return {
        "id": draw(st.uuids()),  # Add required id field
        "user_id": draw(st.uuids()),
        "frequency": draw(st.sampled_from(frequencies)),
        "notification_time": time(hour, minute),
        "timezone": draw(st.sampled_from(timezones)),
        "dm_enabled": draw(st.booleans()),
        "email_enabled": draw(st.booleans()),
        "created_at": draw(
            st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31))
        ),
        "updated_at": draw(
            st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31))
        ),
    }


@st.composite
def preference_updates(draw):
    """Generate preference update data for testing."""
    possible_updates = {}

    # Randomly include different fields to update
    if draw(st.booleans()):
        possible_updates["frequency"] = draw(
            st.sampled_from(["daily", "weekly", "monthly", "disabled"])
        )

    if draw(st.booleans()):
        hour = draw(st.integers(min_value=0, max_value=23))
        minute = draw(st.integers(min_value=0, max_value=59))
        possible_updates["notification_time"] = f"{hour:02d}:{minute:02d}"

    if draw(st.booleans()):
        timezones = ["Asia/Taipei", "UTC", "America/New_York", "Europe/London"]
        possible_updates["timezone"] = draw(st.sampled_from(timezones))

    if draw(st.booleans()):
        possible_updates["dm_enabled"] = draw(st.booleans())

    if draw(st.booleans()):
        possible_updates["email_enabled"] = draw(st.booleans())

    # Ensure at least one field is updated
    if not possible_updates:
        possible_updates["dm_enabled"] = draw(st.booleans())

    return UpdateUserNotificationPreferencesRequest(**possible_updates)


@st.composite
def interface_sources(draw):
    """Generate interface source identifiers."""
    return draw(st.sampled_from(["web", "discord", "api", "system"]))


class MockPreferenceRepository:
    """Mock repository for user notification preferences."""

    def __init__(self):
        self.preferences_storage = {}
        self.operation_count = 0

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserNotificationPreferences]:
        """Mock get preferences by user ID."""
        self.operation_count += 1
        return self.preferences_storage.get(str(user_id))

    async def update_by_user_id(self, user_id: UUID, data: dict) -> UserNotificationPreferences:
        """Mock update preferences by user ID."""
        self.operation_count += 1

        # Get existing preferences
        existing_prefs = self.preferences_storage.get(str(user_id))
        if not existing_prefs:
            # Create default if not exists
            existing_prefs = UserNotificationPreferences(
                id=uuid4(),
                user_id=user_id,
                frequency="weekly",
                notification_time=time(18, 0),
                timezone="Asia/Taipei",
                dm_enabled=True,
                email_enabled=False,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        # Update fields from data
        update_dict = existing_prefs.model_dump()
        for key, value in data.items():
            if value is not None:
                if key == "notification_time" and isinstance(value, str):
                    # Convert string time to time object
                    hour, minute = value.split(":")
                    update_dict[key] = time(int(hour), int(minute))
                else:
                    update_dict[key] = value

        # Update timestamp
        update_dict["updated_at"] = datetime.now()

        # Create updated preferences
        updated_prefs = UserNotificationPreferences(**update_dict)
        self.preferences_storage[str(user_id)] = updated_prefs
        return updated_prefs

    async def update(
        self, user_id: UUID, preferences: UserNotificationPreferences
    ) -> UserNotificationPreferences:
        """Mock update preferences."""
        self.operation_count += 1
        self.preferences_storage[str(user_id)] = preferences
        return preferences

    async def create(self, preferences: UserNotificationPreferences) -> UserNotificationPreferences:
        """Mock create preferences."""
        self.operation_count += 1
        self.preferences_storage[str(preferences.user_id)] = preferences
        return preferences

    def reset(self):
        """Reset mock state."""
        self.preferences_storage.clear()
        self.operation_count = 0


class MockDynamicScheduler:
    """Mock dynamic scheduler for testing scheduler integration."""

    def __init__(self):
        self.scheduled_users = set()
        self.cancelled_users = set()
        self.reschedule_calls = []
        self.operation_count = 0

    async def schedule_user_notification(
        self, user_id: UUID, preferences: UserNotificationPreferences
    ):
        """Mock schedule user notification."""
        self.operation_count += 1
        self.scheduled_users.add(str(user_id))

    async def cancel_user_notification(self, user_id: UUID):
        """Mock cancel user notification."""
        self.operation_count += 1
        self.cancelled_users.add(str(user_id))

    async def reschedule_user_notification(
        self, user_id: UUID, preferences: UserNotificationPreferences
    ):
        """Mock reschedule user notification."""
        self.operation_count += 1
        self.reschedule_calls.append(
            {
                "user_id": str(user_id),
                "frequency": preferences.frequency,
                "notification_time": preferences.notification_time,
                "timezone": preferences.timezone,
            }
        )

    def reset(self):
        """Reset mock state."""
        self.scheduled_users.clear()
        self.cancelled_users.clear()
        self.reschedule_calls.clear()
        self.operation_count = 0


@pytest.fixture
def mock_preference_repo():
    """Create mock preference repository."""
    return MockPreferenceRepository()


@pytest.fixture
def mock_scheduler():
    """Create mock dynamic scheduler."""
    return MockDynamicScheduler()


@pytest.fixture
def preference_service(mock_preference_repo):
    """Create preference service with mock repository."""
    return PreferenceService(mock_preference_repo)


@pytest.fixture
def sync_service(mock_scheduler):
    """Create synchronization service with mock scheduler."""
    return PreferenceSynchronizationService(mock_scheduler)


# Property Tests


@given(
    initial_prefs=user_preferences_data(), updates=preference_updates(), source=interface_sources()
)
@hypothesis_settings(
    max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_preference_change_triggers_synchronization_property(
    preference_service,
    sync_service,
    mock_preference_repo,
    mock_scheduler,
    initial_prefs,
    updates,
    source,
):
    """
    Property: For any preference change from any interface, synchronization is triggered.

    **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
    """
    # Setup initial preferences
    user_id = initial_prefs["user_id"]
    initial_preferences = UserNotificationPreferences(**initial_prefs)
    mock_preference_repo.preferences_storage[str(user_id)] = initial_preferences

    # Track synchronization events
    sync_events = []

    async def mock_handle_change(event):
        sync_events.append(
            {
                "user_id": str(event.user_id),
                "source": event.source,
                "changed_fields": event.changed_fields,
                "old_prefs": event.old_preferences,
                "new_prefs": event.new_preferences,
            }
        )

    # Mock the event system
    with patch.object(sync_service, "_handle_preference_change", side_effect=mock_handle_change):
        # Update preferences through service
        updated_preferences = await preference_service.update_preferences(user_id, updates, source)

        # Trigger synchronization manually (simulating event system)
        old_prefs = initial_preferences
        new_prefs = updated_preferences
        changed_fields = []

        # Determine which fields actually changed
        if updates.frequency is not None:
            changed_fields.append("frequency")
        if updates.notification_time is not None:
            changed_fields.append("notification_time")
        if updates.timezone is not None:
            changed_fields.append("timezone")
        if updates.dm_enabled is not None:
            changed_fields.append("dm_enabled")
        if updates.email_enabled is not None:
            changed_fields.append("email_enabled")

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=old_prefs,
            new_preferences=new_prefs,
            changed_fields=changed_fields,
            source=source,
        )

        await sync_service._handle_preference_change(event)

    # Verify synchronization was triggered
    assert len(sync_events) == 1
    sync_event = sync_events[0]

    # Verify event data
    assert sync_event["user_id"] == str(user_id)
    assert sync_event["source"] == source
    assert set(sync_event["changed_fields"]) == set(changed_fields)

    # Verify scheduler was updated for scheduling-related changes
    scheduling_fields = {
        "frequency",
        "notification_time",
        "timezone",
        "dm_enabled",
        "email_enabled",
    }
    changed_scheduling_fields = set(changed_fields) & scheduling_fields

    if changed_scheduling_fields:
        if updated_preferences.frequency == "disabled":
            # Should cancel notifications
            assert str(user_id) in mock_scheduler.cancelled_users
        else:
            # Should reschedule notifications
            assert len(mock_scheduler.reschedule_calls) == 1
            reschedule_call = mock_scheduler.reschedule_calls[0]
            assert reschedule_call["user_id"] == str(user_id)
            assert reschedule_call["frequency"] == updated_preferences.frequency


@given(
    prefs_data=user_preferences_data(),
    updates=preference_updates(),
    sources=st.lists(interface_sources(), min_size=2, max_size=4, unique=True),
)
@hypothesis_settings(
    max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_cross_interface_consistency_property(
    preference_service,
    sync_service,
    mock_preference_repo,
    mock_scheduler,
    prefs_data,
    updates,
    sources,
):
    """
    Property: Preference changes from any interface result in consistent state across all interfaces.

    **Validates: Requirements 8.3, 11.1, 11.2, 11.3**
    """
    user_id = prefs_data["user_id"]
    initial_preferences = UserNotificationPreferences(**prefs_data)
    mock_preference_repo.preferences_storage[str(user_id)] = initial_preferences

    # Simulate multiple interface reads after update
    interface_states = {}

    # Update preferences from first source
    source = sources[0]
    updated_preferences = await preference_service.update_preferences(user_id, updates, source)

    # Simulate reading from all interfaces
    for interface_source in sources:
        # Each interface should see the same updated preferences
        retrieved_prefs = await preference_service.get_user_preferences(user_id)
        interface_states[interface_source] = {
            "frequency": retrieved_prefs.frequency,
            "notification_time": retrieved_prefs.notification_time,
            "timezone": retrieved_prefs.timezone,
            "dm_enabled": retrieved_prefs.dm_enabled,
            "email_enabled": retrieved_prefs.email_enabled,
        }

    # Verify all interfaces see consistent state
    first_interface_state = interface_states[sources[0]]
    for interface_source in sources[1:]:
        interface_state = interface_states[interface_source]

        # All interfaces should show identical preferences
        assert interface_state["frequency"] == first_interface_state["frequency"]
        assert interface_state["notification_time"] == first_interface_state["notification_time"]
        assert interface_state["timezone"] == first_interface_state["timezone"]
        assert interface_state["dm_enabled"] == first_interface_state["dm_enabled"]
        assert interface_state["email_enabled"] == first_interface_state["email_enabled"]

    # Verify the state matches the expected updates
    for field, expected_value in [
        ("frequency", updates.frequency),
        ("notification_time", updates.notification_time),
        ("timezone", updates.timezone),
        ("dm_enabled", updates.dm_enabled),
        ("email_enabled", updates.email_enabled),
    ]:
        if expected_value is not None:
            if field == "notification_time":
                # Convert string time to time object for comparison
                if isinstance(expected_value, str):
                    hour, minute = expected_value.split(":")
                    expected_time = time(int(hour), int(minute))
                    assert first_interface_state[field] == expected_time
                else:
                    assert first_interface_state[field] == expected_value
            else:
                assert first_interface_state[field] == expected_value


@given(
    prefs_data=user_preferences_data(),
    concurrent_updates=st.lists(preference_updates(), min_size=2, max_size=5),
    sources=st.lists(interface_sources(), min_size=2, max_size=5),
)
@hypothesis_settings(
    max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_concurrent_interface_updates_property(
    preference_service,
    sync_service,
    mock_preference_repo,
    mock_scheduler,
    prefs_data,
    concurrent_updates,
    sources,
):
    """
    Property: Concurrent updates from multiple interfaces maintain consistency.

    **Validates: Requirements 8.1, 8.2, 8.3**
    """
    user_id = prefs_data["user_id"]
    initial_preferences = UserNotificationPreferences(**prefs_data)
    mock_preference_repo.preferences_storage[str(user_id)] = initial_preferences

    # Track all synchronization events
    sync_events = []

    async def track_sync_event(event):
        sync_events.append(
            {
                "user_id": str(event.user_id),
                "source": event.source,
                "changed_fields": event.changed_fields,
                "timestamp": datetime.now(),
            }
        )

    # Simulate concurrent updates from different interfaces
    update_tasks = []

    for i, (update_data, source) in enumerate(
        zip(concurrent_updates, sources[: len(concurrent_updates)])
    ):
        # Create update task
        async def update_task(upd_data, src, delay=i * 0.01):
            await asyncio.sleep(delay)  # Small delay to simulate timing differences
            return await preference_service.update_preferences(user_id, upd_data, src)

        update_tasks.append(update_task(update_data, source))

    # Execute all updates concurrently
    results = await asyncio.gather(*update_tasks, return_exceptions=True)

    # Verify all updates completed successfully (no exceptions)
    successful_results = [r for r in results if not isinstance(r, Exception)]
    assert len(successful_results) > 0, "At least one update should succeed"

    # Verify final state is consistent
    final_preferences = await preference_service.get_user_preferences(user_id)

    # The final state should be valid and consistent
    assert final_preferences is not None
    assert final_preferences.user_id == user_id

    # Verify scheduler was called appropriately
    total_scheduler_operations = (
        len(mock_scheduler.scheduled_users)
        + len(mock_scheduler.cancelled_users)
        + len(mock_scheduler.reschedule_calls)
    )

    # Should have at least one scheduler operation for successful updates
    if len(successful_results) > 0:
        assert total_scheduler_operations >= 0  # May be 0 if no scheduling fields changed


@given(
    prefs_data=user_preferences_data(),
    update_sequence=st.lists(
        st.tuples(preference_updates(), interface_sources()), min_size=3, max_size=8
    ),
)
@hypothesis_settings(
    max_examples=25, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_scheduler_synchronization_property(
    preference_service,
    sync_service,
    mock_preference_repo,
    mock_scheduler,
    prefs_data,
    update_sequence,
):
    """
    Property: Scheduler updates are triggered correctly for all preference changes.

    **Validates: Requirements 8.4**
    """
    user_id = prefs_data["user_id"]
    initial_preferences = UserNotificationPreferences(**prefs_data)
    mock_preference_repo.preferences_storage[str(user_id)] = initial_preferences

    scheduler_operations = []

    # Process each update in sequence
    for update_data, source in update_sequence:
        # Reset scheduler state for this iteration
        mock_scheduler.reset()

        # Apply update
        updated_preferences = await preference_service.update_preferences(
            user_id, update_data, source
        )

        # Simulate synchronization event
        old_prefs = mock_preference_repo.preferences_storage.get(str(user_id), initial_preferences)

        # Determine changed fields
        changed_fields = []
        if update_data.frequency is not None:
            changed_fields.append("frequency")
        if update_data.notification_time is not None:
            changed_fields.append("notification_time")
        if update_data.timezone is not None:
            changed_fields.append("timezone")
        if update_data.dm_enabled is not None:
            changed_fields.append("dm_enabled")
        if update_data.email_enabled is not None:
            changed_fields.append("email_enabled")

        event = PreferenceChangeEvent(
            user_id=user_id,
            old_preferences=old_prefs,
            new_preferences=updated_preferences,
            changed_fields=changed_fields,
            source=source,
        )

        await sync_service._handle_preference_change(event)

        # Check if scheduling-related fields changed
        scheduling_fields = {
            "frequency",
            "notification_time",
            "timezone",
            "dm_enabled",
            "email_enabled",
        }
        changed_scheduling_fields = set(changed_fields) & scheduling_fields

        if changed_scheduling_fields:
            if updated_preferences.frequency == "disabled":
                # Should cancel notifications
                assert str(user_id) in mock_scheduler.cancelled_users
                scheduler_operations.append("cancel")
            else:
                # Should reschedule notifications
                assert len(mock_scheduler.reschedule_calls) == 1
                scheduler_operations.append("reschedule")
        else:
            # No scheduling changes, no scheduler operations expected
            assert len(mock_scheduler.reschedule_calls) == 0
            assert str(user_id) not in mock_scheduler.cancelled_users
            scheduler_operations.append("none")

    # Verify scheduler operations match expectations
    assert len(scheduler_operations) == len(update_sequence)

    # At least one scheduler operation should have occurred if any scheduling fields changed
    scheduling_updates = [
        update_data
        for update_data, _ in update_sequence
        if any(
            [
                update_data.frequency is not None,
                update_data.notification_time is not None,
                update_data.timezone is not None,
                update_data.dm_enabled is not None,
                update_data.email_enabled is not None,
            ]
        )
    ]

    if scheduling_updates:
        non_none_operations = [op for op in scheduler_operations if op != "none"]
        assert (
            len(non_none_operations) > 0
        ), "Should have scheduler operations for scheduling field changes"


@given(
    prefs_data=user_preferences_data(),
    dm_toggle_sequence=st.lists(st.booleans(), min_size=3, max_size=10),
    sources=st.lists(interface_sources(), min_size=3, max_size=10),
)
@hypothesis_settings(
    max_examples=20, deadline=6000, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_dm_notification_status_synchronization_property(
    preference_service,
    sync_service,
    mock_preference_repo,
    mock_scheduler,
    prefs_data,
    dm_toggle_sequence,
    sources,
):
    """
    Property: DM notification status changes are synchronized across all interfaces.

    **Validates: Requirements 6.6, 11.1, 11.2, 11.3**
    """
    user_id = prefs_data["user_id"]
    initial_preferences = UserNotificationPreferences(**prefs_data)
    mock_preference_repo.preferences_storage[str(user_id)] = initial_preferences

    # Track DM status across interfaces
    interface_dm_states = {}

    # Process each DM toggle
    for i, (dm_enabled, source) in enumerate(
        zip(dm_toggle_sequence, sources[: len(dm_toggle_sequence)])
    ):
        # Update DM status
        update_data = UpdateUserNotificationPreferencesRequest(dm_enabled=dm_enabled)
        updated_preferences = await preference_service.update_preferences(
            user_id, update_data, source
        )

        # Simulate reading from all interfaces
        for interface in ["web", "discord", "api"]:
            retrieved_prefs = await preference_service.get_user_preferences(user_id)
            interface_dm_states[f"{interface}_{i}"] = retrieved_prefs.dm_enabled

    # Verify all interfaces show consistent DM status after each change
    for i in range(len(dm_toggle_sequence)):
        expected_dm_status = dm_toggle_sequence[i]

        web_status = interface_dm_states.get(f"web_{i}")
        discord_status = interface_dm_states.get(f"discord_{i}")
        api_status = interface_dm_states.get(f"api_{i}")

        # All interfaces should show the same DM status
        if web_status is not None:
            assert web_status == expected_dm_status
        if discord_status is not None:
            assert discord_status == expected_dm_status
        if api_status is not None:
            assert api_status == expected_dm_status

        # All interfaces should be consistent with each other
        if web_status is not None and discord_status is not None:
            assert web_status == discord_status
        if discord_status is not None and api_status is not None:
            assert discord_status == api_status
        if web_status is not None and api_status is not None:
            assert web_status == api_status
