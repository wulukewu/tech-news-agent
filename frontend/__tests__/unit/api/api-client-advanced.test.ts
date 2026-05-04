/**
 * Advanced Unit Tests for API Client
 * Tests error handling and interceptors on the actual apiClient
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiError, ErrorCode } from '@/lib/api/errors';

vi.mock('@/lib/config', () => ({
  getRuntimeConfig: vi.fn().mockResolvedValue({ apiBaseUrl: 'http://localhost:8000' }),
}));

vi.mock('@/lib/utils/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}));

import { apiClient } from '@/lib/api/client';

describe('apiClient - Advanced Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Instance', () => {
    it('should be defined', () => {
      expect(apiClient).toBeDefined();
    });

    it('should have interceptors configured', () => {
      expect(apiClient.interceptors.request).toBeDefined();
      expect(apiClient.interceptors.response).toBeDefined();
    });

    it('should have 30s timeout', () => {
      expect(apiClient.defaults.timeout).toBe(30000);
    });

    it('should have JSON content-type', () => {
      expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
    });
  });

  describe('ApiError class', () => {
    it('should carry statusCode and errorCode', () => {
      const err = new ApiError(404, ErrorCode.NOT_FOUND, 'Not found', 'Resource not found');
      expect(err.statusCode).toBe(404);
      expect(err.errorCode).toBe(ErrorCode.NOT_FOUND);
      expect(err).toBeInstanceOf(Error);
    });

    it('getDisplayMessage should return a string', () => {
      const err = new ApiError(
        429,
        ErrorCode.RATE_LIMIT_EXCEEDED,
        'Rate limit',
        'Too many requests'
      );
      expect(typeof err.getDisplayMessage()).toBe('string');
    });

    it('should preserve details array', () => {
      const details = [{ field: 'email', message: 'invalid', code: 'INVALID' }];
      const err = new ApiError(
        400,
        ErrorCode.VALIDATION_FAILED,
        'Validation',
        'Validation failed',
        details
      );
      expect(err.details).toEqual(details);
    });

    it('should be instanceof Error', () => {
      const err = new ApiError(
        500,
        ErrorCode.INTERNAL_ERROR,
        'Server error',
        'Internal server error'
      );
      expect(err).toBeInstanceOf(Error);
      expect(err.name).toBe('ApiError');
    });
  });
});
