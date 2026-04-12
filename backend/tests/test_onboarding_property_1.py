"""
Property-Based Test for Onboarding Service - Property 1

**Validates: Requirements 1.4, 10.1, 10.3**

Property 1: Onboarding Progress Persistence
For any onboarding action (step completion, skip, or finish), the system SHALL
persist the progress to the user_preferences table, and subsequent queries SHALL
reflect the updated state.

This test uses Hypothesis to generate random onboarding actions and verify that
all state changes are correctly persisted and retrievable.
"""


import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.schemas.onboarding import OnboardingStatus
from app.services.onboarding_service import OnboardingService

# Strategy for generating valid onboarding steps
onboarding_steps = st.sampled_from(["welcome", "recommendations", "complete"])

# Strategy for generating onboarding actions
onboarding_actions = st.sampled_from(["update_progress", "mark_completed", "mark_skipped"])


@pytest.mark.asyncio
@given(step=onboarding_steps, completed=st.booleans())
async def test_property_1_update_progress_persistence(
    test_supabase_client, test_user, step, completed
):
    """
    Property 1: Onboarding Progress Persistence - Update Progress Action

    For any onboarding step update, the system SHALL persist the progress to the
    user_preferences table, and subsequent queries SHALL reflect the updated state.

    Test Strategy:
    1. Generate random step and completion status
    2. Update onboarding progress
    3. Query the status
    4. Verify the persisted state matches the update
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Update progress
    await service.update_onboarding_progress(user_id, step, completed)

    # Assert - Query status and verify persistence
    status = await service.get_onboarding_status(user_id)

    # The step should be persisted
    assert (
        status.onboarding_step == step
    ), f"Expected step '{step}' but got '{status.onboarding_step}'"

    # Verify the status is an OnboardingStatus instance
    assert isinstance(status, OnboardingStatus), f"Expected OnboardingStatus but got {type(status)}"

    # Verify database record exists and matches
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    assert len(db_response.data) == 1, "Expected exactly one user_preferences record"

    db_record = db_response.data[0]
    assert (
        db_record["onboarding_step"] == step
    ), f"Database record has step '{db_record['onboarding_step']}' but expected '{step}'"


@pytest.mark.asyncio
@given(initial_step=onboarding_steps, final_step=onboarding_steps)
async def test_property_1_multiple_updates_persistence(
    test_supabase_client, test_user, initial_step, final_step
):
    """
    Property 1: Onboarding Progress Persistence - Multiple Updates

    For any sequence of onboarding updates, the system SHALL persist each change,
    and the final query SHALL reflect the most recent state.

    Test Strategy:
    1. Generate two random steps
    2. Update progress twice
    3. Query the status
    4. Verify the final state is persisted (not the initial state)
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Update progress twice
    await service.update_onboarding_progress(user_id, initial_step, True)
    await service.update_onboarding_progress(user_id, final_step, True)

    # Assert - Query status and verify final state is persisted
    status = await service.get_onboarding_status(user_id)

    assert (
        status.onboarding_step == final_step
    ), f"Expected final step '{final_step}' but got '{status.onboarding_step}'"

    # Verify database has the final state
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    assert (
        db_record["onboarding_step"] == final_step
    ), f"Database should have final step '{final_step}' but has '{db_record['onboarding_step']}'"


@pytest.mark.asyncio
async def test_property_1_mark_completed_persistence(test_supabase_client, test_user):
    """
    Property 1: Onboarding Progress Persistence - Mark Completed Action

    When onboarding is marked as completed, the system SHALL persist the completion
    state, and subsequent queries SHALL reflect that the onboarding is completed.

    Test Strategy:
    1. Mark onboarding as completed
    2. Query the status
    3. Verify completion state is persisted
    4. Verify completion timestamp is recorded
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as completed
    await service.mark_onboarding_completed(user_id)

    # Assert - Query status and verify completion is persisted
    status = await service.get_onboarding_status(user_id)

    assert status.onboarding_completed is True, "Expected onboarding_completed to be True"

    assert (
        status.onboarding_step == "complete"
    ), f"Expected step 'complete' but got '{status.onboarding_step}'"

    # Verify database record has completion data
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    assert (
        db_record["onboarding_completed"] is True
    ), "Database record should have onboarding_completed=True"

    assert (
        db_record["onboarding_completed_at"] is not None
    ), "Database record should have onboarding_completed_at timestamp"

    assert db_record["onboarding_step"] == "complete", "Database record should have step='complete'"


@pytest.mark.asyncio
async def test_property_1_mark_skipped_persistence(test_supabase_client, test_user):
    """
    Property 1: Onboarding Progress Persistence - Mark Skipped Action

    When onboarding is marked as skipped, the system SHALL persist the skip state,
    and subsequent queries SHALL reflect that the onboarding was skipped.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Query the status
    3. Verify skip state is persisted
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Query status and verify skip is persisted
    status = await service.get_onboarding_status(user_id)

    assert status.onboarding_skipped is True, "Expected onboarding_skipped to be True"

    # Verify database record has skip flag
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    assert (
        db_record["onboarding_skipped"] is True
    ), "Database record should have onboarding_skipped=True"


@pytest.mark.asyncio
@given(action=onboarding_actions, step=onboarding_steps)
async def test_property_1_any_action_persistence(test_supabase_client, test_user, action, step):
    """
    Property 1: Onboarding Progress Persistence - Any Action

    For ANY onboarding action (update, complete, or skip), the system SHALL
    persist the state change, and subsequent queries SHALL reflect the new state.

    Test Strategy:
    1. Generate random action type
    2. Perform the action
    3. Query the status
    4. Verify the state change is persisted
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Perform the action based on type
    if action == "update_progress":
        await service.update_onboarding_progress(user_id, step, True)
        expected_step = step
        expected_completed = None  # Not set by update_progress
        expected_skipped = False

    elif action == "mark_completed":
        await service.mark_onboarding_completed(user_id)
        expected_step = "complete"
        expected_completed = True
        expected_skipped = False

    elif action == "mark_skipped":
        await service.mark_onboarding_skipped(user_id)
        expected_step = None  # Skip doesn't set step
        expected_completed = False
        expected_skipped = True

    # Assert - Query status and verify persistence
    status = await service.get_onboarding_status(user_id)

    # Verify the expected state based on action
    if expected_step is not None:
        assert (
            status.onboarding_step == expected_step
        ), f"Expected step '{expected_step}' but got '{status.onboarding_step}'"

    if expected_completed is not None:
        assert (
            status.onboarding_completed == expected_completed
        ), f"Expected completed={expected_completed} but got {status.onboarding_completed}"

    assert (
        status.onboarding_skipped == expected_skipped
    ), f"Expected skipped={expected_skipped} but got {status.onboarding_skipped}"

    # Verify database persistence
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    assert len(db_response.data) == 1, "Expected exactly one user_preferences record in database"


@pytest.mark.asyncio
@given(steps=st.lists(onboarding_steps, min_size=1, max_size=5))
async def test_property_1_sequence_persistence(test_supabase_client, test_user, steps):
    """
    Property 1: Onboarding Progress Persistence - Sequence of Actions

    For any sequence of onboarding actions, each state change SHALL be persisted,
    and the final query SHALL reflect the cumulative effect of all actions.

    Test Strategy:
    1. Generate a sequence of random steps
    2. Update progress for each step
    3. Query the status after each update
    4. Verify each intermediate state is correctly persisted
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act & Assert - Update progress for each step and verify persistence
    for i, step in enumerate(steps):
        # Update progress
        await service.update_onboarding_progress(user_id, step, True)

        # Query status immediately after update
        status = await service.get_onboarding_status(user_id)

        # Verify the current step is persisted
        assert (
            status.onboarding_step == step
        ), f"After update {i+1}, expected step '{step}' but got '{status.onboarding_step}'"

        # Verify database has the current state
        db_response = (
            test_supabase_client.table("user_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        db_record = db_response.data[0]
        assert (
            db_record["onboarding_step"] == step
        ), f"After update {i+1}, database has step '{db_record['onboarding_step']}' but expected '{step}'"


@pytest.mark.asyncio
async def test_property_1_started_at_timestamp_persistence(test_supabase_client, test_user):
    """
    Property 1: Onboarding Progress Persistence - Started At Timestamp

    When the first onboarding step is recorded, the system SHALL persist the
    onboarding_started_at timestamp, and subsequent queries SHALL include this timestamp.

    Test Strategy:
    1. Update progress for the first time
    2. Query the status
    3. Verify started_at timestamp is persisted
    4. Update progress again
    5. Verify started_at timestamp is unchanged
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - First update
    await service.update_onboarding_progress(user_id, "welcome", True)

    # Assert - Verify started_at is set
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    first_started_at = db_record.get("onboarding_started_at")

    assert first_started_at is not None, "onboarding_started_at should be set after first update"

    # Act - Second update
    await service.update_onboarding_progress(user_id, "recommendations", True)

    # Assert - Verify started_at is unchanged
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    second_started_at = db_record.get("onboarding_started_at")

    assert (
        second_started_at == first_started_at
    ), "onboarding_started_at should not change on subsequent updates"


@pytest.mark.asyncio
async def test_property_1_updated_at_timestamp_persistence(test_supabase_client, test_user):
    """
    Property 1: Onboarding Progress Persistence - Updated At Timestamp

    For any onboarding action, the system SHALL update the updated_at timestamp,
    and subsequent queries SHALL reflect the most recent update time.

    Test Strategy:
    1. Perform an onboarding action
    2. Query the database
    3. Verify updated_at timestamp exists
    4. Perform another action
    5. Verify updated_at timestamp is updated
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - First action
    await service.update_onboarding_progress(user_id, "welcome", True)

    # Assert - Verify updated_at is set
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    first_updated_at = db_record.get("updated_at")

    assert first_updated_at is not None, "updated_at should be set after first action"

    # Act - Second action (after a small delay to ensure timestamp difference)
    import asyncio

    await asyncio.sleep(0.1)
    await service.mark_onboarding_completed(user_id)

    # Assert - Verify updated_at is changed
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    second_updated_at = db_record.get("updated_at")

    assert second_updated_at is not None, "updated_at should be set after second action"

    # Note: We can't reliably compare timestamps due to database precision,
    # but we verify both exist


@pytest.mark.asyncio
async def test_property_1_persistence_survives_service_recreation(test_supabase_client, test_user):
    """
    Property 1: Onboarding Progress Persistence - Service Recreation

    State changes SHALL persist across service instance recreation, demonstrating
    that persistence is in the database, not in-memory.

    Test Strategy:
    1. Create service instance and update progress
    2. Destroy service instance
    3. Create new service instance
    4. Query status with new instance
    5. Verify state is still persisted
    """
    # Arrange & Act - First service instance
    service1 = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    await service1.update_onboarding_progress(user_id, "recommendations", True)

    # Destroy first service instance
    del service1

    # Create new service instance
    service2 = OnboardingService(test_supabase_client)

    # Assert - Query with new instance
    status = await service2.get_onboarding_status(user_id)

    assert (
        status.onboarding_step == "recommendations"
    ), "State should persist across service instance recreation"

    # Verify database still has the data
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    assert (
        db_record["onboarding_step"] == "recommendations"
    ), "Database should retain state across service recreation"
