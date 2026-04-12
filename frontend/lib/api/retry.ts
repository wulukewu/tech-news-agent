/**
 * API Retry Logic - Exponential Backoff
 * Requirements: 1.2, 4.3
 *
 * This module provides retry logic with exponential backoff for transient errors.
 */

import { AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { ApiError, parseApiError, isNetworkError, isTimeoutError, getRetryDelay } from './errors';

/**
 * Retry configuration options
 */
export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  retryableStatusCodes: number[];
  onRetry?: (attempt: number, error: ApiError, delay: number) => void;
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 30000, // 30 seconds
  retryableStatusCodes: [408, 429, 500, 502, 503, 504],
};

/**
 * Extended Axios request config with retry metadata
 */
export interface RetryableRequestConfig extends AxiosRequestConfig {
  _retryCount?: number;
  _retryConfig?: RetryConfig;
}

/**
 * Check if error should be retried
 */
export function shouldRetry(error: AxiosError, config: RetryableRequestConfig): boolean {
  const retryConfig = config._retryConfig || DEFAULT_RETRY_CONFIG;
  const retryCount = config._retryCount || 0;

  // Don't retry if max retries reached
  if (retryCount >= retryConfig.maxRetries) {
    return false;
  }

  // Retry network errors
  if (isNetworkError(error)) {
    return true;
  }

  // Retry timeout errors
  if (isTimeoutError(error)) {
    return true;
  }

  // Retry specific status codes
  const statusCode = error.response?.status;
  if (statusCode && retryConfig.retryableStatusCodes.includes(statusCode)) {
    return true;
  }

  // Check if error is retryable based on error code
  const apiError = parseApiError(error);
  return apiError.isRetryable();
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry interceptor for Axios
 * Implements exponential backoff retry logic
 */
export async function retryInterceptor(error: AxiosError): Promise<any> {
  const config = error.config as RetryableRequestConfig;

  if (!config) {
    return Promise.reject(error);
  }

  // Check if should retry
  if (!shouldRetry(error, config)) {
    return Promise.reject(error);
  }

  // Initialize retry count
  config._retryCount = config._retryCount || 0;
  config._retryCount += 1;

  const retryConfig = config._retryConfig || DEFAULT_RETRY_CONFIG;
  const delay = getRetryDelay(config._retryCount, retryConfig.baseDelay, retryConfig.maxDelay);

  // Call onRetry callback if provided
  if (retryConfig.onRetry) {
    const apiError = parseApiError(error);
    retryConfig.onRetry(config._retryCount, apiError, delay);
  }

  // Wait before retry
  await sleep(delay);

  // Import axios dynamically to avoid circular dependency
  const axios = (await import('axios')).default;

  // Retry the request
  return axios.request(config);
}

/**
 * Create retry config for specific request
 */
export function createRetryConfig(options: Partial<RetryConfig> = {}): RetryConfig {
  return {
    ...DEFAULT_RETRY_CONFIG,
    ...options,
  };
}

/**
 * Add retry config to Axios request config
 */
export function withRetry(
  config: AxiosRequestConfig,
  retryConfig?: Partial<RetryConfig>
): AxiosRequestConfig {
  return {
    ...config,
    _retryConfig: createRetryConfig(retryConfig),
  } as AxiosRequestConfig;
}
