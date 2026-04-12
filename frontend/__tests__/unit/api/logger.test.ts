/**
 * Unit tests for API logger
 * Requirements: 1.2, 4.3
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiLogger, LogLevel, apiLogger } from '@/lib/api/logger';
import { ApiError, ErrorCode } from '@/lib/api/errors';

describe('ApiLogger', () => {
  let logger: ApiLogger;

  beforeEach(() => {
    // Get fresh instance and clear logs
    logger = ApiLogger.getInstance();
    logger.clearLogs();
  });

  describe('singleton pattern', () => {
    it('should return same instance', () => {
      const instance1 = ApiLogger.getInstance();
      const instance2 = ApiLogger.getInstance();

      expect(instance1).toBe(instance2);
    });
  });

  describe('logging methods', () => {
    it('should log debug messages', () => {
      logger.debug('Debug message', { key: 'value' });

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.DEBUG);
      expect(logs[0].message).toBe('Debug message');
      expect(logs[0].context).toEqual({ key: 'value' });
    });

    it('should log info messages', () => {
      logger.info('Info message');

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.INFO);
      expect(logs[0].message).toBe('Info message');
    });

    it('should log warning messages', () => {
      logger.warn('Warning message');

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.WARN);
      expect(logs[0].message).toBe('Warning message');
    });

    it('should log error messages', () => {
      logger.error('Error message');

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.ERROR);
      expect(logs[0].message).toBe('Error message');
    });

    it('should include timestamp in log entries', () => {
      logger.info('Test message');

      const logs = logger.getLogs();
      expect(logs[0].timestamp).toBeDefined();
      expect(new Date(logs[0].timestamp).getTime()).toBeGreaterThan(0);
    });
  });

  describe('log management', () => {
    it('should limit number of logs', () => {
      // Log more than maxLogs (100)
      for (let i = 0; i < 150; i++) {
        logger.info(`Message ${i}`);
      }

      const logs = logger.getLogs();
      expect(logs.length).toBeLessThanOrEqual(100);
      // Should keep most recent logs
      expect(logs[logs.length - 1].message).toBe('Message 149');
    });

    it('should clear logs', () => {
      logger.info('Message 1');
      logger.info('Message 2');
      expect(logger.getLogs()).toHaveLength(2);

      logger.clearLogs();
      expect(logger.getLogs()).toHaveLength(0);
    });

    it('should return copy of logs', () => {
      logger.info('Message');
      const logs1 = logger.getLogs();
      const logs2 = logger.getLogs();

      expect(logs1).not.toBe(logs2); // Different array instances
      expect(logs1).toEqual(logs2); // Same content
    });
  });

  describe('logRequest', () => {
    it('should log request details', () => {
      const config: AxiosRequestConfig = {
        method: 'POST',
        url: '/api/users',
        params: { page: 1 },
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer token123',
        },
      };

      logger.logRequest(config);

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.DEBUG);
      expect(logs[0].message).toBe('API Request');
      expect(logs[0].context?.method).toBe('POST');
      expect(logs[0].context?.url).toBe('/api/users');
      expect(logs[0].context?.params).toEqual({ page: 1 });
    });

    it('should sanitize sensitive headers', () => {
      const config: AxiosRequestConfig = {
        method: 'GET',
        url: '/api/data',
        headers: {
          Authorization: 'Bearer secret-token',
          Cookie: 'session=abc123',
          'X-API-Key': 'api-key-123',
          'Content-Type': 'application/json',
        },
      };

      logger.logRequest(config);

      const logs = logger.getLogs();
      const headers = logs[0].context?.headers;

      expect(headers.Authorization).toBe('[REDACTED]');
      expect(headers.Cookie).toBe('[REDACTED]');
      expect(headers['X-API-Key']).toBe('[REDACTED]');
      expect(headers['Content-Type']).toBe('application/json');
    });
  });

  describe('logResponse', () => {
    it('should log response details', () => {
      const response: AxiosResponse = {
        status: 200,
        statusText: 'OK',
        config: {
          url: '/api/users',
          method: 'GET',
        },
        headers: {},
        data: {},
      };

      logger.logResponse(response);

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.DEBUG);
      expect(logs[0].message).toBe('API Response');
      expect(logs[0].context?.status).toBe(200);
      expect(logs[0].context?.statusText).toBe('OK');
      expect(logs[0].context?.url).toBe('/api/users');
      expect(logs[0].context?.method).toBe('GET');
    });
  });

  describe('logApiError', () => {
    it('should log API error details', () => {
      const error = new ApiError(
        500,
        ErrorCode.INTERNAL_ERROR,
        'Internal server error',
        'An error occurred',
        [{ field: 'test', message: 'Test error' }]
      );

      const config: AxiosRequestConfig = {
        url: '/api/users',
        method: 'POST',
      };

      logger.logApiError(error, config);

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.ERROR);
      expect(logs[0].message).toBe('API Error');
      expect(logs[0].context?.statusCode).toBe(500);
      expect(logs[0].context?.errorCode).toBe(ErrorCode.INTERNAL_ERROR);
      expect(logs[0].context?.message).toBe('Internal server error');
      expect(logs[0].context?.userMessage).toBe('An error occurred');
      expect(logs[0].context?.url).toBe('/api/users');
      expect(logs[0].context?.method).toBe('POST');
    });
  });

  describe('logRetry', () => {
    it('should log retry attempt', () => {
      const error = new ApiError(
        503,
        ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        'Service unavailable',
        'Try again'
      );

      const config: AxiosRequestConfig = {
        url: '/api/external',
        method: 'GET',
      };

      logger.logRetry(2, error, 2000, config);

      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe(LogLevel.WARN);
      expect(logs[0].message).toBe('API Retry');
      expect(logs[0].context?.attempt).toBe(2);
      expect(logs[0].context?.delay).toBe(2000);
      expect(logs[0].context?.errorCode).toBe(ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE);
      expect(logs[0].context?.url).toBe('/api/external');
    });
  });
});

describe('apiLogger singleton', () => {
  it('should export singleton instance', () => {
    expect(apiLogger).toBeDefined();
    expect(apiLogger).toBe(ApiLogger.getInstance());
  });
});
