/**
 * System Monitor API Service
 *
 * API functions for fetching system status, scheduler information,
 * and triggering manual operations.
 */

import { apiClient } from '@/lib/api/client';
import type {
  SystemStatus,
  SchedulerStatus,
  FeedStatus,
  SystemHealth,
  FetchStatistics,
  SystemResources,
} from '../types';

/**
 * Backend scheduler status response
 */
interface SchedulerStatusResponse {
  last_execution_time: string | null;
  next_execution_time: string | null;
  is_running: boolean;
  articles_processed: number;
  failed_operations: number;
  total_operations: number;
  is_healthy: boolean;
  issues: string[];
}

/**
 * Get current scheduler status
 *
 * Requirements: 5.1, 5.2
 */
export async function getSchedulerStatus(): Promise<SchedulerStatus> {
  const response = await apiClient.get<{ success: boolean; data: SchedulerStatusResponse }>(
    '/api/scheduler/status'
  );
  const data = response.data.data; // Extract data from success_response wrapper

  return {
    isRunning: data.is_running || false,
    lastExecutionTime: data.last_execution_time ? new Date(data.last_execution_time) : null,
    nextExecutionTime: data.next_execution_time ? new Date(data.next_execution_time) : null,
    articlesProcessed: data.articles_processed,
    failedOperations: data.failed_operations,
    totalOperations: data.total_operations,
    isHealthy: data.is_healthy,
    issues: data.issues || [], // Provide default empty array
  };
}

/**
 * Trigger manual fetch operation
 *
 * Requirements: 5.3
 */
export async function triggerManualFetch(): Promise<{ status: string; message: string }> {
  return apiClient.post('/api/scheduler/trigger', {});
}

/**
 * Get system health metrics
 *
 * Requirements: 5.4
 */
export async function getSystemHealth(): Promise<SystemHealth> {
  const response = await apiClient.get<{ success: boolean; data: any }>('/api/system/health');
  const data = response.data.data;

  return {
    database: {
      connected: data.database.connected,
      responseTime: data.database.response_time,
      lastChecked: new Date(data.database.last_checked),
    },
    api: {
      averageResponseTime: data.api.average_response_time,
      p95ResponseTime: data.api.p95_response_time,
      p99ResponseTime: data.api.p99_response_time,
      lastChecked: new Date(data.api.last_checked),
    },
    errors: {
      rate: data.errors.rate,
      total24h: data.errors.total_24h,
      lastError: data.errors.last_error ? new Date(data.errors.last_error) : undefined,
    },
  };
}

/**
 * Get feed status information
 *
 * Requirements: 5.6
 *
 * Note: This is a placeholder implementation. The backend endpoint
 * needs to be implemented to provide real feed status.
 */
export async function getFeedStatus(): Promise<FeedStatus[]> {
  // TODO: Implement backend endpoint for feed status
  // For now, return empty array
  return [];
}

/**
 * Get fetch statistics
 *
 * Requirements: 5.5
 */
export async function getFetchStatistics(): Promise<FetchStatistics> {
  const response = await apiClient.get<{ success: boolean; data: any }>('/api/system/statistics');
  const data = response.data.data;

  return {
    totalArticles24h: data.total_articles_24h,
    successRate: data.success_rate,
    averageProcessingTime: data.average_processing_time,
    totalFetches24h: data.total_fetches_24h,
    failedFetches24h: data.failed_fetches_24h,
  };
}

/**
 * Get system resource usage
 *
 * Requirements: 5.8
 *
 * Note: This is a placeholder implementation. The backend endpoint
 * needs to be implemented to provide real resource metrics.
 */
export async function getSystemResources(): Promise<SystemResources | null> {
  try {
    // TODO: Implement backend endpoint for system resources
    // For now, return null to indicate resources are not available
    return null;
  } catch (error) {
    console.error('Failed to fetch system resources:', error);
    return null;
  }
}

/**
 * Get complete system status
 *
 * Requirements: 5.1, 5.2, 5.4, 5.5, 5.6, 5.8
 */
export async function getSystemStatus(): Promise<SystemStatus> {
  const [scheduler, health, feeds, statistics, resources] = await Promise.all([
    getSchedulerStatus(),
    getSystemHealth(),
    getFeedStatus(),
    getFetchStatistics(),
    getSystemResources(),
  ]);

  return {
    scheduler,
    health,
    feeds,
    statistics,
    resources: resources || undefined,
    lastUpdated: new Date(),
  };
}
