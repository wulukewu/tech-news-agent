/**
 * Frontend Logger with Batching
 * Task 9.1: Create frontend logger with batching
 *
 * This module provides structured logging for the frontend with automatic
 * batching and periodic flushing to the backend.
 *
 * Requirements: 5.4
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
  userAgent?: string;
  url?: string;
  userId?: string;
}

export interface LoggerConfig {
  batchSize: number;
  flushInterval: number; // milliseconds
  endpoint: string;
  enabled: boolean;
  minLevel: LogLevel;
}

const DEFAULT_CONFIG: LoggerConfig = {
  batchSize: 10,
  flushInterval: 30000, // 30 seconds
  endpoint: '/api/logs',
  enabled: process.env.NODE_ENV === 'production',
  minLevel: LogLevel.INFO,
};

/**
 * Frontend Logger with automatic batching and periodic flushing
 *
 * Features:
 * - Structured logging with context
 * - Automatic batching to reduce network requests
 * - Periodic flush to backend
 * - Configurable batch size and flush interval
 * - User context tracking
 * - Error tracking with stack traces
 *
 * Validates: Requirement 5.4
 */
class FrontendLogger {
  private static instance: FrontendLogger | null = null;
  private config: LoggerConfig;
  private logBuffer: LogEntry[] = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private isFlushing: boolean = false;

  private constructor(config?: Partial<LoggerConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.startFlushTimer();
    this.setupBeforeUnload();
  }

  /**
   * Get singleton instance
   */
  public static getInstance(config?: Partial<LoggerConfig>): FrontendLogger {
    if (!FrontendLogger.instance) {
      FrontendLogger.instance = new FrontendLogger(config);
    }
    return FrontendLogger.instance;
  }

  /**
   * Reset singleton (for testing)
   */
  public static resetInstance(): void {
    if (FrontendLogger.instance) {
      FrontendLogger.instance.stopFlushTimer();
      FrontendLogger.instance = null;
    }
  }

  /**
   * Configure logger
   */
  public configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
    this.restartFlushTimer();
  }

  /**
   * Log debug message
   */
  public debug(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  /**
   * Log info message
   */
  public info(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, context);
  }

  /**
   * Log warning message
   */
  public warn(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, context);
  }

  /**
   * Log error message
   */
  public error(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.ERROR, message, context);
  }

  /**
   * Log error with Error object
   */
  public logError(error: Error, context?: Record<string, any>): void {
    this.log(LogLevel.ERROR, error.message, {
      ...context,
      stack: error.stack,
      name: error.name,
    });
  }

  /**
   * Core logging method
   */
  private log(level: LogLevel, message: string, context?: Record<string, any>): void {
    // Check if logging is enabled
    if (!this.config.enabled) {
      return;
    }

    // Check if level meets minimum threshold
    if (!this.shouldLog(level)) {
      return;
    }

    // Create log entry
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: this.sanitizeContext(context),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      userId: this.getUserId(),
    };

    // Add to buffer
    this.logBuffer.push(entry);

    // Console output in development
    if (process.env.NODE_ENV === 'development') {
      this.consoleLog(entry);
    }

    // Flush if buffer is full
    if (this.logBuffer.length >= this.config.batchSize) {
      this.flush();
    }
  }

  /**
   * Check if log level should be logged
   */
  private shouldLog(level: LogLevel): boolean {
    const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
    const currentLevelIndex = levels.indexOf(level);
    const minLevelIndex = levels.indexOf(this.config.minLevel);
    return currentLevelIndex >= minLevelIndex;
  }

  /**
   * Sanitize context to remove sensitive data
   */
  private sanitizeContext(context?: Record<string, any>): Record<string, any> | undefined {
    if (!context) {
      return undefined;
    }

    const sanitized: Record<string, any> = {};
    const sensitiveKeys = ['password', 'token', 'apikey', 'secret', 'authorization'];

    for (const [key, value] of Object.entries(context)) {
      const lowerKey = key.toLowerCase();
      const isSensitive = sensitiveKeys.some((sensitive) => lowerKey.includes(sensitive));

      if (isSensitive && value !== '') {
        sanitized[key] = '[REDACTED]';
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Get user ID from localStorage or session
   */
  private getUserId(): string | undefined {
    if (typeof window === 'undefined') {
      return undefined;
    }

    try {
      // Try to get user ID from localStorage
      const userId = localStorage.getItem('user_id');
      return userId || undefined;
    } catch {
      return undefined;
    }
  }

  /**
   * Console output for development
   */
  private consoleLog(entry: LogEntry): void {
    const consoleMethod =
      entry.level === LogLevel.ERROR
        ? 'error'
        : entry.level === LogLevel.WARN
          ? 'warn'
          : entry.level === LogLevel.INFO
            ? 'info'
            : 'log';

    console[consoleMethod](`[${entry.level}] ${entry.message}`, entry.context ? entry.context : '');
  }

  /**
   * Flush logs to backend
   */
  public async flush(): Promise<void> {
    // Skip if already flushing or buffer is empty
    if (this.isFlushing || this.logBuffer.length === 0) {
      return;
    }

    this.isFlushing = true;

    // Get logs to send
    const logsToSend = [...this.logBuffer];
    this.logBuffer = [];

    try {
      // Send logs to backend
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend }),
      });

      if (!response.ok) {
        // If failed, put logs back in buffer
        this.logBuffer.unshift(...logsToSend);
        console.error('Failed to send logs to backend:', response.statusText);
      }
    } catch (error) {
      // If failed, put logs back in buffer
      this.logBuffer.unshift(...logsToSend);
      console.error('Error sending logs to backend:', error);
    } finally {
      this.isFlushing = false;
    }
  }

  /**
   * Start periodic flush timer
   */
  private startFlushTimer(): void {
    if (typeof window === 'undefined') {
      return;
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  }

  /**
   * Stop flush timer
   */
  private stopFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  /**
   * Restart flush timer with new interval
   */
  private restartFlushTimer(): void {
    this.stopFlushTimer();
    this.startFlushTimer();
  }

  /**
   * Setup beforeunload handler to flush logs before page unload
   */
  private setupBeforeUnload(): void {
    if (typeof window === 'undefined') {
      return;
    }

    window.addEventListener('beforeunload', () => {
      // Flush remaining logs synchronously
      if (this.logBuffer.length > 0) {
        const logsToSend = [...this.logBuffer];
        this.logBuffer = [];

        // Use sendBeacon for reliable delivery during page unload
        const blob = new Blob([JSON.stringify({ logs: logsToSend })], {
          type: 'application/json',
        });
        navigator.sendBeacon(this.config.endpoint, blob);
      }
    });
  }

  /**
   * Get current buffer size
   */
  public getBufferSize(): number {
    return this.logBuffer.length;
  }

  /**
   * Get current buffer (for testing)
   */
  public getBuffer(): LogEntry[] {
    return [...this.logBuffer];
  }

  /**
   * Clear buffer (for testing)
   */
  public clearBuffer(): void {
    this.logBuffer = [];
  }

  /**
   * Get configuration
   */
  public getConfig(): LoggerConfig {
    return { ...this.config };
  }
}

/**
 * Export singleton instance
 */
export const logger = FrontendLogger.getInstance();

/**
 * Export class for testing
 */
export default FrontendLogger;
