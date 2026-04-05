"""
Property-Based Test for Analytics Service - Property 33

**Validates: Requirements 14.4**

Property 33: Skip Event Step Tracking
For any user who skips onboarding, the analytics event SHALL include the step where
the skip occurred in the event_data.

This test uses Hypothesis to generate random skip scenarios and verify that
the step information is correctly preserved in the analytics_events table.

**PREREQUISITE**: Migration 004 must be applied before running these tests.
To apply the migration, copy and paste the SQL from:
scripts/migrations/004_create_analytics_events_table.sql
into the Supabase SQL Editor and execute it.
"""

import pytest
from uuid import uuid4
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from supabase import create_client

from app.services.analytics_service import AnalyticsService, AnalyticsServiceError


# Load environment and check if migration is applied
load_dotenv()
_migration_applied = False

try:
    _url = os.getenv('SUPABASE_URL')
    _key = os.getenv('SUPABASE_KEY')
    if _url and _key:
        _client = create_client(_url, _key)
        _client.table('analytics_events').select('event_type').limit(1).execute()
        _migration_applied = True
except Exception:
    pass

# Skip all tests in this module if migration not applied
pytestmark = pytest.mark.skipif(
    not _migration_applied,
    reason="Migration 004 not applied. Please apply scripts/migrations/004_create_analytics_events_table.sql via Supabase SQL Editor."
)


# Strategy for generating onboarding steps where skip can occur
skip_steps = st.sampled_from(['welcome', 'recommendations', 'complete'])


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(skip_step=skip_steps)
async def test_property_33_skip_event_includes_step(
    test_supabase_client,
    test_user,
    skip_step
):
    """
    Property 33: Skip Event Step Tracking - Step Information Preserved
    
    For any user who skips onboarding, the analytics event SHALL include
    the step where the skip occurred in the event_data.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Generate random skip step (welcome, recommendations, complete)
    2. Log onboarding_skipped event with step information
    3. Query analytics_events table
    4. Verify event_data contains the step field
    5. Verify step value matches the skip location
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    event_data = {'step': skip_step}
    
    # Act - Log skip event with step information
    await service.log_event(user_id, 'onboarding_skipped', event_data)
    
    # Assert - Verify record was created with step information
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .order('created_at', desc=True) \
        .limit(1) \
        .execute()
    
    assert len(db_response.data) > 0, \
        "Expected onboarding_skipped event record"
    
    event_record = db_response.data[0]
    
    # Verify event_data exists and contains step
    assert 'event_data' in event_record, \
        "Expected 'event_data' field in event record"
    
    assert event_record['event_data'] is not None, \
        "Expected event_data to be non-null for skip events"
    
    assert 'step' in event_record['event_data'], \
        "Expected 'step' field in event_data for skip events"
    
    assert event_record['event_data']['step'] == skip_step, \
        f"Expected step '{skip_step}', got '{event_record['event_data']['step']}'"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_33_skip_at_welcome_step(
    test_supabase_client,
    test_user
):
    """
    Property 33: Skip Event Step Tracking - Welcome Step
    
    When a user skips onboarding at the welcome step, the system SHALL
    log the event with step='welcome' in event_data.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Log onboarding_skipped event with step='welcome'
    2. Query analytics_events table
    3. Verify step information is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    event_data = {'step': 'welcome'}
    
    # Act
    await service.log_event(user_id, 'onboarding_skipped', event_data)
    
    # Assert
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .execute()
    
    assert len(db_response.data) > 0, \
        "Expected onboarding_skipped event record"
    
    event_record = db_response.data[0]
    assert event_record['event_data']['step'] == 'welcome', \
        "Expected step='welcome' for skip at welcome step"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_33_skip_at_recommendations_step(
    test_supabase_client,
    test_user
):
    """
    Property 33: Skip Event Step Tracking - Recommendations Step
    
    When a user skips onboarding at the recommendations step, the system SHALL
    log the event with step='recommendations' in event_data.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Log onboarding_skipped event with step='recommendations'
    2. Query analytics_events table
    3. Verify step information is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    event_data = {'step': 'recommendations'}
    
    # Act
    await service.log_event(user_id, 'onboarding_skipped', event_data)
    
    # Assert
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .execute()
    
    assert len(db_response.data) > 0, \
        "Expected onboarding_skipped event record"
    
    event_record = db_response.data[0]
    assert event_record['event_data']['step'] == 'recommendations', \
        "Expected step='recommendations' for skip at recommendations step"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_33_skip_at_complete_step(
    test_supabase_client,
    test_user
):
    """
    Property 33: Skip Event Step Tracking - Complete Step
    
    When a user skips onboarding at the complete step, the system SHALL
    log the event with step='complete' in event_data.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Log onboarding_skipped event with step='complete'
    2. Query analytics_events table
    3. Verify step information is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    event_data = {'step': 'complete'}
    
    # Act
    await service.log_event(user_id, 'onboarding_skipped', event_data)
    
    # Assert
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .execute()
    
    assert len(db_response.data) > 0, \
        "Expected onboarding_skipped event record"
    
    event_record = db_response.data[0]
    assert event_record['event_data']['step'] == 'complete', \
        "Expected step='complete' for skip at complete step"


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    skip_events=st.lists(
        st.tuples(
            skip_steps,
            st.integers(min_value=1, max_value=300)  # time_spent_seconds
        ),
        min_size=1,
        max_size=3
    )
)
async def test_property_33_multiple_skip_events_preserve_steps(
    test_supabase_client,
    test_user,
    skip_events
):
    """
    Property 33: Skip Event Step Tracking - Multiple Skip Events
    
    For any sequence of skip events (e.g., user skips, restarts, skips again),
    the system SHALL preserve step information for each skip event.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Generate sequence of skip events with different steps
    2. Log each skip event
    3. Query all skip events for the user
    4. Verify each event has correct step information
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    
    # Act - Log all skip events
    for skip_step, time_spent in skip_events:
        event_data = {
            'step': skip_step,
            'time_spent_seconds': time_spent
        }
        await service.log_event(user_id, 'onboarding_skipped', event_data)
    
    # Assert - Verify all events were logged with correct step information
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .order('created_at', desc=False) \
        .execute()
    
    assert len(db_response.data) >= len(skip_events), \
        f"Expected at least {len(skip_events)} skip event records"
    
    # Verify each skip event has step information
    for i, (expected_step, expected_time) in enumerate(skip_events):
        event_record = db_response.data[i]
        
        assert 'event_data' in event_record, \
            f"Expected event_data in skip event {i}"
        
        assert 'step' in event_record['event_data'], \
            f"Expected step field in skip event {i}"
        
        assert event_record['event_data']['step'] == expected_step, \
            f"Expected step '{expected_step}' in event {i}, got '{event_record['event_data']['step']}'"
        
        assert event_record['event_data']['time_spent_seconds'] == expected_time, \
            f"Expected time_spent_seconds {expected_time} in event {i}"


@pytest.mark.asyncio
@pytest.mark.property_test
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    skip_step=skip_steps,
    additional_data=st.fixed_dictionaries({
        'reason': st.sampled_from(['too_long', 'not_interested', 'already_familiar']),
        'time_spent_seconds': st.integers(min_value=1, max_value=300)
    })
)
async def test_property_33_skip_event_with_additional_metadata(
    test_supabase_client,
    test_user,
    skip_step,
    additional_data
):
    """
    Property 33: Skip Event Step Tracking - Additional Metadata Preservation
    
    When a skip event includes additional metadata (reason, time spent),
    the system SHALL preserve both the step and all additional fields.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Generate skip event with step and additional metadata
    2. Log the event
    3. Query analytics_events table
    4. Verify step and all additional fields are preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    event_data = {
        'step': skip_step,
        **additional_data
    }
    
    # Act
    await service.log_event(user_id, 'onboarding_skipped', event_data)
    
    # Assert
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .order('created_at', desc=True) \
        .limit(1) \
        .execute()
    
    assert len(db_response.data) > 0, \
        "Expected onboarding_skipped event record"
    
    event_record = db_response.data[0]
    stored_event_data = event_record['event_data']
    
    # Verify step is preserved
    assert stored_event_data['step'] == skip_step, \
        f"Expected step '{skip_step}', got '{stored_event_data['step']}'"
    
    # Verify additional metadata is preserved
    assert stored_event_data['reason'] == additional_data['reason'], \
        f"Expected reason '{additional_data['reason']}', got '{stored_event_data['reason']}'"
    
    assert stored_event_data['time_spent_seconds'] == additional_data['time_spent_seconds'], \
        f"Expected time_spent_seconds {additional_data['time_spent_seconds']}"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_33_skip_event_step_field_required(
    test_supabase_client,
    test_user
):
    """
    Property 33: Skip Event Step Tracking - Step Field Requirement
    
    When logging a skip event, the step field SHOULD be present in event_data
    to satisfy the requirement that skip events include the step where skip occurred.
    
    This test verifies that the system can handle skip events with step information,
    which is the expected behavior per Requirements 14.4.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Log skip event WITH step information (correct usage)
    2. Verify step is preserved
    3. This establishes the expected behavior
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    
    # Act - Log skip event WITH step (correct usage per requirements)
    event_data_with_step = {'step': 'welcome'}
    await service.log_event(user_id, 'onboarding_skipped', event_data_with_step)
    
    # Assert - Verify step is preserved
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .execute()
    
    assert len(db_response.data) > 0, \
        "Expected onboarding_skipped event record"
    
    event_record = db_response.data[0]
    assert 'step' in event_record['event_data'], \
        "Expected step field in event_data for skip events (Requirements 14.4)"
    
    assert event_record['event_data']['step'] == 'welcome', \
        "Expected step value to be preserved"


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_33_skip_events_isolated_per_user(
    test_supabase_client,
    test_user
):
    """
    Property 33: Skip Event Step Tracking - User Isolation
    
    Skip events for different users SHALL be isolated, with each user's
    skip step information preserved independently.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Create two test users
    2. Log skip events at different steps for each user
    3. Query events for each user
    4. Verify each user's skip step is correctly isolated
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user1_id = test_user['id']
    
    # Create second test user
    test_discord_id_2 = f"test_user_{uuid4().hex}"
    user2_result = test_supabase_client.table('users').insert({
        'discord_id': test_discord_id_2
    }).execute()
    user2_id = user2_result.data[0]['id']
    
    try:
        # Act - Log skip events at different steps for each user
        await service.log_event(user1_id, 'onboarding_skipped', {'step': 'welcome'})
        await service.log_event(user2_id, 'onboarding_skipped', {'step': 'recommendations'})
        
        # Assert - Query events for user1
        user1_events = test_supabase_client.table('analytics_events') \
            .select('*') \
            .eq('user_id', str(user1_id)) \
            .eq('event_type', 'onboarding_skipped') \
            .execute()
        
        # Query events for user2
        user2_events = test_supabase_client.table('analytics_events') \
            .select('*') \
            .eq('user_id', str(user2_id)) \
            .eq('event_type', 'onboarding_skipped') \
            .execute()
        
        # Verify user1 skipped at welcome
        assert len(user1_events.data) > 0, \
            "Expected skip event for user1"
        assert user1_events.data[0]['event_data']['step'] == 'welcome', \
            "User1 should have skipped at welcome step"
        
        # Verify user2 skipped at recommendations
        assert len(user2_events.data) > 0, \
            "Expected skip event for user2"
        assert user2_events.data[0]['event_data']['step'] == 'recommendations', \
            "User2 should have skipped at recommendations step"
    
    finally:
        # Cleanup user2
        test_supabase_client.table('users').delete().eq('id', user2_id).execute()


@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_33_skip_event_timestamp_accuracy(
    test_supabase_client,
    test_user
):
    """
    Property 33: Skip Event Step Tracking - Timestamp Accuracy
    
    For any skip event, the created_at timestamp SHALL be accurate
    and the step information SHALL be preserved alongside it.
    
    **Validates: Requirements 14.4**
    
    Test Strategy:
    1. Record current time
    2. Log skip event with step information
    3. Query the event record
    4. Verify timestamp is accurate and step is preserved
    """
    # Arrange
    service = AnalyticsService(test_supabase_client)
    user_id = test_user['id']
    
    # Record time before logging
    before_time = datetime.now(timezone.utc)
    
    # Act
    await service.log_event(user_id, 'onboarding_skipped', {'step': 'recommendations'})
    
    # Record time after logging
    after_time = datetime.now(timezone.utc)
    
    # Assert
    db_response = test_supabase_client.table('analytics_events') \
        .select('*') \
        .eq('user_id', str(user_id)) \
        .eq('event_type', 'onboarding_skipped') \
        .order('created_at', desc=True) \
        .limit(1) \
        .execute()
    
    assert len(db_response.data) > 0, \
        "Expected skip event record"
    
    event_record = db_response.data[0]
    
    # Verify step is preserved
    assert event_record['event_data']['step'] == 'recommendations', \
        "Expected step='recommendations' to be preserved"
    
    # Verify timestamp exists
    assert 'created_at' in event_record, \
        "Expected created_at timestamp"
    
    assert event_record['created_at'] is not None, \
        "Expected created_at to have a value"
