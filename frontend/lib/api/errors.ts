/**
 * API Error Handling - Error Mapping and Types
 * Requirements: 1.2, 1.4, 4.3
 *
 * This module provides:
 * - Error type definitions matching backend error codes
 * - Error mapping from backend codes to user-friendly messages
 * - Custom error classes for API errors
 */

import { AxiosError } from 'axios';

/**
 * Backend error codes (must match backend/app/core/errors.py ErrorCode enum)
 */
export enum ErrorCode {
  // Authentication & Authorization
  AUTH_INVALID_TOKEN = 'AUTH_INVALID_TOKEN',
  AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED',
  AUTH_MISSING_TOKEN = 'AUTH_MISSING_TOKEN',
  AUTH_INSUFFICIENT_PERMISSIONS = 'AUTH_INSUFFICIENT_PERMISSIONS',
  AUTH_OAUTH_FAILED = 'AUTH_OAUTH_FAILED',

  // Database Errors
  DB_CONNECTION_FAILED = 'DB_CONNECTION_FAILED',
  DB_QUERY_FAILED = 'DB_QUERY_FAILED',
  DB_CONSTRAINT_VIOLATION = 'DB_CONSTRAINT_VIOLATION',
  DB_TRANSACTION_FAILED = 'DB_TRANSACTION_FAILED',

  // Validation Errors
  VALIDATION_FAILED = 'VALIDATION_FAILED',
  VALIDATION_MISSING_FIELD = 'VALIDATION_MISSING_FIELD',
  VALIDATION_INVALID_FORMAT = 'VALIDATION_INVALID_FORMAT',
  VALIDATION_BUSINESS_RULE = 'VALIDATION_BUSINESS_RULE',

  // External Service Errors
  EXTERNAL_SERVICE_UNAVAILABLE = 'EXTERNAL_SERVICE_UNAVAILABLE',
  EXTERNAL_SERVICE_TIMEOUT = 'EXTERNAL_SERVICE_TIMEOUT',
  EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR',
  EXTERNAL_RSS_FETCH_FAILED = 'EXTERNAL_RSS_FETCH_FAILED',
  EXTERNAL_LLM_ERROR = 'EXTERNAL_LLM_ERROR',
  EXTERNAL_DISCORD_ERROR = 'EXTERNAL_DISCORD_ERROR',

  // Resource Errors
  NOT_FOUND = 'NOT_FOUND',
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',

  // Rate Limiting
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',

  // Configuration Errors
  CONFIG_MISSING = 'CONFIG_MISSING',
  CONFIG_INVALID = 'CONFIG_INVALID',

  // Internal Errors
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  INTERNAL_UNEXPECTED = 'INTERNAL_UNEXPECTED',
}

/**
 * Error detail from backend validation errors
 */
export interface ErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

/**
 * Standardized error response from backend
 * Requirement 1.2: Standardized error responses
 */
export interface ApiErrorResponse {
  success: false;
  error: string;
  error_code: string;
  details?: ErrorDetail[];
  metadata?: Record<string, any>;
}

/**
 * User-friendly error messages mapped from backend error codes
 * Requirement 4.3: Map backend errors to user-friendly messages
 */
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  // Authentication & Authorization
  [ErrorCode.AUTH_INVALID_TOKEN]: 'Your session is invalid. Please log in again.',
  [ErrorCode.AUTH_TOKEN_EXPIRED]: 'Your session has expired. Please log in again.',
  [ErrorCode.AUTH_MISSING_TOKEN]: 'Authentication required. Please log in.',
  [ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS]: 'You do not have permission to perform this action.',
  [ErrorCode.AUTH_OAUTH_FAILED]: 'Authentication failed. Please try again.',

  // Database Errors
  [ErrorCode.DB_CONNECTION_FAILED]: 'Unable to connect to the database. Please try again later.',
  [ErrorCode.DB_QUERY_FAILED]: 'A database error occurred. Please try again.',
  [ErrorCode.DB_CONSTRAINT_VIOLATION]:
    'This operation violates data constraints. Please check your input.',
  [ErrorCode.DB_TRANSACTION_FAILED]: 'The operation could not be completed. Please try again.',

  // Validation Errors
  [ErrorCode.VALIDATION_FAILED]: 'Please check your input and try again.',
  [ErrorCode.VALIDATION_MISSING_FIELD]: 'Required fields are missing. Please complete the form.',
  [ErrorCode.VALIDATION_INVALID_FORMAT]:
    'Some fields have invalid format. Please check your input.',
  [ErrorCode.VALIDATION_BUSINESS_RULE]:
    'This operation violates business rules. Please review your input.',

  // External Service Errors
  [ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE]:
    'An external service is temporarily unavailable. Please try again later.',
  [ErrorCode.EXTERNAL_SERVICE_TIMEOUT]: 'The request timed out. Please try again.',
  [ErrorCode.EXTERNAL_API_ERROR]: 'An external service error occurred. Please try again later.',
  [ErrorCode.EXTERNAL_RSS_FETCH_FAILED]: 'Unable to fetch RSS feed. Please try again later.',
  [ErrorCode.EXTERNAL_LLM_ERROR]: 'AI service is temporarily unavailable. Please try again later.',
  [ErrorCode.EXTERNAL_DISCORD_ERROR]: 'Discord service error. Please try again later.',

  // Resource Errors
  [ErrorCode.NOT_FOUND]: 'The requested resource was not found.',
  [ErrorCode.RESOURCE_NOT_FOUND]: 'The requested resource was not found.',

  // Rate Limiting
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 'Too many requests. Please wait a moment and try again.',

  // Configuration Errors
  [ErrorCode.CONFIG_MISSING]: 'System configuration error. Please contact support.',
  [ErrorCode.CONFIG_INVALID]: 'System configuration error. Please contact support.',

  // Internal Errors
  [ErrorCode.INTERNAL_ERROR]: 'An internal error occurred. Please try again later.',
  [ErrorCode.INTERNAL_UNEXPECTED]: 'An unexpected error occurred. Please try again later.',
};

/**
 * Custom API Error class
 * Requirement 1.2, 1.4: Standardized error responses with type safety
 */
export class ApiError extends Error {
  public readonly statusCode: number;
  public readonly errorCode: ErrorCode;
  public readonly userMessage: string;
  public readonly details?: ErrorDetail[];
  public readonly metadata?: Record<string, any>;
  public readonly originalError?: AxiosError;

  constructor(
    statusCode: number,
    errorCode: ErrorCode,
    message: string,
    userMessage: string,
    details?: ErrorDetail[],
    metadata?: Record<string, any>,
    originalError?: AxiosError
  ) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.userMessage = userMessage;
    this.details = details;
    this.metadata = metadata;
    this.originalError = originalError;

    // Maintains proper stack trace for where error was thrown (V8 only)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }

  /**
   * Get formatted error message for display to users
   */
  public getDisplayMessage(): string {
    if (this.details && this.details.length > 0) {
      const detailMessages = this.details.map((d) => d.message).join(', ');
      return `${this.userMessage} ${detailMessages}`;
    }
    return this.userMessage;
  }

  /**
   * Check if error is retryable (transient error)
   */
  public isRetryable(): boolean {
    const retryableErrors = [
      ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
      ErrorCode.EXTERNAL_SERVICE_TIMEOUT,
      ErrorCode.EXTERNAL_API_ERROR,
      ErrorCode.DB_CONNECTION_FAILED,
      ErrorCode.DB_TRANSACTION_FAILED,
    ];

    return (
      retryableErrors.includes(this.errorCode) || this.statusCode === 503 || this.statusCode === 504
    );
  }

  /**
   * Convert to plain object for logging
   */
  public toJSON(): Record<string, any> {
    return {
      name: this.name,
      message: this.message,
      statusCode: this.statusCode,
      errorCode: this.errorCode,
      userMessage: this.userMessage,
      details: this.details,
      metadata: this.metadata,
    };
  }
}

/**
 * Parse error response from backend and create ApiError
 * Requirement 1.2: Standardized error responses
 */
export function parseApiError(error: AxiosError): ApiError {
  const statusCode = error.response?.status || 500;
  const responseData = error.response?.data as ApiErrorResponse | undefined;

  // Extract error code and message from response
  const errorCode = (responseData?.error_code as ErrorCode) || ErrorCode.INTERNAL_UNEXPECTED;
  const backendMessage = responseData?.error || error.message;
  const details = responseData?.details;
  const metadata = responseData?.metadata;

  // Get user-friendly message
  const userMessage = ERROR_MESSAGES[errorCode] || ERROR_MESSAGES[ErrorCode.INTERNAL_UNEXPECTED];

  return new ApiError(statusCode, errorCode, backendMessage, userMessage, details, metadata, error);
}

/**
 * Check if error is a network error (no response from server)
 */
export function isNetworkError(error: AxiosError): boolean {
  return !error.response && error.code !== 'ECONNABORTED';
}

/**
 * Check if error is a timeout error
 */
export function isTimeoutError(error: AxiosError): boolean {
  return (
    error.code === 'ECONNABORTED' || (error.message && error.message.includes('timeout')) || false
  );
}

/**
 * Get retry delay based on attempt number (exponential backoff)
 */
export function getRetryDelay(
  attempt: number,
  baseDelay: number = 1000,
  maxDelay: number = 30000
): number {
  const delay = baseDelay * Math.pow(2, attempt - 1);
  return Math.min(delay, maxDelay);
}
