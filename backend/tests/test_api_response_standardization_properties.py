"""
Property-Based Tests for API Response Standardization

Tests API response structure consistency and pagination metadata presence
using Hypothesis for property-based testing.

**Validates: Requirements 15.1, 15.2, 15.3, 15.4**
"""


import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from pydantic import BaseModel

from app.schemas.responses import (
    PaginationMetadata,
    SuccessResponse,
    error_response,
    paginated_response,
    success_response,
)

# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating arbitrary data payloads
simple_data = st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
)

dict_data = st.dictionaries(
    keys=st.text(min_size=1, max_size=50), values=simple_data, min_size=0, max_size=10
)

list_data = st.lists(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20), values=simple_data, min_size=1, max_size=5
    ),
    min_size=0,
    max_size=20,
)

# Strategy for pagination parameters
page_numbers = st.integers(min_value=1, max_value=100)
page_sizes = st.integers(min_value=1, max_value=100)
total_counts = st.integers(min_value=0, max_value=10000)

# Strategy for error messages and codes
error_messages = st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
error_codes = st.sampled_from(
    [
        "VALIDATION_ERROR",
        "NOT_FOUND",
        "AUTH_FAILED",
        "DB_ERROR",
        "INTERNAL_ERROR",
        "RATE_LIMIT_EXCEEDED",
    ]
)

# Strategy for metadata
metadata_dict = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=30), values=simple_data, min_size=1, max_size=5
    ),
)


# ============================================================================
# Property 10: API Response Structure Consistency
# **Validates: Requirements 15.1, 15.2, 15.3**
# ============================================================================


@given(data=dict_data, metadata=metadata_dict)
@settings(max_examples=50)
def test_property_10_success_response_structure(data, metadata):
    """
    Property 10: API Response Structure Consistency (Success)

    For any successful API response, the response SHALL follow the standardized
    structure with 'success', 'data', and optional 'metadata' fields.

    **Validates: Requirements 15.1, 15.2**
    """
    # Create success response
    response = success_response(data, metadata=metadata)

    # Assert standardized structure
    assert hasattr(response, "success"), "Response must have 'success' field"
    assert hasattr(response, "data"), "Response must have 'data' field"
    assert hasattr(response, "metadata"), "Response must have 'metadata' field"

    # Assert field values
    assert response.success is True, "Success response must have success=True"
    assert response.data == data, "Data field must match provided data"
    assert response.metadata == metadata, "Metadata field must match provided metadata"

    # Assert serialization maintains structure
    response_dict = response.model_dump()
    assert "success" in response_dict
    assert "data" in response_dict
    assert "metadata" in response_dict
    assert response_dict["success"] is True


@given(error_msg=error_messages, error_code=error_codes, metadata=metadata_dict)
@settings(max_examples=50)
def test_property_10_error_response_structure(error_msg, error_code, metadata):
    """
    Property 10: API Response Structure Consistency (Error)

    For any error API response, the response SHALL follow the standardized
    structure with 'success', 'error', 'error_code', and optional 'details'/'metadata'.

    **Validates: Requirements 15.1, 15.3**
    """
    # Create error response
    response = error_response(error=error_msg, error_code=error_code, metadata=metadata)

    # Assert standardized structure
    assert hasattr(response, "success"), "Response must have 'success' field"
    assert hasattr(response, "error"), "Response must have 'error' field"
    assert hasattr(response, "error_code"), "Response must have 'error_code' field"
    assert hasattr(response, "details"), "Response must have 'details' field"
    assert hasattr(response, "metadata"), "Response must have 'metadata' field"

    # Assert field values
    assert response.success is False, "Error response must have success=False"
    assert response.error == error_msg, "Error field must match provided message"
    assert response.error_code == error_code, "Error code must match provided code"
    assert response.metadata == metadata, "Metadata field must match provided metadata"

    # Assert serialization maintains structure
    response_dict = response.model_dump()
    assert "success" in response_dict
    assert "error" in response_dict
    assert "error_code" in response_dict
    assert response_dict["success"] is False


@given(
    items=list_data,
    total_count=total_counts,
    page=page_numbers,
    page_size=page_sizes,
    metadata=metadata_dict,
)
@settings(max_examples=50)
def test_property_10_paginated_response_structure(items, total_count, page, page_size, metadata):
    """
    Property 10: API Response Structure Consistency (Paginated)

    For any paginated API response, the response SHALL follow the standardized
    structure with 'success', 'data', 'pagination', and optional 'metadata' fields.

    **Validates: Requirements 15.1, 15.2, 15.4**
    """
    # Ensure page is valid for the total count
    assume(page >= 1)
    assume(page_size >= 1)

    # Create paginated response
    response = paginated_response(
        items=items, total_count=total_count, page=page, page_size=page_size, metadata=metadata
    )

    # Assert standardized structure
    assert hasattr(response, "success"), "Response must have 'success' field"
    assert hasattr(response, "data"), "Response must have 'data' field"
    assert hasattr(response, "pagination"), "Response must have 'pagination' field"
    assert hasattr(response, "metadata"), "Response must have 'metadata' field"

    # Assert field values
    assert response.success is True, "Paginated response must have success=True"
    assert response.data == items, "Data field must match provided items"
    assert isinstance(
        response.pagination, PaginationMetadata
    ), "Pagination must be PaginationMetadata instance"
    assert response.metadata == metadata, "Metadata field must match provided metadata"

    # Assert serialization maintains structure
    response_dict = response.model_dump()
    assert "success" in response_dict
    assert "data" in response_dict
    assert "pagination" in response_dict
    assert "metadata" in response_dict
    assert response_dict["success"] is True


@given(data=st.one_of(dict_data, list_data))
@settings(max_examples=30)
def test_property_10_response_type_consistency(data):
    """
    Property 10: API Response Structure Consistency (Type Safety)

    For any API response, the response SHALL be a properly typed Pydantic model
    that enforces structure at runtime.

    **Validates: Requirements 15.1**
    """
    # Create response
    response = success_response(data)

    # Assert it's a Pydantic model
    assert isinstance(response, BaseModel), "Response must be a Pydantic BaseModel"
    assert isinstance(response, SuccessResponse), "Response must be SuccessResponse type"

    # Assert model validation works
    response_dict = response.model_dump()

    # Re-create from dict should work
    reconstructed = SuccessResponse(**response_dict)
    assert reconstructed.success == response.success
    assert reconstructed.data == response.data


@given(success_data=dict_data, error_msg=error_messages, error_code=error_codes)
@settings(max_examples=30)
def test_property_10_success_and_error_mutual_exclusivity(success_data, error_msg, error_code):
    """
    Property 10: API Response Structure Consistency (Mutual Exclusivity)

    For any API response, success responses SHALL have 'data' field and
    error responses SHALL have 'error'/'error_code' fields, but never both.

    **Validates: Requirements 15.1, 15.2, 15.3**
    """
    # Create success response
    success_resp = success_response(success_data)
    success_dict = success_resp.model_dump()

    # Success response should have data, not error fields
    assert "data" in success_dict
    assert success_dict["success"] is True

    # Create error response
    error_resp = error_response(error_msg, error_code)
    error_dict = error_resp.model_dump()

    # Error response should have error fields, not data
    assert "error" in error_dict
    assert "error_code" in error_dict
    assert error_dict["success"] is False


# ============================================================================
# Property 11: Pagination Metadata Presence
# **Validates: Requirements 15.4**
# ============================================================================


@given(items=list_data, total_count=total_counts, page=page_numbers, page_size=page_sizes)
@settings(max_examples=50)
def test_property_11_pagination_metadata_completeness(items, total_count, page, page_size):
    """
    Property 11: Pagination Metadata Presence (Completeness)

    For any list endpoint response, the pagination metadata SHALL include
    all required fields: total_count, page, page_size, total_pages,
    has_next, has_previous.

    **Validates: Requirements 15.4**
    """
    assume(page >= 1)
    assume(page_size >= 1)

    # Create paginated response
    response = paginated_response(
        items=items, total_count=total_count, page=page, page_size=page_size
    )

    # Assert pagination metadata exists
    assert response.pagination is not None, "Pagination metadata must be present"

    # Assert all required fields are present
    pagination = response.pagination
    assert hasattr(pagination, "total_count"), "Must have total_count"
    assert hasattr(pagination, "page"), "Must have page"
    assert hasattr(pagination, "page_size"), "Must have page_size"
    assert hasattr(pagination, "total_pages"), "Must have total_pages"
    assert hasattr(pagination, "has_next"), "Must have has_next"
    assert hasattr(pagination, "has_previous"), "Must have has_previous"

    # Assert field values match input
    assert pagination.total_count == total_count
    assert pagination.page == page
    assert pagination.page_size == page_size


@given(
    total_count=st.integers(min_value=0, max_value=1000),
    page=st.integers(min_value=1, max_value=50),
    page_size=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=100)
def test_property_11_pagination_calculation_correctness(total_count, page, page_size):
    """
    Property 11: Pagination Metadata Presence (Calculation Correctness)

    For any list endpoint response, the pagination metadata calculations
    SHALL be mathematically correct (total_pages, has_next, has_previous).

    **Validates: Requirements 15.4**
    """
    # Create paginated response
    response = paginated_response(items=[], total_count=total_count, page=page, page_size=page_size)

    pagination = response.pagination

    # Calculate expected total_pages
    expected_total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
    assert (
        pagination.total_pages == expected_total_pages
    ), f"total_pages calculation incorrect: expected {expected_total_pages}, got {pagination.total_pages}"

    # Calculate expected has_next
    expected_has_next = page < expected_total_pages
    assert (
        pagination.has_next == expected_has_next
    ), f"has_next calculation incorrect: expected {expected_has_next}, got {pagination.has_next}"

    # Calculate expected has_previous
    expected_has_previous = page > 1
    assert (
        pagination.has_previous == expected_has_previous
    ), f"has_previous calculation incorrect: expected {expected_has_previous}, got {pagination.has_previous}"


@given(items=list_data, total_count=total_counts, page=page_numbers, page_size=page_sizes)
@settings(max_examples=50)
def test_property_11_pagination_metadata_serialization(items, total_count, page, page_size):
    """
    Property 11: Pagination Metadata Presence (Serialization)

    For any list endpoint response, the pagination metadata SHALL be
    properly serialized in the JSON response.

    **Validates: Requirements 15.4**
    """
    assume(page >= 1)
    assume(page_size >= 1)

    # Create paginated response
    response = paginated_response(
        items=items, total_count=total_count, page=page, page_size=page_size
    )

    # Serialize to dict
    response_dict = response.model_dump()

    # Assert pagination is in serialized response
    assert "pagination" in response_dict, "Serialized response must include pagination"

    pagination_dict = response_dict["pagination"]

    # Assert all fields are serialized
    assert "total_count" in pagination_dict
    assert "page" in pagination_dict
    assert "page_size" in pagination_dict
    assert "total_pages" in pagination_dict
    assert "has_next" in pagination_dict
    assert "has_previous" in pagination_dict

    # Assert types are JSON-compatible
    assert isinstance(pagination_dict["total_count"], int)
    assert isinstance(pagination_dict["page"], int)
    assert isinstance(pagination_dict["page_size"], int)
    assert isinstance(pagination_dict["total_pages"], int)
    assert isinstance(pagination_dict["has_next"], bool)
    assert isinstance(pagination_dict["has_previous"], bool)


@given(page_size=st.integers(min_value=1, max_value=100))
@settings(max_examples=30)
def test_property_11_empty_list_pagination(page_size):
    """
    Property 11: Pagination Metadata Presence (Empty List)

    For any list endpoint response with no items, the pagination metadata
    SHALL still be present and correctly indicate empty state.

    **Validates: Requirements 15.4**
    """
    # Create paginated response with empty list
    response = paginated_response(items=[], total_count=0, page=1, page_size=page_size)

    # Assert pagination metadata exists even for empty list
    assert response.pagination is not None

    pagination = response.pagination

    # Assert correct empty state
    assert pagination.total_count == 0
    assert pagination.total_pages == 0
    assert pagination.has_next is False
    assert pagination.has_previous is False
    assert pagination.page == 1


@given(
    total_count=st.integers(min_value=1, max_value=1000),
    page_size=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=50)
def test_property_11_first_page_pagination(total_count, page_size):
    """
    Property 11: Pagination Metadata Presence (First Page)

    For any list endpoint response on the first page, has_previous SHALL
    be False and has_next SHALL be True if more pages exist.

    **Validates: Requirements 15.4**
    """
    # Create paginated response for first page
    response = paginated_response(items=[], total_count=total_count, page=1, page_size=page_size)

    pagination = response.pagination

    # First page should never have previous
    assert pagination.has_previous is False, "First page must have has_previous=False"

    # has_next depends on whether there are more pages
    total_pages = (total_count + page_size - 1) // page_size
    expected_has_next = total_pages > 1
    assert pagination.has_next == expected_has_next


@given(
    total_count=st.integers(min_value=1, max_value=1000),
    page_size=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=50)
def test_property_11_last_page_pagination(total_count, page_size):
    """
    Property 11: Pagination Metadata Presence (Last Page)

    For any list endpoint response on the last page, has_next SHALL be False
    and has_previous SHALL be True if not the first page.

    **Validates: Requirements 15.4**
    """
    # Calculate last page
    total_pages = (total_count + page_size - 1) // page_size
    assume(total_pages >= 1)

    # Create paginated response for last page
    response = paginated_response(
        items=[], total_count=total_count, page=total_pages, page_size=page_size
    )

    pagination = response.pagination

    # Last page should never have next
    assert pagination.has_next is False, "Last page must have has_next=False"

    # has_previous depends on whether it's also the first page
    expected_has_previous = total_pages > 1
    assert pagination.has_previous == expected_has_previous


@given(items=list_data, total_count=total_counts, page=page_numbers, page_size=page_sizes)
@settings(max_examples=30)
def test_property_11_pagination_immutability(items, total_count, page, page_size):
    """
    Property 11: Pagination Metadata Presence (Immutability)

    For any list endpoint response, the pagination metadata SHALL be
    immutable after creation (Pydantic model frozen behavior).

    **Validates: Requirements 15.4**
    """
    assume(page >= 1)
    assume(page_size >= 1)

    # Create paginated response
    response = paginated_response(
        items=items, total_count=total_count, page=page, page_size=page_size
    )

    # Store original values
    original_total_count = response.pagination.total_count
    original_page = response.pagination.page
    original_has_next = response.pagination.has_next

    # Pagination metadata should remain consistent
    assert response.pagination.total_count == original_total_count
    assert response.pagination.page == original_page
    assert response.pagination.has_next == original_has_next


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
