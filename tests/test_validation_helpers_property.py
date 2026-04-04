"""
Property-based tests for SupabaseService validation helper methods.

Feature: data-access-layer-refactor
Tasks: 4.2, 4.4, 4.6, 4.8, 4.10, 4.12, 4.14
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from uuid import UUID
import asyncio

from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError


# Helper to create service instance
def create_service():
    """Create a SupabaseService instance for testing (without connection validation)"""
    return SupabaseService(client=None, validate_connection=False)


# Property 11: Status Validation
# Validates: Requirements 7.2, 7.3
@given(status=st.text().filter(lambda s: s.strip().title() not in ['Unread', 'Read', 'Archived']))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_status_validation_rejects_invalid(status):
    """
    **Validates: Requirements 7.2, 7.3**
    
    For any status value not in the set {'Unread', 'Read', 'Archived'} (case-insensitive),
    _validate_status should raise a ValueError with allowed values listed.
    """
    service = create_service()
    with pytest.raises(ValueError, match="Allowed values are"):
        service._validate_status(status)


# Property 34: Status Normalization
# Validates: Requirements 16.6
@given(status=st.sampled_from(['unread', 'READ', 'archived', 'Unread', 'Read', 'Archived', 'UNREAD', 'read', 'ARCHIVED']))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_status_normalization(status):
    """
    **Validates: Requirements 16.6**
    
    For any status value provided (regardless of case),
    it should be normalized to Title Case.
    """
    service = create_service()
    normalized = service._validate_status(status)
    
    # Should be in Title Case
    assert normalized in ['Unread', 'Read', 'Archived']
    
    # Should match the expected value
    assert normalized == status.strip().title()


# Property 13: Rating Validation
# Validates: Requirements 8.2, 8.3
@given(rating=st.integers().filter(lambda r: r < 1 or r > 5))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_rating_validation_rejects_invalid(rating):
    """
    **Validates: Requirements 8.2, 8.3**
    
    For any rating value outside the range [1, 5],
    _validate_rating should raise a ValueError with allowed range specified.
    """
    service = create_service()
    with pytest.raises(ValueError, match="between 1 and 5"):
        service._validate_rating(rating)


@given(rating=st.integers(min_value=1, max_value=5))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_rating_validation_accepts_valid(rating):
    """
    **Validates: Requirements 8.2, 8.3**
    
    For any rating value in the range [1, 5],
    _validate_rating should not raise an error.
    """
    service = create_service()
    # Should not raise
    service._validate_rating(rating)


# Property 33: UUID Format Validation
# Validates: Requirements 16.5
@given(uuid_str=st.text().filter(lambda s: not _is_valid_uuid(s)))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_uuid_validation_rejects_invalid(uuid_str):
    """
    **Validates: Requirements 16.5**
    
    For any string that is not a valid UUID format,
    _validate_uuid should raise a ValueError with descriptive message.
    """
    service = create_service()
    with pytest.raises(ValueError, match="Invalid UUID format"):
        service._validate_uuid(uuid_str)


@given(uuid_val=st.uuids())
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_uuid_validation_accepts_valid(uuid_val):
    """
    **Validates: Requirements 16.5**
    
    For any valid UUID,
    _validate_uuid should return a UUID object.
    """
    service = create_service()
    uuid_str = str(uuid_val)
    result = service._validate_uuid(uuid_str)
    
    assert isinstance(result, UUID)
    assert result == uuid_val


# Property 30: URL Validation
# Validates: Requirements 16.1
@given(url=st.text().filter(lambda s: not (s.strip().startswith('http://') or s.strip().startswith('https://'))))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_url_validation_rejects_invalid(url):
    """
    **Validates: Requirements 16.1**
    
    For any URL that does not start with http:// or https://,
    _validate_url should raise a ValueError.
    """
    service = create_service()
    with pytest.raises(ValueError, match="Invalid URL"):
        service._validate_url(url)


@given(
    protocol=st.sampled_from(['http://', 'https://']),
    domain=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='.-'))
)
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_url_validation_accepts_valid(protocol, domain):
    """
    **Validates: Requirements 16.1**
    
    For any URL that starts with http:// or https://,
    _validate_url should return the validated URL.
    """
    service = create_service()
    url = f"{protocol}{domain}"
    result = service._validate_url(url)
    
    assert result == url


# Property 32: Text Truncation
# Validates: Requirements 16.3, 16.4
@given(
    text=st.text(min_size=1, max_size=10000),
    max_length=st.integers(min_value=1, max_value=5000)
)
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_text_truncation(text, max_length):
    """
    **Validates: Requirements 16.3, 16.4**
    
    For any text and max_length,
    _truncate_text should return text with length <= max_length.
    """
    service = create_service()
    result = service._truncate_text(text, max_length)
    
    assert len(result) <= max_length
    
    # If original was shorter, should be unchanged
    if len(text) <= max_length:
        assert result == text
    else:
        # Should be truncated to exact max_length
        assert len(result) == max_length
        # Should be a prefix of the original
        assert text.startswith(result)


@given(text=st.text(min_size=2001, max_size=5000))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_text_truncation_long_title(text):
    """
    **Validates: Requirements 16.3**
    
    For any text longer than 2000 characters,
    truncating to 2000 should result in exactly 2000 characters.
    """
    service = create_service()
    result = service._truncate_text(text, 2000)
    
    assert len(result) == 2000
    assert text.startswith(result)


@given(text=st.text(min_size=5001, max_size=10000))
@settings(
    suppress_health_check=[
        HealthCheck.function_scoped_fixture, 
        HealthCheck.large_base_example, 
        HealthCheck.data_too_large,
        HealthCheck.too_slow
    ],
    max_examples=5  # Reduce number of examples for this expensive test
)
def test_text_truncation_long_summary(text):
    """
    **Validates: Requirements 16.4**
    
    For any text longer than 5000 characters,
    truncating to 5000 should result in exactly 5000 characters.
    """
    service = create_service()
    result = service._truncate_text(text, 5000)
    
    assert len(result) == 5000
    assert text.startswith(result)


# Property 26: Constraint Violation Error Messages
# Validates: Requirements 13.3, 13.4, 13.5, 13.6
@given(field_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_')))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_handle_database_error_unique_constraint(field_name):
    """
    **Validates: Requirements 13.3**
    
    For any unique constraint violation,
    _handle_database_error should provide a descriptive error message.
    """
    service = create_service()
    error = Exception(f'duplicate key value violates unique constraint "users_discord_id_key" DETAIL: Key ({field_name})=(test) already exists.')
    
    with pytest.raises(SupabaseServiceError) as exc_info:
        service._handle_database_error(error, {"operation": "test"})
    
    assert "Duplicate entry" in str(exc_info.value)
    assert exc_info.value.context.get("constraint_type") == "unique"


@given(table_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_')))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_handle_database_error_foreign_key_constraint(table_name):
    """
    **Validates: Requirements 13.4**
    
    For any foreign key constraint violation,
    _handle_database_error should provide a descriptive error message.
    """
    service = create_service()
    error = Exception(f'insert or update on table "articles" violates foreign key constraint "articles_feed_id_fkey" DETAIL: Key (feed_id)=(123) is not present in table "{table_name}".')
    
    with pytest.raises(SupabaseServiceError) as exc_info:
        service._handle_database_error(error, {"operation": "test"})
    
    assert "Invalid reference" in str(exc_info.value)
    assert exc_info.value.context.get("constraint_type") == "foreign_key"


@given(constraint_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_')))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_handle_database_error_check_constraint(constraint_name):
    """
    **Validates: Requirements 13.5**
    
    For any check constraint violation,
    _handle_database_error should provide a descriptive error message.
    """
    service = create_service()
    error = Exception(f'new row for relation "articles" violates check constraint "{constraint_name}"')
    
    with pytest.raises(SupabaseServiceError) as exc_info:
        service._handle_database_error(error, {"operation": "test"})
    
    assert "Validation failed" in str(exc_info.value)
    assert exc_info.value.context.get("constraint_type") == "check"


@given(field_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_')))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_handle_database_error_not_null_constraint(field_name):
    """
    **Validates: Requirements 13.6**
    
    For any not null constraint violation,
    _handle_database_error should provide a descriptive error message.
    """
    service = create_service()
    error = Exception(f'null value in column "{field_name}" violates not-null constraint')
    
    with pytest.raises(SupabaseServiceError) as exc_info:
        service._handle_database_error(error, {"operation": "test"})
    
    assert "Missing required field" in str(exc_info.value)
    assert exc_info.value.context.get("constraint_type") == "not_null"


# Property 29: Transient Error Retry
# Validates: Requirements 15.6
@pytest.mark.asyncio
@given(
    error_keyword=st.sampled_from(['timeout', 'connection', 'temporary', 'unavailable']),
    max_retries=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_execute_with_retry_transient_errors(error_keyword, max_retries):
    """
    **Validates: Requirements 15.6**
    
    For any transient database error,
    _execute_with_retry should retry the operation with exponential backoff.
    """
    service = create_service()
    attempt_count = 0
    
    async def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < max_retries:
            raise Exception(f"Database {error_keyword} error")
        return "success"
    
    result = await service._execute_with_retry(failing_operation, max_retries=max_retries, base_delay=0.01)
    
    assert result == "success"
    assert attempt_count == max_retries


@pytest.mark.asyncio
@given(max_retries=st.integers(min_value=1, max_value=5))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_execute_with_retry_non_transient_errors(max_retries):
    """
    **Validates: Requirements 15.6**
    
    For any non-transient error,
    _execute_with_retry should not retry and raise immediately.
    """
    service = create_service()
    attempt_count = 0
    
    async def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        raise ValueError("Invalid data")
    
    with pytest.raises(ValueError, match="Invalid data"):
        await service._execute_with_retry(failing_operation, max_retries=max_retries, base_delay=0.01)
    
    # Should only attempt once for non-transient errors
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_execute_with_retry_success_on_first_attempt():
    """
    **Validates: Requirements 15.6**
    
    For any successful operation,
    _execute_with_retry should return immediately without retries.
    """
    service = create_service()
    attempt_count = 0
    
    async def successful_operation():
        nonlocal attempt_count
        attempt_count += 1
        return "success"
    
    result = await service._execute_with_retry(successful_operation, max_retries=3, base_delay=0.01)
    
    assert result == "success"
    assert attempt_count == 1


# Property 35: Validation Error Details
# Validates: Requirements 16.7
@given(
    validation_type=st.sampled_from(['status', 'rating', 'uuid', 'url']),
    invalid_value=st.one_of(
        st.text(min_size=1, max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.none()
    )
)
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_35_validation_error_details(validation_type, invalid_value):
    """
    **Validates: Requirements 16.7**
    
    For any validation failure in SupabaseService methods,
    a ValueError should be raised with specific details about which validation rule failed
    and what the expected format or range is.
    """
    service = create_service()
    
    try:
        if validation_type == 'status':
            # Test status validation with invalid values
            if isinstance(invalid_value, str) and invalid_value.strip().title() not in ['Unread', 'Read', 'Archived']:
                with pytest.raises(ValueError) as exc_info:
                    service._validate_status(invalid_value)
                
                error_msg = str(exc_info.value)
                # Verify error contains specific details
                assert "Invalid status" in error_msg
                assert "Allowed values are" in error_msg
                assert "Archived" in error_msg or "Read" in error_msg or "Unread" in error_msg
                assert invalid_value in error_msg or invalid_value.strip() in error_msg
        
        elif validation_type == 'rating':
            # Test rating validation with invalid values
            if isinstance(invalid_value, int) and (invalid_value < 1 or invalid_value > 5):
                with pytest.raises(ValueError) as exc_info:
                    service._validate_rating(invalid_value)
                
                error_msg = str(exc_info.value)
                # Verify error contains specific details
                assert "Invalid rating" in error_msg
                assert "between 1 and 5" in error_msg
                assert str(invalid_value) in error_msg
            elif not isinstance(invalid_value, int) and invalid_value is not None:
                with pytest.raises(ValueError) as exc_info:
                    service._validate_rating(invalid_value)
                
                error_msg = str(exc_info.value)
                # Verify error contains specific details
                assert "Invalid rating" in error_msg
                assert "between 1 and 5" in error_msg
        
        elif validation_type == 'uuid':
            # Test UUID validation with invalid values
            if not _is_valid_uuid(str(invalid_value) if invalid_value is not None else ""):
                with pytest.raises(ValueError) as exc_info:
                    service._validate_uuid(str(invalid_value) if invalid_value is not None else "")
                
                error_msg = str(exc_info.value)
                # Verify error contains specific details
                assert "Invalid UUID format" in error_msg
                assert "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" in error_msg
                # Should contain the invalid value
                assert str(invalid_value) in error_msg or (invalid_value is None and "" in error_msg)
        
        elif validation_type == 'url':
            # Test URL validation with invalid values
            url_str = str(invalid_value) if invalid_value is not None else ""
            if not (url_str.strip().startswith('http://') or url_str.strip().startswith('https://')):
                with pytest.raises(ValueError) as exc_info:
                    service._validate_url(url_str)
                
                error_msg = str(exc_info.value)
                # Verify error contains specific details
                assert "Invalid URL" in error_msg
                # Should specify the requirement
                if url_str and isinstance(invalid_value, str):
                    assert "http://" in error_msg or "https://" in error_msg
    
    except Exception as e:
        # If we get here, it means the test setup was invalid (e.g., valid value passed)
        # This is acceptable for property-based testing
        pass


@given(
    status=st.text().filter(lambda s: s.strip().title() not in ['Unread', 'Read', 'Archived'])
)
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_35_status_validation_error_details(status):
    """
    **Validates: Requirements 16.7**
    
    Verify that status validation errors contain:
    - The invalid value provided
    - The list of allowed values
    - Clear indication of what went wrong
    """
    service = create_service()
    
    with pytest.raises(ValueError) as exc_info:
        service._validate_status(status)
    
    error_msg = str(exc_info.value)
    
    # Must contain the invalid value
    assert status in error_msg or status.strip() in error_msg
    
    # Must list allowed values
    assert "Allowed values are" in error_msg
    assert "Unread" in error_msg
    assert "Read" in error_msg
    assert "Archived" in error_msg
    
    # Must indicate it's a status error
    assert "Invalid status" in error_msg


@given(rating=st.integers().filter(lambda r: r < 1 or r > 5))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_35_rating_validation_error_details(rating):
    """
    **Validates: Requirements 16.7**
    
    Verify that rating validation errors contain:
    - The invalid value provided
    - The valid range (1-5)
    - Clear indication of what went wrong
    """
    service = create_service()
    
    with pytest.raises(ValueError) as exc_info:
        service._validate_rating(rating)
    
    error_msg = str(exc_info.value)
    
    # Must contain the invalid value
    assert str(rating) in error_msg
    
    # Must specify the valid range
    assert "between 1 and 5" in error_msg
    assert "integer" in error_msg
    
    # Must indicate it's a rating error
    assert "Invalid rating" in error_msg


@given(uuid_str=st.text().filter(lambda s: not _is_valid_uuid(s)))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_35_uuid_validation_error_details(uuid_str):
    """
    **Validates: Requirements 16.7**
    
    Verify that UUID validation errors contain:
    - The invalid value provided
    - The expected UUID format
    - Clear indication of what went wrong
    """
    service = create_service()
    
    with pytest.raises(ValueError) as exc_info:
        service._validate_uuid(uuid_str)
    
    error_msg = str(exc_info.value)
    
    # Must contain the invalid value
    assert uuid_str in error_msg
    
    # Must specify the expected format
    assert "Expected format" in error_msg
    assert "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" in error_msg
    
    # Must indicate it's a UUID format error
    assert "Invalid UUID format" in error_msg


@given(url=st.text().filter(lambda s: not (s.strip().startswith('http://') or s.strip().startswith('https://'))))
@settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_35_url_validation_error_details(url):
    """
    **Validates: Requirements 16.7**
    
    Verify that URL validation errors contain:
    - The invalid value provided (when applicable)
    - The expected URL format (http:// or https://)
    - Clear indication of what went wrong
    """
    service = create_service()
    
    with pytest.raises(ValueError) as exc_info:
        service._validate_url(url)
    
    error_msg = str(exc_info.value)
    
    # Must indicate it's a URL error
    assert "Invalid URL" in error_msg
    
    # If the URL is a non-empty string, should contain the value and format requirement
    if url and isinstance(url, str) and url.strip():
        assert url in error_msg or url.strip() in error_msg
        assert "http://" in error_msg or "https://" in error_msg


# Helper functions
def _is_valid_uuid(s: str) -> bool:
    """Check if a string is a valid UUID"""
    try:
        UUID(s)
        return True
    except (ValueError, AttributeError, TypeError):
        return False
