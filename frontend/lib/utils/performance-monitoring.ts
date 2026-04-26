/**
 * Core Web Vitals and Performance Monitoring
 * Requirements: 12.8, 12.9, 12.10
 *
 * This module provides comprehensive performance monitoring including
 * Core Web Vitals tracking, error reporting, and slow connection handling.
 */
import { logger } from '@/lib/utils/logger';

/**
 * Core Web Vitals metrics
 */
export interface CoreWebVitals {
  LCP: number | null; // Largest Contentful Paint
  FID: number | null; // First Input Delay
  CLS: number | null; // Cumulative Layout Shift
  FCP: number | null; // First Contentful Paint
  TTFB: number | null; // Time to First Byte
}

/**
 * Performance thresholds (Google recommendations)
 */
export const PERFORMANCE_THRESHOLDS = {
  LCP: { good: 2500, needsImprovement: 4000 }, // ms
  FID: { good: 100, needsImprovement: 300 }, // ms
  CLS: { good: 0.1, needsImprovement: 0.25 }, // score
  FCP: { good: 1800, needsImprovement: 3000 }, // ms
  TTFB: { good: 800, needsImprovement: 1800 }, // ms
} as const;

/**
 * Performance monitoring class
 */
export class PerformanceMonitor {
  private static instance: PerformanceMonitor | null = null;
  private vitals: Partial<CoreWebVitals> = {};
  private observers: PerformanceObserver[] = [];
  private isSlowConnection = false;
  private connectionType: string = 'unknown';

  private constructor() {
    this.setupConnectionMonitoring();
    this.setupVitalsMonitoring();
    this.setupErrorTracking();
  }

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
   * Setup connection monitoring
   */
  private setupConnectionMonitoring() {
    if (typeof window === 'undefined') return;

    // Monitor connection type and speed
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;

      const updateConnection = () => {
        this.connectionType = connection.effectiveType || 'unknown';
        this.isSlowConnection = ['slow-2g', '2g', '3g'].includes(connection.effectiveType);

        // Report connection changes
        this.reportMetric('connection_change', {
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData,
        });
      };

      connection.addEventListener('change', updateConnection);
      updateConnection();
    }

    // Monitor online/offline status
    window.addEventListener('online', () => {
      this.reportMetric('connection_status', { status: 'online' });
    });

    window.addEventListener('offline', () => {
      this.reportMetric('connection_status', { status: 'offline' });
    });
  }

  /**
   * Setup Core Web Vitals monitoring
   */
  private setupVitalsMonitoring() {
    if (typeof window === 'undefined') return;

    // Largest Contentful Paint (LCP)
    this.observePerformanceEntry('largest-contentful-paint', (entries) => {
      const lastEntry = entries[entries.length - 1];
      this.vitals.LCP = lastEntry.startTime;
      this.checkThreshold('LCP', lastEntry.startTime);
    });

    // First Input Delay (FID)
    this.observePerformanceEntry('first-input', (entries) => {
      const firstEntry = entries[0] as any; // PerformanceEventTiming not fully typed
      this.vitals.FID = firstEntry.processingStart - firstEntry.startTime;
      this.checkThreshold('FID', this.vitals.FID);
    });

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    this.observePerformanceEntry('layout-shift', (entries) => {
      for (const entry of entries) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      }
      this.vitals.CLS = clsValue;
      this.checkThreshold('CLS', clsValue);
    });

    // First Contentful Paint (FCP)
    this.observePerformanceEntry('paint', (entries) => {
      const fcpEntry = entries.find((entry) => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        this.vitals.FCP = fcpEntry.startTime;
        this.checkThreshold('FCP', fcpEntry.startTime);
      }
    });

    // Time to First Byte (TTFB)
    this.observePerformanceEntry('navigation', (entries) => {
      const navEntry = entries[0] as PerformanceNavigationTiming;
      this.vitals.TTFB = navEntry.responseStart - navEntry.requestStart;
      this.checkThreshold('TTFB', this.vitals.TTFB);
    });

    // Additional performance metrics
    this.setupAdditionalMetrics();
  }

  /**
   * Setup additional performance metrics
   */
  private setupAdditionalMetrics() {
    if (typeof window === 'undefined') return;

    // Monitor long tasks (> 50ms)
    this.observePerformanceEntry('longtask', (entries) => {
      entries.forEach((entry) => {
        this.reportMetric('long_task', {
          duration: entry.duration,
          startTime: entry.startTime,
          name: entry.name,
        });
      });
    });

    // Monitor resource loading
    this.observePerformanceEntry('resource', (entries) => {
      entries.forEach((entry) => {
        const resource = entry as PerformanceResourceTiming;

        // Report slow resources
        if (resource.duration > 1000) {
          this.reportMetric('slow_resource', {
            name: resource.name,
            duration: resource.duration,
            size: resource.transferSize,
            type: this.getResourceType(resource.name),
          });
        }
      });
    });

    // Monitor memory usage (if available)
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        const memoryUsage = {
          used: memory.usedJSHeapSize,
          total: memory.totalJSHeapSize,
          limit: memory.jsHeapSizeLimit,
          percentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100,
        };

        // Report high memory usage
        if (memoryUsage.percentage > 80) {
          this.reportMetric('high_memory_usage', memoryUsage);
        }
      }, 30000); // Check every 30 seconds
    }
  }

  /**
   * Setup error tracking
   */
  private setupErrorTracking() {
    if (typeof window === 'undefined') return;

    // JavaScript errors
    window.addEventListener('error', (event) => {
      this.reportMetric('javascript_error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
      });
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.reportMetric('unhandled_rejection', {
        reason: event.reason,
        stack: event.reason?.stack,
      });
    });

    // Resource loading errors
    window.addEventListener(
      'error',
      (event) => {
        if (event.target !== window) {
          this.reportMetric('resource_error', {
            tagName: (event.target as Element)?.tagName,
            src: (event.target as any)?.src || (event.target as any)?.href,
            message: event.message,
          });
        }
      },
      true
    );
  }

  /**
   * Observe performance entries
   */
  private observePerformanceEntry(
    entryType: string,
    callback: (entries: PerformanceEntry[]) => void
  ) {
    try {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries());
      });

      observer.observe({ entryTypes: [entryType] });
      this.observers.push(observer);
    } catch (error) {
      logger.warn(`Failed to observe ${entryType}:`, error);
    }
  }

  /**
   * Check if metric exceeds threshold
   */
  private checkThreshold(metric: keyof typeof PERFORMANCE_THRESHOLDS, value: number) {
    const threshold = PERFORMANCE_THRESHOLDS[metric];
    let status: 'good' | 'needs-improvement' | 'poor';

    if (value <= threshold.good) {
      status = 'good';
    } else if (value <= threshold.needsImprovement) {
      status = 'needs-improvement';
    } else {
      status = 'poor';
    }

    this.reportMetric('core_web_vital', {
      metric,
      value,
      status,
      threshold,
    });

    // Log poor performance in development
    if (process.env.NODE_ENV === 'development' && status === 'poor') {
      logger.warn(`⚠️ Poor ${metric}: ${value} (threshold: ${threshold.good})`);
    }
  }

  /**
   * Get resource type from URL
   */
  private getResourceType(url: string): string {
    if (url.match(/\.(css)$/)) return 'stylesheet';
    if (url.match(/\.(js)$/)) return 'script';
    if (url.match(/\.(jpg|jpeg|png|gif|webp|avif|svg)$/)) return 'image';
    if (url.match(/\.(woff|woff2|ttf|eot)$/)) return 'font';
    return 'other';
  }

  /**
   * Report metric to analytics
   */
  private reportMetric(name: string, data: any) {
    // In production, this would send to your analytics service
    if (process.env.NODE_ENV === 'development') {
      logger.debug(`📊 Performance metric: ${name}`, data);
    }

    // Send to analytics service (implement based on your needs)
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', name, {
        custom_parameter: JSON.stringify(data),
      });
    }
  }

  /**
   * Get current Core Web Vitals
   */
  public getVitals(): CoreWebVitals {
    return { ...this.vitals } as CoreWebVitals;
  }

  /**
   * Get performance score (0-100)
   */
  public getPerformanceScore(): number {
    const vitals = this.getVitals();
    let score = 0;
    let count = 0;

    // Calculate score based on thresholds
    Object.entries(vitals).forEach(([metric, value]) => {
      if (value !== null && metric in PERFORMANCE_THRESHOLDS) {
        const threshold = PERFORMANCE_THRESHOLDS[metric as keyof typeof PERFORMANCE_THRESHOLDS];

        if (value <= threshold.good) {
          score += 100;
        } else if (value <= threshold.needsImprovement) {
          score += 50;
        } else {
          score += 0;
        }
        count++;
      }
    });

    return count > 0 ? Math.round(score / count) : 0;
  }

  /**
   * Check if connection is slow
   */
  public isSlowConnectionDetected(): boolean {
    return this.isSlowConnection;
  }

  /**
   * Get connection info
   */
  public getConnectionInfo() {
    return {
      type: this.connectionType,
      isSlow: this.isSlowConnection,
    };
  }

  /**
   * Optimize for slow connections
   */
  public optimizeForSlowConnection() {
    if (!this.isSlowConnection) return;

    // Reduce image quality
    const images = document.querySelectorAll('img[data-optimize]');
    images.forEach((img) => {
      const src = img.getAttribute('src');
      if (src && !src.includes('q_auto:low')) {
        img.setAttribute('src', src.replace('q_auto', 'q_auto:low'));
      }
    });

    // Disable non-critical animations
    document.body.classList.add('reduce-motion');

    // Defer non-critical resources
    const nonCriticalScripts = document.querySelectorAll('script[data-defer-slow]');
    nonCriticalScripts.forEach((script) => {
      script.setAttribute('defer', '');
    });

    this.reportMetric('slow_connection_optimization', {
      optimizations: ['reduced_image_quality', 'disabled_animations', 'deferred_scripts'],
    });
  }

  /**
   * Generate performance report
   */
  public generateReport() {
    const vitals = this.getVitals();
    const score = this.getPerformanceScore();
    const connection = this.getConnectionInfo();

    return {
      timestamp: new Date().toISOString(),
      score,
      vitals,
      connection,
      recommendations: this.getRecommendations(),
    };
  }

  /**
   * Get performance recommendations
   */
  private getRecommendations(): string[] {
    const recommendations: string[] = [];
    const vitals = this.getVitals();

    if (vitals.LCP && vitals.LCP > PERFORMANCE_THRESHOLDS.LCP.good) {
      recommendations.push(
        'Optimize Largest Contentful Paint by reducing server response times and optimizing critical resources'
      );
    }

    if (vitals.FID && vitals.FID > PERFORMANCE_THRESHOLDS.FID.good) {
      recommendations.push(
        'Improve First Input Delay by reducing JavaScript execution time and breaking up long tasks'
      );
    }

    if (vitals.CLS && vitals.CLS > PERFORMANCE_THRESHOLDS.CLS.good) {
      recommendations.push(
        'Reduce Cumulative Layout Shift by setting dimensions for images and avoiding dynamic content insertion'
      );
    }

    if (this.isSlowConnection) {
      recommendations.push(
        'Optimize for slow connections by reducing resource sizes and deferring non-critical content'
      );
    }

    return recommendations;
  }

  /**
   * Cleanup observers
   */
  public cleanup() {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers = [];
  }
}

/**
 * Initialize performance monitoring
 */
export function initializePerformanceMonitoring() {
  if (typeof window === 'undefined') return null;

  const monitor = PerformanceMonitor.getInstance();

  // Optimize for slow connections
  monitor.optimizeForSlowConnection();

  // Generate report on page unload
  window.addEventListener('beforeunload', () => {
    const report = monitor.generateReport();

    // Send report using sendBeacon for reliability
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/performance', JSON.stringify(report));
    }
  });

  // Generate periodic reports in development
  if (process.env.NODE_ENV === 'development') {
    setInterval(() => {
      const report = monitor.generateReport();
      console.group('📊 Performance Report');
      logger.debug('Score:', report.score);
      logger.debug('Core Web Vitals:', report.vitals);
      logger.debug('Connection:', report.connection);
      logger.debug('Recommendations:', report.recommendations);
      console.groupEnd();
    }, 30000); // Every 30 seconds
  }

  return monitor;
}

/**
 * Export singleton instance
 */
export const performanceMonitor = PerformanceMonitor.getInstance();
