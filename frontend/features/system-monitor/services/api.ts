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
      lastError: data.errors.last_error ? new Date(data.errors.last_error) : null,
    },
  };
}

/**
 * Get feed status information
 *
 * Requirements: 5.6
 */
export async function getFeedStatus(): Promise<FeedStatus[]> {
  try {
    // Get feeds from the feeds API
    const response = await apiClient.get<{ success: boolean; data: any[] }>('/api/feeds');
    const feeds = response.data.data || [];

    // Transform to FeedStatus format
    return feeds.map((feed: any) => ({
      id: feed.id,
      name: feed.name,
      url: feed.url,
      lastFetch: feed.last_fetched_at ? new Date(feed.last_fetched_at) : null,
      nextFetch: null,
      status: (feed.is_active !== false ? 'healthy' : 'warning') as 'healthy' | 'warning' | 'error',
      errorMessage: undefined,
      articlesProcessed: 0,
      processingTime: 0,
    }));
  } catch (error) {
    console.error('Failed to fetch feed status:', error);
    return [];
  }
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
 * Note: System resource monitoring requires additional infrastructure.
 * Returns null to indicate resources are not available in current setup.
 */
export async function getSystemResources(): Promise<SystemResources | null> {
  // System resource monitoring (CPU, memory, disk) requires:
  // - Container metrics API (Docker stats)
  // - System monitoring agent (Prometheus, etc.)
  // - Cloud provider metrics (if deployed)
  //
  // This is intentionally not implemented as it requires infrastructure
  // that may not be available in all deployment scenarios.
  return null;
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
