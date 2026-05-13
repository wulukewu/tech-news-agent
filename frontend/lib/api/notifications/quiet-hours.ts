'use client';

import { apiClient } from '../client';

/**
 * Quiet Hours Settings
 */
export interface QuietHoursSettings {
  id?: string;
  user_id?: string;
  start_time: string;
  end_time: string;
  timezone: string;
  weekdays: number[];
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Quiet Hours Status
 */
export interface QuietHoursStatus {
  is_in_quiet_hours: boolean;
  quiet_hours: QuietHoursSettings | null;
  next_notification_time: string | null;
  current_time: string;
  message: string;
}

/**
 * Technical Depth Settings
 */
export interface TechnicalDepthSettings {
  user_id: string;
  threshold: 'basic' | 'intermediate' | 'advanced' | 'expert';
  enabled: boolean;
  threshold_description?: string;
  threshold_numeric?: number;
}

/**
 * Technical Depth Level
 */
export interface TechnicalDepthLevel {
  value: string;
  label: string;
  description: string;
  numeric_value: number;
}

/**
 * Technical Depth Stats
 */
export interface TechnicalDepthStats {
  enabled: boolean;
  threshold?: string;
  threshold_description?: string;
  threshold_numeric?: number;
  message: string;
  error?: string;
}

/**
 * Notification History Record
 */
export interface NotificationHistoryRecord {
  id?: string;
  user_id?: string;
  sent_at?: string;
  channel: string;
  status: string;
  content?: string;
  feed_source?: string;
  error_message?: string;
  retry_count?: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * Notification History Response
 */
export interface NotificationHistoryResponse {
  records: NotificationHistoryRecord[];
  total_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/**
 * Notification Stats Response
 */
export interface NotificationStatsResponse {
  period_days: number;
  total_notifications: number;
  sent_count: number;
  failed_count: number;
  queued_count: number;
  cancelled_count: number;
  success_rate: number;
  channel_breakdown: {
    discord: number;
    email: number;
  };
  last_notification?: string;
}

// Quiet Hours API Functions

/**
 * Get user's quiet hours settings
 *
 * @returns Promise<QuietHoursSettings> - Quiet hours settings
 * @throws Error if request fails
 */
export async function getQuietHours(): Promise<QuietHoursSettings> {
  const response = await apiClient.get<{
    success: boolean;
    data: QuietHoursSettings;
  }>('/api/notifications/quiet-hours');
  return response.data.data;
}

/**
 * Update user's quiet hours settings
 *
 * @param updates - Updated quiet hours settings
 * @returns Promise<QuietHoursSettings> - Updated quiet hours settings
 * @throws Error if request fails
 */
export async function updateQuietHours(
  updates: Partial<QuietHoursSettings>
): Promise<QuietHoursSettings> {
  const response = await apiClient.put<{
    success: boolean;
    data: QuietHoursSettings;
  }>('/api/notifications/quiet-hours', updates);
  return response.data.data;
}

/**
 * Get quiet hours status
 *
 * @returns Promise<QuietHoursStatus> - Current quiet hours status
 * @throws Error if request fails
 */
export async function getQuietHoursStatus(): Promise<QuietHoursStatus> {
  const response = await apiClient.get<{
    success: boolean;
    data: QuietHoursStatus;
  }>('/api/notifications/quiet-hours/status');
  return response.data.data;
}

/**
 * Create default quiet hours settings
 *
 * @param timezone - IANA timezone identifier
 * @returns Promise<QuietHoursSettings> - Created quiet hours settings
 * @throws Error if request fails
 */
export async function createDefaultQuietHours(
  timezone: string = 'UTC'
): Promise<QuietHoursSettings> {
  const response = await apiClient.post<{
    success: boolean;
    data: QuietHoursSettings;
  }>('/api/notifications/quiet-hours/default', { timezone });
  return response.data.data;
}

/**
 * Delete quiet hours settings
 *
 * @returns Promise<void>
 * @throws Error if request fails
 */
export async function deleteQuietHours(): Promise<void> {
  await apiClient.delete('/api/notifications/quiet-hours');
}

// Technical Depth API Functions
