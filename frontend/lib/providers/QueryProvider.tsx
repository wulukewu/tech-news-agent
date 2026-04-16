'use client';

/**
 * React Query Provider with Intelligent Caching
 *
 * This module provides the React Query client configuration for the application.
 * Implements server state management with automatic caching, background refetching,
 * and error handling.
 *
 * Requirements: 2.3, 2.4, 12.1
 * - 2.3: Use React Query for server state caching and synchronization
 * - 2.4: Separate server state from client state management
 * - 12.1: Implement intelligent data caching and synchronization
 *
 * Enhanced Features:
 * - Intelligent caching strategies per data type
 * - Memory management and cleanup
 * - Background sync and prefetching
 * - Performance monitoring
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, useEffect } from 'react';
import { createOptimizedQueryClient, PrefetchStrategy, MemoryManager } from '../cache/strategies';

/**
 * QueryProvider Component
 *
 * Wraps the application with React Query client provider.
 * Provides server state management capabilities to all child components.
 *
 * Enhanced Features:
 * - Intelligent caching with different strategies per data type
 * - Automatic memory management and cleanup
 * - Background prefetching for better UX
 * - Performance monitoring and optimization
 *
 * @param children - Child components to wrap
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => createOptimizedQueryClient());

  useEffect(() => {
    // Initialize performance monitoring
    if (typeof window !== 'undefined') {
      const prefetchStrategy = new PrefetchStrategy(queryClient);
      const memoryManager = new MemoryManager(queryClient);

      // Setup intelligent prefetching based on user behavior
      const setupIntelligentPrefetching = () => {
        // Prefetch recommendations when user visits articles
        const articlesPageObserver = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
              const articlesPage = document.querySelector('[data-page="articles"]');
              if (articlesPage) {
                prefetchStrategy.prefetchRecommendations();
                prefetchStrategy.prefetchReadingList();
              }
            }
          });
        });

        articlesPageObserver.observe(document.body, {
          childList: true,
          subtree: true,
        });

        // Prefetch article details on hover
        document.addEventListener('mouseover', (event) => {
          const articleCard = (event.target as Element)?.closest('[data-article-id]');
          if (articleCard) {
            const articleId = articleCard.getAttribute('data-article-id');
            if (articleId) {
              prefetchStrategy.prefetchArticleDetails(articleId);
            }
          }
        });

        return () => {
          articlesPageObserver.disconnect();
        };
      };

      const cleanup = setupIntelligentPrefetching();

      // Setup memory management
      memoryManager.setupMemoryManagement();

      // Performance monitoring
      const logPerformanceMetrics = () => {
        const queries = queryClient.getQueryCache().getAll();
        const activeQueries = queries.filter((q) => q.getObserversCount() > 0);

        console.log('Query Cache Stats:', {
          totalQueries: queries.length,
          activeQueries: activeQueries.length,
          memoryUsage: queries.reduce(
            (acc, q) => acc + JSON.stringify(q.state.data || {}).length,
            0
          ),
        });
      };

      // Log performance metrics every 5 minutes in development
      if (process.env.NODE_ENV === 'development') {
        const interval = setInterval(logPerformanceMetrics, 5 * 60 * 1000);
        return () => {
          cleanup();
          clearInterval(interval);
        };
      }

      return cleanup;
    }
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Enhanced DevTools with performance insights */}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
