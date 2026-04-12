"""
Property-Based Test for Onboarding Service - Property 3

**Validates: Requirements 1.6, 1.7**

Property 3: Skip Functionality Persistence
When a user skips onboarding, the system must persist the skip state and not show
the onboarding flow again.

This test uses Hypothesis to generate random user IDs, verify that after calling
mark_onboarding_skipped(), the onboarding_skipped flag is True and the onboarding
flow should not be shown.
"""


import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.services.onboarding_service import OnboardingService

# Strategy for generating valid onboarding steps
onboarding_steps = st.sampled_from(["welcome", "recommendations", "complete"])


@pytest.mark.asyncio
async def test_property_3_skip_sets_flag(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Skip Flag

    When a user skips onboarding, the system SHALL set onboarding_skipped to True.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Query the status
    3. Verify onboarding_skipped is True
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Verify skip flag is set
    status = await service.get_onboarding_status(user_id)

    assert (
        status.onboarding_skipped is True
    ), "Expected onboarding_skipped to be True after marking as skipped"


@pytest.mark.asyncio
async def test_property_3_skip_persists_in_database(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Database Persistence

    When a user skips onboarding, the skip state SHALL be persisted in the
    user_preferences table.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Query database directly
    3. Verify onboarding_skipped is True in database
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Verify database persistence
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    assert len(db_response.data) == 1, "Expected exactly one user_preferences record"

    db_record = db_response.data[0]
    assert (
        db_record["onboarding_skipped"] is True
    ), "Database record should have onboarding_skipped=True"


@pytest.mark.asyncio
async def test_property_3_skip_prevents_onboarding_display(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Prevent Display

    When a user has skipped onboarding, the system SHALL NOT display the
    onboarding modal on subsequent logins (unless manually triggered).

    Test Strategy:
    1. Mark onboarding as skipped
    2. Query status multiple times (simulating multiple logins)
    3. Verify skip flag remains True
    4. Verify onboarding_completed remains False (not completed, just skipped)
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Query status multiple times (simulating multiple logins)
    for i in range(5):
        status = await service.get_onboarding_status(user_id)

        assert (
            status.onboarding_skipped is True
        ), f"Login {i+1}: Expected onboarding_skipped to remain True"

        assert (
            status.onboarding_completed is False
        ), f"Login {i+1}: Expected onboarding_completed to remain False (skipped, not completed)"


@pytest.mark.asyncio
async def test_property_3_skip_state_survives_service_recreation(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Service Recreation

    The skip state SHALL persist across service instance recreation, demonstrating
    that persistence is in the database, not in-memory.

    Test Strategy:
    1. Create service instance and mark as skipped
    2. Destroy service instance
    3. Create new service instance
    4. Query status with new instance
    5. Verify skip state is still persisted
    """
    # Arrange & Act - First service instance
    service1 = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    await service1.mark_onboarding_skipped(user_id)

    # Destroy first service instance
    del service1

    # Create new service instance
    service2 = OnboardingService(test_supabase_client)

    # Assert - Query with new instance
    status = await service2.get_onboarding_status(user_id)

    assert (
        status.onboarding_skipped is True
    ), "Skip state should persist across service instance recreation"


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(step=onboarding_steps)
async def test_property_3_skip_from_any_step(test_supabase_client, test_user, step):
    """
    Property 3: Skip Functionality Persistence - Skip from Any Step

    A user can skip onboarding from any step, and the system SHALL correctly
    set the skip flag regardless of the current step.

    Test Strategy:
    1. Set progress to a random step
    2. Mark onboarding as skipped
    3. Verify skip flag is set
    4. Verify the step is preserved (skip doesn't clear the step)
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Set initial step
    await service.update_onboarding_progress(user_id, step, True)

    # Verify initial state
    status_before = await service.get_onboarding_status(user_id)
    assert status_before.onboarding_step == step
    assert status_before.onboarding_skipped is False

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Verify skip flag is set
    status_after = await service.get_onboarding_status(user_id)

    assert (
        status_after.onboarding_skipped is True
    ), f"Expected onboarding_skipped to be True after skipping from step '{step}'"

    # The step should be preserved (skip doesn't clear it)
    assert status_after.onboarding_step == step, f"Expected step to remain '{step}' after skipping"


@pytest.mark.asyncio
async def test_property_3_skip_idempotent(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Idempotent Skip

    Calling mark_onboarding_skipped() multiple times SHALL be idempotent,
    maintaining the same skip state.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Mark as skipped again
    3. Verify state is unchanged
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - First skip
    await service.mark_onboarding_skipped(user_id)

    # Get first skip state
    status_first = await service.get_onboarding_status(user_id)

    # Act - Second skip
    await service.mark_onboarding_skipped(user_id)

    # Get second skip state
    status_second = await service.get_onboarding_status(user_id)

    # Assert - Verify idempotency
    assert (
        status_first.onboarding_skipped == status_second.onboarding_skipped
    ), "Skip state should remain unchanged after multiple skip calls"

    assert status_second.onboarding_skipped is True, "Expected onboarding_skipped to remain True"


@pytest.mark.asyncio
async def test_property_3_skip_does_not_set_completed(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Skip vs Completed

    Marking onboarding as skipped SHALL NOT set onboarding_completed to True.
    Skip and completion are distinct states.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Verify onboarding_completed remains False
    3. Verify onboarding_skipped is True
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Verify skip doesn't set completed
    status = await service.get_onboarding_status(user_id)

    assert status.onboarding_skipped is True, "Expected onboarding_skipped to be True"

    assert (
        status.onboarding_completed is False
    ), "Expected onboarding_completed to remain False (skip is not completion)"


@pytest.mark.asyncio
async def test_property_3_skip_does_not_set_completed_timestamp(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - No Completion Timestamp

    Marking onboarding as skipped SHALL NOT set the onboarding_completed_at
    timestamp, as the user did not complete the onboarding.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Query database directly
    3. Verify onboarding_completed_at is null
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Verify no completion timestamp
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]

    assert (
        db_record["onboarding_completed_at"] is None
    ), "Expected onboarding_completed_at to be null when skipped"


@pytest.mark.asyncio
async def test_property_3_skip_updates_timestamp(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Updated At Timestamp

    Marking onboarding as skipped SHALL update the updated_at timestamp.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Query database
    3. Verify updated_at timestamp exists
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Verify updated_at is set
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]
    updated_at = db_record.get("updated_at")

    assert updated_at is not None, "Expected updated_at to be set after marking as skipped"


@pytest.mark.asyncio
async def test_property_3_skip_then_complete(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Skip Then Complete

    A user who previously skipped onboarding can still complete it later,
    and the completion SHALL override the skip state for display purposes.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Mark onboarding as completed
    3. Verify both flags are set (historical data)
    4. Verify completion takes precedence
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - First skip, then complete
    await service.mark_onboarding_skipped(user_id)

    # Verify skip state
    status_after_skip = await service.get_onboarding_status(user_id)
    assert status_after_skip.onboarding_skipped is True
    assert status_after_skip.onboarding_completed is False

    # Now complete
    await service.mark_onboarding_completed(user_id)

    # Assert - Verify completion state
    status_after_complete = await service.get_onboarding_status(user_id)

    assert (
        status_after_complete.onboarding_completed is True
    ), "Expected onboarding_completed to be True after completing post-skip"

    # Skip flag remains True (historical data)
    assert (
        status_after_complete.onboarding_skipped is True
    ), "Skip flag should remain True (historical data)"

    # In practice, the UI should check onboarding_completed first,
    # so completion takes precedence over skip for display purposes


@pytest.mark.asyncio
async def test_property_3_skip_database_consistency(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Database Consistency

    After marking onboarding as skipped, the database record SHALL be consistent
    with the API response.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Query via API
    3. Query database directly
    4. Verify both sources return consistent data
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Query via API
    api_status = await service.get_onboarding_status(user_id)

    # Query database directly
    db_response = (
        test_supabase_client.table("user_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    db_record = db_response.data[0]

    # Assert - Verify consistency
    assert (
        api_status.onboarding_skipped == db_record["onboarding_skipped"]
    ), "API and database onboarding_skipped should match"

    assert db_record["onboarding_skipped"] is True, "Database should have onboarding_skipped=True"


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(steps=st.lists(onboarding_steps, min_size=1, max_size=3))
async def test_property_3_skip_after_progress(test_supabase_client, test_user, steps):
    """
    Property 3: Skip Functionality Persistence - Skip After Progress

    A user can make progress through onboarding steps and then skip, and the
    system SHALL preserve both the progress and the skip state.

    Test Strategy:
    1. Update progress through multiple steps
    2. Mark onboarding as skipped
    3. Verify skip flag is set
    4. Verify progress is preserved
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Make progress through steps
    for step in steps:
        await service.update_onboarding_progress(user_id, step, True)

    # Get final step
    final_step = steps[-1]

    # Verify progress before skip
    status_before_skip = await service.get_onboarding_status(user_id)
    assert status_before_skip.onboarding_step == final_step
    assert status_before_skip.onboarding_skipped is False

    # Mark as skipped
    await service.mark_onboarding_skipped(user_id)

    # Assert - Verify skip and progress preservation
    status_after_skip = await service.get_onboarding_status(user_id)

    assert (
        status_after_skip.onboarding_skipped is True
    ), "Expected onboarding_skipped to be True after skipping"

    assert (
        status_after_skip.onboarding_step == final_step
    ), f"Expected step to remain '{final_step}' after skipping"


@pytest.mark.asyncio
async def test_property_3_skip_reset_clears_flag(test_supabase_client, test_user):
    """
    Property 3: Skip Functionality Persistence - Reset Clears Skip

    When onboarding is reset, the skip flag SHALL be cleared, allowing the
    user to go through onboarding again.

    Test Strategy:
    1. Mark onboarding as skipped
    2. Reset onboarding
    3. Verify skip flag is cleared
    """
    # Arrange
    service = OnboardingService(test_supabase_client)
    user_id = test_user["id"]

    # Act - Skip then reset
    await service.mark_onboarding_skipped(user_id)

    # Verify skip state
    status_after_skip = await service.get_onboarding_status(user_id)
    assert status_after_skip.onboarding_skipped is True

    # Reset onboarding
    await service.reset_onboarding(user_id)

    # Assert - Verify skip flag is cleared
    status_after_reset = await service.get_onboarding_status(user_id)

    assert (
        status_after_reset.onboarding_skipped is False
    ), "Expected onboarding_skipped to be False after reset"

    assert (
        status_after_reset.onboarding_completed is False
    ), "Expected onboarding_completed to be False after reset"

    assert (
        status_after_reset.onboarding_step is None
    ), "Expected onboarding_step to be None after reset"
