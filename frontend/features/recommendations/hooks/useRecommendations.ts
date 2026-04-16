/**
 * Recommendations React Query Hooks
 *
 * Provides hooks for fetching and managing recommendations with caching
 *
 * Validates Requirements 3.1-3.10
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRecommendations,
  refreshRecommendations,
  dismissRecommendation,
  trackRecommendationInteraction,
} from '../services/recommendationApi';
import {
  RefreshRecommendationsRequest,
  DismissRecommendationRequest,
  RecommendationInteraction,
} from '@/types/recommendation';

/**
 * Query keys for recommendations
 */
export const recommendationKeys = {
  all: ['recommendations'] as const,
  list: (limit?: number) => [...recommendationKeys.all, 'list', limit] as const,
};

/**
 * Hook to fetch recommendations
 *
 * Validates: Requirements 3.1, 3.2
 */
export function useRecommendations(limit?: number) {
  return useQuery({
    queryKey: recommendationKeys.list(limit),
    queryFn: () => getRecommendations(limit),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}

/**
 * Hook to refresh recommendations
 *
 * Validates: Requirement 3.5
 */
export function useRefreshRecommendations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: RefreshRecommendationsRequest) => refreshRecommendations(request),
    onSuccess: () => {
      // Invalidate all recommendation queries to refetch
      queryClient.invalidateQueries({ queryKey: recommendationKeys.all });
    },
  });
}

/**
 * Hook to dismiss a recommendation
 *
 * Validates: Requirement 3.7
 */
export function useDismissRecommendation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: DismissRecommendationRequest) => dismissRecommendation(request),
    onSuccess: () => {
      // Invalidate recommendation queries to refetch
      queryClient.invalidateQueries({ queryKey: recommendationKeys.all });
    },
  });
}

/**
 * Hook to track recommendation interactions
 *
 * Validates: Requirement 3.8
 */
export function useTrackRecommendationInteraction() {
  return useMutation({
    mutationFn: (interaction: RecommendationInteraction) =>
      trackRecommendationInteraction(interaction),
    // Don't show errors for analytics tracking
    onError: (error) => {
      console.error('Failed to track recommendation interaction:', error);
    },
  });
}
