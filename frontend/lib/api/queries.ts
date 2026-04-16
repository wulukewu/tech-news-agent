/**
 * TanStack Query Keys and Hooks
 * Requirements: 12.1, 12.3, 12.4
 *
 * This module provides query keys and hooks with optimized caching strategies.
 * Each query type uses appropriate cache settings based on data characteristics.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cacheStrategies, invalidationPatterns } from '@/lib/cache';

/**
 * Query Key Factory
 * Provides consistent query keys across the application
 */
export const queryKeys = {
  // Article queries
  articles: {
    all: ['articles'] as const,
    lists: () => [...queryKeys.articles.all, 'list'] as const,
    list: (filters: any) => [...queryKeys.articles.lists(), filters] as const,
    details: () => [...queryKeys.articles.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.articles.details(), id] as const,
    analysis: (id: string) => [...queryKeys.articles.detail(id), 'analysis'] as const,
  },

  // User queries
  user: {
    all: ['user'] as const,
    profile: () => [...queryKeys.user.all, 'profile'] as const,
    settings: () => [...queryKeys.user.all, 'settings'] as const,
    preferences: () => [...queryKeys.user.all, 'preferences'] as const,
  },

  // Reading list queries
  readingList: {
    all: ['reading-list'] as const,
    items: () => [...queryKeys.readingList.all, 'items'] as const,
    item: (id: string) => [...queryKeys.readingList.items(), id] as const,
  },

  // Recommendations queries
  recommendations: {
    all: ['recommendations'] as const,
    list: () => [...queryKeys.recommendations.all, 'list'] as const,
    personalized: () => [...queryKeys.recommendations.all, 'personalized'] as const,
  },

  // Subscriptions queries
  subscriptions: {
    all: ['subscriptions'] as const,
    list: () => [...queryKeys.subscriptions.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.subscriptions.all, 'detail', id] as const,
  },

  // System queries
  system: {
    all: ['system'] as const,
    status: () => [...queryKeys.system.all, 'status'] as const,
    scheduler: () => [...queryKeys.system.all, 'scheduler'] as const,
  },

  // Analytics queries
  analytics: {
    all: ['analytics'] as const,
    user: () => [...queryKeys.analytics.all, 'user'] as const,
    reading: () => [...queryKeys.analytics.all, 'reading'] as const,
    trends: () => [...queryKeys.analytics.all, 'trends'] as const,
  },
} as const;

/**
 * Example: Article List Query Hook with Optimized Caching
 * Uses 5-minute stale time for article lists
 */
export function useArticles(filters: any) {
  return useQuery({
    queryKey: queryKeys.articles.list(filters),
    queryFn: async () => {
      const response = await fetch(`/api/articles?${new URLSearchParams(filters)}`);
      if (!response.ok) throw new Error('Failed to fetch articles');
      return response.json();
    },
    ...cacheStrategies.articleList,
  });
}

/**
 * Example: AI Analysis Query Hook with Long-term Caching
 * Uses 24-hour stale time for AI analysis results
 */
export function useArticleAnalysis(articleId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.articles.analysis(articleId),
    queryFn: async () => {
      const response = await fetch(`/api/articles/${articleId}/analysis`);
      if (!response.ok) throw new Error('Failed to fetch analysis');
      return response.json();
    },
    enabled,
    ...cacheStrategies.aiAnalysis,
  });
}

/**
 * Example: User Settings Query Hook with Immediate Updates
 * Uses 0 stale time for user settings (always fresh)
 */
export function useUserSettings() {
  return useQuery({
    queryKey: queryKeys.user.settings(),
    queryFn: async () => {
      const response = await fetch('/api/user/settings');
      if (!response.ok) throw new Error('Failed to fetch settings');
      return response.json();
    },
    ...cacheStrategies.userSettings,
  });
}

/**
 * Example: System Status Query Hook with Frequent Updates
 * Uses 30-second stale time with auto-refresh
 */
export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.system.status(),
    queryFn: async () => {
      const response = await fetch('/api/system/status');
      if (!response.ok) throw new Error('Failed to fetch system status');
      return response.json();
    },
    ...cacheStrategies.systemStatus,
  });
}

/**
 * Example: Mutation Hook with Cache Invalidation
 * Automatically invalidates related queries after mutation
 */
export function useRateArticle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ articleId, rating }: { articleId: string; rating: number }) => {
      const response = await fetch(`/api/articles/${articleId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating }),
      });
      if (!response.ok) throw new Error('Failed to rate article');
      return response.json();
    },
    onSuccess: (data, variables) => {
      // Invalidate related queries using the invalidation pattern
      invalidationPatterns.onArticleRating(queryClient, variables.articleId);
    },
  });
}

/**
 * Example: Reading List Mutation with Cache Updates
 */
export function useAddToReadingList() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (articleId: string) => {
      const response = await fetch('/api/reading-list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ articleId }),
      });
      if (!response.ok) throw new Error('Failed to add to reading list');
      return response.json();
    },
    onSuccess: (data, articleId) => {
      // Invalidate related queries
      invalidationPatterns.onReadingListChange(queryClient, articleId);
    },
  });
}

/**
 * Example: Subscription Mutation with Cache Updates
 */
export function useUpdateSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ feedId, subscribed }: { feedId: string; subscribed: boolean }) => {
      const response = await fetch(`/api/subscriptions/${feedId}`, {
        method: subscribed ? 'POST' : 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to update subscription');
      return response.json();
    },
    onSuccess: () => {
      // Invalidate related queries
      invalidationPatterns.onSubscriptionChange(queryClient);
    },
  });
}

/**
 * Prefetch Utilities
 * Use these to preload data before user needs it
 */
export function usePrefetchArticleDetails() {
  const queryClient = useQueryClient();

  return (articleId: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.articles.detail(articleId),
      queryFn: async () => {
        const response = await fetch(`/api/articles/${articleId}`);
        if (!response.ok) throw new Error('Failed to fetch article');
        return response.json();
      },
      ...cacheStrategies.articleDetail,
    });
  };
}

export function usePrefetchAnalysis() {
  const queryClient = useQueryClient();

  return (articleId: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.articles.analysis(articleId),
      queryFn: async () => {
        const response = await fetch(`/api/articles/${articleId}/analysis`);
        if (!response.ok) throw new Error('Failed to fetch analysis');
        return response.json();
      },
      ...cacheStrategies.aiAnalysis,
    });
  };
}
