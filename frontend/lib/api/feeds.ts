/**
 * Feed API functions
 *
 * Validates Requirements 7.5, 8.2, 8.6:
 * - 7.5: THE API client SHALL provide the following functions: fetchFeeds(), toggleSubscription(feedId)
 * - 8.2: THE page SHALL fetch all feeds from GET /api/feeds endpoint
 * - 8.6: WHEN a user toggles a subscription, THE System SHALL call POST /api/subscriptions/toggle
 */

import { apiClient } from './client';
import type { Feed, SubscriptionToggleResponse } from '@/types/feed';

/**
 * Fetch all available feeds from the backend
 *
 * @returns Promise resolving to array of Feed objects
 * @throws Error if the API request fails
 *
 * **Validates: Requirements 7.5, 8.2**
 */
export async function fetchFeeds(): Promise<Feed[]> {
  const response = await apiClient.get<{ success: boolean; data: Feed[] }>('/api/feeds');
  return response.data;
}

/**
 * Toggle subscription status for a specific feed
 *
 * @param feedId - The unique identifier of the feed to toggle
 * @returns Promise resolving to the updated subscription status
 * @throws Error if the API request fails
 *
 * **Validates: Requirements 7.5, 8.6**
 */
export async function toggleSubscription(feedId: string): Promise<SubscriptionToggleResponse> {
  const response = await apiClient.post<{
    success: boolean;
    data: SubscriptionToggleResponse;
  }>('/api/subscriptions/toggle', {
    feed_id: feedId,
  });
  return response.data;
}

/**
 * Batch subscribe response
 */
export interface BatchSubscribeResponse {
  subscribed_count: number;
  failed_count: number;
  failed_feeds: string[];
  message: string;
}

/**
 * Subscribe to multiple feeds at once
 *
 * @param feedIds - Array of feed IDs to subscribe to
 * @returns Promise resolving to batch subscription result
 * @throws Error if the API request fails
 */
export async function batchSubscribe(feedIds: string[]): Promise<BatchSubscribeResponse> {
  return apiClient.post<BatchSubscribeResponse>('/api/subscriptions/batch', { feed_ids: feedIds });
}
