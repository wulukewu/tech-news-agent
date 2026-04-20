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
  const response = await apiClient.get<{
    success: boolean;
    data: Array<{ id: string; name: string; category: string }>;
  }>('/api/feeds');
  return response.data.data; // Extract data from SuccessResponse wrapper
}

// Personalized Notification Preferences API

/**
 * User notification preferences for personalized scheduling
 */
export interface UserNotificationPreferences {
  id: string;
  userId: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'disabled';
  notificationTime: string; // HH:MM format
  timezone: string;
  dmEnabled: boolean;
  emailEnabled: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * Request model for updating user notification preferences
 */
export interface UpdateUserNotificationPreferencesRequest {
  frequency?: 'daily' | 'weekly' | 'monthly' | 'disabled';
  notificationTime?: string; // HH:MM format
  timezone?: string;
  dmEnabled?: boolean;
  emailEnabled?: boolean;
}

/**
 * Timezone option for selector
 */
export interface TimezoneOption {
  value: string;
  label: string;
  offset: string;
}

/**
 * Notification preview response
 */
export interface NotificationPreviewResponse {
  nextNotificationTime: string | null;
  localTime: string | null;
  utcTime: string | null;
  message: string;
}

/**
 * Notification status response
 */
export interface NotificationStatusResponse {
  scheduled: boolean;
  jobId?: string;
  nextRunTime?: string;
  message: string;
}

/**
 * Get user's personalized notification preferences
 *
 * @returns Promise<UserNotificationPreferences> - User's notification preferences
 * @throws Error if request fails
 */
export async function getNotificationPreferences(): Promise<UserNotificationPreferences> {
  const response = await apiClient.get<{
    success: boolean;
    data: UserNotificationPreferences;
  }>('/api/notifications/preferences');
  return response.data.data;
}

/**
 * Update user's personalized notification preferences
 *
 * @param updates - Updated notification preferences
 * @returns Promise<UserNotificationPreferences> - Updated notification preferences
 * @throws Error if request fails
 */
export async function updateNotificationPreferences(
  updates: UpdateUserNotificationPreferencesRequest
): Promise<UserNotificationPreferences> {
  const response = await apiClient.put<{
    success: boolean;
    data: UserNotificationPreferences;
  }>('/api/notifications/preferences', updates);
  return response.data.data;
}

/**
 * Preview next notification time based on preferences
 *
 * @param frequency - Notification frequency
 * @param notificationTime - Time in HH:MM format
 * @param timezone - IANA timezone identifier
 * @returns Promise<NotificationPreviewResponse> - Preview information
 * @throws Error if request fails
 */
export async function previewNotificationTime(
  frequency: string,
  notificationTime: string,
  timezone: string
): Promise<NotificationPreviewResponse> {
  const response = await apiClient.get<{
    success: boolean;
    data: NotificationPreviewResponse;
  }>('/api/notifications/preferences/preview', {
    params: { frequency, notification_time: notificationTime, timezone },
  });
  return response.data.data;
}

/**
 * Get list of supported timezones
 *
 * @returns Promise<TimezoneOption[]> - List of timezone options
 * @throws Error if request fails
 */
export async function getSupportedTimezones(): Promise<TimezoneOption[]> {
  const response = await apiClient.get<{
    success: boolean;
    data: { timezones: TimezoneOption[]; total: number };
  }>('/api/notifications/preferences/timezones');
  return response.data.data.timezones;
}

/**
 * Get notification scheduling status
 *
 * @returns Promise<NotificationStatusResponse> - Scheduling status
 * @throws Error if request fails
 */
export async function getNotificationStatus(): Promise<NotificationStatusResponse> {
  const response = await apiClient.get<{
    success: boolean;
    data: NotificationStatusResponse;
  }>('/api/notifications/preferences/status');
  return response.data.data;
}
