/**
 * Cache Strategies Unit Tests
 * Requirements: 12.1, 12.3, 12.4
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { QueryClient } from '@tanstack/react-query';
import {
  cacheStrategies,
  invalidationPatterns,
  PrefetchStrategy,
  createOptimizedQueryClient,
} from '@/lib/cache';

describe('Cache Strategies', () => {
  describe('cacheStrategies', () => {
    it('should define article list strategy with 5 minute stale time', () => {
      expect(cacheStrategies.articleList.staleTime).toBe(5 * 60 * 1000);
      expect(cacheStrategies.articleList.gcTime).toBe(10 * 60 * 1000);
      expect(cacheStrategies.articleList.refetchOnWindowFocus).toBe(true);
    });

    it('should define AI analysis strategy with 24 hour stale time', () => {
      expect(cacheStrategies.aiAnalysis.staleTime).toBe(24 * 60 * 60 * 1000);
      expect(cacheStrategies.aiAnalysis.gcTime).toBe(7 * 24 * 60 * 60 * 1000);
      expect(cacheStrategies.aiAnalysis.refetchOnWindowFocus).toBe(false);
    });

    it('should define user settings strategy with immediate updates', () => {
      expect(cacheStrategies.userSettings.staleTime).toBe(0);
      expect(cacheStrategies.userSettings.refetchOnWindowFocus).toBe(true);
    });

    it('should define system status strategy with 30 second stale time', () => {
      expect(cacheStrategies.systemStatus.staleTime).toBe(30 * 1000);
      expect(cacheStrategies.systemStatus.refetchInterval).toBe(60 * 1000);
    });
  });

  describe('invalidationPatterns', () => {
    let queryClient: QueryClient;

    beforeEach(() => {
      queryClient = new QueryClient();
      vi.spyOn(queryClient, 'invalidateQueries');
    });

    it('should invalidate related queries on article rating', () => {
      invalidationPatterns.onArticleRating(queryClient, 'article-123');

      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['articles'],
      });
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['recommendations'],
      });
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['analytics', 'user'],
      });
    });

    it('should invalidate related queries on reading list change', () => {
      invalidationPatterns.onReadingListChange(queryClient, 'article-123');

      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['reading-list'],
      });
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['articles', 'detail', 'article-123'],
      });
    });

    it('should invalidate related queries on subscription change', () => {
      invalidationPatterns.onSubscriptionChange(queryClient);

      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['subscriptions'],
      });
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['articles'],
      });
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['recommendations'],
      });
    });
  });

  describe('PrefetchStrategy', () => {
    let queryClient: QueryClient;
    let prefetchStrategy: PrefetchStrategy;

    beforeEach(() => {
      queryClient = new QueryClient();
      prefetchStrategy = new PrefetchStrategy(queryClient);
      vi.spyOn(queryClient, 'prefetchQuery');
    });

    it('should prefetch next article page', () => {
      const filters = { category: 'tech', page: 1 };
      prefetchStrategy.prefetchNextArticlePage(filters, 1);

      expect(queryClient.prefetchQuery).toHaveBeenCalledWith(
        expect.objectContaining({
          queryKey: ['articles', 'list', { category: 'tech', page: 2 }],
        })
      );
    });

    it('should prefetch article details', () => {
      prefetchStrategy.prefetchArticleDetails('article-123');

      expect(queryClient.prefetchQuery).toHaveBeenCalledWith(
        expect.objectContaining({
          queryKey: ['articles', 'detail', 'article-123'],
        })
      );
    });
  });

  describe('createOptimizedQueryClient', () => {
    it('should create query client with optimized defaults', () => {
      const queryClient = createOptimizedQueryClient();

      expect(queryClient).toBeInstanceOf(QueryClient);
      expect(queryClient.getDefaultOptions().queries?.networkMode).toBe('offlineFirst');
    });
  });
});
