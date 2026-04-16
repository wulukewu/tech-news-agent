'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, useEffect } from 'react';
import { createOptimizedQueryClient } from '@/lib/cache';

interface QueryProviderProps {
  children: React.ReactNode;
}

/**
 * QueryProvider with Optimized Caching Strategies
 * Requirements: 12.1, 12.3, 12.4
 *
 * Provides intelligent caching with different strategies for different data types:
 * - Article lists: 5 minutes stale time
 * - AI analysis: 24 hours stale time
 * - User settings: immediate updates
 * - System status: 30 seconds stale time
 */
export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(() => createOptimizedQueryClient());

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      queryClient.clear();
    };
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
      )}
    </QueryClientProvider>
  );
}
