/**
 * Unit tests for retry logic
 * Requirements: 1.2, 4.3
 */

import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { AxiosError, AxiosRequestConfig } from 'axios';
import {
  shouldRetry,
  sleep,
  createRetryConfig,
  withRetry,
  DEFAULT_RETRY_CONFIG,
  RetryableRequestConfig,
} from '@/lib/api/retry';
import { ErrorCode } from '@/lib/api/errors';

describe('shouldRetry', () => {
  it('should not retry if max retries reached', () => {
    const config: RetryableRequestConfig = {
      _retryCount: 3,
      _retryConfig: { ...DEFAULT_RETRY_CONFIG, maxRetries: 3 },
    } as RetryableRequestConfig;

    const error = {
      response: { status: 503 },
      config,
    } as AxiosError;

    expect(shouldRetry(error, config)).toBe(false);
  });

  it('should retry network errors', () => {
    const config: RetryableRequestConfig = {
      _retryCount: 0,
    } as RetryableRequestConfig;

    const error = {
      message: 'Network Error',
      config,
    } as AxiosError;

    expect(shouldRetry(error, config)).toBe(true);
  });

  it('should retry timeout errors', () => {
    const config: RetryableRequestConfig = {
      _retryCount: 0,
    } as RetryableRequestConfig;

    const error = {
      code: 'ECONNABORTED',
      message: 'timeout',
      config,
    } as AxiosError;

    expect(shouldRetry(error, config)).toBe(true);
  });

  it('should retry retryable status codes', () => {
    const config: RetryableRequestConfig = {
      _retryCount: 0,
    } as RetryableRequestConfig;

    const retryableStatuses = [408, 429, 500, 502, 503, 504];

    retryableStatuses.forEach((status) => {
      const error = {
        response: { status },
        config,
      } as AxiosError;

      expect(shouldRetry(error, config)).toBe(true);
    });
  });

  it('should not retry non-retryable status codes', () => {
    const config: RetryableRequestConfig = {
      _retryCount: 0,
    } as RetryableRequestConfig;

    const nonRetryableStatuses = [400, 401, 403, 404, 422];

    nonRetryableStatuses.forEach((status) => {
      const error = {
        response: {
          status,
          data: {
            error_code: ErrorCode.VALIDATION_FAILED,
          },
        },
        config,
      } as AxiosError;

      expect(shouldRetry(error, config)).toBe(false);
    });
  });

  it('should retry based on error code', () => {
    const config: RetryableRequestConfig = {
      _retryCount: 0,
    } as RetryableRequestConfig;

    const error = {
      response: {
        status: 500,
        data: {
          error_code: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        },
      },
      config,
    } as AxiosError;

    expect(shouldRetry(error, config)).toBe(true);
  });
});

describe('sleep', () => {
  it('should sleep for specified duration', async () => {
    const start = Date.now();
    await sleep(100);
    const duration = Date.now() - start;

    expect(duration).toBeGreaterThanOrEqual(90); // Allow some margin
    expect(duration).toBeLessThan(150);
  });
});

describe('createRetryConfig', () => {
  it('should create config with defaults', () => {
    const config = createRetryConfig();

    expect(config.maxRetries).toBe(DEFAULT_RETRY_CONFIG.maxRetries);
    expect(config.baseDelay).toBe(DEFAULT_RETRY_CONFIG.baseDelay);
    expect(config.maxDelay).toBe(DEFAULT_RETRY_CONFIG.maxDelay);
  });

  it('should merge custom options with defaults', () => {
    const config = createRetryConfig({
      maxRetries: 5,
      baseDelay: 2000,
    });

    expect(config.maxRetries).toBe(5);
    expect(config.baseDelay).toBe(2000);
    expect(config.maxDelay).toBe(DEFAULT_RETRY_CONFIG.maxDelay);
  });

  it('should allow custom onRetry callback', () => {
    const onRetry = vi.fn();
    const config = createRetryConfig({ onRetry });

    expect(config.onRetry).toBe(onRetry);
  });
});

describe('withRetry', () => {
  it('should add retry config to request config', () => {
    const requestConfig: AxiosRequestConfig = {
      url: '/api/test',
      method: 'GET',
    };

    const configWithRetry = withRetry(requestConfig, { maxRetries: 5 });

    expect((configWithRetry as any)._retryConfig).toBeDefined();
    expect((configWithRetry as any)._retryConfig.maxRetries).toBe(5);
  });

  it('should use default retry config if not provided', () => {
    const requestConfig: AxiosRequestConfig = {
      url: '/api/test',
      method: 'GET',
    };

    const configWithRetry = withRetry(requestConfig);

    expect((configWithRetry as any)._retryConfig).toBeDefined();
    expect((configWithRetry as any)._retryConfig.maxRetries).toBe(DEFAULT_RETRY_CONFIG.maxRetries);
  });
});
