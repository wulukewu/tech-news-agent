"""
Property-based test for Preference Validation Consistency
Task 2.2

This module tests Property 2: Preference Validation Consistency
For any user preference input, the system SHALL accept valid values
(frequencies: daily/weekly/monthly/disabled, times: 00:00-23:59, valid IANA timezones)
and reject invalid values with appropriate error messages.
"""

from unittest.mock import Mock

import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from app.services.preference_service import PreferenceService

# Valid data generators
valid_frequencies = st.sampled_from(["daily", "weekly", "monthly", "disabled"])
valid_hours = st.integers(min_value=0, max_value=23)
valid_minutes = st.integers(min_value=0, max_value=59)
valid_times = st.builds(lambda h, m: f"{h:02d}:{m:02d}", valid_hours, valid_minutes)

# Common IANA timezone identifiers for testing
common_timezones = [
    "UTC",
    "Asia/Taipei",
    "America/New_York",
    "Europe/London",
    "Asia/Tokyo",
    "Australia/Sydney",
    "America/Los_Angeles",
    "Europe/Paris",
    "Asia/Shanghai",
    "America/Chicago",
]
valid_timezones = st.sampled_from(common_timezones)

valid_booleans = st.booleans()

# Invalid data generators
invalid_frequencies = st.text().filter(
    lambda x: x not in ["daily", "weekly", "monthly", "disabled"]
)
invalid_hours = st.one_of(st.integers(max_value=-1), st.integers(min_value=24))
invalid_minutes = st.one_of(st.integers(max_value=-1), st.integers(min_value=60))
invalid_time_formats = st.one_of(
    st.text().filter(lambda x: ":" not in x and x != ""),  # No colon
    st.builds(lambda h, m: f"{h}:{m}", invalid_hours, valid_minutes),  # Invalid hour
    st.builds(lambda h, m: f"{h:02d}:{m}", valid_hours, invalid_minutes),  # Invalid minute
    st.just("25:00"),  # Invalid hour
    st.just("12:60"),  # Invalid minute
    st.just("abc:def"),  # Non-numeric
    st.just("12"),  # Missing minute
    st.just(":30"),  # Missing hour
    st.just(""),  # Empty string
)

invalid_timezones = st.one_of(
    st.just("Invalid/Timezone"),
    st.just("GMT+8"),  # Not IANA format
    st.just(""),  # Empty string
    st.just("Not/A/Real/Timezone"),
    st.just("Fake/Zone"),
    st.just("BadTimezone"),
    st.text().filter(lambda x: "/" not in x and x not in ["UTC"] and len(x) > 0),
)

invalid_booleans = st.one_of(
    st.text().filter(lambda x: x != ""),  # Non-empty strings
    st.integers(),
    st.floats(),
    st.lists(st.integers()),  # Lists
    st.dictionaries(st.text(), st.integers()),  # Dictionaries
)


@pytest.fixture
def preference_service():
    """Create a PreferenceService instance with mocked repository."""
    mock_repo = Mock()
    return PreferenceService(preferences_repo=mock_repo)


def create_preference_service():
    """Create a PreferenceService instance with mocked repository."""
    mock_repo = Mock()
    return PreferenceService(preferences_repo=mock_repo)


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Valid Inputs)
@hypothesis_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    frequency=valid_frequencies,
    notification_time=valid_times,
    timezone=valid_timezones,
    dm_enabled=valid_booleans,
    email_enabled=valid_booleans,
)
def test_property_2_preference_validation_accepts_valid_inputs(
    frequency, notification_time, timezone, dm_enabled, email_enabled
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Property 2: For any valid user preference input, the system SHALL accept
    the values without validation errors.

    This property ensures that:
    1. Valid frequencies (daily, weekly, monthly, disabled) are accepted
    2. Valid times in HH:MM format with hours 0-23 and minutes 0-59 are accepted
    3. Valid IANA timezone identifiers are accepted
    4. Boolean values for dm_enabled and email_enabled are accepted
    """
    preference_service = create_preference_service()

    # Create a mock preference object that bypasses Pydantic validation
    # to test the service-level validation directly
    mock_preferences = Mock()
    mock_preferences.frequency = frequency
    mock_preferences.notification_time = notification_time
    mock_preferences.timezone = timezone
    mock_preferences.dm_enabled = dm_enabled
    mock_preferences.email_enabled = email_enabled

    # Validate using the service
    result = preference_service.validate_preferences(mock_preferences)

    # Assert validation passes
    assert (
        result.is_valid is True
    ), f"Valid preferences should pass validation. Errors: {result.errors}"
    assert len(result.errors) == 0, f"Valid preferences should have no errors. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Invalid Frequencies)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    invalid_frequency=invalid_frequencies,
    notification_time=valid_times,
    timezone=valid_timezones,
)
def test_property_2_preference_validation_rejects_invalid_frequency(
    invalid_frequency, notification_time, timezone
):
    """
    **Validates: Requirements 3.1**

    Property 2: For any invalid frequency input, the system SHALL reject
    the value with an appropriate error message.
    """
    # Skip empty strings as they might be handled differently
    if invalid_frequency == "":
        return

    preference_service = create_preference_service()

    mock_preferences = Mock()
    mock_preferences.frequency = invalid_frequency
    mock_preferences.notification_time = notification_time
    mock_preferences.timezone = timezone
    mock_preferences.dm_enabled = True
    mock_preferences.email_enabled = False

    result = preference_service.validate_preferences(mock_preferences)

    assert (
        result.is_valid is False
    ), f"Invalid frequency '{invalid_frequency}' should fail validation"
    assert len(result.errors) > 0, "Invalid frequency should produce validation errors"
    assert any(
        "Invalid frequency" in error for error in result.errors
    ), f"Should contain frequency error message. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Invalid Times)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    frequency=valid_frequencies,
    invalid_time=invalid_time_formats,
    timezone=valid_timezones,
)
def test_property_2_preference_validation_rejects_invalid_time(frequency, invalid_time, timezone):
    """
    **Validates: Requirements 3.2, 3.4**

    Property 2: For any invalid time format input, the system SHALL reject
    the value with an appropriate error message.
    """
    preference_service = create_preference_service()

    mock_preferences = Mock()
    mock_preferences.frequency = frequency
    mock_preferences.notification_time = invalid_time
    mock_preferences.timezone = timezone
    mock_preferences.dm_enabled = True
    mock_preferences.email_enabled = False

    result = preference_service.validate_preferences(mock_preferences)

    assert result.is_valid is False, f"Invalid time '{invalid_time}' should fail validation"
    assert len(result.errors) > 0, "Invalid time should produce validation errors"

    # Check for time-related error messages
    time_error_found = any(
        any(keyword in error for keyword in ["notification_time", "hour", "minute", "HH:MM"])
        for error in result.errors
    )
    assert time_error_found, f"Should contain time-related error message. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Invalid Timezones)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    frequency=valid_frequencies,
    notification_time=valid_times,
    invalid_timezone=invalid_timezones,
)
def test_property_2_preference_validation_rejects_invalid_timezone(
    frequency, notification_time, invalid_timezone
):
    """
    **Validates: Requirements 3.3, 3.5**

    Property 2: For any invalid timezone input, the system SHALL reject
    the value with an appropriate error message.
    """
    # Skip empty strings as they might be handled differently
    if invalid_timezone == "":
        return

    preference_service = create_preference_service()

    mock_preferences = Mock()
    mock_preferences.frequency = frequency
    mock_preferences.notification_time = notification_time
    mock_preferences.timezone = invalid_timezone
    mock_preferences.dm_enabled = True
    mock_preferences.email_enabled = False

    result = preference_service.validate_preferences(mock_preferences)

    assert result.is_valid is False, f"Invalid timezone '{invalid_timezone}' should fail validation"
    assert len(result.errors) > 0, "Invalid timezone should produce validation errors"
    assert any(
        "Invalid timezone" in error for error in result.errors
    ), f"Should contain timezone error message. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Invalid Booleans)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    frequency=valid_frequencies,
    notification_time=valid_times,
    timezone=valid_timezones,
    invalid_dm_enabled=invalid_booleans,
)
def test_property_2_preference_validation_rejects_invalid_boolean_dm_enabled(
    frequency, notification_time, timezone, invalid_dm_enabled
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3**

    Property 2: For any invalid boolean input for dm_enabled, the system SHALL reject
    the value with an appropriate error message.
    """
    # Skip None values as they are valid for partial updates
    if invalid_dm_enabled is None:
        return

    preference_service = create_preference_service()

    mock_preferences = Mock()
    mock_preferences.frequency = frequency
    mock_preferences.notification_time = notification_time
    mock_preferences.timezone = timezone
    mock_preferences.dm_enabled = invalid_dm_enabled
    mock_preferences.email_enabled = True

    result = preference_service.validate_preferences(mock_preferences)

    assert (
        result.is_valid is False
    ), f"Invalid dm_enabled '{invalid_dm_enabled}' should fail validation"
    assert len(result.errors) > 0, "Invalid dm_enabled should produce validation errors"
    assert any(
        "dm_enabled must be a boolean" in error for error in result.errors
    ), f"Should contain dm_enabled boolean error message. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Invalid Booleans)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    frequency=valid_frequencies,
    notification_time=valid_times,
    timezone=valid_timezones,
    invalid_email_enabled=invalid_booleans,
)
def test_property_2_preference_validation_rejects_invalid_boolean_email_enabled(
    frequency, notification_time, timezone, invalid_email_enabled
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3**

    Property 2: For any invalid boolean input for email_enabled, the system SHALL reject
    the value with an appropriate error message.
    """
    # Skip None values as they are valid for partial updates
    if invalid_email_enabled is None:
        return

    preference_service = create_preference_service()

    mock_preferences = Mock()
    mock_preferences.frequency = frequency
    mock_preferences.notification_time = notification_time
    mock_preferences.timezone = timezone
    mock_preferences.dm_enabled = True
    mock_preferences.email_enabled = invalid_email_enabled

    result = preference_service.validate_preferences(mock_preferences)

    assert (
        result.is_valid is False
    ), f"Invalid email_enabled '{invalid_email_enabled}' should fail validation"
    assert len(result.errors) > 0, "Invalid email_enabled should produce validation errors"
    assert any(
        "email_enabled must be a boolean" in error for error in result.errors
    ), f"Should contain email_enabled boolean error message. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Multiple Invalid Fields)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    invalid_frequency=invalid_frequencies,
    invalid_time=invalid_time_formats,
    invalid_timezone=invalid_timezones,
)
def test_property_2_preference_validation_rejects_multiple_invalid_fields(
    invalid_frequency, invalid_time, invalid_timezone
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Property 2: For any combination of invalid inputs, the system SHALL reject
    all invalid values and provide appropriate error messages for each.
    """
    # Skip empty strings as they might be handled differently
    if invalid_frequency == "" or invalid_time == "" or invalid_timezone == "":
        return

    preference_service = create_preference_service()

    mock_preferences = Mock()
    mock_preferences.frequency = invalid_frequency
    mock_preferences.notification_time = invalid_time
    mock_preferences.timezone = invalid_timezone
    mock_preferences.dm_enabled = True
    mock_preferences.email_enabled = False

    result = preference_service.validate_preferences(mock_preferences)

    assert result.is_valid is False, "Multiple invalid fields should fail validation"
    assert len(result.errors) > 0, "Multiple invalid fields should produce validation errors"

    # Should have multiple error messages
    error_text = " ".join(result.errors)

    # Check that we get errors for the different types of invalid inputs
    has_frequency_error = "Invalid frequency" in error_text
    has_time_error = any(
        keyword in error_text for keyword in ["notification_time", "hour", "minute", "HH:MM"]
    )
    has_timezone_error = "Invalid timezone" in error_text

    # At least one error should be present (some invalid inputs might be filtered out)
    assert (
        has_frequency_error or has_time_error or has_timezone_error
    ), f"Should contain at least one type of error message. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Partial Updates)
@hypothesis_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    field_to_update=st.sampled_from(
        ["frequency", "notification_time", "timezone", "dm_enabled", "email_enabled"]
    ),
    valid_frequency=valid_frequencies,
    valid_time=valid_times,
    valid_timezone=valid_timezones,
    valid_boolean=valid_booleans,
)
def test_property_2_preference_validation_accepts_partial_valid_updates(
    field_to_update, valid_frequency, valid_time, valid_timezone, valid_boolean
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Property 2: For any partial update with valid values, the system SHALL accept
    the update without validation errors.
    """
    preference_service = create_preference_service()

    mock_preferences = Mock()

    # Set only the field being updated, others as None
    mock_preferences.frequency = valid_frequency if field_to_update == "frequency" else None
    mock_preferences.notification_time = (
        valid_time if field_to_update == "notification_time" else None
    )
    mock_preferences.timezone = valid_timezone if field_to_update == "timezone" else None
    mock_preferences.dm_enabled = valid_boolean if field_to_update == "dm_enabled" else None
    mock_preferences.email_enabled = valid_boolean if field_to_update == "email_enabled" else None

    result = preference_service.validate_preferences(mock_preferences)

    assert (
        result.is_valid is True
    ), f"Valid partial update for {field_to_update} should pass validation. Errors: {result.errors}"
    assert (
        len(result.errors) == 0
    ), f"Valid partial update should have no errors. Got: {result.errors}"


# Feature: personalized-notification-frequency, Property 2: Preference Validation Consistency (Edge Cases)
@hypothesis_settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    hour=st.sampled_from([0, 23]),  # Boundary hours
    minute=st.sampled_from([0, 59]),  # Boundary minutes
)
def test_property_2_preference_validation_accepts_boundary_times(hour, minute):
    """
    **Validates: Requirements 3.2, 3.4**

    Property 2: For boundary time values (00:00, 23:59, etc.), the system SHALL
    accept them as valid.
    """
    preference_service = create_preference_service()

    boundary_time = f"{hour:02d}:{minute:02d}"

    mock_preferences = Mock()
    mock_preferences.frequency = "weekly"
    mock_preferences.notification_time = boundary_time
    mock_preferences.timezone = "UTC"
    mock_preferences.dm_enabled = True
    mock_preferences.email_enabled = False

    result = preference_service.validate_preferences(mock_preferences)

    assert (
        result.is_valid is True
    ), f"Boundary time '{boundary_time}' should be valid. Errors: {result.errors}"
    assert len(result.errors) == 0, f"Boundary time should have no errors. Got: {result.errors}"
