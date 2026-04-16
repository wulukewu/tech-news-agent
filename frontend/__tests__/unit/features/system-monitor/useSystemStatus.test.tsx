/**
 * Unit Tests for useSystemStatus Hook
 *
 * Tests real-time update mechanism using TanStack Query polling.
 *
 * Requirements: 5.7
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSystemStatus } from '@/features/system-monitor/hooks/useSystemStatus';
import * as api from '@/features/system-monitor/services/api';
import type { SystemStatus } from '@/features/system-monitor/types';

// Mock the API module
vi.mock('@/features/system-monitor/services/api');

describe('useSystemStatus Hook', () => {
  let queryClient: QueryClient;

  const mockSystemStatus: SystemStatus = {
    scheduler: {
      isRunning: false,
      lastExecutionTime: new Date('2024-01-01T12:00:00Z'),
      nextExecutionTime: new Date('2024-01-01T13:00:00Z'),
      articlesProcessed: 15,
      failedOperations: 0,
      totalOperations: 15,
      isHealthy: true,
      issues: [],
    },
    health: {
      database: {
        connected: true,
        responseTime: 50,
        lastChecked: new Date('2024-01-01T12:00:00Z'),
      },
      api: {
        averageResponseTime: 100,
        p95ResponseTime: 200,
        p99ResponseTime: 300,
        lastChecked: new Date('2024-01-01T12:00:00Z'),
      },
      errors: {
        rate: 0.5,
        total24h: 10,
        lastError: null,
      },
    },
    feeds: [],
    statistics: {
      totalArticles24h: 100,
      successRate: 95,
      averageProcessingTime: 500,
      totalFetches24h: 20,
      failedFetches24h: 1,
    },
    lastUpdated: new Date('2024-01-01T12:00:00Z'),
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  describe('Data Fetching', () => {
    it('should fetch system status successfully', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      const { result } = renderHook(() => useSystemStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockSystemStatus);
      expect(api.getSystemStatus).toHaveBeenCalledTimes(1);
    });

    it('should handle fetch errors', async () => {
      const error = new Error('Network error');
      vi.mocked(api.getSystemStatus).mockRejectedValue(error);

      const { result } = renderHook(() => useSystemStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });

    it('should show loading state initially', () => {
      vi.mocked(api.getSystemStatus).mockImplementation(() => new Promise(() => {}));

      const { result } = renderHook(() => useSystemStatus(), { wrapper });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('Polling Configuration', () => {
    it('should configure default polling interval of 30 seconds', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      const { result } = renderHook(() => useSystemStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Check that the query has the correct refetchInterval
      const queries = queryClient.getQueryCache().getAll();
      expect(queries.length).toBe(1);
      expect(queries[0].options.refetchInterval).toBe(30000);
    });

    it('should configure custom polling interval', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      const customInterval = 10000;
      const { result } = renderHook(() => useSystemStatus({ refetchInterval: customInterval }), {
        wrapper,
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const queries = queryClient.getQueryCache().getAll();
      expect(queries[0].options.refetchInterval).toBe(customInterval);
    });

    it('should not fetch when enabled is false', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      renderHook(() => useSystemStatus({ enabled: false }), { wrapper });

      // Wait a bit to ensure no fetch happens
      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(api.getSystemStatus).not.toHaveBeenCalled();
    });
  });

  describe('Refetch Behavior', () => {
    it('should configure refetch on window focus', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      const { result } = renderHook(() => useSystemStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const queries = queryClient.getQueryCache().getAll();
      expect(queries[0].options.refetchOnWindowFocus).toBe(true);
    });

    it('should configure refetch on reconnect', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      const { result } = renderHook(() => useSystemStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const queries = queryClient.getQueryCache().getAll();
      expect(queries[0].options.refetchOnReconnect).toBe(true);
    });
  });

  describe('Stale Time Configuration', () => {
    it('should configure stale time of 10 seconds', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      const { result } = renderHook(() => useSystemStatus(), { wrapper });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const queries = queryClient.getQueryCache().getAll();
      expect(queries[0].options.staleTime).toBe(10000);
    });
  });

  describe('Query Key Management', () => {
    it('should use correct query key', async () => {
      vi.mocked(api.getSystemStatus).mockResolvedValue(mockSystemStatus);

      renderHook(() => useSystemStatus(), { wrapper });

      await waitFor(() => {
        const queries = queryClient.getQueryCache().getAll();
        expect(queries.length).toBe(1);
        expect(queries[0].queryKey).toEqual(['system-status', 'status']);
      });
    });
  });
});
