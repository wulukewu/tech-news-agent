'use client';

import { apiClient } from '../client';
import {
  NotificationHistoryRecord,
  NotificationHistoryResponse,
  NotificationStatsResponse,
} from './quiet-hours';

/**
 * Get notification history with pagination
 *
 * @param page - Page number (1-indexed)
 * @param pageSize - Number of records per page
 * @param channel - Filter by channel (optional)
 * @param status - Filter by status (optional)
 * @param daysBack - Only include last N days (optional)
 * @returns Promise<NotificationHistoryResponse> - Notification history
 * @throws Error if request fails
 */
export async function getNotificationHistoryPaginated(
  page: number = 1,
  pageSize: number = 20,
  channel?: string,
  status?: string,
  daysBack?: number
): Promise<NotificationHistoryResponse> {
  const params: Record<string, unknown> = { page, page_size: pageSize };
  if (channel) params.channel = channel;
  if (status) params.status = status;
  if (daysBack) params.days_back = daysBack;

  const response = await apiClient.get<{
    success: boolean;
    data: NotificationHistoryResponse;
  }>('/api/notifications/history', { params });
  return response.data.data;
}

/**
 * Get notification statistics
 *
 * @param daysBack - Number of days to include in statistics
 * @returns Promise<NotificationStatsResponse> - Notification statistics
 * @throws Error if request fails
 */
export async function getNotificationStats(
  daysBack: number = 30
): Promise<NotificationStatsResponse> {
  const response = await apiClient.get<{
    success: boolean;
    data: NotificationStatsResponse;
  }>('/api/notifications/history/stats', {
    params: { days_back: daysBack },
  });
  return response.data.data;
}

// ── Proactive Recommendation Frequency ───────────────────────────────────────
