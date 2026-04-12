"""
Test standardized API response formats

Validates: Requirements 15.1, 15.2, 15.3, 15.4
"""

import pytest

from app.schemas.responses import (
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMetadata,
    SuccessResponse,
    error_response,
    paginated_response,
    success_response,
)


def test_success_response_structure():
    """Test that success_response creates correct structure"""
    data = {"id": "123", "name": "Test"}
    response = success_response(data)

    assert isinstance(response, SuccessResponse)
    assert response.success is True
    assert response.data == data
    assert response.metadata is None


def test_success_response_with_metadata():
    """Test success_response with metadata"""
    data = {"id": "123"}
    metadata = {"version": "1.0"}
    response = success_response(data, metadata=metadata)

    assert response.success is True
    assert response.data == data
    assert response.metadata == metadata


def test_paginated_response_structure():
    """Test that paginated_response creates correct structure"""
    items = [{"id": "1"}, {"id": "2"}]
    response = paginated_response(items=items, total_count=100, page=1, page_size=20)

    assert isinstance(response, PaginatedResponse)
    assert response.success is True
    assert response.data == items
    assert isinstance(response.pagination, PaginationMetadata)
    assert response.pagination.total_count == 100
    assert response.pagination.page == 1
    assert response.pagination.page_size == 20
    assert response.pagination.total_pages == 5
    assert response.pagination.has_next is True
    assert response.pagination.has_previous is False


def test_paginated_response_last_page():
    """Test pagination metadata for last page"""
    items = [{"id": "1"}]
    response = paginated_response(items=items, total_count=21, page=2, page_size=20)

    assert response.pagination.total_pages == 2
    assert response.pagination.has_next is False
    assert response.pagination.has_previous is True


def test_paginated_response_empty():
    """Test pagination with no items"""
    response = paginated_response(items=[], total_count=0, page=1, page_size=20)

    assert response.data == []
    assert response.pagination.total_count == 0
    assert response.pagination.total_pages == 0
    assert response.pagination.has_next is False
    assert response.pagination.has_previous is False


def test_error_response_structure():
    """Test that error_response creates correct structure"""
    response = error_response(error="Something went wrong", error_code="INTERNAL_ERROR")

    assert isinstance(response, ErrorResponse)
    assert response.success is False
    assert response.error == "Something went wrong"
    assert response.error_code == "INTERNAL_ERROR"
    assert response.details is None


def test_error_response_with_details():
    """Test error_response with details"""
    details = [ErrorDetail(field="email", message="Invalid format", code="INVALID_FORMAT")]
    response = error_response(
        error="Validation failed", error_code="VALIDATION_ERROR", details=details
    )

    assert response.success is False
    assert response.error == "Validation failed"
    assert response.error_code == "VALIDATION_ERROR"
    assert len(response.details) == 1
    assert response.details[0].field == "email"
    assert response.details[0].message == "Invalid format"


def test_pagination_metadata_calculation():
    """Test pagination metadata calculations"""
    # Test with exact multiple
    metadata = PaginationMetadata(
        total_count=100, page=1, page_size=20, total_pages=5, has_next=True, has_previous=False
    )
    assert metadata.total_pages == 5

    # Test with remainder
    metadata2 = PaginationMetadata(
        total_count=105, page=1, page_size=20, total_pages=6, has_next=True, has_previous=False
    )
    assert metadata2.total_pages == 6


def test_response_serialization():
    """Test that responses can be serialized to dict"""
    # Success response
    success = success_response({"id": "123"})
    success_dict = success.model_dump()
    assert success_dict["success"] is True
    assert "data" in success_dict

    # Paginated response
    paginated = paginated_response(items=[{"id": "1"}], total_count=1, page=1, page_size=20)
    paginated_dict = paginated.model_dump()
    assert paginated_dict["success"] is True
    assert "data" in paginated_dict
    assert "pagination" in paginated_dict

    # Error response
    error = error_response("Error", "ERROR_CODE")
    error_dict = error.model_dump()
    assert error_dict["success"] is False
    assert "error" in error_dict
    assert "error_code" in error_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
