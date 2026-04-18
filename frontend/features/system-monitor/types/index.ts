/**
 * System Monitor Types
 *
 * Type definitions for system monitoring features including
 * scheduler status, system health, and feed status.
 */

/**
 * Scheduler execution status
 */
export interface SchedulerStatus {
  /** Whether the scheduler is currently running */
  isRunning: boolean;
  /** Last execution timestamp */
  lastExecutionTime: Date | null;
  /** Next scheduled execution timestamp */
  nextExecutionTime: Date | null;
  /** Number of articles processed in last execution */
  articlesProcessed: number;
  /** Number of failed operations in last execution */
  failedOperations: number;
  /** Total operations in last execution */
  totalOperations: number;
  /** Whether the scheduler is healthy */
  isHealthy: boolean;
  /** List of health issues (optional, defaults to empty array) */
  issues?: string[];
}

/**
 * System health metrics
 */
export interface SystemHealth {
  /** Database connection status */
  database: {
    connected: boolean;
    responseTime: number; // milliseconds
    lastChecked: Date;
  };
  /** API response time metrics */
  api: {
    averageResponseTime: number; // milliseconds
    p95ResponseTime: number; // milliseconds
    p99ResponseTime: number; // milliseconds
    lastChecked: Date;
  };
  /** Error rate metrics */
  errors: {
    rate: number; // errors per minute
    total24h: number;
    lastError: Date | null;
  };
}

/**
 * Individual feed status
 */
export interface FeedStatus {
  /** Feed ID */
  id: string;
  /** Feed name */
  name: string;
  /** Feed URL */
  url: string;
  /** Last successful fetch timestamp */
  lastFetch: Date | null;
  /** Next scheduled fetch timestamp */
  nextFetch: Date | null;
  /** Feed health status */
  status: 'healthy' | 'warning' | 'error';
  /** Error message if status is error */
  errorMessage?: string;
  /** Number of articles processed in last fetch */
  articlesProcessed: number;
  /** Processing time in milliseconds */
  processingTime: number;
}

/**
 * Fetch statistics
 */
export interface FetchStatistics {
  /** Total articles processed in last 24 hours */
  totalArticles24h: number;
  /** Success rate percentage */
  successRate: number;
  /** Average processing time in milliseconds */
  averageProcessingTime: number;
  /** Total fetch operations in last 24 hours */
  totalFetches24h: number;
  /** Failed fetch operations in last 24 hours */
  failedFetches24h: number;
}

/**
 * System resource usage metrics
 *
 * Requirements: 5.8
 */
export interface SystemResources {
  /** CPU usage percentage (0-100) */
  cpu: {
    usage: number;
    cores: number;
    loadAverage: number[];
  };
  /** Memory usage in bytes */
  memory: {
    total: number;
    used: number;
    free: number;
    usagePercentage: number;
  };
  /** Disk usage in bytes */
  disk: {
    total: number;
    used: number;
    free: number;
    usagePercentage: number;
  };
  /** Last updated timestamp */
  lastUpdated: Date;
}

/**
 * Complete system status
 */
export interface SystemStatus {
  scheduler: SchedulerStatus;
  health: SystemHealth;
  feeds: FeedStatus[];
  statistics: FetchStatistics;
  resources?: SystemResources; // Optional as backend may not provide it
  lastUpdated: Date;
}
