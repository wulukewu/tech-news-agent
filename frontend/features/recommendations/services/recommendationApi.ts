/**
 * Recommendation API Service
 *
 * Provides API methods for fetching and managing article recommendations
 *
 * Validates Requirements 3.1-3.10
 */

import { apiClient, handleApiError } from '@/lib/api/client';
import {
  RecommendationsResponse,
  RefreshRecommendationsRequest,
  DismissRecommendationRequest,
  RecommendationInteraction,
} from '@/types/recommendation';

/**
 * Get personalized article recommendations for the current user
 *
 * Validates: Requirements 3.1, 3.2
 */
export async function getRecommendations(limit?: number): Promise<RecommendationsResponse> {
  try {
    const response = await apiClient.get<RecommendationsResponse>('/api/v1/recommendations', {
      params: { limit },
    });
    return response.data;
  } catch (error: any) {
    const apiError = handleApiError(error);
    throw new Error(apiError.message);
  }
}

/**
 * Refresh recommendations to generate new suggestions
 *
 * Validates: Requirement 3.5
 */
export async function refreshRecommendations(
  request: RefreshRecommendationsRequest = {}
): Promise<RecommendationsResponse> {
  try {
    const response = await apiClient.post<RecommendationsResponse>(
      '/api/v1/recommendations/refresh',
      request
    );
    return response.data;
  } catch (error: any) {
    const apiError = handleApiError(error);
    throw new Error(apiError.message);
  }
}

/**
 * Dismiss a recommendation
 *
 * Validates: Requirement 3.7
 */
export async function dismissRecommendation(request: DismissRecommendationRequest): Promise<void> {
  try {
    await apiClient.post('/api/v1/recommendations/dismiss', request);
  } catch (error: any) {
    const apiError = handleApiError(error);
    throw new Error(apiError.message);
  }
}

/**
 * Track recommendation interaction for analytics
 *
 * Validates: Requirement 3.8
 */
export async function trackRecommendationInteraction(
  interaction: RecommendationInteraction
): Promise<void> {
  try {
    await apiClient.post('/api/v1/recommendations/track', interaction);
  } catch (error: any) {
    const apiError = handleApiError(error);
    throw new Error(apiError.message);
  }
}
