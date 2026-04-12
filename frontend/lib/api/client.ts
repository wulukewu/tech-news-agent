/**
 * Unified API Client - Singleton Pattern
 * Requirements: 1.1, 1.3
 *
 * This module provides a singleton HTTP client for all API communications.
 * Features:
 * - Single instance pattern (Requirement 1.1)
 * - Request/response interceptor support (Requirement 1.3)
 * - Automatic authentication header injection
 * - Centralized error handling
 * - TypeScript generics for type-safe requests
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
  AxiosError,
} from 'axios';
import { parseApiError, ApiError } from './errors';
import { retryInterceptor, RetryConfig, createRetryConfig } from './retry';
import { apiLogger } from './logger';
import { performanceMonitor } from './performance';
import { API_FEATURE_FLAGS } from './featureFlags';

/**
 * Type definitions for interceptors
 */
export type RequestInterceptor = {
  onFulfilled?: (
    config: InternalAxiosRequestConfig
  ) => InternalAxiosRequestConfig | Promise<InternalAxiosRequestConfig>;
  onRejected?: (error: any) => any;
};

export type ResponseInterceptor = {
  onFulfilled?: (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>;
  onRejected?: (error: any) => any;
};

/**
 * API Client configuration options
 */
export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  retryConfig?: Partial<RetryConfig>;
  enableLogging?: boolean;
}

/**
 * ApiClient - Singleton HTTP client for all API communications
 *
 * Implements singleton pattern to ensure only one HTTP client instance exists.
 * Provides request/response interceptor support for authentication, logging, and error handling.
 *
 * Requirements:
 * - 1.1: Singleton pattern
 * - 1.2: Unified error handling with retry logic
 * - 1.3: Request/response interceptors
 * - 1.4: Type-safe error responses
 * - 4.3: User-friendly error messages
 */
class ApiClient {
  private static instance: ApiClient | null = null;
  private axiosInstance: AxiosInstance;
  private requestInterceptorIds: number[] = [];
  private responseInterceptorIds: number[] = [];
  private retryConfig: RetryConfig;
  private enableLogging: boolean;

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor(config?: ApiClientConfig) {
    this.retryConfig = createRetryConfig(config?.retryConfig);
    this.enableLogging = config?.enableLogging ?? process.env.NODE_ENV === 'development';

    this.axiosInstance = axios.create({
      baseURL: config?.baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: config?.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupDefaultInterceptors();
  }

  /**
   * Get the singleton instance of ApiClient
   * Requirement 1.1: Single HTTP client instance for all API communications
   */
  public static getInstance(config?: ApiClientConfig): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient(config);
    }
    return ApiClient.instance;
  }

  /**
   * Reset singleton instance (useful for testing)
   */
  public static resetInstance(): void {
    ApiClient.instance = null;
  }

  /**
   * Setup default request and response interceptors
   * Requirements:
   * - 1.2: Error handling and retry logic
   * - 1.3: Request/response interceptors
   * - 4.3: Error logging
   * - 11.1: Performance monitoring
   */
  private setupDefaultInterceptors(): void {
    // Request interceptor: Add authentication token, log request, and start performance tracking
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Start performance tracking if enabled
        if (API_FEATURE_FLAGS.ENABLE_API_MONITORING) {
          (config as any)._perfStartTime = performanceMonitor.startRequest(config);
        }

        // Log request if logging enabled
        if (this.enableLogging) {
          apiLogger.logRequest(config);
        }

        // Only access localStorage in browser environment
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('access_token');
          if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }

        // Add retry config to request (cast to any to avoid type issues)
        const configWithRetry = config as any;
        if (!configWithRetry._retryConfig) {
          configWithRetry._retryConfig = this.retryConfig;
        }

        return config;
      },
      (error) => {
        if (this.enableLogging) {
          apiLogger.error('Request interceptor error', { error: error.message });
        }
        return Promise.reject(error);
      }
    );

    // Response interceptor: Log response, record performance, and handle success
    this.axiosInstance.interceptors.response.use(
      (response) => {
        // Record performance if enabled
        if (API_FEATURE_FLAGS.ENABLE_API_MONITORING && (response.config as any)._perfStartTime) {
          performanceMonitor.recordSuccess(
            response.config,
            response,
            (response.config as any)._perfStartTime
          );
        }

        // Log response if logging enabled
        if (this.enableLogging) {
          apiLogger.logResponse(response);
        }
        return response;
      },
      async (error: AxiosError) => {
        // Parse error to ApiError
        const apiError = parseApiError(error);

        // Record performance if enabled
        if (API_FEATURE_FLAGS.ENABLE_API_MONITORING && (error.config as any)?._perfStartTime) {
          performanceMonitor.recordError(
            error.config,
            apiError,
            (error.config as any)._perfStartTime
          );
        }

        // Log error if logging enabled
        if (this.enableLogging) {
          apiLogger.logApiError(apiError, error.config);
        }

        // Handle 401 Unauthorized - redirect to login
        if (error.response?.status === 401 && typeof window !== 'undefined') {
          // Clear token and redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }

        // Try retry logic
        try {
          return await retryInterceptor(error);
        } catch (retryError) {
          // If retry fails, reject with ApiError
          return Promise.reject(apiError);
        }
      }
    );

    // Add retry callback to log retry attempts
    this.retryConfig.onRetry = (attempt, error, delay) => {
      if (this.enableLogging) {
        apiLogger.logRetry(attempt, error, delay);
      }
    };
  }

  /**
   * Add a custom request interceptor
   * Requirement 1.3: Support request/response interceptors
   *
   * @param interceptor - Request interceptor with onFulfilled and onRejected handlers
   * @returns Interceptor ID that can be used to remove the interceptor
   */
  public addRequestInterceptor(interceptor: RequestInterceptor): number {
    const id = this.axiosInstance.interceptors.request.use(
      interceptor.onFulfilled,
      interceptor.onRejected
    );
    this.requestInterceptorIds.push(id);
    return id;
  }

  /**
   * Add a custom response interceptor
   * Requirement 1.3: Support request/response interceptors
   *
   * @param interceptor - Response interceptor with onFulfilled and onRejected handlers
   * @returns Interceptor ID that can be used to remove the interceptor
   */
  public addResponseInterceptor(interceptor: ResponseInterceptor): number {
    const id = this.axiosInstance.interceptors.response.use(
      interceptor.onFulfilled,
      interceptor.onRejected
    );
    this.responseInterceptorIds.push(id);
    return id;
  }

  /**
   * Remove a request interceptor by ID
   *
   * @param id - Interceptor ID returned from addRequestInterceptor
   */
  public removeRequestInterceptor(id: number): void {
    this.axiosInstance.interceptors.request.eject(id);
    this.requestInterceptorIds = this.requestInterceptorIds.filter(
      (interceptorId) => interceptorId !== id
    );
  }

  /**
   * Remove a response interceptor by ID
   *
   * @param id - Interceptor ID returned from addResponseInterceptor
   */
  public removeResponseInterceptor(id: number): void {
    this.axiosInstance.interceptors.response.eject(id);
    this.responseInterceptorIds = this.responseInterceptorIds.filter(
      (interceptorId) => interceptorId !== id
    );
  }

  /**
   * Get the underlying Axios instance
   * Useful for advanced use cases that need direct access to Axios
   */
  public getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }

  /**
   * Update retry configuration
   */
  public setRetryConfig(config: Partial<RetryConfig>): void {
    this.retryConfig = createRetryConfig(config);
  }

  /**
   * Enable or disable logging
   */
  public setLogging(enabled: boolean): void {
    this.enableLogging = enabled;
  }

  /**
   * Perform a GET request
   * Requirement 1.5: TypeScript generics for type-safe request/response handling
   *
   * @param url - Request URL
   * @param config - Optional Axios request configuration
   * @returns Promise resolving to response data of type T
   * @throws ApiError with user-friendly message
   */
  public async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.get<T>(url, config);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw parseApiError(error as AxiosError);
    }
  }

  /**
   * Perform a POST request
   * Requirement 1.5: TypeScript generics for type-safe request/response handling
   *
   * @param url - Request URL
   * @param data - Request body data
   * @param config - Optional Axios request configuration
   * @returns Promise resolving to response data of type T
   * @throws ApiError with user-friendly message
   */
  public async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw parseApiError(error as AxiosError);
    }
  }

  /**
   * Perform a PUT request
   * Requirement 1.5: TypeScript generics for type-safe request/response handling
   *
   * @param url - Request URL
   * @param data - Request body data
   * @param config - Optional Axios request configuration
   * @returns Promise resolving to response data of type T
   * @throws ApiError with user-friendly message
   */
  public async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw parseApiError(error as AxiosError);
    }
  }

  /**
   * Perform a PATCH request
   * Requirement 1.5: TypeScript generics for type-safe request/response handling
   *
   * @param url - Request URL
   * @param data - Request body data
   * @param config - Optional Axios request configuration
   * @returns Promise resolving to response data of type T
   * @throws ApiError with user-friendly message
   */
  public async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.patch<T>(url, data, config);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw parseApiError(error as AxiosError);
    }
  }

  /**
   * Perform a DELETE request
   * Requirement 1.5: TypeScript generics for type-safe request/response handling
   *
   * @param url - Request URL
   * @param config - Optional Axios request configuration
   * @returns Promise resolving to response data of type T
   * @throws ApiError with user-friendly message
   */
  public async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axiosInstance.delete<T>(url, config);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw parseApiError(error as AxiosError);
    }
  }
}

/**
 * Export singleton instance for use throughout the application
 * Requirement 1.1: Single HTTP client instance
 */
export const apiClient = ApiClient.getInstance();

/**
 * Export ApiClient class for type definitions and testing
 */
export default ApiClient;

/**
 * Export error types and utilities
 */
export { ApiError, ErrorCode, parseApiError } from './errors';
export { apiLogger } from './logger';
export type { RetryConfig } from './retry';
