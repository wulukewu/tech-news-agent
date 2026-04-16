/**
 * Error Tracking and Reporting
 * Requirements: 12.9
 *
 * This module provides comprehensive error tracking, reporting,
 * and recovery mechanisms for better user experience.
 */

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

/**
 * Error categories
 */
export enum ErrorCategory {
  JAVASCRIPT = 'javascript',
  NETWORK = 'network',
  RESOURCE = 'resource',
  PERFORMANCE = 'performance',
  USER_ACTION = 'user_action',
  API = 'api',
  RENDERING = 'rendering',
}

/**
 * Error context information
 */
interface ErrorContext {
  userId?: string;
  sessionId: string;
  userAgent: string;
  url: string;
  timestamp: number;
  viewport: { width: number; height: number };
  connectionType?: string;
  memoryUsage?: {
    used: number;
    total: number;
    limit: number;
  };
  customData?: Record<string, any>;
}

/**
 * Structured error report
 */
interface ErrorReport {
  id: string;
  message: string;
  stack?: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  context: ErrorContext;
  breadcrumbs: Breadcrumb[];
  tags: string[];
  fingerprint: string;
  count: number;
  firstSeen: number;
  lastSeen: number;
}

/**
 * Breadcrumb for error context
 */
interface Breadcrumb {
  timestamp: number;
  category: string;
  message: string;
  level: 'info' | 'warning' | 'error';
  data?: Record<string, any>;
}

/**
 * Error tracking class
 */
export class ErrorTracker {
  private static instance: ErrorTracker | null = null;
  private breadcrumbs: Breadcrumb[] = [];
  private errorCounts: Map<string, number> = new Map();
  private sessionId: string;
  private userId?: string;
  private isEnabled = true;
  private maxBreadcrumbs = 50;

  private constructor() {
    this.sessionId = this.generateSessionId();
    this.setupErrorHandlers();
    this.setupBreadcrumbTracking();
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): ErrorTracker {
    if (!ErrorTracker.instance) {
      ErrorTracker.instance = new ErrorTracker();
    }
    return ErrorTracker.instance;
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Setup global error handlers
   */
  private setupErrorHandlers() {
    if (typeof window === 'undefined') return;

    // JavaScript errors
    window.addEventListener('error', (event) => {
      this.captureError(
        {
          message: event.message,
          stack: event.error?.stack,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
        ErrorCategory.JAVASCRIPT,
        ErrorSeverity.HIGH
      );
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError(
        {
          message: `Unhandled Promise Rejection: ${event.reason}`,
          stack: event.reason?.stack,
          reason: event.reason,
        },
        ErrorCategory.JAVASCRIPT,
        ErrorSeverity.HIGH
      );
    });

    // Resource loading errors
    window.addEventListener(
      'error',
      (event) => {
        if (event.target !== window && event.target) {
          const target = event.target as HTMLElement;
          this.captureError(
            {
              message: `Failed to load resource: ${target.tagName}`,
              src: (target as any).src || (target as any).href,
              tagName: target.tagName,
            },
            ErrorCategory.RESOURCE,
            ErrorSeverity.MEDIUM
          );
        }
      },
      true
    );

    // Network errors (fetch failures)
    this.interceptFetch();
  }

  /**
   * Intercept fetch requests to track network errors
   */
  private interceptFetch() {
    if (typeof window === 'undefined') return;

    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();

      try {
        const response = await originalFetch(...args);
        const duration = performance.now() - startTime;

        // Track slow requests
        if (duration > 5000) {
          this.addBreadcrumb({
            category: 'network',
            message: `Slow request: ${args[0]}`,
            level: 'warning',
            data: { duration, url: args[0] },
          });
        }

        // Track HTTP errors
        if (!response.ok) {
          this.captureError(
            {
              message: `HTTP ${response.status}: ${response.statusText}`,
              url: args[0],
              status: response.status,
              statusText: response.statusText,
            },
            ErrorCategory.NETWORK,
            this.getNetworkErrorSeverity(response.status)
          );
        }

        return response;
      } catch (error) {
        const duration = performance.now() - startTime;

        this.captureError(
          {
            message: `Network request failed: ${error}`,
            url: args[0],
            duration,
            error: error,
          },
          ErrorCategory.NETWORK,
          ErrorSeverity.HIGH
        );

        throw error;
      }
    };
  }

  /**
   * Get error severity based on HTTP status
   */
  private getNetworkErrorSeverity(status: number): ErrorSeverity {
    if (status >= 500) return ErrorSeverity.CRITICAL;
    if (status >= 400) return ErrorSeverity.HIGH;
    return ErrorSeverity.MEDIUM;
  }

  /**
   * Setup breadcrumb tracking for user actions
   */
  private setupBreadcrumbTracking() {
    if (typeof window === 'undefined') return;

    // Track clicks
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      const tagName = target.tagName.toLowerCase();
      const text = target.textContent?.slice(0, 50) || '';

      this.addBreadcrumb({
        category: 'user_action',
        message: `Clicked ${tagName}${text ? `: ${text}` : ''}`,
        level: 'info',
        data: {
          tagName,
          className: target.className,
          id: target.id,
        },
      });
    });

    // Track navigation
    window.addEventListener('popstate', () => {
      this.addBreadcrumb({
        category: 'navigation',
        message: `Navigated to ${window.location.pathname}`,
        level: 'info',
        data: { url: window.location.href },
      });
    });

    // Track console errors
    const originalConsoleError = console.error;
    console.error = (...args) => {
      this.addBreadcrumb({
        category: 'console',
        message: `Console error: ${args.join(' ')}`,
        level: 'error',
        data: { args },
      });
      originalConsoleError.apply(console, args);
    };
  }

  /**
   * Add breadcrumb
   */
  public addBreadcrumb(breadcrumb: Omit<Breadcrumb, 'timestamp'>) {
    if (!this.isEnabled) return;

    this.breadcrumbs.push({
      ...breadcrumb,
      timestamp: Date.now(),
    });

    // Keep only recent breadcrumbs
    if (this.breadcrumbs.length > this.maxBreadcrumbs) {
      this.breadcrumbs.shift();
    }
  }

  /**
   * Capture error with context
   */
  public captureError(
    error: any,
    category: ErrorCategory = ErrorCategory.JAVASCRIPT,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    tags: string[] = [],
    customData: Record<string, any> = {}
  ) {
    if (!this.isEnabled) return;

    const errorMessage = typeof error === 'string' ? error : error.message || 'Unknown error';
    const stack = error.stack || new Error().stack;

    // Generate fingerprint for error deduplication
    const fingerprint = this.generateFingerprint(errorMessage, stack, category);

    // Update error count
    const currentCount = this.errorCounts.get(fingerprint) || 0;
    this.errorCounts.set(fingerprint, currentCount + 1);

    const errorReport: ErrorReport = {
      id: this.generateErrorId(),
      message: errorMessage,
      stack,
      category,
      severity,
      context: this.getErrorContext(customData),
      breadcrumbs: [...this.breadcrumbs],
      tags: [...tags, category, severity],
      fingerprint,
      count: currentCount + 1,
      firstSeen: currentCount === 0 ? Date.now() : this.getFirstSeenTime(fingerprint),
      lastSeen: Date.now(),
    };

    // Send error report
    this.sendErrorReport(errorReport);

    // Add error as breadcrumb
    this.addBreadcrumb({
      category: 'error',
      message: errorMessage,
      level: 'error',
      data: { category, severity, fingerprint },
    });

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 Error Captured [${severity}]`);
      console.error('Message:', errorMessage);
      console.error('Category:', category);
      console.error('Stack:', stack);
      console.error('Context:', errorReport.context);
      console.error('Breadcrumbs:', this.breadcrumbs.slice(-5));
      console.groupEnd();
    }
  }

  /**
   * Generate error fingerprint for deduplication
   */
  private generateFingerprint(message: string, stack?: string, category?: ErrorCategory): string {
    const stackLines = stack?.split('\n').slice(0, 3).join('') || '';
    const content = `${category}-${message}-${stackLines}`;

    // Simple hash function
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }

    return Math.abs(hash).toString(36);
  }

  /**
   * Generate unique error ID
   */
  private generateErrorId(): string {
    return `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get error context
   */
  private getErrorContext(customData: Record<string, any> = {}): ErrorContext {
    const context: ErrorContext = {
      userId: this.userId,
      sessionId: this.sessionId,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: Date.now(),
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      customData,
    };

    // Add connection info if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      context.connectionType = connection.effectiveType;
    }

    // Add memory info if available
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      context.memoryUsage = {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
      };
    }

    return context;
  }

  /**
   * Get first seen time for error fingerprint
   */
  private getFirstSeenTime(fingerprint: string): number {
    // In a real implementation, this would be stored persistently
    return Date.now();
  }

  /**
   * Send error report to tracking service
   */
  private async sendErrorReport(errorReport: ErrorReport) {
    try {
      // In production, send to your error tracking service
      if (process.env.NODE_ENV === 'production') {
        // Example: Send to Sentry, LogRocket, or custom endpoint
        await fetch('/api/errors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(errorReport),
        });
      }
    } catch (error) {
      console.warn('Failed to send error report:', error);
    }
  }

  /**
   * Set user ID for error context
   */
  public setUserId(userId: string) {
    this.userId = userId;
  }

  /**
   * Enable/disable error tracking
   */
  public setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
  }

  /**
   * Clear breadcrumbs
   */
  public clearBreadcrumbs() {
    this.breadcrumbs = [];
  }

  /**
   * Get error statistics
   */
  public getErrorStats() {
    const totalErrors = Array.from(this.errorCounts.values()).reduce(
      (sum, count) => sum + count,
      0
    );
    const uniqueErrors = this.errorCounts.size;

    return {
      totalErrors,
      uniqueErrors,
      sessionId: this.sessionId,
      breadcrumbsCount: this.breadcrumbs.length,
      isEnabled: this.isEnabled,
    };
  }

  /**
   * Export error data for debugging
   */
  public exportErrorData() {
    return {
      sessionId: this.sessionId,
      userId: this.userId,
      breadcrumbs: this.breadcrumbs,
      errorCounts: Object.fromEntries(this.errorCounts),
      stats: this.getErrorStats(),
    };
  }
}

/**
 * Initialize error tracking
 */
export function initializeErrorTracking(userId?: string) {
  const tracker = ErrorTracker.getInstance();

  if (userId) {
    tracker.setUserId(userId);
  }

  // Add initial breadcrumb
  tracker.addBreadcrumb({
    category: 'session',
    message: 'Error tracking initialized',
    level: 'info',
    data: { userAgent: navigator.userAgent },
  });

  return tracker;
}

/**
 * Capture custom error
 */
export function captureError(
  error: any,
  category: ErrorCategory = ErrorCategory.JAVASCRIPT,
  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
  tags: string[] = [],
  customData: Record<string, any> = {}
) {
  const tracker = ErrorTracker.getInstance();
  tracker.captureError(error, category, severity, tags, customData);
}

/**
 * Add breadcrumb
 */
export function addBreadcrumb(breadcrumb: Omit<Breadcrumb, 'timestamp'>) {
  const tracker = ErrorTracker.getInstance();
  tracker.addBreadcrumb(breadcrumb);
}

/**
 * Export singleton instance
 */
export const errorTracker = ErrorTracker.getInstance();
