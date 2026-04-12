"""
Standardized API Response Models

This module defines standardized response formats for all API endpoints,
ensuring consistency across the application.

Requirements: 15.1, 15.2, 15.3, 15.4
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMetadata(BaseModel):
    """
    Pagination metadata for list endpoints.

    Validates: Requirement 15.4
    """

    total_count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False,
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """
    Standardized success response format.

    All successful API responses should use this format.

    Validates: Requirements 15.1, 15.2
    """

    success: bool = Field(True, description="Indicates successful operation")
    data: T = Field(..., description="Response data")
    metadata: Optional[dict[str, Any]] = Field(None, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {"success": True, "data": {"id": "123", "name": "Example"}, "metadata": None}
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized paginated response format.

    Used for list endpoints that support pagination.

    Validates: Requirements 15.1, 15.2, 15.4
    """

    success: bool = Field(True, description="Indicates successful operation")
    data: list[T] = Field(..., description="List of items")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    metadata: Optional[dict[str, Any]] = Field(None, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [{"id": "1"}, {"id": "2"}],
                "pagination": {
                    "total_count": 100,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 5,
                    "has_next": True,
                    "has_previous": False,
                },
                "metadata": None,
            }
        }


class ErrorDetail(BaseModel):
    """
    Detailed error information.

    Validates: Requirement 15.3
    """

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """
    Standardized error response format.

    All error responses should use this format.

    Validates: Requirements 15.1, 15.3
    """

    success: bool = Field(False, description="Indicates failed operation")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[list[ErrorDetail]] = Field(None, description="Detailed error information")
    metadata: Optional[dict[str, Any]] = Field(None, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "details": [
                    {"field": "email", "message": "Invalid email format", "code": "INVALID_FORMAT"}
                ],
                "metadata": None,
            }
        }


# Response wrapper utilities


def success_response(data: T, metadata: Optional[dict[str, Any]] = None) -> SuccessResponse[T]:
    """
    Create a standardized success response.

    Args:
        data: Response data
        metadata: Optional metadata

    Returns:
        SuccessResponse with the provided data
    """
    return SuccessResponse(success=True, data=data, metadata=metadata)


def paginated_response(
    items: list[T],
    total_count: int,
    page: int,
    page_size: int,
    metadata: Optional[dict[str, Any]] = None,
) -> PaginatedResponse[T]:
    """
    Create a standardized paginated response.

    Args:
        items: List of items for current page
        total_count: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Number of items per page
        metadata: Optional metadata

    Returns:
        PaginatedResponse with items and pagination metadata
    """
    total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    pagination = PaginationMetadata(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )

    return PaginatedResponse(success=True, data=items, pagination=pagination, metadata=metadata)


def error_response(
    error: str,
    error_code: str,
    details: Optional[list[ErrorDetail]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ErrorResponse:
    """
    Create a standardized error response.

    Args:
        error: Human-readable error message
        error_code: Machine-readable error code
        details: Optional detailed error information
        metadata: Optional metadata

    Returns:
        ErrorResponse with error information
    """
    return ErrorResponse(
        success=False, error=error, error_code=error_code, details=details, metadata=metadata
    )
