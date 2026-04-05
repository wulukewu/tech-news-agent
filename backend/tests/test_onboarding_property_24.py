"""
Property-Based Test for Onboarding Service - Property 24

**Validates: Requirements 10.4, 10.5**

Property 24: Onboarding UI Conditional Display
For any user, before displaying onboarding UI, the system SHALL check user_preferences;
if onboarding_completed is true OR onboarding_skipped is true, onboarding modals SHALL
NOT be displayed (should_show_onboarding = False).

This test uses Hypothesis to generate random user states and verify that the
should_show_onboarding flag is correctly computed based on completion and skip states.

Test Strategy:
- Generate random combinations of onboarding_completed and onboarding_skipped states
- Verify that should_show_onboarding is True only when BOTH flags are False
- Test all four possible state combinations
- Verify the logic persists across service calls

IMPORTANT: Before running these tests, ensure the user_preferences table exists:
  python3 scripts/migrations/apply_user_preferences_migration.py
  
Or apply the migration manually using psql or Supabase Dashboard SQL Editor:
  psql $DATABASE_URL -f scripts/migrations/002_create_user_preferences_table.sql
"""

import pytest
from uuid import uuid4
from hypothesis import given, strategies as st, assume, settings, HealthCheck

from app.services.onboarding_service import OnboardingService, OnboardingServiceError
from app.schemas.onboarding import OnboardingStatus


@pytest.mark.asyncio
@given(
    completed=st.booleans(),
    skipped=st.booleans()
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_24_should_show_onboarding_logic(
    test_supabase_client,
    test_user,
    completed,
    skipped
):
    """
    Property 24: Onboarding UI Conditional Display - Core Logic
    
    For any combination of onboarding_completed and onboarding_skipped states,
    the system SHALL return should_show_onboarding = True ONLY when BOTH
    completed and skipped are False.
    
    Truth table:
    completed | skipped | should_show_onboarding
    ----------|---------|----------------------
    False     | False   | True
    False     | True    | False
    True      | False   | False
    True      | True    | False
    
    Test Strategy:
    1. Generate random completed and skipped states
    2. Set user preferences to these states
    3. Query onboarding status
    4. Verify should_show_onboarding follows the truth table
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Ensure preferences exist
    await service._ensure_preferences_exist(user_id)
    
    # Set the states directly in database
    update_data = {
        'onboarding_completed': completed,
        'onboarding_skipped': skipped,
    }
    
    test_supabase_client.table('user_preferences') \
        .update(update_data) \
        .eq('user_id', str(user_id)) \
        .execute()
    
    # Act - Query status
    status = await service.get_onboarding_status(user_id)
    
    # Assert - Verify should_show_onboarding follows the truth table
    expected_should_show = not completed and not skipped
    
    assert status.should_show_onboarding == expected_should_show, \
        f"For completed={completed}, skipped={skipped}, expected should_show_onboarding={expected_should_show} but got {status.should_show_onboarding}"
    
    # Verify the status reflects the database state
    assert status.onboarding_completed == completed, \
        f"Expected onboarding_completed={completed} but got {status.onboarding_completed}"
    
    assert status.onboarding_skipped == skipped, \
        f"Expected onboarding_skipped={skipped} but got {status.onboarding_skipped}"


@pytest.mark.asyncio
async def test_property_24_new_user_should_show_onboarding(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - New User
    
    For a new user with no preferences record, the system SHALL return
    should_show_onboarding = True (Requirements 10.4).
    
    Test Strategy:
    1. Query status for user with no preferences
    2. Verify should_show_onboarding is True
    3. Verify default states are set correctly
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Ensure no preferences exist (delete if exists)
    test_supabase_client.table('user_preferences') \
        .delete() \
        .eq('user_id', str(user_id)) \
        .execute()
    
    # Act - Query status (will create default preferences)
    status = await service.get_onboarding_status(user_id)
    
    # Assert - New user should see onboarding
    assert status.should_show_onboarding is True, \
        "New user should have should_show_onboarding=True"
    
    assert status.onboarding_completed is False, \
        "New user should have onboarding_completed=False"
    
    assert status.onboarding_skipped is False, \
        "New user should have onboarding_skipped=False"


@pytest.mark.asyncio
async def test_property_24_completed_user_should_not_show_onboarding(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - Completed User
    
    For a user who has completed onboarding, the system SHALL return
    should_show_onboarding = False (Requirements 10.5).
    
    Test Strategy:
    1. Mark onboarding as completed
    2. Query status
    3. Verify should_show_onboarding is False
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Act - Mark as completed
    await service.mark_onboarding_completed(user_id)
    
    # Query status
    status = await service.get_onboarding_status(user_id)
    
    # Assert - Completed user should NOT see onboarding
    assert status.should_show_onboarding is False, \
        "User who completed onboarding should have should_show_onboarding=False"
    
    assert status.onboarding_completed is True, \
        "User should have onboarding_completed=True"


@pytest.mark.asyncio
async def test_property_24_skipped_user_should_not_show_onboarding(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - Skipped User
    
    For a user who has skipped onboarding, the system SHALL return
    should_show_onboarding = False (Requirements 10.5).
    
    Test Strategy:
    1. Mark onboarding as skipped
    2. Query status
    3. Verify should_show_onboarding is False
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)
    
    # Query status
    status = await service.get_onboarding_status(user_id)
    
    # Assert - Skipped user should NOT see onboarding
    assert status.should_show_onboarding is False, \
        "User who skipped onboarding should have should_show_onboarding=False"
    
    assert status.onboarding_skipped is True, \
        "User should have onboarding_skipped=True"


@pytest.mark.asyncio
async def test_property_24_in_progress_user_should_show_onboarding(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - In Progress User
    
    For a user who has started but not completed or skipped onboarding,
    the system SHALL return should_show_onboarding = True.
    
    Test Strategy:
    1. Update progress to an intermediate step
    2. Query status
    3. Verify should_show_onboarding is True
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Act - Update to intermediate step
    await service.update_onboarding_progress(user_id, 'recommendations', False)
    
    # Query status
    status = await service.get_onboarding_status(user_id)
    
    # Assert - In-progress user should still see onboarding
    assert status.should_show_onboarding is True, \
        "User in progress should have should_show_onboarding=True"
    
    assert status.onboarding_completed is False, \
        "User in progress should have onboarding_completed=False"
    
    assert status.onboarding_skipped is False, \
        "User in progress should have onboarding_skipped=False"
    
    assert status.onboarding_step == 'recommendations', \
        "User should be on recommendations step"


@pytest.mark.asyncio
@given(
    step=st.sampled_from(['welcome', 'recommendations', 'complete'])
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_24_progress_update_preserves_should_show_logic(
    test_supabase_client,
    test_user,
    step
):
    """
    Property 24: Onboarding UI Conditional Display - Progress Updates
    
    For any progress update that doesn't mark completion or skip,
    the system SHALL maintain should_show_onboarding = True.
    
    Test Strategy:
    1. Generate random onboarding step
    2. Update progress without completing or skipping
    3. Query status
    4. Verify should_show_onboarding remains True
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Act - Update progress
    await service.update_onboarding_progress(user_id, step, False)
    
    # Query status
    status = await service.get_onboarding_status(user_id)
    
    # Assert - Should still show onboarding
    assert status.should_show_onboarding is True, \
        f"After updating to step '{step}', should_show_onboarding should be True"
    
    assert status.onboarding_step == step, \
        f"Expected step '{step}' but got '{status.onboarding_step}'"


@pytest.mark.asyncio
async def test_property_24_both_completed_and_skipped_should_not_show(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - Both Flags Set
    
    For a user with both onboarding_completed and onboarding_skipped set to True
    (edge case), the system SHALL return should_show_onboarding = False.
    
    Test Strategy:
    1. Set both flags to True directly in database
    2. Query status
    3. Verify should_show_onboarding is False
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Ensure preferences exist
    await service._ensure_preferences_exist(user_id)
    
    # Set both flags to True (edge case)
    test_supabase_client.table('user_preferences') \
        .update({
            'onboarding_completed': True,
            'onboarding_skipped': True
        }) \
        .eq('user_id', str(user_id)) \
        .execute()
    
    # Act - Query status
    status = await service.get_onboarding_status(user_id)
    
    # Assert - Should NOT show onboarding when either flag is True
    assert status.should_show_onboarding is False, \
        "When both completed and skipped are True, should_show_onboarding should be False"


@pytest.mark.asyncio
@given(
    initial_completed=st.booleans(),
    initial_skipped=st.booleans()
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_24_multiple_queries_consistent_result(
    test_supabase_client,
    test_user,
    initial_completed,
    initial_skipped
):
    """
    Property 24: Onboarding UI Conditional Display - Query Consistency
    
    For any user state, multiple queries SHALL return consistent
    should_show_onboarding values without modifying the state.
    
    Test Strategy:
    1. Generate random initial state
    2. Query status multiple times
    3. Verify all queries return the same should_show_onboarding value
    4. Verify state is not modified by queries
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Set initial state
    await service._ensure_preferences_exist(user_id)
    
    test_supabase_client.table('user_preferences') \
        .update({
            'onboarding_completed': initial_completed,
            'onboarding_skipped': initial_skipped
        }) \
        .eq('user_id', str(user_id)) \
        .execute()
    
    # Act - Query status multiple times
    status1 = await service.get_onboarding_status(user_id)
    status2 = await service.get_onboarding_status(user_id)
    status3 = await service.get_onboarding_status(user_id)
    
    # Assert - All queries return consistent results
    assert status1.should_show_onboarding == status2.should_show_onboarding == status3.should_show_onboarding, \
        "Multiple queries should return consistent should_show_onboarding values"
    
    # Verify the expected value
    expected_should_show = not initial_completed and not initial_skipped
    
    assert status1.should_show_onboarding == expected_should_show, \
        f"Expected should_show_onboarding={expected_should_show} but got {status1.should_show_onboarding}"
    
    # Verify state is unchanged
    assert status1.onboarding_completed == status3.onboarding_completed, \
        "Queries should not modify onboarding_completed state"
    
    assert status1.onboarding_skipped == status3.onboarding_skipped, \
        "Queries should not modify onboarding_skipped state"


@pytest.mark.asyncio
async def test_property_24_state_transition_completed_updates_should_show(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - State Transition to Completed
    
    When a user transitions from in-progress to completed, should_show_onboarding
    SHALL change from True to False.
    
    Test Strategy:
    1. Start with in-progress state (should_show = True)
    2. Mark as completed
    3. Query status
    4. Verify should_show_onboarding changed to False
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Start with in-progress state
    await service.update_onboarding_progress(user_id, 'recommendations', False)
    
    # Verify initial state
    status_before = await service.get_onboarding_status(user_id)
    assert status_before.should_show_onboarding is True, \
        "Before completion, should_show_onboarding should be True"
    
    # Act - Mark as completed
    await service.mark_onboarding_completed(user_id)
    
    # Query status after completion
    status_after = await service.get_onboarding_status(user_id)
    
    # Assert - should_show_onboarding changed to False
    assert status_after.should_show_onboarding is False, \
        "After completion, should_show_onboarding should be False"
    
    assert status_after.onboarding_completed is True, \
        "After completion, onboarding_completed should be True"


@pytest.mark.asyncio
async def test_property_24_state_transition_skipped_updates_should_show(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - State Transition to Skipped
    
    When a user transitions from in-progress to skipped, should_show_onboarding
    SHALL change from True to False.
    
    Test Strategy:
    1. Start with in-progress state (should_show = True)
    2. Mark as skipped
    3. Query status
    4. Verify should_show_onboarding changed to False
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Start with in-progress state
    await service.update_onboarding_progress(user_id, 'welcome', False)
    
    # Verify initial state
    status_before = await service.get_onboarding_status(user_id)
    assert status_before.should_show_onboarding is True, \
        "Before skipping, should_show_onboarding should be True"
    
    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)
    
    # Query status after skipping
    status_after = await service.get_onboarding_status(user_id)
    
    # Assert - should_show_onboarding changed to False
    assert status_after.should_show_onboarding is False, \
        "After skipping, should_show_onboarding should be False"
    
    assert status_after.onboarding_skipped is True, \
        "After skipping, onboarding_skipped should be True"


@pytest.mark.asyncio
async def test_property_24_reset_restores_should_show_onboarding(
    test_supabase_client,
    test_user
):
    """
    Property 24: Onboarding UI Conditional Display - Reset Restores Display
    
    When a user resets onboarding after completion or skip, should_show_onboarding
    SHALL return to True (Requirements 10.6, 10.7).
    
    Test Strategy:
    1. Mark onboarding as completed (should_show = False)
    2. Reset onboarding
    3. Query status
    4. Verify should_show_onboarding is True again
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Mark as completed
    await service.mark_onboarding_completed(user_id)
    
    # Verify completed state
    status_completed = await service.get_onboarding_status(user_id)
    assert status_completed.should_show_onboarding is False, \
        "After completion, should_show_onboarding should be False"
    
    # Act - Reset onboarding
    await service.reset_onboarding(user_id)
    
    # Query status after reset
    status_reset = await service.get_onboarding_status(user_id)
    
    # Assert - should_show_onboarding is True again
    assert status_reset.should_show_onboarding is True, \
        "After reset, should_show_onboarding should be True"
    
    assert status_reset.onboarding_completed is False, \
        "After reset, onboarding_completed should be False"
    
    assert status_reset.onboarding_skipped is False, \
        "After reset, onboarding_skipped should be False"


@pytest.mark.asyncio
@given(
    actions=st.lists(
        st.sampled_from(['progress', 'complete', 'skip', 'reset']),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_24_action_sequence_maintains_correct_should_show(
    test_supabase_client,
    test_user,
    actions
):
    """
    Property 24: Onboarding UI Conditional Display - Action Sequence
    
    For any sequence of onboarding actions, should_show_onboarding SHALL
    always reflect the current state correctly.
    
    Test Strategy:
    1. Generate random sequence of actions
    2. Execute each action
    3. After each action, verify should_show_onboarding is correct
    4. Track expected state and compare with actual
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user['id']
    
    # Track expected state
    expected_completed = False
    expected_skipped = False
    
    # Act & Assert - Execute actions and verify state after each
    for i, action in enumerate(actions):
        if action == 'progress':
            await service.update_onboarding_progress(user_id, 'recommendations', False)
            # Progress doesn't change completed or skipped flags
            
        elif action == 'complete':
            await service.mark_onboarding_completed(user_id)
            expected_completed = True
            
        elif action == 'skip':
            await service.mark_onboarding_skipped(user_id)
            expected_skipped = True
            
        elif action == 'reset':
            await service.reset_onboarding(user_id)
            expected_completed = False
            expected_skipped = False
        
        # Query status after action
        status = await service.get_onboarding_status(user_id)
        
        # Verify should_show_onboarding matches expected state
        expected_should_show = not expected_completed and not expected_skipped
        
        assert status.should_show_onboarding == expected_should_show, \
            f"After action {i+1} ('{action}'), expected should_show_onboarding={expected_should_show} but got {status.should_show_onboarding}"
        
        # Verify state flags
        assert status.onboarding_completed == expected_completed, \
            f"After action {i+1} ('{action}'), expected completed={expected_completed} but got {status.onboarding_completed}"
        
        assert status.onboarding_skipped == expected_skipped, \
            f"After action {i+1} ('{action}'), expected skipped={expected_skipped} but got {status.onboarding_skipped}"
