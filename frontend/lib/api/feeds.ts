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
  return apiClient.get<Feed[]>('/api/feeds');
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
export async function toggleSubscription(
  feedId: string,
): Promise<SubscriptionToggleResponse> {
  return apiClient.post<SubscriptionToggleResponse>(
    '/api/subscriptions/toggle',
    { feed_id: feedId },
  );
}
