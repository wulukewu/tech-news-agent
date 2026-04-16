/**
 * Cache and Data Management Module
 * Requirements: 12.1, 12.3, 12.4
 *
 * This module exports all caching strategies and utilities for the application.
 * It provides intelligent caching for different data types with optimized stale times.
 */

export {
  cacheStrategies,
  invalidationPatterns,
  PrefetchStrategy,
  BackgroundSyncStrategy,
  MemoryManager,
  createOptimizedQueryClient,
} from './strategies';

// Re-export for convenience
export type { QueryClient } from '@tanstack/react-query';
