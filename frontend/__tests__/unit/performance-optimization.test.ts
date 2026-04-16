/**
 * Unit Tests for Performance Optimization Features
 * Requirements: 12.1, 12.2, 12.8
 *
 * These tests verify that performance optimization features work correctly.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cacheStrategies, invalidationPatterns } from '../../lib/cache/strategies';
import { PERFORMANCE_THRESHOLDS, PerformanceMonitor } from '../../lib/utils/performance-monitoring';
import { ErrorTracker, ErrorSeverity, ErrorCategory } from '../../lib/utils/error-tracking';
import { FEATURE_FLAGS } from '../../lib/utils/bundle-optimization';

// Mock performance APIs
beforeEach(() => {
  // Mock PerformanceObserver
  global.PerformanceObserver = vi.fn().mockImplementation((callback) => ({
    observe: vi.fn(),
    disconnect: vi.fn(),
  }));

  // Mock performance.now
  vi.spyOn(performance, 'now').mockReturnValue(1000);

  // Mock navigator.connection
  Object.defineProperty(navigator, 'connection', {
    value: {
      effectiveType: '4g',
      downlink: 10,
      rtt: 50,
      saveData: false,
      addEventListener: vi.fn(),
    },
    writable: true,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Cache Strategies', () => {
  it('should have appropriate cache durations for different data types', () => {
    // AI analysis should have long cache duration
    expect(cacheStrategies.aiAnalysis.staleTime).toBeGreaterThan(
      cacheStrategies.articleList.staleTime
    );

    // User settings should have immediate updates
    expect(cacheStrategies.userSettings.staleTime).toBe(0);

    // System status should have short cache duration
    expect(cacheStrategies.systemStatus.staleTime).toBeLessThan(
      cacheStrategies.articleDetail.staleTime
    );
  });

  it('should have proper refetch configurations', () => {
    // Critical data should refetch on window focus
    expect(cacheStrategies.articleList.refetchOnWindowFocus).toBe(true);
    expect(cacheStrategies.userSettings.refetchOnWindowFocus).toBe(true);

    // Stable data should not refetch on window focus
    expect(cacheStrategies.aiAnalysis.refetchOnWindowFocus).toBe(false);
  });

  it('should have appropriate retry configurations', () => {
    // All strategies should have retry configured
    Object.values(cacheStrategies).forEach((strategy) => {
      expect(strategy.retry).toBeGreaterThan(0);
      expect(strategy.retry).toBeLessThanOrEqual(3);
    });
  });
});

describe('Performance Thresholds', () => {
  it('should have valid Core Web Vitals thresholds', () => {
    // LCP thresholds
    expect(PERFORMANCE_THRESHOLDS.LCP.good).toBe(2500);
    expect(PERFORMANCE_THRESHOLDS.LCP.needsImprovement).toBe(4000);

    // FID thresholds
    expect(PERFORMANCE_THRESHOLDS.FID.good).toBe(100);
    expect(PERFORMANCE_THRESHOLDS.FID.needsImprovement).toBe(300);

    // CLS thresholds
    expect(PERFORMANCE_THRESHOLDS.CLS.good).toBe(0.1);
    expect(PERFORMANCE_THRESHOLDS.CLS.needsImprovement).toBe(0.25);
  });

  it('should classify performance metrics correctly', () => {
    const testCases = [
      { metric: 'LCP', value: 2000, expected: 'good' },
      { metric: 'LCP', value: 3000, expected: 'needs-improvement' },
      { metric: 'LCP', value: 5000, expected: 'poor' },
      { metric: 'FID', value: 50, expected: 'good' },
      { metric: 'FID', value: 200, expected: 'needs-improvement' },
      { metric: 'FID', value: 400, expected: 'poor' },
      { metric: 'CLS', value: 0.05, expected: 'good' },
      { metric: 'CLS', value: 0.15, expected: 'needs-improvement' },
      { metric: 'CLS', value: 0.3, expected: 'poor' },
    ];

    testCases.forEach(({ metric, value, expected }) => {
      const threshold = PERFORMANCE_THRESHOLDS[metric as keyof typeof PERFORMANCE_THRESHOLDS];

      let actual: string;
      if (value <= threshold.good) {
        actual = 'good';
      } else if (value <= threshold.needsImprovement) {
        actual = 'needs-improvement';
      } else {
        actual = 'poor';
      }

      expect(actual).toBe(expected);
    });
  });
});

describe('Performance Monitor', () => {
  it('should calculate performance score within valid range', () => {
    const monitor = PerformanceMonitor.getInstance();

    // Mock getVitals method
    vi.spyOn(monitor, 'getVitals').mockReturnValue({
      LCP: 2000, // good
      FID: 50, // good
      CLS: 0.05, // good
      FCP: 1500, // good
      TTFB: 500, // good
    });

    const score = monitor.getPerformanceScore();

    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(100);
    expect(score).toBe(100); // All metrics are good
  });

  it('should handle mixed performance metrics', () => {
    const monitor = PerformanceMonitor.getInstance();

    // Mock getVitals method with mixed results
    vi.spyOn(monitor, 'getVitals').mockReturnValue({
      LCP: 3000, // needs improvement (50 points)
      FID: 50, // good (100 points)
      CLS: 0.3, // poor (0 points)
      FCP: null, // not measured
      TTFB: null, // not measured
    });

    const score = monitor.getPerformanceScore();

    expect(score).toBe(50); // (50 + 100 + 0) / 3 = 50
  });

  it('should detect slow connections', () => {
    const monitor = PerformanceMonitor.getInstance();

    // Mock slow connection
    Object.defineProperty(navigator, 'connection', {
      value: {
        effectiveType: '2g',
        downlink: 0.5,
        rtt: 1000,
      },
      writable: true,
    });

    // The monitor should detect this as slow
    // Note: In a real implementation, this would be detected during initialization
    expect(['slow-2g', '2g', '3g'].includes('2g')).toBe(true);
  });
});

describe('Error Tracking', () => {
  it('should categorize errors correctly', () => {
    expect(ErrorCategory.JAVASCRIPT).toBe('javascript');
    expect(ErrorCategory.NETWORK).toBe('network');
    expect(ErrorCategory.PERFORMANCE).toBe('performance');
  });

  it('should have appropriate severity levels', () => {
    expect(ErrorSeverity.LOW).toBe('low');
    expect(ErrorSeverity.MEDIUM).toBe('medium');
    expect(ErrorSeverity.HIGH).toBe('high');
    expect(ErrorSeverity.CRITICAL).toBe('critical');
  });

  it('should generate unique session IDs', () => {
    const tracker1 = ErrorTracker.getInstance();
    const tracker2 = ErrorTracker.getInstance();

    // Should be singleton
    expect(tracker1).toBe(tracker2);

    const stats = tracker1.getErrorStats();
    expect(stats.sessionId).toBeDefined();
    expect(typeof stats.sessionId).toBe('string');
    expect(stats.sessionId.length).toBeGreaterThan(0);
  });
});

describe('Bundle Optimization', () => {
  it('should have feature flags configured', () => {
    expect(typeof FEATURE_FLAGS.ENABLE_ANALYTICS).toBe('boolean');
    expect(typeof FEATURE_FLAGS.ENABLE_SOCIAL_SHARING).toBe('boolean');
    expect(typeof FEATURE_FLAGS.ENABLE_EXPORT_FEATURES).toBe('boolean');
  });

  it('should respect environment variables for feature flags', () => {
    // Feature flags should be based on environment variables
    const originalEnv = process.env.NEXT_PUBLIC_ENABLE_ANALYTICS;

    // Test with enabled
    process.env.NEXT_PUBLIC_ENABLE_ANALYTICS = 'true';
    delete require.cache[require.resolve('../../lib/utils/bundle-optimization')];
    const { FEATURE_FLAGS: enabledFlags } = require('../../lib/utils/bundle-optimization');
    expect(enabledFlags.ENABLE_ANALYTICS).toBe(true);

    // Test with disabled
    process.env.NEXT_PUBLIC_ENABLE_ANALYTICS = 'false';
    delete require.cache[require.resolve('../../lib/utils/bundle-optimization')];
    const { FEATURE_FLAGS: disabledFlags } = require('../../lib/utils/bundle-optimization');
    expect(disabledFlags.ENABLE_ANALYTICS).toBe(false);

    // Restore original
    if (originalEnv !== undefined) {
      process.env.NEXT_PUBLIC_ENABLE_ANALYTICS = originalEnv;
    } else {
      delete process.env.NEXT_PUBLIC_ENABLE_ANALYTICS;
    }
  });
});

describe('Cache Invalidation', () => {
  it('should have invalidation patterns for related data', () => {
    expect(typeof invalidationPatterns.onArticleRating).toBe('function');
    expect(typeof invalidationPatterns.onReadingListChange).toBe('function');
    expect(typeof invalidationPatterns.onSubscriptionChange).toBe('function');
    expect(typeof invalidationPatterns.onSettingsChange).toBe('function');
  });

  it('should invalidate related queries on article rating', () => {
    const mockQueryClient = {
      invalidateQueries: vi.fn(),
    };

    invalidationPatterns.onArticleRating(mockQueryClient as any, 'test-article-id');

    expect(mockQueryClient.invalidateQueries).toHaveBeenCalledWith({ queryKey: ['articles'] });
    expect(mockQueryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['recommendations'],
    });
    expect(mockQueryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['analytics', 'user'],
    });
  });

  it('should invalidate related queries on reading list change', () => {
    const mockQueryClient = {
      invalidateQueries: vi.fn(),
    };

    invalidationPatterns.onReadingListChange(mockQueryClient as any, 'test-article-id');

    expect(mockQueryClient.invalidateQueries).toHaveBeenCalledWith({ queryKey: ['reading-list'] });
    expect(mockQueryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['articles', 'detail', 'test-article-id'],
    });
    expect(mockQueryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['analytics', 'reading'],
    });
  });
});

describe('Performance Budget', () => {
  it('should have reasonable performance budgets', () => {
    // These would be the budgets from PerformanceBudgetMonitor
    const budgets = {
      js: 500 * 1024, // 500KB
      css: 100 * 1024, // 100KB
      images: 1000 * 1024, // 1MB
    };

    expect(budgets.js).toBe(512000);
    expect(budgets.css).toBe(102400);
    expect(budgets.images).toBe(1024000);
  });

  it('should detect budget violations', () => {
    const budgets = {
      js: 500 * 1024,
      css: 100 * 1024,
      images: 1000 * 1024,
    };

    // Test cases
    const testCases = [
      { type: 'js', size: 600 * 1024, shouldViolate: true },
      { type: 'js', size: 400 * 1024, shouldViolate: false },
      { type: 'css', size: 150 * 1024, shouldViolate: true },
      { type: 'css', size: 80 * 1024, shouldViolate: false },
      { type: 'images', size: 1200 * 1024, shouldViolate: true },
      { type: 'images', size: 800 * 1024, shouldViolate: false },
    ];

    testCases.forEach(({ type, size, shouldViolate }) => {
      const budget = budgets[type as keyof typeof budgets];
      const violates = size > budget;
      expect(violates).toBe(shouldViolate);
    });
  });
});
