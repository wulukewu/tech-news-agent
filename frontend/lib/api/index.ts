/**
 * API Client Module - Unified API Layer
 * Requirements: 1.1, 1.2, 1.3, 1.4, 4.3, 10.3, 11.1
 *
 * This module provides a unified API client with:
 * - Singleton HTTP client (Requirement 1.1)
 * - Standardized error handling (Requirement 1.2)
 * - Request/response interceptors (Requirement 1.3)
 * - Type-safe requests (Requirement 1.4)
 * - User-friendly error messages (Requirement 4.3)
 * - Feature flags for A/B testing (Requirement 10.3)
 * - Performance monitoring (Requirement 11.1)
 * - Retry logic with exponential backoff
 * - Error logging and reporting
 */

// Export main API client
export { apiClient, default as ApiClient } from './client';
export type { ApiClientConfig, RequestInterceptor, ResponseInterceptor } from './client';

// Export error types and utilities
export { ApiError, ErrorCode, parseApiError, isNetworkError, isTimeoutError } from './errors';
export type { ApiErrorResponse, ErrorDetail } from './errors';

// Export retry utilities
export { createRetryConfig, withRetry } from './retry';
export type { RetryConfig } from './retry';

// Export logger
export { apiLogger } from './logger';
export { LogLevel } from './logger';
export type { LogEntry } from './logger';

// Export feature flags
export {
  API_FEATURE_FLAGS,
  isFeatureEnabled,
  getEnabledFeatures,
  getFeatureFlagsConfig,
  logFeatureFlags,
} from './featureFlags';
export type { FeatureFlagKey } from './featureFlags';

// Export performance monitoring
export { performanceMonitor, performanceInterceptor } from './performance';
export type { PerformanceMetric, PerformanceStats } from './performance';

// Export error recovery utilities
export {
  withRecovery,
  batchWithRecovery,
  withTimeout,
  debounceApiCall,
  throttleApiCall,
  responseCache,
} from './errorRecovery';
export type {
  RecoveryStrategy,
  RecoveryResult,
  RecoveryOptions,
  FallbackProvider,
} from './errorRecovery';

// Export validation utilities (Task 11.3)
export {
  validateApiCall,
  runParallelValidation,
  compareImplementations,
  monitorErrorRates,
  exportValidationReport,
} from './validation';
export type { ValidationResult, ValidationReport, ExpectedResponse } from './validation';

// Export domain-specific API modules
export * from './articles';
export * from './auth';
export * from './feeds';
export * from './readingList';
export * from './scheduler';
export * from './analytics';
export * from './recommendations';
export * from './onboarding';
