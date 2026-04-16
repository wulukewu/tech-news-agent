/**
 * Notification API functions
 *
 * This module provides functions for notification-related API calls:
 * - getNotificationSettings: Get user's notification preferences
 * - updateNotificationSettings: Update user's notification preferences
 * - getNotificationHistory: Get notification delivery history
 * - testNotification: Send a test notification
 */

import { apiClient } from './client';
import {
  NotificationSettings,
  NotificationDeliveryStatus,
  NotificationHistoryEntry,
} from '@/types/notification';

/**
 * Get user's notification settings
 *
 * @returns Promise<NotificationSettings> - User's notification preferences
 * @throws Error if request fails
 */
export async function getNotificationSettings(): Promise<NotificationSettings> {
  const response = await apiClient.get<NotificationSettings>('/api/notifications/settings');
  return response.data;
}

/**
 * Update user's notification settings
 *
 * @param settings - Updated notification settings
 * @param context - TanStack Query mutation context (optional)
 * @returns Promise<NotificationSettings> - Updated notification settings
 * @throws Error if request fails
 */
export async function updateNotificationSettings(
  settings: Partial<NotificationSettings>,
  context?: any
): Promise<NotificationSettings> {
  const response = await apiClient.patch<NotificationSettings>(
    '/api/notifications/settings',
    settings
  );
  return response.data;
}

/**
 * Get notification delivery history
 *
 * @param limit - Maximum number of history entries to return
 * @returns Promise<NotificationDeliveryStatus> - Notification delivery status and history
 * @throws Error if request fails
 */
export async function getNotificationHistory(
  limit: number = 50
): Promise<NotificationDeliveryStatus> {
  const response = await apiClient.get<NotificationDeliveryStatus>('/api/notifications/history', {
    params: { limit },
  });
  return response.data;
}

/**
 * Send a test notification
 *
 * @returns Promise<void>
 * @throws Error if request fails
 */
export async function sendTestNotification(): Promise<void> {
  await apiClient.post('/api/notifications/test');
}

/**
 * Get available feeds for notification settings
 *
 * @returns Promise<Array<{ id: string; name: string; category: string }>>
 * @throws Error if request fails
 */
export async function getAvailableFeeds(): Promise<
  Array<{ id: string; name: string; category: string }>
> {
  const response =
    await apiClient.get<Array<{ id: string; name: string; category: string }>>('/api/feeds');
  return response.data;
}
