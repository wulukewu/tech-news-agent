/**
 * TanStack Query Smart Caching Strategies
 *
 * Features for Task 14.1:
 * - Intelligent cache invalidation based on data freshness
 * - Optimistic updates for better UX
 * - Background refetch strategies
 * - Memory-efficient cache management
 * - Network-aware caching
 *
 * Requirements:
 * - 12.1: TanStack Query intelligent caching strategies
 */

import { QueryClient, QueryKey, UseQueryOptions } from '@tanstack/react-query';

export interface CacheConfig {
  /** Cache time in milliseconds */
  cacheTime?: number;
  /** Stale time in milliseconds */
  staleTime?: number;
  /** Retry count for failed queries */
  retry?: number;
  /** Retry delay function */
  retryDelay?: (attemptIndex: number) => number;
  /** Background refetch interval */
  refetchInterval?: number;
  /** Refetch on window focus */
  refetchOnWindowFocus?: boolean;
  /** Refetch on reconnect */
  refetchOnReconnect?: boolean;
}

/**
 * Cache strategy types based on data characteristics
 */
export enum CacheStrategy {
  /** Frequently changing data - short cache, frequent updates */
  REALTIME = 'realtime',
  /** Moderately changing data - balanced cache */
  DYNAMIC = 'dynamic',
  /** Rarely changing data - long cache */
  STATIC = 'static',
  /** User-specific data - medium cache with background updates */
  USER_SPECIFIC = 'user_specific',
  /** Critical data - aggressive caching with fallbacks */
  CRITICAL = 'critical',
}

/**
 * Predefined cache configurations for different data types
 */
export const CACHE_CONFIGS: Record<CacheStrategy, CacheConfig> = {
  [CacheStrategy.REALTIME]: {
    cacheTime: 1000 * 60 * 5, // 5 minutes
    staleTime: 1000 * 30, // 30 seconds
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    refetchInterval: 1000 * 60, // 1 minute
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
  [CacheStrategy.DYNAMIC]: {
    cacheTime: 1000 * 60 * 15, // 15 minutes
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    refetchInterval: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
  [CacheStrategy.STATIC]: {
    cacheTime: 1000 * 60 * 60 * 24, // 24 hours
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 1,
    retryDelay: () => 5000,
    refetchInterval: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  },
  [CacheStrategy.USER_SPECIFIC]: {
    cacheTime: 1000 * 60 * 30, // 30 minutes
    staleTime: 1000 * 60 * 10, // 10 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 15000),
    refetchInterval: 1000 * 60 * 10, // 10 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
  [CacheStrategy.CRITICAL]: {
    cacheTime: 1000 * 60 * 60, // 1 hour
    staleTime: 1000 * 60 * 15, // 15 minutes
    retry: 5,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 60000),
    refetchInterval: 1000 * 60 * 15, // 15 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
};

/**
 * Network-aware cache configuration
 */
export function getNetworkAwareCacheConfig(strategy: CacheStrategy): CacheConfig {
  const baseConfig = CACHE_CONFIGS[strategy];

  // Detect connection type if available
  const connection = (navigator as any).connection;
  const isSlowConnection =
    connection &&
    (connection.effectiveType === 'slow-2g' ||
      connection.effectiveType === '2g' ||
      connection.saveData);

  if (isSlowConnection) {
    return {
      ...baseConfig,
      // Extend cache times for slow connections
      cacheTime: (baseConfig.cacheTime || 0) * 2,
      staleTime: (baseConfig.staleTime || 0) * 1.5,
      // Reduce background refetch frequency
      refetchInterval: baseConfig.refetchInterval
        ? (baseConfig.refetchInterval as number) * 2
        : false,
      // Be less aggressive with refetching
      refetchOnWindowFocus: false,
    };
  }

  return baseConfig;
}

/**
 * Create optimized query client with intelligent defaults
 */
export function createOptimizedQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Default to dynamic strategy
        ...CACHE_CONFIGS[CacheStrategy.DYNAMIC],
        // Enable network-aware behavior
        networkMode: 'offlineFirst',
        // Intelligent error handling
        useErrorBoundary: (error: any) => {
          // Only use error boundary for unexpected errors
          return error?.status >= 500;
        },
      },
      mutations: {
        // Retry mutations on network errors
        retry: (failureCount, error: any) => {
          if (error?.status >= 400 && error?.status < 500) {
            // Don't retry client errors
            return false;
          }
          return failureCount < 3;
        },
        // Network-aware mutations
        networkMode: 'offlineFirst',
      },
    },
  });
}

/**
 * Query key factory for consistent cache keys
 */
export const queryKeys = {
  // Articles
  articles: {
    all: ['articles'] as const,
    lists: () => [...queryKeys.articles.all, 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.articles.lists(), filters] as const,
    details: () => [...queryKeys.articles.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.articles.details(), id] as const,
  },

  // Feeds
  feeds: {
    all: ['feeds'] as const,
    lists: () => [...queryKeys.feeds.all, 'list'] as const,
    list: (filters?: Record<string, any>) => [...queryKeys.feeds.lists(), filters || {}] as const,
    details: () => [...queryKeys.feeds.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.feeds.details(), id] as const,
  },

  // User data
  user: {
    all: ['user'] as const,
    profile: () => [...queryKeys.user.all, 'profile'] as const,
    settings: () => [...queryKeys.user.all, 'settings'] as const,
    notifications: () => [...queryKeys.user.all, 'notifications'] as const,
  },

  // Analytics
  analytics: {
    all: ['analytics'] as const,
    dashboard: () => [...queryKeys.analytics.all, 'dashboard'] as const,
    reports: () => [...queryKeys.analytics.all, 'reports'] as const,
  },
} as const;

/**
 * Cache invalidation utilities
 */
export class CacheManager {
  constructor(private queryClient: QueryClient) {}

  /**
   * Invalidate all queries matching a pattern
   */
  async invalidatePattern(pattern: QueryKey): Promise<void> {
    await this.queryClient.invalidateQueries({
      queryKey: pattern,
    });
  }

  /**
   * Prefetch data for likely next actions
   */
  async prefetchNextActions(currentRoute: string): Promise<void> {
    const prefetchPromises: Promise<void>[] = [];

    switch (currentRoute) {
      case '/articles': {
        // Prefetch article details for first few articles
        const articlesData = this.queryClient.getQueryData(queryKeys.articles.lists());
        if (Array.isArray(articlesData)) {
          articlesData.slice(0, 3).forEach((article: any) => {
            prefetchPromises.push(
              this.queryClient.prefetchQuery({
                queryKey: queryKeys.articles.detail(article.id),
                queryFn: () => fetch(`/api/articles/${article.id}`).then((r) => r.json()),
                ...CACHE_CONFIGS[CacheStrategy.STATIC],
              })
            );
          });
        }
        break;
      }

      case '/feeds':
        // Prefetch user settings when viewing feeds
        prefetchPromises.push(
          this.queryClient.prefetchQuery({
            queryKey: queryKeys.user.settings(),
            queryFn: () => fetch('/api/user/settings').then((r) => r.json()),
            ...CACHE_CONFIGS[CacheStrategy.USER_SPECIFIC],
          })
        );
        break;
    }

    await Promise.allSettled(prefetchPromises);
  }

  /**
   * Optimistic update helper
   */
  async optimisticUpdate<T>(
    queryKey: QueryKey,
    updater: (oldData: T | undefined) => T,
    mutationPromise: Promise<T>
  ): Promise<T> {
    // Cancel outgoing refetches
    await this.queryClient.cancelQueries({ queryKey });

    // Snapshot previous value
    const previousData = this.queryClient.getQueryData<T>(queryKey);

    // Optimistically update
    this.queryClient.setQueryData(queryKey, updater);

    try {
      const result = await mutationPromise;
      // Update with server response
      this.queryClient.setQueryData(queryKey, result);
      return result;
    } catch (error) {
      // Rollback on error
      this.queryClient.setQueryData(queryKey, previousData);
      throw error;
    }
  }

  /**
   * Memory cleanup for large datasets
   */
  cleanupMemory(): void {
    // Remove unused queries older than 30 minutes
    this.queryClient
      .getQueryCache()
      .getAll()
      .forEach((query) => {
        const lastUpdated = query.state.dataUpdatedAt;
        const thirtyMinutesAgo = Date.now() - 30 * 60 * 1000;

        if (lastUpdated < thirtyMinutesAgo && query.getObserversCount() === 0) {
          this.queryClient.removeQueries({ queryKey: query.queryKey });
        }
      });

    // Garbage collect if available
    if (typeof window !== 'undefined' && 'gc' in window) {
      (window as any).gc();
    }
  }
}

/**
 * Hook for using cache manager
 */
export function useCacheManager() {
  const queryClient = useQueryClient();
  return new CacheManager(queryClient);
}

/**
 * Performance-optimized query hook factory
 */
export function createOptimizedQuery<T>(strategy: CacheStrategy = CacheStrategy.DYNAMIC) {
  return function useOptimizedQuery<TData = T>(
    queryKey: QueryKey,
    queryFn: () => Promise<TData>,
    options?: Partial<UseQueryOptions<TData>>
  ) {
    const config = getNetworkAwareCacheConfig(strategy);

    return useQuery({
      queryKey,
      queryFn,
      ...config,
      ...options,
    });
  };
}
