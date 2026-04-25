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
  return response.data.data;
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
  return response.data.data;
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
  const response = await apiClient.post<BatchSubscribeResponse>('/api/subscriptions/batch', {
    feed_ids: feedIds,
  });
  return response.data;
}

/**
 * Add custom RSS feed
 *
 * @param url - RSS feed URL
 * @param name - Optional feed name
 * @param category - Optional feed category
 * @returns Promise resolving to the created feed
 * @throws Error if the API request fails
 */
export async function addCustomFeed(url: string, name?: string, category?: string): Promise<Feed> {
  const response = await apiClient.post<{ success: boolean; data: Feed }>('/api/feeds/custom', {
    url,
    name,
    category,
  });
  return response.data.data;
}

/**
 * Preview RSS feed before subscribing
 *
 * @param url - RSS feed URL to preview
 * @returns Promise resolving to feed preview data
 * @throws Error if the API request fails
 */
export async function previewFeed(url: string): Promise<{
  title: string;
  description?: string;
  url: string;
  category?: string;
  articleCount?: number;
  lastUpdated?: string;
}> {
  const response = await apiClient.post<{
    success: boolean;
    data: {
      title: string;
      description?: string;
      url: string;
      category?: string;
      articleCount?: number;
      lastUpdated?: string;
    };
  }>('/api/feeds/preview', { url });
  return response.data.data;
}

/**
 * Update feed notification preferences
 *
 * @param feedId - Feed ID
 * @param enabled - Whether notifications are enabled for this feed
 * @returns Promise resolving to updated feed
 * @throws Error if the API request fails
 */
export async function updateFeedNotificationPreference(
  feedId: string,
  enabled: boolean
): Promise<Feed> {
  const response = await apiClient.patch<{ success: boolean; data: Feed }>(
    `/api/feeds/${feedId}/notifications`,
    { enabled }
  );
  return response.data.data;
}

/**
 * Delete a feed entirely
 */
export async function deleteFeed(feedId: string): Promise<void> {
  await apiClient.delete(`/api/feeds/${feedId}`);
}

/**
 * Update feed tags
 *
 * @param feedId - Feed ID
 * @param tags - Array of tags
 * @returns Promise resolving to updated feed
 * @throws Error if the API request fails
 */
export async function updateFeedTags(feedId: string, tags: string[]): Promise<Feed> {
  const response = await apiClient.patch<{ success: boolean; data: Feed }>(
    `/api/feeds/${feedId}/tags`,
    { tags }
  );
  return response.data.data;
}
