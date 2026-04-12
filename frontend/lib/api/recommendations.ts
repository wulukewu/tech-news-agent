import { apiClient } from './client';

/**
 * Recommendations API functions
 *
 * Provides methods for fetching personalized feed recommendations.
 */

/**
 * Recommended feed item
 */
export interface RecommendedFeed {
  feed_id: string;
  feed_url: string;
  title: string;
  description?: string;
  category?: string;
  reason: string;
  confidence_score: number;
}

/**
 * Recommended feeds response
 */
export interface RecommendedFeedsResponse {
  recommendations: RecommendedFeed[];
  total_count: number;
}

/**
 * Get personalized feed recommendations
 *
 * @returns Promise resolving to recommended feeds
 */
export async function getRecommendedFeeds(): Promise<RecommendedFeedsResponse> {
  return apiClient.get<RecommendedFeedsResponse>('/api/feeds/recommended');
}
