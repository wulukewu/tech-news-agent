import { apiClient } from './client';

/**
 * Scheduler API functions
 */

export interface SchedulerStatus {
  last_execution_time: string | null;
  articles_processed: number;
  failed_operations: number;
  total_operations: number;
  is_healthy: boolean;
  issues: string[];
}

/**
 * Manually trigger the scheduler to fetch new articles
 *
 * @returns Promise resolving to trigger response
 */
export async function triggerScheduler(): Promise<{
  status: string;
  message: string;
}> {
  return apiClient.post('/api/scheduler/trigger', {});
}

/**
 * Get the current status of the scheduler
 *
 * @returns Promise resolving to scheduler status
 */
export async function getSchedulerStatus(): Promise<SchedulerStatus> {
  return apiClient.get<SchedulerStatus>('/api/scheduler/status');
}
