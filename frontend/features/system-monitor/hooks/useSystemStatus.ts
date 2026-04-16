/**
 * System Status Hooks
 *
 * React Query hooks for fetching and managing system status data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSystemStatus, getSchedulerStatus, triggerManualFetch } from '../services/api';
import { toast } from '@/lib/toast';

/**
 * Query keys for system status
 */
export const systemStatusKeys = {
  all: ['system-status'] as const,
  status: () => [...systemStatusKeys.all, 'status'] as const,
  scheduler: () => [...systemStatusKeys.all, 'scheduler'] as const,
};

/**
 * Hook to fetch complete system status
 *
 * Supports real-time updates through configurable polling interval.
 *
 * Requirements: 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8
 *
 * @param options - Query options
 * @param options.refetchInterval - Polling interval in milliseconds (default: 30000)
 * @param options.enabled - Whether to enable the query (default: true)
 * @returns Query result with system status
 */
export function useSystemStatus(options?: { refetchInterval?: number; enabled?: boolean }) {
  return useQuery({
    queryKey: systemStatusKeys.status(),
    queryFn: getSystemStatus,
    refetchInterval: options?.refetchInterval ?? 30000, // Default: 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
    enabled: options?.enabled ?? true,
    refetchOnWindowFocus: true, // Refetch when window regains focus
    refetchOnReconnect: true, // Refetch when network reconnects
  });
}

/**
 * Hook to fetch scheduler status only
 *
 * Requirements: 5.1, 5.2
 *
 * @param options - Query options
 * @returns Query result with scheduler status
 */
export function useSchedulerStatus(options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: systemStatusKeys.scheduler(),
    queryFn: getSchedulerStatus,
    refetchInterval: options?.refetchInterval || 30000, // Refetch every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  });
}

/**
 * Hook to trigger manual fetch
 *
 * Requirements: 5.3
 *
 * @returns Mutation result with trigger function
 */
export function useTriggerManualFetch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: triggerManualFetch,
    onSuccess: (data) => {
      toast.success(data.message || '已觸發文章抓取任務');

      // Invalidate system status queries to refetch
      queryClient.invalidateQueries({ queryKey: systemStatusKeys.all });
    },
    onError: (error: Error) => {
      toast.error(`觸發失敗: ${error.message}`);
    },
  });
}
