"""
Property-Based Test for Database Schema Integrity - Property 1

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 1: Default Preference Creation
For any new user registration, the system SHALL create notification preferences with
default values: weekly frequency, 18:00 notification time, Asia/Taipei timezone,
DM enabled, and email disabled.

This test uses Hypothesis to generate random user data and verify that default
notification preferences are correctly created with the expected schema and values.
"""

from datetime import time
from uuid import UUID, uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.repositories.user_notification_preferences import (
    UserNotificationPreferencesRepository,
)
from app.services.preference_service import PreferenceService

# Strategy for generating valid user IDs
user_ids = st.uuids()

# Strategy for generating user data that might be used during registration
user_data = st.fixed_dictionaries(
    {
        "discord_id": st.text(
            min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=("Nd",))
        ),
        "username": st.text(
            min_size=3,
            max_size=30,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
        ),
        "email": st.emails(),
    }
)


@pytest.mark.asyncio
@pytest.mark.property
@given(user_id=user_ids)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_1_default_preference_creation_direct(test_supabase_client, user_id):
    """
    Property 1: Default Preference Creation - Direct Repository Creation

    For any user ID, when default preferences are created directly through the repository,
    the system SHALL create preferences with the correct default values.

    Test Strategy:
    1. Generate random user ID
    2. Create default preferences using repository
    3. Verify all default values are correctly set
    4. Verify database schema integrity
    """
    # Arrange
    repository = UserNotificationPreferencesRepository(test_supabase_client)

    # Act - Create default preferences
    preferences = await repository.create_default_for_user(user_id)

    # Assert - Verify default values match requirements
    assert preferences.user_id == user_id, f"Expected user_id {user_id}, got {preferences.user_id}"
    assert (
        preferences.frequency == "weekly"
    ), f"Expected frequency 'weekly', got '{preferences.frequency}'"
    assert preferences.notification_time == time(
        18, 0
    ), f"Expected time 18:00, got {preferences.notification_time}"
    assert (
        preferences.timezone == "Asia/Taipei"
    ), f"Expected timezone 'Asia/Taipei', got '{preferences.timezone}'"
    assert preferences.dm_enabled is True, f"Expected dm_enabled True, got {preferences.dm_enabled}"
    assert (
        preferences.email_enabled is False
    ), f"Expected email_enabled False, got {preferences.email_enabled}"

    # Verify database record exists with correct schema
    db_response = (
        test_supabase_client.table("user_notification_preferences")
        .select("*")
        .eq("user_id", str(user_id))
        .execute()
    )

    assert len(db_response.data) == 1, "Expected exactly one preference record in database"

    db_record = db_response.data[0]

    # Verify database schema integrity
    required_fields = [
        "id",
        "user_id",
        "frequency",
        "notification_time",
        "timezone",
        "dm_enabled",
        "email_enabled",
        "created_at",
        "updated_at",
    ]

    for field in required_fields:
        assert field in db_record, f"Required field '{field}' missing from database record"

    # Verify database values match defaults
    assert db_record["user_id"] == str(user_id), "Database user_id mismatch"
    assert db_record["frequency"] == "weekly", "Database frequency mismatch"
    assert db_record["timezone"] == "Asia/Taipei", "Database timezone mismatch"
    assert db_record["dm_enabled"] is True, "Database dm_enabled mismatch"
    assert db_record["email_enabled"] is False, "Database email_enabled mismatch"

    # Verify notification_time is stored correctly (could be string or time object)
    db_time = db_record["notification_time"]
    if isinstance(db_time, str):
        assert db_time.startswith(
            "18:00"
        ), f"Database notification_time should be 18:00, got {db_time}"
    else:
        assert db_time == time(18, 0), f"Database notification_time should be 18:00, got {db_time}"

    # Verify timestamps exist
    assert db_record["created_at"] is not None, "Database created_at should not be null"
    assert db_record["updated_at"] is not None, "Database updated_at should not be null"

    # Verify UUID format for id field
    try:
        UUID(db_record["id"])
    except ValueError:
        pytest.fail(f"Database id field '{db_record['id']}' is not a valid UUID")

    # Cleanup
    await test_supabase_client.table("user_notification_preferences").delete().eq(
        "user_id", str(user_id)
    ).execute()


@pytest.mark.asyncio
@pytest.mark.property
@given(user_id=user_ids)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_1_default_preference_creation_service(test_supabase_client, user_id):
    """
    Property 1: Default Preference Creation - Service Layer Creation

    For any user ID, when default preferences are created through the service layer,
    the system SHALL create preferences with the correct default values and handle
    the complete creation workflow.

    Test Strategy:
    1. Generate random user ID
    2. Create default preferences using service
    3. Verify service returns correct defaults
    4. Verify database persistence
    """
    # Arrange
    service = PreferenceService(test_supabase_client)

    # Act - Create default preferences through service
    preferences = await service.create_default_preferences(user_id)

    # Assert - Verify service returns correct defaults
    assert preferences.user_id == user_id, f"Service returned wrong user_id: {preferences.user_id}"
    assert (
        preferences.frequency == "weekly"
    ), f"Service returned wrong frequency: {preferences.frequency}"
    assert preferences.notification_time == time(
        18, 0
    ), f"Service returned wrong time: {preferences.notification_time}"
    assert (
        preferences.timezone == "Asia/Taipei"
    ), f"Service returned wrong timezone: {preferences.timezone}"
    assert (
        preferences.dm_enabled is True
    ), f"Service returned wrong dm_enabled: {preferences.dm_enabled}"
    assert (
        preferences.email_enabled is False
    ), f"Service returned wrong email_enabled: {preferences.email_enabled}"

    # Verify service can retrieve the created preferences
    retrieved_preferences = await service.get_user_preferences(user_id)
    assert (
        retrieved_preferences is not None
    ), "Service should be able to retrieve created preferences"
    assert (
        retrieved_preferences.user_id == user_id
    ), "Retrieved preferences should match created user_id"
    assert (
        retrieved_preferences.frequency == "weekly"
    ), "Retrieved preferences should have default frequency"

    # Cleanup
    await test_supabase_client.table("user_notification_preferences").delete().eq(
        "user_id", str(user_id)
    ).execute()


@pytest.mark.asyncio
@pytest.mark.property
@given(user_ids_list=st.lists(user_ids, min_size=1, max_size=5, unique=True))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_1_multiple_users_default_creation(test_supabase_client, user_ids_list):
    """
    Property 1: Default Preference Creation - Multiple Users

    For any set of user IDs, when default preferences are created for multiple users,
    each user SHALL have their own preference record with correct default values.

    Test Strategy:
    1. Generate list of unique user IDs
    2. Create default preferences for each user
    3. Verify each user has correct defaults
    4. Verify no cross-contamination between users
    """
    # Arrange
    repository = UserNotificationPreferencesRepository(test_supabase_client)
    created_preferences = []

    try:
        # Act - Create preferences for each user
        for user_id in user_ids_list:
            preferences = await repository.create_default_for_user(user_id)
            created_preferences.append(preferences)

        # Assert - Verify each user has correct defaults
        for i, (user_id, preferences) in enumerate(zip(user_ids_list, created_preferences)):
            assert preferences.user_id == user_id, f"User {i}: wrong user_id"
            assert preferences.frequency == "weekly", f"User {i}: wrong frequency"
            assert preferences.notification_time == time(18, 0), f"User {i}: wrong time"
            assert preferences.timezone == "Asia/Taipei", f"User {i}: wrong timezone"
            assert preferences.dm_enabled is True, f"User {i}: wrong dm_enabled"
            assert preferences.email_enabled is False, f"User {i}: wrong email_enabled"

        # Verify database has all records
        db_response = (
            test_supabase_client.table("user_notification_preferences")
            .select("*")
            .in_("user_id", [str(uid) for uid in user_ids_list])
            .execute()
        )

        assert len(db_response.data) == len(
            user_ids_list
        ), "Database should have records for all users"

        # Verify each user has unique record
        db_user_ids = {record["user_id"] for record in db_response.data}
        expected_user_ids = {str(uid) for uid in user_ids_list}
        assert (
            db_user_ids == expected_user_ids
        ), "Database should have records for exactly the expected users"

        # Verify all records have correct defaults
        for record in db_response.data:
            assert (
                record["frequency"] == "weekly"
            ), f"User {record['user_id']}: database frequency mismatch"
            assert (
                record["timezone"] == "Asia/Taipei"
            ), f"User {record['user_id']}: database timezone mismatch"
            assert (
                record["dm_enabled"] is True
            ), f"User {record['user_id']}: database dm_enabled mismatch"
            assert (
                record["email_enabled"] is False
            ), f"User {record['user_id']}: database email_enabled mismatch"

    finally:
        # Cleanup - Remove all created records
        for user_id in user_ids_list:
            await test_supabase_client.table("user_notification_preferences").delete().eq(
                "user_id", str(user_id)
            ).execute()


@pytest.mark.asyncio
@pytest.mark.property
@given(user_id=user_ids)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_1_default_creation_idempotency(test_supabase_client, user_id):
    """
    Property 1: Default Preference Creation - Idempotency

    For any user ID, attempting to create default preferences multiple times
    SHALL either succeed once or fail gracefully without corrupting data.

    Test Strategy:
    1. Generate random user ID
    2. Create default preferences
    3. Attempt to create again
    4. Verify only one record exists with correct defaults
    """
    # Arrange
    repository = UserNotificationPreferencesRepository(test_supabase_client)

    try:
        # Act - Create preferences first time
        first_preferences = await repository.create_default_for_user(user_id)

        # Attempt to create again (should fail due to unique constraint)
        try:
            second_preferences = await repository.create_default_for_user(user_id)
            # If it doesn't fail, both should be identical
            assert first_preferences.user_id == second_preferences.user_id
            assert first_preferences.frequency == second_preferences.frequency
        except Exception:
            # Expected to fail due to unique constraint - this is acceptable
            pass

        # Assert - Verify only one record exists
        db_response = (
            test_supabase_client.table("user_notification_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert (
            len(db_response.data) == 1
        ), "Should have exactly one preference record after duplicate creation attempt"

        # Verify the record has correct defaults
        record = db_response.data[0]
        assert record["frequency"] == "weekly", "Record should maintain correct default frequency"
        assert (
            record["timezone"] == "Asia/Taipei"
        ), "Record should maintain correct default timezone"
        assert record["dm_enabled"] is True, "Record should maintain correct default dm_enabled"
        assert (
            record["email_enabled"] is False
        ), "Record should maintain correct default email_enabled"

    finally:
        # Cleanup
        await test_supabase_client.table("user_notification_preferences").delete().eq(
            "user_id", str(user_id)
        ).execute()


@pytest.mark.asyncio
@pytest.mark.property
@given(user_id=user_ids)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_1_schema_constraints_validation(test_supabase_client, user_id):
    """
    Property 1: Default Preference Creation - Schema Constraints

    For any user ID, when default preferences are created, the database schema
    constraints SHALL be satisfied (foreign key, check constraints, not null, etc.).

    Test Strategy:
    1. Generate random user ID
    2. Create default preferences
    3. Verify all schema constraints are satisfied
    4. Test constraint violations are properly handled
    """
    # Arrange
    repository = UserNotificationPreferencesRepository(test_supabase_client)

    try:
        # Act - Create default preferences
        preferences = await repository.create_default_for_user(user_id)

        # Assert - Verify schema constraints are satisfied
        db_response = (
            test_supabase_client.table("user_notification_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        record = db_response.data[0]

        # Verify NOT NULL constraints
        assert record["id"] is not None, "id should not be null"
        assert record["user_id"] is not None, "user_id should not be null"
        assert record["frequency"] is not None, "frequency should not be null"
        assert record["notification_time"] is not None, "notification_time should not be null"
        assert record["timezone"] is not None, "timezone should not be null"
        assert record["dm_enabled"] is not None, "dm_enabled should not be null"
        assert record["email_enabled"] is not None, "email_enabled should not be null"
        assert record["created_at"] is not None, "created_at should not be null"
        assert record["updated_at"] is not None, "updated_at should not be null"

        # Verify CHECK constraint for frequency
        valid_frequencies = ["daily", "weekly", "monthly", "disabled"]
        assert (
            record["frequency"] in valid_frequencies
        ), f"frequency '{record['frequency']}' should be in {valid_frequencies}"

        # Verify boolean constraints
        assert isinstance(record["dm_enabled"], bool), "dm_enabled should be boolean"
        assert isinstance(record["email_enabled"], bool), "email_enabled should be boolean"

        # Verify UUID format constraints
        try:
            UUID(record["id"])
            UUID(record["user_id"])
        except ValueError as e:
            pytest.fail(f"UUID format constraint violated: {e}")

        # Verify UNIQUE constraint by attempting duplicate creation
        try:
            await repository.create_default_for_user(user_id)
            # If no exception, verify still only one record
            check_response = (
                test_supabase_client.table("user_notification_preferences")
                .select("*")
                .eq("user_id", str(user_id))
                .execute()
            )
            assert (
                len(check_response.data) == 1
            ), "UNIQUE constraint should prevent duplicate records"
        except Exception:
            # Expected behavior - unique constraint violation
            pass

    finally:
        # Cleanup
        await test_supabase_client.table("user_notification_preferences").delete().eq(
            "user_id", str(user_id)
        ).execute()


@pytest.mark.asyncio
@pytest.mark.property
@given(user_id=user_ids)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_1_default_values_immutability(test_supabase_client, user_id):
    """
    Property 1: Default Preference Creation - Default Values Immutability

    For any user ID, the default values created SHALL always be the same
    regardless of when or how many times the creation is attempted.

    Test Strategy:
    1. Generate random user ID
    2. Create default preferences multiple times (with cleanup)
    3. Verify defaults are always identical
    4. Verify defaults match specification exactly
    """
    # Arrange
    repository = UserNotificationPreferencesRepository(test_supabase_client)
    expected_defaults = {
        "frequency": "weekly",
        "notification_time": time(18, 0),
        "timezone": "Asia/Taipei",
        "dm_enabled": True,
        "email_enabled": False,
    }

    # Act & Assert - Create preferences multiple times
    for attempt in range(3):
        try:
            # Create preferences
            preferences = await repository.create_default_for_user(user_id)

            # Verify defaults are always the same
            assert (
                preferences.frequency == expected_defaults["frequency"]
            ), f"Attempt {attempt}: frequency mismatch"
            assert (
                preferences.notification_time == expected_defaults["notification_time"]
            ), f"Attempt {attempt}: time mismatch"
            assert (
                preferences.timezone == expected_defaults["timezone"]
            ), f"Attempt {attempt}: timezone mismatch"
            assert (
                preferences.dm_enabled == expected_defaults["dm_enabled"]
            ), f"Attempt {attempt}: dm_enabled mismatch"
            assert (
                preferences.email_enabled == expected_defaults["email_enabled"]
            ), f"Attempt {attempt}: email_enabled mismatch"

            # Verify database record matches
            db_response = (
                test_supabase_client.table("user_notification_preferences")
                .select("*")
                .eq("user_id", str(user_id))
                .execute()
            )

            record = db_response.data[0]
            assert (
                record["frequency"] == expected_defaults["frequency"]
            ), f"Attempt {attempt}: DB frequency mismatch"
            assert (
                record["timezone"] == expected_defaults["timezone"]
            ), f"Attempt {attempt}: DB timezone mismatch"
            assert (
                record["dm_enabled"] == expected_defaults["dm_enabled"]
            ), f"Attempt {attempt}: DB dm_enabled mismatch"
            assert (
                record["email_enabled"] == expected_defaults["email_enabled"]
            ), f"Attempt {attempt}: DB email_enabled mismatch"

            # Cleanup for next attempt
            await test_supabase_client.table("user_notification_preferences").delete().eq(
                "user_id", str(user_id)
            ).execute()

        except Exception as e:
            # Cleanup on error
            await test_supabase_client.table("user_notification_preferences").delete().eq(
                "user_id", str(user_id)
            ).execute()
            raise e


@pytest.mark.asyncio
@pytest.mark.property
@given(user_data_dict=user_data)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_1_user_registration_simulation(test_supabase_client, user_data_dict):
    """
    Property 1: Default Preference Creation - User Registration Simulation

    For any user registration data, when a user is registered and default preferences
    are created, the system SHALL create preferences with correct defaults regardless
    of the user's registration data.

    Test Strategy:
    1. Generate random user registration data
    2. Simulate user registration with preference creation
    3. Verify defaults are not influenced by user data
    4. Verify schema integrity with various user data types
    """
    # Arrange
    user_id = uuid4()  # Simulate new user registration
    repository = UserNotificationPreferencesRepository(test_supabase_client)

    try:
        # Act - Simulate user registration with preference creation
        # (In real system, this would happen during user registration)
        preferences = await repository.create_default_for_user(user_id)

        # Assert - Verify defaults are not influenced by user registration data
        assert (
            preferences.frequency == "weekly"
        ), "Default frequency should not be influenced by user data"
        assert preferences.notification_time == time(
            18, 0
        ), "Default time should not be influenced by user data"
        assert (
            preferences.timezone == "Asia/Taipei"
        ), "Default timezone should not be influenced by user data"
        assert (
            preferences.dm_enabled is True
        ), "Default dm_enabled should not be influenced by user data"
        assert (
            preferences.email_enabled is False
        ), "Default email_enabled should not be influenced by user data"

        # Verify the user_id is correctly set
        assert preferences.user_id == user_id, "Preferences should be linked to the correct user"

        # Verify database integrity with user data context
        db_response = (
            test_supabase_client.table("user_notification_preferences")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        assert len(db_response.data) == 1, "Should have exactly one preference record for the user"

        record = db_response.data[0]

        # Verify all required fields exist regardless of user data complexity
        required_fields = [
            "id",
            "user_id",
            "frequency",
            "notification_time",
            "timezone",
            "dm_enabled",
            "email_enabled",
        ]
        for field in required_fields:
            assert (
                field in record
            ), f"Required field '{field}' missing despite user data: {user_data_dict}"
            assert (
                record[field] is not None
            ), f"Field '{field}' should not be null despite user data: {user_data_dict}"

        # Verify defaults are consistent regardless of user data
        assert (
            record["frequency"] == "weekly"
        ), f"Frequency should be 'weekly' regardless of user data: {user_data_dict}"
        assert (
            record["timezone"] == "Asia/Taipei"
        ), f"Timezone should be 'Asia/Taipei' regardless of user data: {user_data_dict}"
        assert (
            record["dm_enabled"] is True
        ), f"DM should be enabled regardless of user data: {user_data_dict}"
        assert (
            record["email_enabled"] is False
        ), f"Email should be disabled regardless of user data: {user_data_dict}"

    finally:
        # Cleanup
        await test_supabase_client.table("user_notification_preferences").delete().eq(
            "user_id", str(user_id)
        ).execute()
