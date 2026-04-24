# Remaining Tasks Implementation Guide

## Overview

This guide provides detailed instructions for completing tasks 7-19 of the project architecture refactoring spec. Tasks 1-6 have been completed successfully.

## Completed Foundation (Tasks 1-6)

✅ **Task 1**: Foundational infrastructure (config, logging, errors)
✅ **Task 2**: Checkpoint - verified infrastructure
✅ **Task 3**: Backend repository layer implemented
✅ **Task 4**: Database audit and integrity features
✅ **Task 5**: Backend service layer refactored
✅ **Task 6**: Checkpoint - backend refactoring verified

## Remaining Tasks Summary

### Backend Tasks (7)

- Task 7: Standardize API response formats
- Task 13: Refactor Discord bot architecture

### Frontend Tasks (8-12)

- Task 8: Implement unified frontend API client
- Task 9: Implement frontend logging system
- Task 10: Refactor frontend state management
- Task 11: Migrate existing API clients
- Task 12: Checkpoint - verify frontend refactoring

### Infrastructure Tasks (14-18)

- Task 14: Reorganize test structure
- Task 15: Implement code quality enforcement
- Task 16: Improve developer experience
- Task 17: Performance validation
- Task 18: Final integration and documentation

### Final Tasks (19)

- Task 19: Final checkpoint

---

## Task 7: Standardize API Response Formats

### 7.1 Create standardized response models

**File**: `backend/app/schemas/responses.py`

```python
"""
Standardized API Response Models

This module defines standardized response formats for all API endpoints,
ensuring consistency across the application.

Requirements: 15.1, 15.2, 15.3, 15.4
"""

from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, Field


T = TypeVar('T')


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
                "has_previous": False
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
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "metadata": None
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized paginated response format.

    Used for list endpoints that support pagination.

    Validates: Requirements 15.1, 15.2, 15.4
    """
    success: bool = Field(True, description="Indicates successful operation")
    data: List[T] = Field(..., description="List of items")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

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
                    "has_previous": False
                },
                "metadata": None
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
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_FORMAT"
                    }
                ],
                "metadata": None
            }
        }


# Response wrapper utilities

def success_response(data: T, metadata: Optional[Dict[str, Any]] = None) -> SuccessResponse[T]:
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
    items: List[T],
    total_count: int,
    page: int,
    page_size: int,
    metadata: Optional[Dict[str, Any]] = None
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
        has_previous=has_previous
    )

    return PaginatedResponse(
        success=True,
        data=items,
        pagination=pagination,
        metadata=metadata
    )


def error_response(
    error: str,
    error_code: str,
    details: Optional[List[ErrorDetail]] = None,
    metadata: Optional[Dict[str, Any]] = None
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
        success=False,
        error=error,
        error_code=error_code,
        details=details,
        metadata=metadata
    )
```

### 7.2 Update API routes to use standardized responses

**Instructions**:

1. Import response utilities in each API route file
2. Wrap all successful responses with `success_response()` or `paginated_response()`
3. Update exception handlers to return `error_response()`

**Example** (`backend/app/api/feeds.py`):

```python
from app.schemas.responses import success_response, paginated_response, error_response

@router.get("/feeds")
async def list_feeds(
    page: int = 1,
    page_size: int = 20,
    service: FeedService = Depends(get_feed_service)
):
    """List feeds with pagination."""
    result = await service.list_feeds_paginated(page, page_size)

    return paginated_response(
        items=result.items,
        total_count=result.total_count,
        page=page,
        page_size=page_size
    )

@router.get("/feeds/{feed_id}")
async def get_feed(
    feed_id: UUID,
    service: FeedService = Depends(get_feed_service)
):
    """Get a single feed."""
    feed = await service.get_feed(feed_id)
    return success_response(data=feed)
```

### 7.3 Write property tests for API response standardization

**File**: `backend/tests/test_api_response_property.py`

```python
"""
Property Tests for API Response Standardization

Property 10: API Response Structure Consistency
Property 11: Pagination Metadata Presence

Requirements: 15.1, 15.2, 15.3, 15.4
"""

import pytest
from hypothesis import given, strategies as st
from app.schemas.responses import (
    success_response,
    paginated_response,
    error_response,
    PaginationMetadata
)


@given(
    data=st.dictionaries(st.text(), st.integers()),
    metadata=st.one_of(st.none(), st.dictionaries(st.text(), st.text()))
)
def test_property_10_success_response_structure(data, metadata):
    """
    Property 10: API Response Structure Consistency

    For any successful response, the structure SHALL contain:
    - success: True
    - data: <response data>
    - metadata: <optional metadata>
    """
    response = success_response(data=data, metadata=metadata)

    assert response.success is True
    assert response.data == data
    assert response.metadata == metadata


@given(
    items=st.lists(st.dictionaries(st.text(), st.integers()), max_size=10),
    total_count=st.integers(min_value=0, max_value=1000),
    page=st.integers(min_value=1, max_value=100),
    page_size=st.integers(min_value=1, max_value=100)
)
def test_property_11_pagination_metadata_presence(items, total_count, page, page_size):
    """
    Property 11: Pagination Metadata Presence

    For any paginated response, pagination metadata SHALL be present with:
    - total_count
    - page
    - page_size
    - total_pages
    - has_next
    - has_previous
    """
    response = paginated_response(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size
    )

    assert response.success is True
    assert response.data == items
    assert response.pagination is not None
    assert response.pagination.total_count == total_count
    assert response.pagination.page == page
    assert response.pagination.page_size == page_size
    assert isinstance(response.pagination.has_next, bool)
    assert isinstance(response.pagination.has_previous, bool)
```

---

## Task 8: Implement Unified Frontend API Client

### 8.1 Create base HTTP client with singleton pattern

**File**: `frontend/lib/api/client.ts`

```typescript
/**
 * Unified API Client
 *
 * Singleton HTTP client for all API communications.
 * Provides consistent error handling, request/response interceptors,
 * and type-safe API methods.
 *
 * Requirements: 1.1, 1.3
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from 'axios';

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface RequestInterceptor {
  onFulfilled?: (
    config: AxiosRequestConfig,
  ) => AxiosRequestConfig | Promise<AxiosRequestConfig>;
  onRejected?: (error: any) => any;
}

export interface ResponseInterceptor {
  onFulfilled?: (
    response: AxiosResponse,
  ) => AxiosResponse | Promise<AxiosResponse>;
  onRejected?: (error: any) => any;
}

class ApiClient {
  private static instance: ApiClient | null = null;
  private axiosInstance: AxiosInstance;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  private constructor(config: ApiClientConfig) {
    this.axiosInstance = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
    });

    this.setupInterceptors();
  }

  /**
   * Get singleton instance of ApiClient
   *
   * Validates: Requirement 1.1 (single HTTP client instance)
   */
  public static getInstance(config?: ApiClientConfig): ApiClient {
    if (!ApiClient.instance) {
      if (!config) {
        throw new Error(
          'ApiClient must be initialized with config on first call',
        );
      }
      ApiClient.instance = new ApiClient(config);
    }
    return ApiClient.instance;
  }

  /**
   * Reset singleton instance (for testing)
   */
  public static resetInstance(): void {
    ApiClient.instance = null;
  }

  /**
   * Add request interceptor
   *
   * Validates: Requirement 1.3 (request/response interceptor support)
   */
  public addRequestInterceptor(interceptor: RequestInterceptor): number {
    this.requestInterceptors.push(interceptor);
    return this.axiosInstance.interceptors.request.use(
      interceptor.onFulfilled,
      interceptor.onRejected,
    );
  }

  /**
   * Add response interceptor
   *
   * Validates: Requirement 1.3 (request/response interceptor support)
   */
  public addResponseInterceptor(interceptor: ResponseInterceptor): number {
    this.responseInterceptors.push(interceptor);
    return this.axiosInstance.interceptors.response.use(
      interceptor.onFulfilled,
      interceptor.onRejected,
    );
  }

  private setupInterceptors(): void {
    // Default request interceptor for authentication
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    // Default response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // Handle common errors
        if (error.response?.status === 401) {
          // Unauthorized - redirect to login
          window.location.href = '/login';
        }
        return Promise.reject(error);
      },
    );
  }

  /**
   * Make GET request
   */
  public async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.get<T>(url, config);
    return response.data;
  }

  /**
   * Make POST request
   */
  public async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.axiosInstance.post<T>(url, data, config);
    return response.data;
  }

  /**
   * Make PUT request
   */
  public async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig,
  ): Promise<T> {
    const response = await this.axiosInstance.put<T>(url, data, config);
    return response.data;
  }

  /**
   * Make DELETE request
   */
  public async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.delete<T>(url, config);
    return response.data;
  }

  /**
   * Get underlying axios instance (for advanced usage)
   */
  public getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }
}

export default ApiClient;

// Export singleton getter
export const getApiClient = (config?: ApiClientConfig) =>
  ApiClient.getInstance(config);
```

---

## Quick Start Commands

### Complete Task 7 (Backend API Responses)

```bash
# 1. Create response models
# Copy the code above to backend/app/schemas/responses.py

# 2. Update one API route as example
# Modify backend/app/api/feeds.py to use standardized responses

# 3. Create property tests
# Copy the test code to backend/tests/test_api_response_property.py

# 4. Run tests
cd backend
python3 -m pytest tests/test_api_response_property.py -v
```

### Complete Task 8.1 (Frontend API Client)

```bash
# 1. Create API client
mkdir -p frontend/lib/api
# Copy the code above to frontend/lib/api/client.ts

# 2. Install dependencies if needed
cd frontend
npm install axios

# 3. Initialize in app
# Add to frontend/lib/api/index.ts:
# export { getApiClient } from './client';
```

---

## Notes

- Each task builds on previous work
- Test after each major change
- Update documentation as you go
- Commit frequently with clear messages

## Next Steps

After completing tasks 7-8, continue with:

- Task 9: Frontend logging
- Task 10: State management refactoring
- Task 11: API client migration
- And so on...

Refer to the main tasks.md file for complete task details.
