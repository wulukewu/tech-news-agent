/**
 * Bundle Size Optimization and Tree Shaking Utilities
 * Requirements: 12.6
 *
 * This module provides utilities for optimizing bundle size through
 * intelligent tree shaking, dead code elimination, and dynamic imports.
 */

/**
 * Feature flags for conditional code inclusion
 */
export const FEATURE_FLAGS = {
  ENABLE_ANALYTICS: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
  ENABLE_ADVANCED_SEARCH: process.env.NEXT_PUBLIC_ENABLE_ADVANCED_SEARCH === 'true',
  ENABLE_SOCIAL_SHARING: process.env.NEXT_PUBLIC_ENABLE_SOCIAL_SHARING === 'true',
  ENABLE_EXPORT_FEATURES: process.env.NEXT_PUBLIC_ENABLE_EXPORT_FEATURES === 'true',
  ENABLE_COLLABORATION: process.env.NEXT_PUBLIC_ENABLE_COLLABORATION === 'true',
  ENABLE_NOTIFICATIONS: process.env.NEXT_PUBLIC_ENABLE_NOTIFICATIONS === 'true',
} as const;

/**
 * Conditional import helper for tree shaking
 */
export async function conditionalImport<T>(
  condition: boolean,
  importFn: () => Promise<{ default: T }>
): Promise<T | null> {
  if (!condition) {
    return null;
  }

  try {
    const loadedModule = await importFn();
    return loadedModule.default;
  } catch (error) {
    console.warn('Failed to load conditional module:', error);
    return null;
  }
}

/**
 * Tree-shakable utility functions
 */
export const TreeShakableUtils = {
  // Analytics utilities (only included if analytics is enabled)
  analytics: FEATURE_FLAGS.ENABLE_ANALYTICS
    ? {
        track: (event: string, properties?: Record<string, any>) => {
          // Analytics implementation
          console.log('Analytics:', event, properties);
        },

        identify: (userId: string, traits?: Record<string, any>) => {
          // User identification
          console.log('Identify:', userId, traits);
        },

        page: (name: string, properties?: Record<string, any>) => {
          // Page tracking
          console.log('Page:', name, properties);
        },
      }
    : undefined,

  // Social sharing utilities
  socialSharing: FEATURE_FLAGS.ENABLE_SOCIAL_SHARING
    ? {
        shareToTwitter: (text: string, url: string) => {
          const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
            text
          )}&url=${encodeURIComponent(url)}`;
          window.open(twitterUrl, '_blank', 'width=550,height=420');
        },

        shareToLinkedIn: (title: string, url: string) => {
          const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(
            url
          )}`;
          window.open(linkedInUrl, '_blank', 'width=550,height=420');
        },

        shareToReddit: (title: string, url: string) => {
          const redditUrl = `https://reddit.com/submit?title=${encodeURIComponent(
            title
          )}&url=${encodeURIComponent(url)}`;
          window.open(redditUrl, '_blank', 'width=550,height=420');
        },
      }
    : undefined,

  // Export utilities
  exportUtils: FEATURE_FLAGS.ENABLE_EXPORT_FEATURES
    ? {
        exportToJSON: (data: any, filename: string) => {
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          a.click();
          URL.revokeObjectURL(url);
        },

        exportToCSV: (data: any[], filename: string) => {
          if (data.length === 0) return;

          const headers = Object.keys(data[0]);
          const csvContent = [
            headers.join(','),
            ...data.map((row) => headers.map((header) => `"${row[header] || ''}"`).join(',')),
          ].join('\n');

          const blob = new Blob([csvContent], { type: 'text/csv' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          a.click();
          URL.revokeObjectURL(url);
        },
      }
    : undefined,

  // Notification utilities
  notifications: FEATURE_FLAGS.ENABLE_NOTIFICATIONS
    ? {
        requestPermission: async (): Promise<boolean> => {
          if (!('Notification' in window)) return false;

          const permission = await Notification.requestPermission();
          return permission === 'granted';
        },

        showNotification: (title: string, options?: NotificationOptions) => {
          if (Notification.permission === 'granted') {
            new Notification(title, options);
          }
        },
      }
    : undefined,
};

/**
 * Dynamic component loader with tree shaking
 */
export class DynamicComponentLoader {
  private static loadedComponents = new Map<string, any>();

  /**
   * Load component dynamically with caching
   */
  static async loadComponent<T>(
    name: string,
    importFn: () => Promise<{ default: T }>,
    condition: boolean = true
  ): Promise<T | null> {
    if (!condition) {
      return null;
    }

    // Check cache first
    if (this.loadedComponents.has(name)) {
      return this.loadedComponents.get(name);
    }

    try {
      const loadedModule = await importFn();
      const component = loadedModule.default;

      // Cache the component
      this.loadedComponents.set(name, component);

      return component;
    } catch (error) {
      console.warn(`Failed to load component ${name}:`, error);
      return null;
    }
  }

  /**
   * Preload components that might be needed
   */
  static async preloadComponents(
    components: Array<{
      name: string;
      importFn: () => Promise<any>;
      condition?: boolean;
    }>
  ) {
    const promises = components
      .filter(({ condition = true }) => condition)
      .map(({ name, importFn }) =>
        this.loadComponent(name, importFn).catch((error) =>
          console.warn(`Failed to preload ${name}:`, error)
        )
      );

    await Promise.allSettled(promises);
  }

  /**
   * Clear component cache
   */
  static clearCache() {
    this.loadedComponents.clear();
  }

  /**
   * Get cache statistics
   */
  static getCacheStats() {
    return {
      cachedComponents: this.loadedComponents.size,
      componentNames: Array.from(this.loadedComponents.keys()),
    };
  }
}

/**
 * Bundle analyzer for runtime optimization
 */
export class BundleAnalyzer {
  private static chunkLoadTimes = new Map<string, number>();
  private static componentSizes = new Map<string, number>();

  /**
   * Track chunk load time
   */
  static trackChunkLoad(chunkName: string, loadTime: number) {
    this.chunkLoadTimes.set(chunkName, loadTime);

    // Report slow chunks in development
    if (process.env.NODE_ENV === 'development' && loadTime > 1000) {
      console.warn(`Slow chunk loading: ${chunkName} took ${loadTime}ms`);
    }
  }

  /**
   * Estimate component size
   */
  static estimateComponentSize(componentName: string, component: any) {
    try {
      const size = JSON.stringify(component).length;
      this.componentSizes.set(componentName, size);
      return size;
    } catch {
      return 0;
    }
  }

  /**
   * Get bundle analysis report
   */
  static getAnalysisReport() {
    const slowChunks = Array.from(this.chunkLoadTimes.entries())
      .filter(([, time]) => time > 1000)
      .sort(([, a], [, b]) => b - a);

    const largeComponents = Array.from(this.componentSizes.entries())
      .filter(([, size]) => size > 10000) // > 10KB
      .sort(([, a], [, b]) => b - a);

    return {
      totalChunks: this.chunkLoadTimes.size,
      slowChunks: slowChunks.slice(0, 5),
      averageChunkLoadTime:
        Array.from(this.chunkLoadTimes.values()).reduce((sum, time) => sum + time, 0) /
          this.chunkLoadTimes.size || 0,
      largeComponents: largeComponents.slice(0, 5),
      totalComponentSize: Array.from(this.componentSizes.values()).reduce(
        (sum, size) => sum + size,
        0
      ),
    };
  }

  /**
   * Optimize bundle based on usage patterns
   */
  static optimizeBundle() {
    const report = this.getAnalysisReport();

    // Log optimization suggestions
    if (process.env.NODE_ENV === 'development') {
      console.group('📦 Bundle Optimization Report');

      if (report.slowChunks.length > 0) {
        console.warn('Slow loading chunks:', report.slowChunks);
      }

      if (report.largeComponents.length > 0) {
        console.warn('Large components:', report.largeComponents);
      }

      console.log(`Average chunk load time: ${report.averageChunkLoadTime.toFixed(0)}ms`);
      console.log(`Total component size: ${(report.totalComponentSize / 1024).toFixed(1)}KB`);

      console.groupEnd();
    }

    return report;
  }
}

/**
 * Dead code elimination helper
 */
export function eliminateDeadCode<T>(code: () => T, condition: boolean): T | undefined {
  return condition ? code() : undefined;
}

/**
 * Conditional feature wrapper
 */
export function withFeature<T>(feature: keyof typeof FEATURE_FLAGS, component: T): T | null {
  return FEATURE_FLAGS[feature] ? component : null;
}

/**
 * Lazy load utilities with tree shaking
 */
export const LazyLoadUtils = {
  // Analytics components
  AnalyticsChart: FEATURE_FLAGS.ENABLE_ANALYTICS
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  AnalyticsDashboard: FEATURE_FLAGS.ENABLE_ANALYTICS
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  // Advanced search
  AdvancedSearchModal: FEATURE_FLAGS.ENABLE_ADVANCED_SEARCH
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  SearchFilters: FEATURE_FLAGS.ENABLE_ADVANCED_SEARCH
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  // Social sharing
  SocialShareButtons: FEATURE_FLAGS.ENABLE_SOCIAL_SHARING
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  ShareModal: FEATURE_FLAGS.ENABLE_SOCIAL_SHARING
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  // Export features
  DataExportModal: FEATURE_FLAGS.ENABLE_EXPORT_FEATURES
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  ExportProgress: FEATURE_FLAGS.ENABLE_EXPORT_FEATURES
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  // Collaboration features
  CollaborationPanel: FEATURE_FLAGS.ENABLE_COLLABORATION
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,

  UserProfile: FEATURE_FLAGS.ENABLE_COLLABORATION
    ? () => Promise.resolve({ default: () => null }) // Placeholder for non-existent component
    : null,
};

/**
 * Initialize bundle optimization
 */
export function initializeBundleOptimization() {
  if (typeof window === 'undefined') return;

  // Track webpack chunk loading
  const originalChunkLoad = (window as any).__webpack_require__;
  if (originalChunkLoad) {
    (window as any).__webpack_require__ = function (chunkId: string) {
      const startTime = performance.now();
      const result = originalChunkLoad.call(this, chunkId);
      const loadTime = performance.now() - startTime;

      BundleAnalyzer.trackChunkLoad(chunkId, loadTime);

      return result;
    };
  }

  // Periodic bundle analysis in development
  if (process.env.NODE_ENV === 'development') {
    setInterval(() => {
      BundleAnalyzer.optimizeBundle();
    }, 60 * 1000); // Every minute
  }

  // Preload critical components based on feature flags
  // Note: Only preload components that actually exist
  const criticalComponents = [
    // Analytics chart component not yet implemented
    // FEATURE_FLAGS.ENABLE_ANALYTICS && {
    //   name: 'AnalyticsChart',
    //   importFn: () => import('../../components/charts/AnalyticsChart'),
    // },
    // Social share buttons not yet implemented
    // FEATURE_FLAGS.ENABLE_SOCIAL_SHARING && {
    //   name: 'SocialShareButtons',
    //   importFn: () => import('../../components/social/SocialShareButtons'),
    // },
  ].filter(Boolean) as Array<{ name: string; importFn: () => Promise<any> }>;

  if (criticalComponents.length > 0) {
    DynamicComponentLoader.preloadComponents(criticalComponents);
  }
}
