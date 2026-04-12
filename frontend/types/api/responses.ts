// Generated from responses.py
// Generated at: 2026-04-11T22:10:26.233504

/**
 * Pagination metadata for list endpoints.
 *
 * Validates: Requirement 15.4
 */
export interface PaginationMetadata {
  /** Total number of items */
  total_count: number;
  /** Current page number (1-indexed) */
  page: number;
  /** Number of items per page */
  page_size: number;
  /** Total number of pages */
  total_pages: number;
  /** Whether there is a next page */
  has_next: boolean;
  /** Whether there is a previous page */
  has_previous: boolean;
}

/**
 * Standardized success response format.
 *
 * All successful API responses should use this format.
 *
 * Validates: Requirements 15.1, 15.2
 */
export interface SuccessResponse<T> {
  /** Indicates successful operation */
  success: boolean;
  /** Response data */
  data: T;
  /** Optional metadata */
  metadata?: Record<string, any> | null;
}

/**
 * Standardized paginated response format.
 *
 * Used for list endpoints that support pagination.
 *
 * Validates: Requirements 15.1, 15.2, 15.4
 */
export interface PaginatedResponse<T> {
  /** Indicates successful operation */
  success: boolean;
  /** List of items */
  data: T[];
  /** Pagination metadata */
  pagination: PaginationMetadata;
  /** Optional metadata */
  metadata?: Record<string, any> | null;
}

/**
 * Detailed error information.
 *
 * Validates: Requirement 15.3
 */
export interface ErrorDetail {
  /** Field that caused the error */
  field?: string | null;
  /** Error message */
  message: string;
  /** Error code */
  code?: string | null;
}

/**
 * Standardized error response format.
 *
 * All error responses should use this format.
 *
 * Validates: Requirements 15.1, 15.3
 */
export interface ErrorResponse {
  /** Indicates failed operation */
  success: boolean;
  /** Error message */
  error: string;
  /** Machine-readable error code */
  error_code: string;
  /** Detailed error information */
  details?: ErrorDetail[] | null;
  /** Optional metadata */
  metadata?: Record<string, any> | null;
}
