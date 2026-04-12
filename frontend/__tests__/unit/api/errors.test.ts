/**
 * Unit tests for API error handling
 * Requirements: 1.2, 1.4, 4.3
 */

import { describe, it, expect } from '@jest/globals';
import { AxiosError } from 'axios';
import {
  ApiError,
  ErrorCode,
  parseApiError,
  isNetworkError,
  isTimeoutError,
  getRetryDelay,
  ERROR_MESSAGES,
} from '@/lib/api/errors';

describe('ApiError', () => {
  it('should create ApiError with all properties', () => {
    const error = new ApiError(
      500,
      ErrorCode.INTERNAL_ERROR,
      'Internal server error',
      'An internal error occurred',
      [{ field: 'test', message: 'Test error' }],
      { requestId: '123' }
    );

    expect(error.statusCode).toBe(500);
    expect(error.errorCode).toBe(ErrorCode.INTERNAL_ERROR);
    expect(error.message).toBe('Internal server error');
    expect(error.userMessage).toBe('An internal error occurred');
    expect(error.details).toHaveLength(1);
    expect(error.metadata).toEqual({ requestId: '123' });
  });

  it('should get display message without details', () => {
    const error = new ApiError(500, ErrorCode.INTERNAL_ERROR, 'Error', 'User friendly error');

    expect(error.getDisplayMessage()).toBe('User friendly error');
  });

  it('should get display message with details', () => {
    const error = new ApiError(
      422,
      ErrorCode.VALIDATION_FAILED,
      'Validation failed',
      'Please check your input',
      [
        { field: 'email', message: 'Invalid email' },
        { field: 'password', message: 'Too short' },
      ]
    );

    expect(error.getDisplayMessage()).toBe('Please check your input Invalid email, Too short');
  });

  it('should identify retryable errors', () => {
    const retryableError = new ApiError(
      503,
      ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
      'Service unavailable',
      'Try again'
    );
    const nonRetryableError = new ApiError(
      400,
      ErrorCode.VALIDATION_FAILED,
      'Validation failed',
      'Check input'
    );

    expect(retryableError.isRetryable()).toBe(true);
    expect(nonRetryableError.isRetryable()).toBe(false);
  });

  it('should convert to JSON', () => {
    const error = new ApiError(500, ErrorCode.INTERNAL_ERROR, 'Error', 'User error', [
      { message: 'Detail' },
    ]);
    const json = error.toJSON();

    expect(json).toEqual({
      name: 'ApiError',
      message: 'Error',
      statusCode: 500,
      errorCode: ErrorCode.INTERNAL_ERROR,
      userMessage: 'User error',
      details: [{ message: 'Detail' }],
      metadata: undefined,
    });
  });
});

describe('parseApiError', () => {
  it('should parse error with backend response', () => {
    const axiosError = {
      response: {
        status: 422,
        data: {
          success: false,
          error: 'Validation failed',
          error_code: 'VALIDATION_FAILED',
          details: [{ field: 'email', message: 'Invalid format' }],
        },
      },
      message: 'Request failed',
      config: {},
    } as AxiosError;

    const apiError = parseApiError(axiosError);

    expect(apiError.statusCode).toBe(422);
    expect(apiError.errorCode).toBe(ErrorCode.VALIDATION_FAILED);
    expect(apiError.message).toBe('Validation failed');
    expect(apiError.userMessage).toBe(ERROR_MESSAGES[ErrorCode.VALIDATION_FAILED]);
    expect(apiError.details).toHaveLength(1);
  });

  it('should parse error without backend response', () => {
    const axiosError = {
      message: 'Network error',
      config: {},
    } as AxiosError;

    const apiError = parseApiError(axiosError);

    expect(apiError.statusCode).toBe(500);
    expect(apiError.errorCode).toBe(ErrorCode.INTERNAL_UNEXPECTED);
    expect(apiError.message).toBe('Network error');
  });

  it('should use default error code for unknown error', () => {
    const axiosError = {
      response: {
        status: 500,
        data: {
          error: 'Unknown error',
        },
      },
      message: 'Request failed',
      config: {},
    } as AxiosError;

    const apiError = parseApiError(axiosError);

    expect(apiError.errorCode).toBe(ErrorCode.INTERNAL_UNEXPECTED);
    expect(apiError.userMessage).toBe(ERROR_MESSAGES[ErrorCode.INTERNAL_UNEXPECTED]);
  });
});

describe('isNetworkError', () => {
  it('should identify network errors', () => {
    const networkError = {
      message: 'Network Error',
      config: {},
    } as AxiosError;

    expect(isNetworkError(networkError)).toBe(true);
  });

  it('should not identify timeout as network error', () => {
    const timeoutError = {
      message: 'timeout',
      code: 'ECONNABORTED',
      config: {},
    } as AxiosError;

    expect(isNetworkError(timeoutError)).toBe(false);
  });

  it('should not identify response errors as network error', () => {
    const responseError = {
      response: { status: 500 },
      message: 'Server error',
      config: {},
    } as AxiosError;

    expect(isNetworkError(responseError)).toBe(false);
  });
});

describe('isTimeoutError', () => {
  it('should identify timeout by code', () => {
    const timeoutError = {
      code: 'ECONNABORTED',
      message: 'Request timeout',
      config: {},
    } as AxiosError;

    expect(isTimeoutError(timeoutError)).toBe(true);
  });

  it('should identify timeout by message', () => {
    const timeoutError = {
      message: 'timeout of 5000ms exceeded',
      config: {},
    } as AxiosError;

    expect(isTimeoutError(timeoutError)).toBe(true);
  });

  it('should not identify non-timeout errors', () => {
    const normalError = {
      message: 'Server error',
      config: {},
    } as AxiosError;

    expect(isTimeoutError(normalError)).toBe(false);
  });
});

describe('getRetryDelay', () => {
  it('should calculate exponential backoff', () => {
    expect(getRetryDelay(1, 1000)).toBe(1000); // 1000 * 2^0
    expect(getRetryDelay(2, 1000)).toBe(2000); // 1000 * 2^1
    expect(getRetryDelay(3, 1000)).toBe(4000); // 1000 * 2^2
    expect(getRetryDelay(4, 1000)).toBe(8000); // 1000 * 2^3
  });

  it('should respect max delay', () => {
    expect(getRetryDelay(10, 1000, 5000)).toBe(5000);
    expect(getRetryDelay(20, 1000, 10000)).toBe(10000);
  });

  it('should use default values', () => {
    expect(getRetryDelay(1)).toBe(1000);
    expect(getRetryDelay(2)).toBe(2000);
  });
});

describe('ERROR_MESSAGES', () => {
  it('should have messages for all error codes', () => {
    const errorCodes = Object.values(ErrorCode);

    errorCodes.forEach((code) => {
      expect(ERROR_MESSAGES[code]).toBeDefined();
      expect(ERROR_MESSAGES[code].length).toBeGreaterThan(0);
    });
  });

  it('should have user-friendly messages', () => {
    // Check that messages are user-friendly (not technical)
    expect(ERROR_MESSAGES[ErrorCode.AUTH_INVALID_TOKEN]).toContain('log in');
    expect(ERROR_MESSAGES[ErrorCode.VALIDATION_FAILED]).toContain('check your input');
    expect(ERROR_MESSAGES[ErrorCode.RATE_LIMIT_EXCEEDED]).toContain('wait');
  });
});
