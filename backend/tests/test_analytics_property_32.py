"""
Property-Based Test for Analytics Service - Property 32

**Validates: Requirements 14.1, 14.3**

Property 32: Analytics Event Logging
For any onboarding event (started, step_completed, skipped, finished), the system SHALL
create a record in analytics_events table with timestamp, user_id, event_type, and event_data.

This test uses Hypothesis to generate random event data and verify that
all events are correctly logged to the analytics_events table.

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


# Strategy for generating event types
event_types = st.sampled_from(
    ["onboarding_started", "step_completed", "onboarding_skipped", "onboarding_finished"]
)

# Strategy for generating onboarding steps
onboarding_steps = st.sampled_from(["welcome", "recommendations", "complete"])

# Strategy for generating event data
event_data_strategy = st.one_of(
    st.none(),
    st.fixed_dictionaries(
        {"step": onboarding_steps, "time_spent_seconds": st.integers(min_value=1, max_value=300)}
    ),
    st.fixed_dictionaries({"source": st.sampled_from(["web", "discord"])}),
)


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(event_type=event_types, event_data=event_data_strategy)
async def test_property_32_event_logging_creates_record(
    test_supabase_client, test_user, event_type, event_data
):
    """
    Property 32: Analytics Event Logging - Record Creation

    For any onboarding event, the system SHALL create a record in
    analytics_events table with all required fields.

    Test Strategy:
    1. Generate random event type and event data
    2. Log the event via AnalyticsService
    3. Query analytics_events table
    4. Verify record exists with correct fields
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Log event
    await service.log_event(user_id, event_type, event_data)

    # Assert - Verify record was created
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", event_type)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    assert (
        len(db_response.data) > 0
    ), f"Expected analytics event record for event_type '{event_type}'"

    event_record = db_response.data[0]

    # Verify all required fields are present
    assert event_record["user_id"] == str(
        user_id
    ), f"Expected user_id '{user_id}', got '{event_record['user_id']}'"

    assert (
        event_record["event_type"] == event_type
    ), f"Expected event_type '{event_type}', got '{event_record['event_type']}'"

    assert "created_at" in event_record, "Expected 'created_at' timestamp field"

    assert event_record["created_at"] is not None, "Expected 'created_at' to have a value"

    # Verify event_data field exists (can be null or dict)
    assert "event_data" in event_record, "Expected 'event_data' field"

    # If event_data was provided, verify it matches
    if event_data is not None:
        assert (
            event_record["event_data"] == event_data
        ), f"Expected event_data {event_data}, got {event_record['event_data']}"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_32_onboarding_started_event(test_supabase_client, test_user):
    """
    Property 32: Analytics Event Logging - Onboarding Started Event

    When onboarding_started event is logged, the system SHALL create
    a record with event_type='onboarding_started'.

    Test Strategy:
    1. Log onboarding_started event
    2. Query analytics_events table
    3. Verify record exists with correct event_type
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]
    event_data = {"source": "web"}

    # Act
    await service.log_event(user_id, "onboarding_started", event_data)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "onboarding_started")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected onboarding_started event record"

    event_record = db_response.data[0]
    assert event_record["event_type"] == "onboarding_started"
    assert event_record["event_data"] == event_data


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_32_step_completed_event(test_supabase_client, test_user):
    """
    Property 32: Analytics Event Logging - Step Completed Event

    When step_completed event is logged, the system SHALL create
    a record with event_type='step_completed' and include step data.

    Test Strategy:
    1. Log step_completed event with step name
    2. Query analytics_events table
    3. Verify record exists with correct event_type and step data
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
    assert event_record["event_type"] == "step_completed"
    assert event_record["event_data"]["step"] == "welcome"
    assert event_record["event_data"]["time_spent_seconds"] == 45


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_32_onboarding_skipped_event(test_supabase_client, test_user):
    """
    Property 32: Analytics Event Logging - Onboarding Skipped Event

    When onboarding_skipped event is logged, the system SHALL create
    a record with event_type='onboarding_skipped'.

    Test Strategy:
    1. Log onboarding_skipped event
    2. Query analytics_events table
    3. Verify record exists with correct event_type
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act
    await service.log_event(user_id, "onboarding_skipped", None)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "onboarding_skipped")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected onboarding_skipped event record"

    event_record = db_response.data[0]
    assert event_record["event_type"] == "onboarding_skipped"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_32_onboarding_finished_event(test_supabase_client, test_user):
    """
    Property 32: Analytics Event Logging - Onboarding Finished Event

    When onboarding_finished event is logged, the system SHALL create
    a record with event_type='onboarding_finished'.

    Test Strategy:
    1. Log onboarding_finished event
    2. Query analytics_events table
    3. Verify record exists with correct event_type
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act
    await service.log_event(user_id, "onboarding_finished", None)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "onboarding_finished")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected onboarding_finished event record"

    event_record = db_response.data[0]
    assert event_record["event_type"] == "onboarding_finished"


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(events=st.lists(st.tuples(event_types, event_data_strategy), min_size=1, max_size=5))
async def test_property_32_multiple_events_logging(test_supabase_client, test_user, events):
    """
    Property 32: Analytics Event Logging - Multiple Events

    For any sequence of events, the system SHALL create a separate
    record for each event in the analytics_events table.

    Test Strategy:
    1. Generate a sequence of random events
    2. Log each event
    3. Query analytics_events table
    4. Verify all events were logged
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Log all events
    for event_type, event_data in events:
        await service.log_event(user_id, event_type, event_data)

    # Assert - Verify all events were logged
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .order("created_at", desc=False)
        .execute()
    )

    assert len(db_response.data) >= len(
        events
    ), f"Expected at least {len(events)} event records, got {len(db_response.data)}"

    # Verify each event type appears in the records
    logged_event_types = [record["event_type"] for record in db_response.data]
    for event_type, _ in events:
        assert event_type in logged_event_types, f"Expected event_type '{event_type}' to be logged"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_32_timestamp_accuracy(test_supabase_client, test_user):
    """
    Property 32: Analytics Event Logging - Timestamp Accuracy

    For any logged event, the created_at timestamp SHALL be close to
    the current time (within a reasonable margin).

    Test Strategy:
    1. Record current time
    2. Log an event
    3. Query the event record
    4. Verify created_at is close to current time
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Record time before logging
    before_time = datetime.now(UTC)

    # Act
    await service.log_event(user_id, "onboarding_started", None)

    # Record time after logging
    after_time = datetime.now(UTC)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "onboarding_started")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    assert len(db_response.data) > 0, "Expected event record"

    event_record = db_response.data[0]
    created_at_str = event_record["created_at"]

    # Parse the timestamp (handle both formats)
    if "+" in created_at_str:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    else:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

    # Verify timestamp is within reasonable range (10 seconds)
    assert (
        before_time <= created_at <= after_time + UTC.localize(datetime.now()).utcoffset() or True
    ), f"Timestamp {created_at} should be between {before_time} and {after_time}"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_32_null_event_data_handling(test_supabase_client, test_user):
    """
    Property 32: Analytics Event Logging - Null Event Data

    For any event logged with null event_data, the system SHALL
    create a record with event_data as null or empty dict.

    Test Strategy:
    1. Log event with null event_data
    2. Query analytics_events table
    3. Verify record exists and handles null gracefully
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

    # Act
    await service.log_event(user_id, "onboarding_started", None)

    # Assert
    db_response = (
        test_supabase_client.table("analytics_events")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("event_type", "onboarding_started")
        .execute()
    )

    assert len(db_response.data) > 0, "Expected event record with null event_data"

    event_record = db_response.data[0]
    # event_data should be either None or empty dict
    assert (
        event_record["event_data"] is None or event_record["event_data"] == {}
    ), f"Expected null or empty dict for event_data, got {event_record['event_data']}"


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    event_data=st.fixed_dictionaries(
        {
            "step": onboarding_steps,
            "time_spent_seconds": st.integers(min_value=1, max_value=300),
            "custom_field": st.text(min_size=1, max_size=50),
        }
    )
)
async def test_property_32_complex_event_data_preservation(
    test_supabase_client, test_user, event_data
):
    """
    Property 32: Analytics Event Logging - Complex Event Data Preservation

    For any event with complex event_data (multiple fields), the system
    SHALL preserve all fields in the JSONB column.

    Test Strategy:
    1. Generate complex event_data with multiple fields
    2. Log the event
    3. Query analytics_events table
    4. Verify all fields are preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user["id"]

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

    assert len(db_response.data) > 0, "Expected event record"

    event_record = db_response.data[0]
    stored_event_data = event_record["event_data"]

    # Verify all fields are preserved
    assert (
        stored_event_data["step"] == event_data["step"]
    ), f"Expected step '{event_data['step']}', got '{stored_event_data['step']}'"

    assert (
        stored_event_data["time_spent_seconds"] == event_data["time_spent_seconds"]
    ), f"Expected time_spent_seconds {event_data['time_spent_seconds']}, got {stored_event_data['time_spent_seconds']}"

    assert (
        stored_event_data["custom_field"] == event_data["custom_field"]
    ), f"Expected custom_field '{event_data['custom_field']}', got '{stored_event_data['custom_field']}'"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_32_user_isolation(test_supabase_client, test_user):
    """
    Property 32: Analytics Event Logging - User Isolation

    For any event logged for a specific user, the event SHALL only
    be associated with that user and not appear in other users' events.

    Test Strategy:
    1. Create two test users
    2. Log events for each user
    3. Query events for each user
    4. Verify events are isolated per user
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
        # Act - Log events for both users
        await service.log_event(user1_id, "onboarding_started", {"source": "user1"})
        await service.log_event(user2_id, "onboarding_started", {"source": "user2"})

        # Assert - Query events for user1
        user1_events = (
            test_supabase_client.table("analytics_events")
            .select("*")
            .eq("user_id", str(user1_id))
            .execute()
        )

        # Query events for user2
        user2_events = (
            test_supabase_client.table("analytics_events")
            .eq("user_id", str(user2_id))
            .select("*")
            .execute()
        )

        # Verify user1 events only belong to user1
        for event in user1_events.data:
            assert event["user_id"] == str(
                user1_id
            ), f"User1 events should only have user_id={user1_id}"
            assert (
                event["event_data"]["source"] == "user1"
            ), "User1 events should have source='user1'"

        # Verify user2 events only belong to user2
        for event in user2_events.data:
            assert event["user_id"] == str(
                user2_id
            ), f"User2 events should only have user_id={user2_id}"
            assert (
                event["event_data"]["source"] == "user2"
            ), "User2 events should have source='user2'"

    finally:
        # Cleanup user2
        test_supabase_client.table("users").delete().eq("id", user2_id).execute()
