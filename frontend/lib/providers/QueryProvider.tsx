'use client';

/**
 * React Query Provider
 *
 * This module provides the React Query client configuration for the application.
 * Implements server state management with automatic caching, background refetching,
 * and error handling.
 *
 * Requirements: 2.3, 2.4
 * - 2.3: Use React Query for server state caching and synchronization
 * - 2.4: Separate server state from client state management
 *
 * Configuration:
 * - Default stale time: 1 minute (data is considered fresh for 1 minute)
 * - Default cache time: 5 minutes (unused data is garbage collected after 5 minutes)
 * - Retry: 2 attempts with exponential backoff
 * - Refetch on window focus: enabled (keeps data fresh when user returns to tab)
 * - Refetch on reconnect: enabled (refetches data when network connection is restored)
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

/**
 * QueryProvider Component
 *
 * Wraps the application with React Query client provider.
 * Provides server state management capabilities to all child components.
 *
 * Features:
 * - Automatic caching with configurable stale time
 * - Background refetching to keep data fresh
 * - Retry logic with exponential backoff
 * - DevTools for debugging (development only)
 *
 * @param children - Child components to wrap
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Data is considered fresh for 1 minute
            staleTime: 60 * 1000, // 1 minute
            // Unused data is garbage collected after 5 minutes
            gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
            // Retry failed requests 2 times with exponential backoff
            retry: 2,
            // Refetch data when window regains focus
            refetchOnWindowFocus: true,
            // Refetch data when network connection is restored
            refetchOnReconnect: true,
            // Don't refetch on mount if data is still fresh
            refetchOnMount: true,
          },
          mutations: {
            // Retry failed mutations once
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* DevTools only in development */}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
