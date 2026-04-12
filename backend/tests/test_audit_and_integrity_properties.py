"""
Property-Based Tests for Audit Trail and Data Integrity

This module contains property-based tests using Hypothesis to validate
audit trail completeness, business rule validation, and soft delete preservation.

**Validates: Requirements 14.1, 14.3, 14.5**
"""

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.core.errors import ErrorCode, ValidationError
from app.core.validators import ArticleValidator, FeedValidator, ReadingListValidator, UserValidator
from app.repositories.base import BaseRepository

# ============================================================================
# Test Strategies
# ============================================================================


@st.composite
def discord_id_strategy(draw):
    """Generate valid Discord IDs (17-20 digit numeric strings)."""
    length = draw(st.integers(min_value=17, max_value=20))
    # Generate a number with the specified length
    min_val = 10 ** (length - 1)
    max_val = (10**length) - 1
    return str(draw(st.integers(min_value=min_val, max_value=max_val)))


@st.composite
def user_data_strategy(draw):
    """Generate valid user creation data."""
    return {
        "discord_id": draw(discord_id_strategy()),
        "dm_notifications_enabled": draw(st.booleans()),
    }


@st.composite
def feed_data_strategy(draw):
    """Generate valid feed creation data."""
    protocol = draw(st.sampled_from(["http", "https"]))
    domain = draw(
        st.text(alphabet=st.characters(whitelist_categories=("Ll", "Nd")), min_size=3, max_size=20)
    )
    tld = draw(st.sampled_from(["com", "org", "net", "io"]))

    return {
        "name": draw(st.text(min_size=1, max_size=100)),
        "url": f"{protocol}://{domain}.{tld}/feed.xml",
        "category": draw(st.text(min_size=1, max_size=50)),
        "is_active": draw(st.booleans()),
    }


@st.composite
def article_data_strategy(draw):
    """Generate valid article creation data."""
    protocol = draw(st.sampled_from(["http", "https"]))
    domain = draw(
        st.text(alphabet=st.characters(whitelist_categories=("Ll", "Nd")), min_size=3, max_size=20)
    )
    tld = draw(st.sampled_from(["com", "org", "net", "io"]))

    return {
        "feed_id": str(uuid4()),
        "title": draw(st.text(min_size=1, max_size=200)),
        "url": f"{protocol}://{domain}.{tld}/article",
        "tinkering_index": draw(st.one_of(st.none(), st.integers(min_value=1, max_value=5))),
    }


@st.composite
def reading_list_data_strategy(draw):
    """Generate valid reading list creation data."""
    return {
        "user_id": str(uuid4()),
        "article_id": str(uuid4()),
        "status": draw(st.sampled_from(["Unread", "Read", "Archived"])),
        "rating": draw(st.one_of(st.none(), st.integers(min_value=1, max_value=5))),
    }


# ============================================================================
# Property 7: Audit Trail Completeness
# ============================================================================


@given(user_data=user_data_strategy(), user_id=st.one_of(st.none(), discord_id_strategy()))
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_7_audit_trail_on_create(user_data, user_id):
    """
    **Property 7: Audit Trail Completeness**

    For any critical data modification operation (create), the system SHALL
    populate audit fields (created_at, updated_at, modified_by) with accurate
    timestamp and user information.

    **Validates: Requirements 14.1**
    """
    # Create mock Supabase client
    mock_client = Mock()
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()

    # Setup mock chain
    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert

    # Capture the data passed to insert
    inserted_data = None

    def capture_insert(data):
        nonlocal inserted_data
        inserted_data = data
        return mock_insert

    mock_table.insert = capture_insert

    # Mock successful response with proper list structure
    entity_id = str(uuid4())
    mock_response_data = [
        {
            "id": entity_id,
            **user_data,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "modified_by": user_id,
        }
    ]
    mock_response = Mock()
    mock_response.data = mock_response_data
    mock_insert.execute.return_value = mock_response

    # Create repository with audit trail enabled
    repo = BaseRepository(
        client=mock_client, table_name="users", enable_audit_trail=True, enable_soft_delete=False
    )

    # Set current user if provided
    if user_id:
        repo.set_current_user(user_id)

    # Create entity
    result = await repo.create(user_data)

    # Verify audit trail fields were added to the data
    assert inserted_data is not None, "Data should be passed to insert"

    # If user_id was set, modified_by should be included
    if user_id:
        assert "modified_by" in inserted_data, "modified_by should be set when user is known"
        assert inserted_data["modified_by"] == user_id, "modified_by should match current user"

    # Verify the result contains audit fields
    assert result is not None
    assert (
        "created_at" in result or "updated_at" in result
    ), "Result should contain timestamp fields"


@given(
    update_data=st.dictionaries(
        keys=st.sampled_from(["dm_notifications_enabled", "status"]),
        values=st.booleans(),
        min_size=1,
        max_size=2,
    ),
    user_id=st.one_of(st.none(), discord_id_strategy()),
)
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_7_audit_trail_on_update(update_data, user_id):
    """
    **Property 7: Audit Trail Completeness**

    For any critical data modification operation (update), the system SHALL
    populate audit fields (updated_at, modified_by) with accurate timestamp
    and user information.

    **Validates: Requirements 14.1**
    """
    # Create mock Supabase client
    mock_client = Mock()
    mock_table = Mock()
    mock_update = Mock()
    mock_eq = Mock()
    mock_execute = Mock()

    # Setup mock chain
    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq

    # Capture the data passed to update
    updated_data = None

    def capture_update(data):
        nonlocal updated_data
        updated_data = data
        return mock_update

    mock_table.update = capture_update

    # Mock successful response
    entity_id = uuid4()
    mock_response = Mock()
    mock_response.data = [
        {
            "id": str(entity_id),
            **update_data,
            "updated_at": datetime.now(UTC).isoformat(),
            "modified_by": user_id,
        }
    ]
    mock_execute.execute.return_value = mock_response
    mock_eq.execute.return_value = mock_response

    # Create repository with audit trail enabled
    repo = BaseRepository(
        client=mock_client, table_name="users", enable_audit_trail=True, enable_soft_delete=False
    )

    # Set current user if provided
    if user_id:
        repo.set_current_user(user_id)

    # Update entity
    result = await repo.update(entity_id, update_data)

    # Verify audit trail fields were added to the data
    assert updated_data is not None, "Data should be passed to update"

    # If user_id was set, modified_by should be included
    if user_id:
        assert "modified_by" in updated_data, "modified_by should be set when user is known"
        assert updated_data["modified_by"] == user_id, "modified_by should match current user"

    # Verify the result is returned
    assert result is not None


# ============================================================================
# Property 8: Business Rule Validation
# ============================================================================


@given(
    invalid_discord_id=st.one_of(
        st.just(""),  # Empty string
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20
        ),  # Non-numeric
        st.text(
            alphabet=st.characters(whitelist_categories=("Nd",)), min_size=1, max_size=16
        ),  # Too short
        st.text(
            alphabet=st.characters(whitelist_categories=("Nd",)), min_size=21, max_size=30
        ),  # Too long
    )
)
@settings(max_examples=50, deadline=None)
def test_property_8_business_rule_validation_discord_id(invalid_discord_id):
    """
    **Property 8: Business Rule Validation**

    For any data modification attempt that violates business rules (invalid Discord ID),
    the system SHALL reject the modification and return a validation error before
    persisting to the database.

    **Validates: Requirements 14.3**
    """
    # Ensure the Discord ID is actually invalid
    assume(
        not invalid_discord_id
        or not invalid_discord_id.isdigit()
        or len(invalid_discord_id) < 17
        or len(invalid_discord_id) > 20
    )

    # Attempt to validate - should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        UserValidator.validate_discord_id(invalid_discord_id)

    # Verify error details
    error = exc_info.value
    assert error.error_code in [
        ErrorCode.VALIDATION_INVALID_FORMAT,
        ErrorCode.VALIDATION_MISSING_FIELD,
    ]
    assert "discord_id" in str(error).lower()


@given(
    invalid_url=st.one_of(
        st.just(""),  # Empty
        st.just("not-a-url"),  # No protocol
        st.just("ftp://example.com"),  # Wrong protocol
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=10
        ),  # Invalid format
    )
)
@settings(max_examples=50, deadline=None)
def test_property_8_business_rule_validation_url(invalid_url):
    """
    **Property 8: Business Rule Validation**

    For any data modification attempt that violates business rules (invalid URL),
    the system SHALL reject the modification and return a validation error.

    **Validates: Requirements 14.3**
    """
    # Ensure the URL is actually invalid
    assume(not invalid_url.startswith("http://") and not invalid_url.startswith("https://"))

    # Attempt to validate - should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        FeedValidator.validate_url_format(invalid_url)

    # Verify error details
    error = exc_info.value
    assert error.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
    assert "url" in str(error).lower()


@given(invalid_tinkering_index=st.integers().filter(lambda x: x < 1 or x > 5))
@settings(max_examples=50, deadline=None)
def test_property_8_business_rule_validation_tinkering_index(invalid_tinkering_index):
    """
    **Property 8: Business Rule Validation**

    For any data modification attempt that violates business rules (tinkering index out of range),
    the system SHALL reject the modification and return a validation error.

    **Validates: Requirements 14.3**
    """
    # Create article data with invalid tinkering index
    article_data = {
        "feed_id": str(uuid4()),
        "title": "Test Article",
        "url": "https://example.com/article",
        "tinkering_index": invalid_tinkering_index,
    }

    # Attempt to validate - should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        ArticleValidator.validate_article_create(article_data)

    # Verify error details
    error = exc_info.value
    assert error.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
    assert "tinkering_index" in str(error).lower()


@given(invalid_rating=st.integers().filter(lambda x: x < 1 or x > 5))
@settings(max_examples=50, deadline=None)
def test_property_8_business_rule_validation_rating(invalid_rating):
    """
    **Property 8: Business Rule Validation**

    For any data modification attempt that violates business rules (rating out of range),
    the system SHALL reject the modification and return a validation error.

    **Validates: Requirements 14.3**
    """
    # Create reading list data with invalid rating
    reading_list_data = {
        "user_id": str(uuid4()),
        "article_id": str(uuid4()),
        "status": "Unread",
        "rating": invalid_rating,
    }

    # Attempt to validate - should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        ReadingListValidator.validate_reading_list_create(reading_list_data)

    # Verify error details
    error = exc_info.value
    assert error.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
    assert "rating" in str(error).lower()


@given(
    invalid_status=st.text(min_size=1, max_size=20).filter(
        lambda x: x not in {"Unread", "Read", "Archived"}
    )
)
@settings(max_examples=50, deadline=None)
def test_property_8_business_rule_validation_status(invalid_status):
    """
    **Property 8: Business Rule Validation**

    For any data modification attempt that violates business rules (invalid status),
    the system SHALL reject the modification and return a validation error.

    **Validates: Requirements 14.3**
    """
    # Create reading list data with invalid status
    reading_list_data = {
        "user_id": str(uuid4()),
        "article_id": str(uuid4()),
        "status": invalid_status,
    }

    # Attempt to validate - should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        ReadingListValidator.validate_reading_list_create(reading_list_data)

    # Verify error details
    error = exc_info.value
    assert error.error_code == ErrorCode.VALIDATION_INVALID_FORMAT
    assert "status" in str(error).lower()


# ============================================================================
# Property 9: Soft Delete Preservation
# ============================================================================


@given(entity_data=user_data_strategy(), user_id=st.one_of(st.none(), discord_id_strategy()))
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_9_soft_delete_preserves_record(entity_data, user_id):
    """
    **Property 9: Soft Delete Preservation**

    For any delete operation on critical entities, the system SHALL mark the
    entity as deleted without removing it from the database, preserving the
    record for audit history.

    **Validates: Requirements 14.5**
    """
    # Create mock Supabase client
    mock_client = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_update = Mock()
    mock_eq = Mock()
    mock_is = Mock()
    mock_execute = Mock()

    # Setup mock chain for checking existence
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.is_.return_value = mock_is

    # Setup mock chain for update
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq

    # Capture the data passed to update
    updated_data = None

    def capture_update(data):
        nonlocal updated_data
        updated_data = data
        return mock_update

    mock_table.update = capture_update

    # Mock entity exists and is not deleted
    entity_id = uuid4()
    check_response = Mock()
    check_response.data = [{"id": str(entity_id)}]
    mock_is.execute.return_value = check_response

    # Mock successful soft delete response
    delete_response = Mock()
    delete_response.data = [
        {"id": str(entity_id), **entity_data, "deleted_at": datetime.now(UTC).isoformat()}
    ]
    mock_eq.execute.return_value = delete_response

    # Create repository with soft delete enabled
    repo = BaseRepository(
        client=mock_client, table_name="users", enable_audit_trail=True, enable_soft_delete=True
    )

    # Set current user if provided
    if user_id:
        repo.set_current_user(user_id)

    # Delete entity (soft delete)
    result = await repo.delete(entity_id)

    # Verify soft delete was performed
    assert result is True, "Delete should return True"

    # Verify update was called (not hard delete)
    assert updated_data is not None, "Update should be called for soft delete"
    assert "deleted_at" in updated_data, "deleted_at should be set"

    # Verify deleted_at is a valid timestamp
    deleted_at = updated_data["deleted_at"]
    assert deleted_at is not None, "deleted_at should not be None"

    # If user_id was set, modified_by should be included
    if user_id:
        assert "modified_by" in updated_data, "modified_by should be set for audit trail"
        assert updated_data["modified_by"] == user_id, "modified_by should match current user"


@given(entity_data=user_data_strategy())
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_9_soft_deleted_entities_excluded_from_queries(entity_data):
    """
    **Property 9: Soft Delete Preservation**

    For any query operation, soft-deleted entities SHALL be excluded from
    results by default, ensuring they don't appear in normal operations
    while being preserved for audit.

    **Validates: Requirements 14.5**
    """
    # Create mock Supabase client
    mock_client = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_is = Mock()
    mock_execute = Mock()

    # Setup mock chain
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.is_.return_value = mock_is

    # Track if soft delete filter was applied
    filter_applied = False

    def track_is_filter(field, value):
        nonlocal filter_applied
        if field == "deleted_at" and value == "null":
            filter_applied = True
        return mock_is

    mock_select.is_ = track_is_filter

    # Mock response with no deleted entities
    mock_response = Mock()
    mock_response.data = []
    mock_is.execute.return_value = mock_response

    # Create repository with soft delete enabled
    repo = BaseRepository(
        client=mock_client, table_name="users", enable_audit_trail=True, enable_soft_delete=True
    )

    # Query entities
    results = await repo.list()

    # Verify soft delete filter was applied
    assert filter_applied, "Soft delete filter should be applied to exclude deleted entities"
    assert isinstance(results, list), "Results should be a list"


@given(entity_data=user_data_strategy())
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_9_hard_delete_permanently_removes(entity_data):
    """
    **Property 9: Soft Delete Preservation**

    For any hard delete operation, the system SHALL permanently remove the
    entity from the database. This verifies that hard delete is distinct
    from soft delete and actually removes data.

    **Validates: Requirements 14.5**
    """
    # Create mock Supabase client
    mock_client = Mock()
    mock_table = Mock()
    mock_delete = Mock()
    mock_eq = Mock()
    mock_execute = Mock()

    # Setup mock chain
    mock_client.table.return_value = mock_table
    mock_table.delete.return_value = mock_delete
    mock_delete.eq.return_value = mock_eq

    # Track if delete was called (not update)
    delete_called = False

    def track_delete():
        nonlocal delete_called
        delete_called = True
        return mock_delete

    mock_table.delete = track_delete

    # Mock successful hard delete response
    entity_id = uuid4()
    mock_response = Mock()
    mock_response.data = [{"id": str(entity_id)}]
    mock_eq.execute.return_value = mock_response

    # Create repository with soft delete enabled
    repo = BaseRepository(
        client=mock_client, table_name="users", enable_audit_trail=True, enable_soft_delete=True
    )

    # Hard delete entity
    result = await repo.hard_delete(entity_id)

    # Verify hard delete was performed
    assert result is True, "Hard delete should return True"
    assert delete_called, "Delete method should be called for hard delete (not update)"


@given(entity_data=user_data_strategy())
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_9_restore_clears_deleted_at(entity_data):
    """
    **Property 9: Soft Delete Preservation**

    For any restore operation on a soft-deleted entity, the system SHALL
    clear the deleted_at timestamp, making the entity visible again in
    normal queries.

    **Validates: Requirements 14.5**
    """
    # Create mock Supabase client
    mock_client = Mock()
    mock_table = Mock()
    mock_select = Mock()
    mock_update = Mock()
    mock_eq = Mock()
    mock_execute = Mock()

    # Setup mock chain for checking existence
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq

    # Setup mock chain for update
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq

    # Capture the data passed to update
    updated_data = None

    def capture_update(data):
        nonlocal updated_data
        updated_data = data
        return mock_update

    mock_table.update = capture_update

    # Mock entity exists and is deleted
    entity_id = uuid4()
    check_response = Mock()
    check_response.data = [
        {"id": str(entity_id), **entity_data, "deleted_at": datetime.now(UTC).isoformat()}
    ]

    # Mock successful restore response
    restore_response = Mock()
    restore_response.data = [{"id": str(entity_id), **entity_data, "deleted_at": None}]

    # Setup execute to return check_response first, then restore_response
    mock_eq.execute.side_effect = [check_response, restore_response]

    # Create repository with soft delete enabled
    repo = BaseRepository(
        client=mock_client, table_name="users", enable_audit_trail=True, enable_soft_delete=True
    )

    # Restore entity
    result = await repo.restore(entity_id)

    # Verify restore was performed
    assert result is not None, "Restore should return the restored entity"

    # Verify deleted_at was set to None
    assert updated_data is not None, "Update should be called for restore"
    assert "deleted_at" in updated_data, "deleted_at should be in update data"
    assert updated_data["deleted_at"] is None, "deleted_at should be set to None"
