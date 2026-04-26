/**
 * Feature Flags for API Client
 * Requirements: 10.3
 *
 * This module provides feature flags for A/B testing and gradual rollout of new API implementations.
 * Feature flags allow switching between old and new implementations without code changes.
 */
import { logger } from '@/lib/utils/logger';

/**
 * API feature flags configuration
 *
 * Each flag can be controlled via environment variables for easy A/B testing.
 * Set to 'true' to enable the new implementation, 'false' to use the old one.
 */
export const API_FEATURE_FLAGS = {
  /**
   * Use new articles API with enhanced caching
   * Environment: NEXT_PUBLIC_USE_NEW_ARTICLES_API
   */
  USE_NEW_ARTICLES_API: process.env.NEXT_PUBLIC_USE_NEW_ARTICLES_API === 'true',

  /**
   * Use new authentication flow with refresh token rotation
   * Environment: NEXT_PUBLIC_USE_NEW_AUTH_API
   */
  USE_NEW_AUTH_API: process.env.NEXT_PUBLIC_USE_NEW_AUTH_API === 'true',

  /**
   * Use new reading list API with optimistic updates
   * Environment: NEXT_PUBLIC_USE_NEW_READING_LIST_API
   */
  USE_NEW_READING_LIST_API: process.env.NEXT_PUBLIC_USE_NEW_READING_LIST_API === 'true',

  /**
   * Use GraphQL API instead of REST
   * Environment: NEXT_PUBLIC_USE_GRAPHQL_API
   */
  USE_GRAPHQL_API: process.env.NEXT_PUBLIC_USE_GRAPHQL_API === 'true',

  /**
   * Enable client-side API response caching
   * Environment: NEXT_PUBLIC_ENABLE_API_CACHING
   */
  ENABLE_API_CACHING: process.env.NEXT_PUBLIC_ENABLE_API_CACHING === 'true',

  /**
   * Enable performance monitoring for API calls
   * Environment: NEXT_PUBLIC_ENABLE_API_MONITORING
   */
  ENABLE_API_MONITORING: process.env.NEXT_PUBLIC_ENABLE_API_MONITORING === 'true',

  /**
   * Enable detailed API logging (useful for debugging)
   * Environment: NEXT_PUBLIC_ENABLE_API_DEBUG_LOGGING
   */
  ENABLE_API_DEBUG_LOGGING: process.env.NEXT_PUBLIC_ENABLE_API_DEBUG_LOGGING === 'true',

  /**
   * Use batch API requests where possible
   * Environment: NEXT_PUBLIC_USE_BATCH_REQUESTS
   */
  USE_BATCH_REQUESTS: process.env.NEXT_PUBLIC_USE_BATCH_REQUESTS === 'true',
} as const;

/**
 * Type for feature flag keys
 */
export type FeatureFlagKey = keyof typeof API_FEATURE_FLAGS;

/**
 * Check if a feature flag is enabled
 *
 * @param flag - Feature flag key to check
 * @returns True if the flag is enabled, false otherwise
 */
export function isFeatureEnabled(flag: FeatureFlagKey): boolean {
  return API_FEATURE_FLAGS[flag];
}

/**
 * Get all enabled feature flags
 *
 * @returns Array of enabled feature flag keys
 */
export function getEnabledFeatures(): FeatureFlagKey[] {
  return Object.entries(API_FEATURE_FLAGS)
    .filter(([_, enabled]) => enabled)
    .map(([key]) => key as FeatureFlagKey);
}

/**
 * Get feature flags configuration as object
 *
 * @returns Object with all feature flags and their values
 */
export function getFeatureFlagsConfig(): Record<FeatureFlagKey, boolean> {
  return { ...API_FEATURE_FLAGS };
}

/**
 * Log current feature flags configuration (useful for debugging)
 */
export function logFeatureFlags(): void {
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    console.group('🚩 API Feature Flags');
    Object.entries(API_FEATURE_FLAGS).forEach(([key, value]) => {
      logger.debug(`${key}: ${value ? '✅ Enabled' : '❌ Disabled'}`);
    });
    console.groupEnd();
  }
}
