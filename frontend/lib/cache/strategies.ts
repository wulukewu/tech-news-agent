/**
 * TanStack Query Intelligent Caching Strategies
 * Requirements: 12.1, 12.3, 12.4
 *
 * This module provides intelligent caching strategies for different types of data
 * to optimize performance and user experience.
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Cache strategy configuration for different data types
 */
export const cacheStrategies = {
  // Article lists - short-term cache, frequent updates
  articleList: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 2,
  },

  // Article details - medium-term cache
  articleDetail: {
    staleTime: 15 * 60 * 1000, // 15 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
    retry: 3,
  },

  // AI analysis - long-term cache, rarely changes
  aiAnalysis: {
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
    gcTime: 7 * 24 * 60 * 60 * 1000, // 7 days
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: 1,
  },

  // User settings - immediate updates
  userSettings: {
    staleTime: 0, // Always fresh
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 3,
  },

  // System status - frequent updates
  systemStatus: {
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 2,
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  },

  // Recommendations - medium-term cache
  recommendations: {
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 2 * 60 * 60 * 1000, // 2 hours
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
    retry: 2,
  },

  // Feed subscriptions - medium-term cache
  subscriptions: {
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 2,
  },

  // Reading list - immediate updates for user actions
  readingList: {
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 3,
  },

  // Analytics data - longer cache for performance
  analytics: {
    staleTime: 60 * 60 * 1000, // 1 hour
    gcTime: 4 * 60 * 60 * 1000, // 4 hours
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: 1,
  },
} as const;

/**
 * Cache invalidation patterns for related data
 */
export const invalidationPatterns = {
  // When user rates an article, invalidate related queries
  onArticleRating: (queryClient: QueryClient, articleId: string) => {
    queryClient.invalidateQueries({ queryKey: ['articles'] });
    queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    queryClient.invalidateQueries({ queryKey: ['analytics', 'user'] });
  },

  // When user adds/removes from reading list
  onReadingListChange: (queryClient: QueryClient, articleId: string) => {
    queryClient.invalidateQueries({ queryKey: ['reading-list'] });
    queryClient.invalidateQueries({ queryKey: ['articles', 'detail', articleId] });
    queryClient.invalidateQueries({ queryKey: ['analytics', 'reading'] });
  },

  // When user changes subscriptions
  onSubscriptionChange: (queryClient: QueryClient) => {
    queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    queryClient.invalidateQueries({ queryKey: ['articles'] });
    queryClient.invalidateQueries({ queryKey: ['recommendations'] });
  },

  // When user updates settings
  onSettingsChange: (queryClient: QueryClient) => {
    queryClient.invalidateQueries({ queryKey: ['user', 'settings'] });
    queryClient.invalidateQueries({ queryKey: ['recommendations'] });
  },

  // When new articles are fetched
  onNewArticles: (queryClient: QueryClient) => {
    queryClient.invalidateQueries({ queryKey: ['articles'] });
    queryClient.invalidateQueries({ queryKey: ['system', 'status'] });
  },
} as const;

/**
 * Prefetch strategies for anticipating user actions
 */
export class PrefetchStrategy {
  private queryClient: QueryClient;

  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient;
  }

  /**
   * Prefetch next page of articles
   */
  prefetchNextArticlePage(currentFilters: any, currentPage: number) {
    const nextPageFilters = { ...currentFilters, page: currentPage + 1 };

    this.queryClient.prefetchQuery({
      queryKey: ['articles', 'list', nextPageFilters],
      queryFn: () =>
        import('../api/articles').then((api) =>
          api.fetchMyArticles(
            nextPageFilters.page,
            nextPageFilters.pageSize,
            nextPageFilters.categories
          )
        ),
      ...cacheStrategies.articleList,
    });
  }

  /**
   * Prefetch article details when user hovers over article card
   */
  prefetchArticleDetails(articleId: string) {
    // Article details prefetching would need a getArticleById function
    // Skipping for now as it doesn't exist in the API
    console.log('Article details prefetch not implemented yet');
  }

  /**
   * Prefetch AI analysis for popular articles
   */
  prefetchPopularAnalyses(popularArticleIds: string[]) {
    // AI analysis prefetching would need a getAnalysis function
    // Skipping for now as it doesn't exist in the API
    console.log('AI analysis prefetch not implemented yet');
  }

  /**
   * Prefetch recommendations when user visits articles page
   */
  prefetchRecommendations() {
    this.queryClient.prefetchQuery({
      queryKey: ['recommendations'],
      queryFn: () => import('../api/recommendations').then((api) => api.getRecommendedFeeds()),
      ...cacheStrategies.recommendations,
    });
  }

  /**
   * Prefetch user's reading list
   */
  prefetchReadingList() {
    this.queryClient.prefetchQuery({
      queryKey: ['reading-list'],
      queryFn: () => import('../api/readingList').then((api) => api.fetchReadingList()),
      ...cacheStrategies.readingList,
    });
  }
}

/**
 * Background sync strategies for offline support
 */
export class BackgroundSyncStrategy {
  private queryClient: QueryClient;

  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient;
  }

  /**
   * Setup background refetch for critical data
   */
  setupBackgroundRefetch() {
    // Only run in browser environment
    if (typeof window === 'undefined') return;

    const activeIntervals = new Map<string, NodeJS.Timeout>();

    // Refetch articles every 5 minutes when tab is active
    this.queryClient.getQueryCache().subscribe((event) => {
      if (event.query.queryKey[0] === 'articles') {
        const query = event.query;
        const queryHash = query.queryHash;

        if (event.type === 'observerAdded' && query.getObserversCount() > 0) {
          // Setup interval refetch for active queries if not already set
          if (!activeIntervals.has(queryHash)) {
            const intervalId = setInterval(
              () => {
                if (
                  typeof document !== 'undefined' &&
                  document.visibilityState === 'visible' &&
                  query.getObserversCount() > 0
                ) {
                  query.fetch();
                }
              },
              5 * 60 * 1000
            ); // 5 minutes

            activeIntervals.set(queryHash, intervalId);
          }
        } else if (event.type === 'observerRemoved' && query.getObserversCount() === 0) {
          // Cleanup when no more observers
          const intervalId = activeIntervals.get(queryHash);
          if (intervalId) {
            clearInterval(intervalId);
            activeIntervals.delete(queryHash);
          }
        }
      }
    });
  }

  /**
   * Sync offline mutations when connection is restored
   */
  syncOfflineMutations() {
    // Only run in browser environment
    if (typeof window === 'undefined' || typeof navigator === 'undefined') return;

    // This would integrate with the service worker
    // to replay failed mutations when online
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        // Check if sync is supported before using it
        if ('sync' in registration) {
          (registration as any).sync.register('background-sync-mutations');
        }
      });
    }
  }
}

/**
 * Memory management for large datasets
 */
export class MemoryManager {
  private queryClient: QueryClient;
  private maxCacheSize: number;

  constructor(queryClient: QueryClient, maxCacheSize = 100) {
    this.queryClient = queryClient;
    this.maxCacheSize = maxCacheSize;
  }

  /**
   * Monitor and cleanup memory usage
   */
  setupMemoryManagement() {
    // Only run in browser environment
    if (typeof window === 'undefined') return;

    // Check memory usage every 2 minutes
    setInterval(
      () => {
        this.cleanupOldQueries();
      },
      2 * 60 * 1000
    );

    // Listen for memory pressure events
    if (typeof performance !== 'undefined' && 'memory' in performance) {
      const checkMemory = () => {
        const memInfo = (performance as any).memory;
        const usedRatio = memInfo.usedJSHeapSize / memInfo.jsHeapSizeLimit;

        if (usedRatio > 0.8) {
          console.warn('High memory usage detected, cleaning up cache');
          this.aggressiveCleanup();
        }
      };

      setInterval(checkMemory, 30 * 1000); // Check every 30 seconds
    }
  }

  /**
   * Remove old and unused queries
   */
  private cleanupOldQueries() {
    const queryCache = this.queryClient.getQueryCache();
    const queries = queryCache.getAll();

    if (queries.length <= this.maxCacheSize) return;

    // Sort by last access time and remove oldest
    const sortedQueries = queries
      .filter((query) => query.getObserversCount() === 0) // Only inactive queries
      .sort((a, b) => (a.state.dataUpdatedAt || 0) - (b.state.dataUpdatedAt || 0));

    const toRemove = sortedQueries.slice(0, queries.length - this.maxCacheSize);

    toRemove.forEach((query) => {
      queryCache.remove(query);
    });

    if (toRemove.length > 0) {
      console.log(`Cleaned up ${toRemove.length} old queries from cache`);
    }
  }

  /**
   * Aggressive cleanup for memory pressure
   */
  private aggressiveCleanup() {
    const queryCache = this.queryClient.getQueryCache();

    // Remove all inactive queries
    queryCache
      .getAll()
      .filter((query) => query.getObserversCount() === 0)
      .forEach((query) => queryCache.remove(query));

    // Force garbage collection if available
    if (typeof window !== 'undefined' && 'gc' in window) {
      (window as any).gc();
    }
  }
}

/**
 * Create optimized query client with intelligent caching
 */
export function createOptimizedQueryClient(): QueryClient {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        // Default to article list strategy
        ...cacheStrategies.articleList,
        // Enable network-only mode when offline
        networkMode: 'offlineFirst',
      },
      mutations: {
        retry: 2,
        networkMode: 'offlineFirst',
      },
    },
  });

  // Setup background strategies
  const prefetchStrategy = new PrefetchStrategy(queryClient);
  const backgroundSync = new BackgroundSyncStrategy(queryClient);
  const memoryManager = new MemoryManager(queryClient);

  // Initialize strategies
  backgroundSync.setupBackgroundRefetch();
  memoryManager.setupMemoryManagement();

  return queryClient;
}
