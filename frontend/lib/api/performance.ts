/**
 * API Performance Monitoring
 * Requirements: 11.1, 11.3
 *
 * This module provides performance monitoring hooks for API calls.
 * Tracks response times, error rates, and other metrics.
 */
import { logger } from '@/lib/utils/logger';

import { AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiError } from './errors';
import { API_FEATURE_FLAGS } from './featureFlags';

/**
 * Extended Axios config with performance tracking
 */
interface AxiosRequestConfigWithPerf extends AxiosRequestConfig {
  _perfStartTime?: number;
  _retryCount?: number;
}

/**
 * Performance metric for a single API call
 */
export interface PerformanceMetric {
  url: string;
  method: string;
  startTime: number;
  endTime: number;
  duration: number;
  statusCode?: number;
  success: boolean;
  errorCode?: string;
  retryCount?: number;
}

/**
 * Aggregated performance statistics
 */
export interface PerformanceStats {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  minResponseTime: number;
  maxResponseTime: number;
  errorRate: number;
  slowRequestsCount: number; // Requests > 1000ms
  byEndpoint: Record<
    string,
    {
      count: number;
      averageTime: number;
      errorCount: number;
    }
  >;
}

/**
 * Performance monitor singleton
 */
class PerformanceMonitor {
  private static instance: PerformanceMonitor | null = null;
  private metrics: PerformanceMetric[] = [];
  private maxMetrics: number = 1000; // Keep last 1000 metrics
  private enabled: boolean = API_FEATURE_FLAGS.ENABLE_API_MONITORING;

  private constructor() {}

  /**
   * Get singleton instance
   */
  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Enable or disable monitoring
   */
  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * Check if monitoring is enabled
   */
  public isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Start tracking a request
   *
   * @param config - Axios request config
   * @returns Start time for the request
   */
  public startRequest(config: AxiosRequestConfig): number {
    if (!this.enabled) return 0;
    return performance.now();
  }

  /**
   * Record successful request
   *
   * @param config - Axios request config
   * @param response - Axios response
   * @param startTime - Start time from startRequest
   */
  public recordSuccess(
    config: AxiosRequestConfigWithPerf,
    response: AxiosResponse,
    startTime: number
  ): void {
    if (!this.enabled || !startTime) return;

    const endTime = performance.now();
    const metric: PerformanceMetric = {
      url: config.url || '',
      method: config.method?.toUpperCase() || 'GET',
      startTime,
      endTime,
      duration: endTime - startTime,
      statusCode: response.status,
      success: true,
      retryCount: config._retryCount || 0,
    };

    this.addMetric(metric);
  }

  /**
   * Record failed request
   *
   * @param config - Axios request config
   * @param error - API error
   * @param startTime - Start time from startRequest
   */
  public recordError(
    config: AxiosRequestConfigWithPerf | undefined,
    error: ApiError,
    startTime: number
  ): void {
    if (!this.enabled || !startTime || !config) return;

    const endTime = performance.now();
    const metric: PerformanceMetric = {
      url: config.url || '',
      method: config.method?.toUpperCase() || 'GET',
      startTime,
      endTime,
      duration: endTime - startTime,
      statusCode: error.statusCode,
      success: false,
      errorCode: error.errorCode,
      retryCount: config._retryCount || 0,
    };

    this.addMetric(metric);
  }

  /**
   * Add metric to collection
   */
  private addMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);

    // Keep only last N metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.shift();
    }

    // Log slow requests in development
    if (process.env.NODE_ENV === 'development' && metric.duration > 1000) {
      logger.warn(
        `⚠️ Slow API request: ${metric.method} ${metric.url} took ${metric.duration.toFixed(0)}ms`
      );
    }
  }

  /**
   * Get all recorded metrics
   */
  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  /**
   * Get aggregated performance statistics
   */
  public getStats(): PerformanceStats {
    if (this.metrics.length === 0) {
      return {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageResponseTime: 0,
        minResponseTime: 0,
        maxResponseTime: 0,
        errorRate: 0,
        slowRequestsCount: 0,
        byEndpoint: {},
      };
    }

    const durations = this.metrics.map((m) => m.duration);
    const successCount = this.metrics.filter((m) => m.success).length;
    const failCount = this.metrics.length - successCount;
    const slowCount = this.metrics.filter((m) => m.duration > 1000).length;

    // Aggregate by endpoint
    const byEndpoint: Record<string, { count: number; averageTime: number; errorCount: number }> =
      {};
    this.metrics.forEach((metric) => {
      const endpoint = `${metric.method} ${metric.url}`;
      if (!byEndpoint[endpoint]) {
        byEndpoint[endpoint] = { count: 0, averageTime: 0, errorCount: 0 };
      }
      byEndpoint[endpoint].count++;
      byEndpoint[endpoint].averageTime += metric.duration;
      if (!metric.success) {
        byEndpoint[endpoint].errorCount++;
      }
    });

    // Calculate averages
    Object.keys(byEndpoint).forEach((endpoint) => {
      byEndpoint[endpoint].averageTime /= byEndpoint[endpoint].count;
    });

    return {
      totalRequests: this.metrics.length,
      successfulRequests: successCount,
      failedRequests: failCount,
      averageResponseTime: durations.reduce((a, b) => a + b, 0) / durations.length,
      minResponseTime: Math.min(...durations),
      maxResponseTime: Math.max(...durations),
      errorRate: failCount / this.metrics.length,
      slowRequestsCount: slowCount,
      byEndpoint,
    };
  }

  /**
   * Clear all metrics
   */
  public clearMetrics(): void {
    this.metrics = [];
  }

  /**
   * Log performance statistics to console
   */
  public logStats(): void {
    if (typeof window === 'undefined') return;

    const stats = this.getStats();
    console.group('📊 API Performance Statistics');
    logger.debug(`Total Requests: ${stats.totalRequests}`);
    logger.debug(
      `Success Rate: ${((stats.successfulRequests / stats.totalRequests) * 100).toFixed(1)}%`
    );
    logger.debug(`Error Rate: ${(stats.errorRate * 100).toFixed(1)}%`);
    logger.debug(`Average Response Time: ${stats.averageResponseTime.toFixed(0)}ms`);
    logger.debug(`Min Response Time: ${stats.minResponseTime.toFixed(0)}ms`);
    logger.debug(`Max Response Time: ${stats.maxResponseTime.toFixed(0)}ms`);
    logger.debug(`Slow Requests (>1s): ${stats.slowRequestsCount}`);

    if (Object.keys(stats.byEndpoint).length > 0) {
      console.group('By Endpoint:');
      Object.entries(stats.byEndpoint)
        .sort((a, b) => b[1].averageTime - a[1].averageTime)
        .slice(0, 10) // Top 10 slowest
        .forEach(([endpoint, data]) => {
          logger.debug(
            `${endpoint}: ${data.count} calls, ${data.averageTime.toFixed(0)}ms avg, ${
              data.errorCount
            } errors`
          );
        });
      console.groupEnd();
    }
    console.groupEnd();
  }

  /**
   * Export metrics as JSON
   */
  public exportMetrics(): string {
    return JSON.stringify(
      {
        metrics: this.metrics,
        stats: this.getStats(),
        timestamp: new Date().toISOString(),
      },
      null,
      2
    );
  }
}

/**
 * Export singleton instance
 */
export const performanceMonitor = PerformanceMonitor.getInstance();

/**
 * Performance monitoring interceptor for API client
 */
export const performanceInterceptor = {
  request: {
    onFulfilled: (config: AxiosRequestConfigWithPerf) => {
      if (performanceMonitor.isEnabled()) {
        config._perfStartTime = performanceMonitor.startRequest(config);
      }
      return config;
    },
  },
  response: {
    onFulfilled: (response: AxiosResponse) => {
      const config = response.config as AxiosRequestConfigWithPerf;
      if (performanceMonitor.isEnabled() && config._perfStartTime) {
        performanceMonitor.recordSuccess(config, response, config._perfStartTime);
      }
      return response;
    },
    onRejected: (error: any) => {
      const config = error.config as AxiosRequestConfigWithPerf;
      if (performanceMonitor.isEnabled() && config?._perfStartTime) {
        performanceMonitor.recordError(config, error, config._perfStartTime);
      }
      return Promise.reject(error);
    },
  },
};
