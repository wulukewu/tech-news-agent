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
    isRunning: false, // TODO: Add real-time status from backend
    lastExecutionTime: data.last_execution_time ? new Date(data.last_execution_time) : null,
    nextExecutionTime: null, // TODO: Calculate based on schedule
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
 *
 * Note: This is a placeholder implementation. The backend endpoint
 * needs to be implemented to provide real health metrics.
 */
export async function getSystemHealth(): Promise<SystemHealth> {
  // TODO: Implement backend endpoint for system health
  // For now, return mock data
  return {
    database: {
      connected: true,
      responseTime: 15,
      lastChecked: new Date(),
    },
    api: {
      averageResponseTime: 120,
      p95ResponseTime: 250,
      p99ResponseTime: 500,
      lastChecked: new Date(),
    },
    errors: {
      rate: 0.5,
      total24h: 12,
      lastError: new Date(Date.now() - 3600000),
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
 *
 * Note: This is a placeholder implementation. The backend endpoint
 * needs to be implemented to provide real statistics.
 */
export async function getFetchStatistics(): Promise<FetchStatistics> {
  // TODO: Implement backend endpoint for fetch statistics
  // For now, return mock data
  return {
    totalArticles24h: 0,
    successRate: 0,
    averageProcessingTime: 0,
    totalFetches24h: 0,
    failedFetches24h: 0,
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
