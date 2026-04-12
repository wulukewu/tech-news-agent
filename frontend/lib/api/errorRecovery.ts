/**
 * Error Recovery Strategies
 * Requirements: 4.5
 *
 * This module provides error recovery strategies for handling edge cases
 * and transient failures in API calls.
 */

import { ApiError, ErrorCode } from './errors';
import { apiClient } from './client';

/**
 * Recovery strategy type
 */
export type RecoveryStrategy = 'retry' | 'fallback' | 'cache' | 'skip' | 'manual';

/**
 * Recovery result
 */
export interface RecoveryResult<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  strategy: RecoveryStrategy;
  message: string;
}

/**
 * Fallback data provider function
 */
export type FallbackProvider<T> = () => T | Promise<T>;

/**
 * Recovery options
 */
export interface RecoveryOptions<T> {
  /**
   * Maximum retry attempts (default: 3)
   */
  maxRetries?: number;

  /**
   * Fallback data provider
   */
  fallback?: FallbackProvider<T>;

  /**
   * Cache key for storing/retrieving cached data
   */
  cacheKey?: string;

  /**
   * Whether to use cached data on error (default: true)
   */
  useCache?: boolean;

  /**
   * Whether to skip error and return undefined (default: false)
   */
  skipOnError?: boolean;

  /**
   * Custom error handler
   */
  onError?: (error: ApiError) => void;
}

/**
 * Simple in-memory cache for API responses
 */
class ResponseCache {
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private maxAge: number = 5 * 60 * 1000; // 5 minutes

  /**
   * Get cached data
   */
  get<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    // Check if cache is expired
    if (Date.now() - cached.timestamp > this.maxAge) {
      this.cache.delete(key);
      return null;
    }

    return cached.data as T;
  }

  /**
   * Set cached data
   */
  set<T>(key: string, data: T): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  /**
   * Clear cache
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Remove specific cache entry
   */
  remove(key: string): void {
    this.cache.delete(key);
  }
}

/**
 * Global response cache instance
 */
export const responseCache = new ResponseCache();

/**
 * Execute API call with error recovery
 *
 * @param apiCall - Function that makes the API call
 * @param options - Recovery options
 * @returns Promise resolving to recovery result
 */
export async function withRecovery<T>(
  apiCall: () => Promise<T>,
  options: RecoveryOptions<T> = {}
): Promise<RecoveryResult<T>> {
  const {
    maxRetries = 3,
    fallback,
    cacheKey,
    useCache = true,
    skipOnError = false,
    onError,
  } = options;

  let lastError: ApiError | null = null;
  let retryCount = 0;

  // Try to get from cache first if enabled
  if (useCache && cacheKey) {
    const cached = responseCache.get<T>(cacheKey);
    if (cached) {
      return {
        success: true,
        data: cached,
        strategy: 'cache',
        message: 'Data retrieved from cache',
      };
    }
  }

  // Retry loop
  while (retryCount < maxRetries) {
    try {
      const data = await apiCall();

      // Cache successful response if cache key provided
      if (cacheKey) {
        responseCache.set(cacheKey, data);
      }

      return {
        success: true,
        data,
        strategy: retryCount > 0 ? 'retry' : 'manual',
        message:
          retryCount > 0 ? `Request succeeded after ${retryCount} retries` : 'Request succeeded',
      };
    } catch (error) {
      if (error instanceof ApiError) {
        lastError = error;

        // Call custom error handler if provided
        if (onError) {
          onError(error);
        }

        // Don't retry if error is not retryable
        if (!error.isRetryable()) {
          break;
        }

        retryCount++;

        // Wait before retry (exponential backoff)
        if (retryCount < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 10000);
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      } else {
        // Non-API error, don't retry
        break;
      }
    }
  }

  // All retries failed, try recovery strategies

  // Strategy 1: Use fallback data
  if (fallback) {
    try {
      const fallbackData = await fallback();
      return {
        success: true,
        data: fallbackData,
        error: lastError || undefined,
        strategy: 'fallback',
        message: 'Using fallback data due to API error',
      };
    } catch (fallbackError) {
      // Fallback also failed, continue to next strategy
    }
  }

  // Strategy 2: Use cached data (even if expired)
  if (useCache && cacheKey) {
    const cached = responseCache.get<T>(cacheKey);
    if (cached) {
      return {
        success: true,
        data: cached,
        error: lastError || undefined,
        strategy: 'cache',
        message: 'Using cached data due to API error',
      };
    }
  }

  // Strategy 3: Skip error and return undefined
  if (skipOnError) {
    return {
      success: false,
      error: lastError || undefined,
      strategy: 'skip',
      message: 'Error skipped, returning undefined',
    };
  }

  // No recovery possible, return error
  return {
    success: false,
    error: lastError || undefined,
    strategy: 'manual',
    message: 'All recovery strategies failed',
  };
}

/**
 * Batch API calls with error recovery
 *
 * @param apiCalls - Array of API call functions
 * @param options - Recovery options
 * @returns Promise resolving to array of recovery results
 */
export async function batchWithRecovery<T>(
  apiCalls: Array<() => Promise<T>>,
  options: RecoveryOptions<T> = {}
): Promise<Array<RecoveryResult<T>>> {
  return Promise.all(apiCalls.map((apiCall) => withRecovery(apiCall, options)));
}

/**
 * Execute API call with timeout
 *
 * @param apiCall - Function that makes the API call
 * @param timeoutMs - Timeout in milliseconds
 * @returns Promise resolving to API response or timeout error
 */
export async function withTimeout<T>(
  apiCall: () => Promise<T>,
  timeoutMs: number = 30000
): Promise<T> {
  return Promise.race([
    apiCall(),
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`Request timeout after ${timeoutMs}ms`)), timeoutMs)
    ),
  ]);
}

/**
 * Debounce API calls to prevent excessive requests
 *
 * @param apiCall - Function that makes the API call
 * @param delayMs - Debounce delay in milliseconds
 * @returns Debounced API call function
 */
export function debounceApiCall<T>(
  apiCall: (...args: any[]) => Promise<T>,
  delayMs: number = 300
): (...args: any[]) => Promise<T> {
  let timeoutId: NodeJS.Timeout | null = null;
  let latestResolve: ((value: T) => void) | null = null;
  let latestReject: ((error: any) => void) | null = null;

  return (...args: any[]): Promise<T> => {
    return new Promise<T>((resolve, reject) => {
      // Clear previous timeout
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // Store latest resolve/reject
      latestResolve = resolve;
      latestReject = reject;

      // Set new timeout
      timeoutId = setTimeout(async () => {
        try {
          const result = await apiCall(...args);
          if (latestResolve) {
            latestResolve(result);
          }
        } catch (error) {
          if (latestReject) {
            latestReject(error);
          }
        }
      }, delayMs);
    });
  };
}

/**
 * Throttle API calls to limit request rate
 *
 * @param apiCall - Function that makes the API call
 * @param limitMs - Minimum time between calls in milliseconds
 * @returns Throttled API call function
 */
export function throttleApiCall<T>(
  apiCall: (...args: any[]) => Promise<T>,
  limitMs: number = 1000
): (...args: any[]) => Promise<T> {
  let lastCallTime = 0;
  let pendingCall: Promise<T> | null = null;

  return async (...args: any[]): Promise<T> => {
    const now = Date.now();
    const timeSinceLastCall = now - lastCallTime;

    // If enough time has passed, make the call immediately
    if (timeSinceLastCall >= limitMs) {
      lastCallTime = now;
      return apiCall(...args);
    }

    // Otherwise, wait for the remaining time
    if (!pendingCall) {
      const waitTime = limitMs - timeSinceLastCall;
      pendingCall = new Promise<T>((resolve, reject) => {
        setTimeout(async () => {
          try {
            lastCallTime = Date.now();
            const result = await apiCall(...args);
            pendingCall = null;
            resolve(result);
          } catch (error) {
            pendingCall = null;
            reject(error);
          }
        }, waitTime);
      });
    }

    return pendingCall;
  };
}
