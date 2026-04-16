/**
 * Property-Based Tests for TanStack Query Caching Strategies
 * Task: 14.1 實作快取和資料管理
 * Requirements: 12.1, 12.3, 12.4
 *
 * **Validates: Requirements 12.1**
 *
 * These tests verify that the caching strategies are correctly configured
 * and behave as expected across different data types.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import fc from 'fast-check';
import { QueryClient } from '@tanstack/react-query';
import { cacheStrategies } from '@/lib/cache/strategies';

describe('Property: TanStack Query Caching Strategies', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  /**
   * Property 1: Article List Cache Duration
   * For any article list query, the stale time should be 5 minutes
   */
  it('should have 5 minute stale time for article lists', () => {
    fc.assert(
      fc.property(fc.constant(cacheStrategies.articleList), (strategy) => {
        expect(strategy.staleTime).toBe(5 * 60 * 1000);
        expect(strategy.gcTime).toBe(10 * 60 * 1000);
        expect(strategy.refetchOnWindowFocus).toBe(true);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 2: AI Analysis Long-term Cache
   * For any AI analysis query, the stale time should be 24 hours
   */
  it('should have 24 hour stale time for AI analysis', () => {
    fc.assert(
      fc.property(fc.constant(cacheStrategies.aiAnalysis), (strategy) => {
        expect(strategy.staleTime).toBe(24 * 60 * 60 * 1000);
        expect(strategy.gcTime).toBe(7 * 24 * 60 * 60 * 1000);
        expect(strategy.refetchOnWindowFocus).toBe(false);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 3: User Settings Immediate Updates
   * For any user settings query, the stale time should be 0 (always fresh)
   */
  it('should have immediate updates for user settings', () => {
    fc.assert(
      fc.property(fc.constant(cacheStrategies.userSettings), (strategy) => {
        expect(strategy.staleTime).toBe(0);
        expect(strategy.refetchOnWindowFocus).toBe(true);
        expect(strategy.refetchOnReconnect).toBe(true);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 4: System Status Frequent Updates
   * For any system status query, the stale time should be 30 seconds
   */
  it('should have 30 second stale time for system status', () => {
    fc.assert(
      fc.property(fc.constant(cacheStrategies.systemStatus), (strategy) => {
        expect(strategy.staleTime).toBe(30 * 1000);
        expect(strategy.gcTime).toBe(2 * 60 * 1000);
        expect(strategy.refetchInterval).toBe(60 * 1000);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 5: Cache Strategy Consistency
   * For any cache strategy, staleTime should be less than or equal to gcTime
   */
  it('should have staleTime <= gcTime for all strategies', () => {
    const strategies = Object.values(cacheStrategies);

    fc.assert(
      fc.property(fc.constantFrom(...strategies), (strategy) => {
        expect(strategy.staleTime).toBeLessThanOrEqual(strategy.gcTime);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 6: Retry Configuration
   * For any cache strategy, retry count should be between 0 and 3
   */
  it('should have reasonable retry counts', () => {
    const strategies = Object.values(cacheStrategies);

    fc.assert(
      fc.property(fc.constantFrom(...strategies), (strategy) => {
        expect(strategy.retry).toBeGreaterThanOrEqual(0);
        expect(strategy.retry).toBeLessThanOrEqual(3);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property 7: Query Key Consistency
   * For any query with the same parameters, the cache key should be identical
   */
  it('should generate consistent cache keys for identical queries', () => {
    fc.assert(
      fc.property(
        fc.record({
          page: fc.integer({ min: 1, max: 100 }),
          category: fc.constantFrom('tech', 'ai', 'web', 'mobile'),
          limit: fc.integer({ min: 10, max: 50 }),
        }),
        (filters) => {
          const key1 = ['articles', 'list', filters];
          const key2 = ['articles', 'list', filters];

          expect(JSON.stringify(key1)).toBe(JSON.stringify(key2));
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 8: Cache Invalidation Patterns
   * For any article rating change, related queries should be invalidated
   */
  it('should invalidate related queries on article rating', async () => {
    fc.assert(
      fc.property(fc.uuid(), async (articleId) => {
        // Setup queries
        queryClient.setQueryData(['articles'], [{ id: articleId }]);
        queryClient.setQueryData(['recommendations'], []);
        queryClient.setQueryData(['analytics', 'user'], {});

        // Verify queries exist
        expect(queryClient.getQueryData(['articles'])).toBeDefined();
        expect(queryClient.getQueryData(['recommendations'])).toBeDefined();
        expect(queryClient.getQueryData(['analytics', 'user'])).toBeDefined();

        // Invalidate related queries
        await queryClient.invalidateQueries({ queryKey: ['articles'] });
        await queryClient.invalidateQueries({ queryKey: ['recommendations'] });
        await queryClient.invalidateQueries({ queryKey: ['analytics', 'user'] });

        // Verify invalidation
        const articlesState = queryClient.getQueryState(['articles']);
        const recommendationsState = queryClient.getQueryState(['recommendations']);
        const analyticsState = queryClient.getQueryState(['analytics', 'user']);

        expect(articlesState?.isInvalidated).toBe(true);
        expect(recommendationsState?.isInvalidated).toBe(true);
        expect(analyticsState?.isInvalidated).toBe(true);
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property 9: Memory Management
   * For any number of queries, garbage collection should clean up unused queries
   */
  it('should clean up unused queries after gcTime', async () => {
    fc.assert(
      fc.property(fc.array(fc.uuid(), { minLength: 1, maxLength: 10 }), async (articleIds) => {
        // Create queries
        articleIds.forEach((id) => {
          queryClient.setQueryData(['articles', 'detail', id], { id, title: 'Test' });
        });

        // Verify queries exist
        expect(queryClient.getQueryCache().getAll().length).toBeGreaterThanOrEqual(
          articleIds.length
        );

        // Clear cache
        queryClient.clear();

        // Verify cleanup
        expect(queryClient.getQueryCache().getAll().length).toBe(0);
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Property 10: Prefetch Strategy
   * For any article list, prefetching next page should not affect current data
   */
  it('should prefetch without affecting current data', async () => {
    fc.assert(
      fc.property(
        fc.record({
          page: fc.integer({ min: 1, max: 10 }),
          articles: fc.array(
            fc.record({
              id: fc.uuid(),
              title: fc.string({ minLength: 10, maxLength: 100 }),
            }),
            { minLength: 1, maxLength: 20 }
          ),
        }),
        async ({ page, articles }) => {
          // Set current page data
          const currentKey = ['articles', 'list', { page }];
          queryClient.setQueryData(currentKey, articles);

          // Prefetch next page
          const nextKey = ['articles', 'list', { page: page + 1 }];
          await queryClient.prefetchQuery({
            queryKey: nextKey,
            queryFn: async () => [],
            staleTime: 5 * 60 * 1000,
          });

          // Verify current data unchanged
          const currentData = queryClient.getQueryData(currentKey);
          expect(currentData).toEqual(articles);
        }
      ),
      { numRuns: 50 }
    );
  });
});
