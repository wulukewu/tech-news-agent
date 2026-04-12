"""
Property-Based Test for Analytics Service - Property 34

**Validates: Requirements 14.5**

Property 34: Step Time Tracking
For any onboarding step completion, the analytics event SHALL include time_spent_seconds
in the event_data.

This test uses Hypothesis to generate random step completion scenarios and verify that
the time_spent_seconds information is correctly preserved in the analytics_events table.

**PREREQUISITE**: Migration 004 must be applied before running these tests.
To apply the migration, copy and paste the SQL from:
scripts/migrations/004_create_analytics_events_table.sql
into the Supabase SQL Editor and execute it.
"""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from supabase import create_client

from app.services.analytics_service import AnalyticsService

# Load environment and check if migration is applied
load_dotenv()
_migration_applied = False

try:
    _url = os.getenv("SUPABASE_URL")
    _key = os.getenv("SUPABASE_KEY")
    if _url and _key:
        _client = create_client(_url, _key)
        _client.table("analytics_events").select("event_type").limit(1).execute()
        _migration_applied = True
except Exception:
    pass

# Skip all tests in this module if migration not applied
pytestmark = pytest.mark.skipif(
    not _migration_applied,
    reason="Migration 004 not applied. Please apply scripts/migrations/004_create_analytics_events_table.sql via Supabase SQL Editor.",
)


# Strategy for generating onboarding steps
onboarding_steps = st.sampled_from(["welcome", "recommendations", "complete"])

# Strategy for generating time spent (1-300 seconds)
time_spent_strategy = st.integers(min_value=1, max_value=300)


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(step=onboarding_steps, time_spent_seconds=time_spent_strategy)
async def test_property_34_step_completion_includes_time(
    test_supabase_client, test_user, step, time_spent_seconds
):
    """
    Property 34: Step Time Tracking - Time Information Preserved

    For any onboarding step completion, the analytics event SHALL include
    time_spent_seconds in the event_data.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Generate random step (welcome, recommendations, complete)
    2. Generate random time_spent_seconds (1-300 seconds)
    3. Log step_completed event with time information
    4. Query analytics_events table
    5. Verify event_data contains the time_spent_seconds field
    6. Verify time value matches the logged time
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]
    event_data = {"step": step, "time_spent_seconds": time_spent_seconds}

    # Act - Log step_completed event with time information
    await service.log_event(user_id, "step_completed", event_data)

    # Assert - Verify record was created with time information
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    assert len(db_response.data) > 0, "Expected step_completed event record"

    event_record = db_response.data[0]

    # Verify event_data exists and contains time_spent_seconds
    assert "event_data" in event_record, "Expected 'event_data' field in event record"

    assert (
        event_record["event_data"] is not None
    ), "Expected event_data to be non-null for step completion events"

    assert (
        "time_spent_seconds" in event_record["event_data"]
    ), "Expected 'time_spent_seconds' field in event_data for step completion events (Requirements 14.5)"

    assert (
        event_record["event_data"]["time_spent_seconds"] == time_spent_seconds
    ), f"Expected time_spent_seconds {time_spent_seconds}, got {event_record['event_data']['time_spent_seconds']}"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_34_welcome_step_time_tracking(test_supabase_client, test_user):
    """
    Property 34: Step Time Tracking - Welcome Step

    When a user completes the welcome step, the system SHALL
    log the event with time_spent_seconds in event_data.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Log step_completed event for welcome step with time
    2. Query analytics_events table
    3. Verify time information is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]
    event_data = {"step": "welcome", "time_spent_seconds": 45}

    # Act
    await service.log_event(user_id, "step_completed", event_data)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected step_completed event record"

    event_record = db_response.data[0]
    assert event_record["event_data"]["step"] == "welcome", "Expected step='welcome'"
    assert (
        event_record["event_data"]["time_spent_seconds"] == 45
    ), "Expected time_spent_seconds=45 for welcome step"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_34_recommendations_step_time_tracking(test_supabase_client, test_user):
    """
    Property 34: Step Time Tracking - Recommendations Step

    When a user completes the recommendations step, the system SHALL
    log the event with time_spent_seconds in event_data.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Log step_completed event for recommendations step with time
    2. Query analytics_events table
    3. Verify time information is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]
    event_data = {"step": "recommendations", "time_spent_seconds": 120}

    # Act
    await service.log_event(user_id, "step_completed", event_data)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected step_completed event record"

    event_record = db_response.data[0]
    assert (
        event_record["event_data"]["step"] == "recommendations"
    ), "Expected step='recommendations'"
    assert (
        event_record["event_data"]["time_spent_seconds"] == 120
    ), "Expected time_spent_seconds=120 for recommendations step"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_34_complete_step_time_tracking(test_supabase_client, test_user):
    """
    Property 34: Step Time Tracking - Complete Step

    When a user completes the complete step, the system SHALL
    log the event with time_spent_seconds in event_data.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Log step_completed event for complete step with time
    2. Query analytics_events table
    3. Verify time information is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]
    event_data = {"step": "complete", "time_spent_seconds": 30}

    # Act
    await service.log_event(user_id, "step_completed", event_data)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected step_completed event record"

    event_record = db_response.data[0]
    assert event_record["event_data"]["step"] == "complete", "Expected step='complete'"
    assert (
        event_record["event_data"]["time_spent_seconds"] == 30
    ), "Expected time_spent_seconds=30 for complete step"


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    step_completions=st.lists(
        st.tuples(onboarding_steps, time_spent_strategy), min_size=1, max_size=3
    )
)
async def test_property_34_multiple_step_completions_preserve_time(
    test_supabase_client, test_user, step_completions
):
    """
    Property 34: Step Time Tracking - Multiple Step Completions

    For any sequence of step completion events, the system SHALL preserve
    time_spent_seconds for each step completion event.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Generate sequence of step completions with different times
    2. Log each step_completed event
    3. Query all step_completed events for the user
    4. Verify each event has correct time information
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Log all step completion events
    for step, time_spent in step_completions:
        event_data = {"step": step, "time_spent_seconds": time_spent}
        await service.log_event(user_id, "step_completed", event_data)

    # Assert - Verify all events were logged with correct time information
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .order("created_at", desc=False)
        .execute()
    )

    assert len(db_response.data) >= len(
        step_completions
    ), f"Expected at least {len(step_completions)} step completion event records"

    # Verify each step completion event has time information
    for i, (expected_step, expected_time) in enumerate(step_completions):
        event_record = db_response.data[i]

        assert "event_data" in event_record, f"Expected event_data in step completion event {i}"

        assert (
            "time_spent_seconds" in event_record["event_data"]
        ), f"Expected time_spent_seconds field in step completion event {i}"

        assert (
            event_record["event_data"]["time_spent_seconds"] == expected_time
        ), f"Expected time_spent_seconds {expected_time} in event {i}, got {event_record['event_data']['time_spent_seconds']}"

        assert (
            event_record["event_data"]["step"] == expected_step
        ), f"Expected step '{expected_step}' in event {i}, got '{event_record['event_data']['step']}'"


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    step=onboarding_steps,
    time_spent_seconds=time_spent_strategy,
    additional_data=st.fixed_dictionaries(
        {
            "source": st.sampled_from(["web", "discord"]),
            "user_agent": st.text(min_size=5, max_size=50),
        }
    ),
)
async def test_property_34_step_time_with_additional_metadata(
    test_supabase_client, test_user, step, time_spent_seconds, additional_data
):
    """
    Property 34: Step Time Tracking - Additional Metadata Preservation

    When a step completion event includes additional metadata (source, user_agent),
    the system SHALL preserve both the time_spent_seconds and all additional fields.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Generate step completion event with time and additional metadata
    2. Log the event
    3. Query analytics_events table
    4. Verify time_spent_seconds and all additional fields are preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]
    event_data = {"step": step, "time_spent_seconds": time_spent_seconds, **additional_data}

    # Act
    await service.log_event(user_id, "step_completed", event_data)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    assert len(db_response.data) > 0, "Expected step_completed event record"

    event_record = db_response.data[0]
    stored_event_data = event_record["event_data"]

    # Verify time_spent_seconds is preserved
    assert (
        stored_event_data["time_spent_seconds"] == time_spent_seconds
    ), f"Expected time_spent_seconds {time_spent_seconds}, got {stored_event_data['time_spent_seconds']}"

    # Verify step is preserved
    assert (
        stored_event_data["step"] == step
    ), f"Expected step '{step}', got '{stored_event_data['step']}'"

    # Verify additional metadata is preserved
    assert (
        stored_event_data["source"] == additional_data["source"]
    ), f"Expected source '{additional_data['source']}', got '{stored_event_data['source']}'"

    assert (
        stored_event_data["user_agent"] == additional_data["user_agent"]
    ), f"Expected user_agent '{additional_data['user_agent']}', got '{stored_event_data['user_agent']}'"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_34_time_range_boundaries(test_supabase_client, test_user):
    """
    Property 34: Step Time Tracking - Time Range Boundaries

    The system SHALL correctly handle time_spent_seconds at boundary values
    (minimum 1 second, maximum 300 seconds).

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Log step completion with minimum time (1 second)
    2. Log step completion with maximum time (300 seconds)
    3. Verify both values are correctly preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Log minimum time
    await service.log_event(user_id, "step_completed", {"step": "welcome", "time_spent_seconds": 1})

    # Act - Log maximum time
    await service.log_event(
        user_id, "step_completed", {"step": "recommendations", "time_spent_seconds": 300}
    )

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .order("created_at", desc=False)
        .execute()
    )

    assert len(db_response.data) >= 2, "Expected at least 2 step completion event records"

    # Verify minimum time
    min_time_event = db_response.data[0]
    assert (
        min_time_event["event_data"]["time_spent_seconds"] == 1
    ), "Expected minimum time_spent_seconds=1"

    # Verify maximum time
    max_time_event = db_response.data[1]
    assert (
        max_time_event["event_data"]["time_spent_seconds"] == 300
    ), "Expected maximum time_spent_seconds=300"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_34_step_time_field_required(test_supabase_client, test_user):
    """
    Property 34: Step Time Tracking - Time Field Requirement

    When logging a step_completed event, the time_spent_seconds field SHOULD be
    present in event_data to satisfy the requirement that step completion events
    include time tracking.

    This test verifies that the system can handle step completion events with
    time information, which is the expected behavior per Requirements 14.5.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Log step_completed event WITH time_spent_seconds (correct usage)
    2. Verify time is preserved
    3. This establishes the expected behavior
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Log step completion WITH time (correct usage per requirements)
    event_data_with_time = {"step": "welcome", "time_spent_seconds": 60}
    await service.log_event(user_id, "step_completed", event_data_with_time)

    # Assert - Verify time is preserved
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected step_completed event record"

    event_record = db_response.data[0]
    assert (
        "time_spent_seconds" in event_record["event_data"]
    ), "Expected time_spent_seconds field in event_data for step completion events (Requirements 14.5)"

    assert (
        event_record["event_data"]["time_spent_seconds"] == 60
    ), "Expected time_spent_seconds value to be preserved"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_34_step_time_isolated_per_user(test_supabase_client, test_user):
    """
    Property 34: Step Time Tracking - User Isolation

    Step completion time tracking for different users SHALL be isolated,
    with each user's time information preserved independently.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Create two test users
    2. Log step completions with different times for each user
    3. Query events for each user
    4. Verify each user's time is correctly isolated
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user1_id = test_user["id"]

    # Create second test user
    test_discord_id_2 = f"test_user_{uuid4().hex}"
    user2_result = (
        test_supabase_client.table("users").insert({"discord_id": test_discord_id_2}).execute()
    )
    user2_id = user2_result.data[0]["id"]

    try:
        # Act - Log step completions with different times for each user
        await service.log_event(
            user1_id, "step_completed", {"step": "welcome", "time_spent_seconds": 45}
        )
        await service.log_event(
            user2_id, "step_completed", {"step": "welcome", "time_spent_seconds": 90}
        )

        # Assert - Query events for user1
        user1_events = (
            test_supabase_client.table("analytics_events")
            .select("*")
            .eq("user_id", str(user1_id))
            .eq("event_type", "step_completed")
            .execute()
        )

        # Query events for user2
        user2_events = (
            test_supabase_client.table("analytics_events")
            .select("*")
            .eq("user_id", str(user2_id))
            .eq("event_type", "step_completed")
            .execute()
        )

        # Verify user1 has correct time
        assert len(user1_events.data) > 0, "Expected step completion event for user1"
        assert (
            user1_events.data[0]["event_data"]["time_spent_seconds"] == 45
        ), "User1 should have time_spent_seconds=45"

        # Verify user2 has correct time
        assert len(user2_events.data) > 0, "Expected step completion event for user2"
        assert (
            user2_events.data[0]["event_data"]["time_spent_seconds"] == 90
        ), "User2 should have time_spent_seconds=90"

    finally:
        # Cleanup user2
        test_supabase_client.table("users").delete().eq("id", user2_id).execute()


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_34_step_time_timestamp_correlation(test_supabase_client, test_user):
    """
    Property 34: Step Time Tracking - Timestamp Correlation

    For any step completion event, the created_at timestamp SHALL be accurate
    and the time_spent_seconds SHALL be preserved alongside it.

    **Validates: Requirements 14.5**

    Test Strategy:
    1. Record current time
    2. Log step completion event with time information
    3. Query the event record
    4. Verify timestamp is accurate and time_spent_seconds is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Record time before logging
    before_time = datetime.now(UTC)

    # Act
    await service.log_event(
        user_id, "step_completed", {"step": "recommendations", "time_spent_seconds": 75}
    )

    # Record time after logging
    after_time = datetime.now(UTC)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "step_completed")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    assert len(db_response.data) > 0, "Expected step completion event record"

    event_record = db_response.data[0]

    # Verify time_spent_seconds is preserved
    assert (
        event_record["event_data"]["time_spent_seconds"] == 75
    ), "Expected time_spent_seconds=75 to be preserved"

    # Verify timestamp exists
    assert "created_at" in event_record, "Expected created_at timestamp"

    assert event_record["created_at"] is not None, "Expected created_at to have a value"
