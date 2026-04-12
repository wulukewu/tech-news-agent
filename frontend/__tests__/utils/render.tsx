/**
 * Custom render functions with different provider configurations
 *
 * Provides specialized render functions for different testing scenarios:
 * - renderWithQueryClient: For testing components that use React Query
 * - renderWithAuth: For testing components that need authentication context
 * - renderWithAllProviders: For testing components that need all contexts
 */

import { ReactElement, ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

/**
 * Create a test QueryClient with sensible defaults for testing
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Don't retry failed queries in tests
        gcTime: 0, // Don't cache query results between tests
        staleTime: 0, // Always consider data stale
      },
      mutations: {
        retry: false, // Don't retry failed mutations in tests
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {}, // Suppress error logs in tests
    },
  });
}

/**
 * Wrapper with QueryClient provider
 */
interface QueryClientWrapperProps {
  children: ReactNode;
  queryClient?: QueryClient;
}

export function QueryClientWrapper({ children, queryClient }: QueryClientWrapperProps) {
  const client = queryClient || createTestQueryClient();
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

/**
 * Render component with QueryClient provider
 */
export function renderWithQueryClient(
  ui: ReactElement,
  options?: {
    queryClient?: QueryClient;
    renderOptions?: Omit<RenderOptions, 'wrapper'>;
  }
) {
  const queryClient = options?.queryClient || createTestQueryClient();

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientWrapper queryClient={queryClient}>{children}</QueryClientWrapper>
  );

  return {
    ...render(ui, { wrapper: Wrapper, ...options?.renderOptions }),
    queryClient,
  };
}

/**
 * Create a wrapper with all providers for comprehensive testing
 */
export function createWrapper(queryClient?: QueryClient) {
  const client = queryClient || createTestQueryClient();

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>
        {/* Add other providers here as needed (Auth, Theme, etc.) */}
        {children}
      </QueryClientProvider>
    );
  };
}

/**
 * Render component with all providers
 */
export function renderWithAllProviders(
  ui: ReactElement,
  options?: {
    queryClient?: QueryClient;
    renderOptions?: Omit<RenderOptions, 'wrapper'>;
  }
) {
  const queryClient = options?.queryClient || createTestQueryClient();
  const wrapper = createWrapper(queryClient);

  return {
    ...render(ui, { wrapper, ...options?.renderOptions }),
    queryClient,
  };
}

/**
 * Wait for loading states to complete
 * Useful for components that show loading indicators
 */
export async function waitForLoadingToFinish() {
  const { waitFor } = await import('@testing-library/react');
  await waitFor(() => {
    const loadingElements = document.querySelectorAll('[data-testid*="loading"]');
    expect(loadingElements.length).toBe(0);
  });
}
