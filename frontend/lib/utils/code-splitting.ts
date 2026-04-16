/**
 * Code Splitting Utilities
 * Requirements: 12.4, 12.5
 *
 * This module provides utilities for intelligent code splitting at both
 * route and component levels to optimize bundle size and loading performance.
 */

import { lazy, ComponentType, LazyExoticComponent } from 'react';
import { QueryClient } from '@tanstack/react-query';

/**
 * Options for lazy loading components
 */
interface LazyLoadOptions {
  /**
   * Delay before showing loading fallback (prevents flash for fast loads)
   */
  delay?: number;

  /**
   * Timeout for loading the component
   */
  timeout?: number;

  /**
   * Prefetch the component on hover/focus
   */
  prefetch?: boolean;

  /**
   * Preload data when component is loaded
   */
  preloadData?: (queryClient: QueryClient) => Promise<void>;
}

/**
 * Enhanced lazy loading with prefetching and error boundaries
 */
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): LazyExoticComponent<T> {
  const { delay = 200, timeout = 10000, prefetch = false } = options;

  // Create the lazy component
  const LazyComponent = lazy(() => {
    const startTime = performance.now();

    // Add timeout to prevent hanging
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Component loading timed out after ${timeout}ms`));
      }, timeout);
    });

    return Promise.race([
      importFn().then((module) => {
        const loadTime = performance.now() - startTime;

        // Log slow loading components in development
        if (process.env.NODE_ENV === 'development' && loadTime > 1000) {
          console.warn(`Slow component loading: ${loadTime.toFixed(0)}ms`);
        }

        return module;
      }),
      timeoutPromise,
    ]);
  });

  // Add prefetch capability
  if (prefetch && typeof window !== 'undefined') {
    // Prefetch on mouse enter or focus
    const prefetchComponent = () => {
      importFn().catch((error) => {
        console.warn('Failed to prefetch component:', error);
      });
    };

    // Store prefetch function on the component for external use
    (LazyComponent as any).prefetch = prefetchComponent;
  }

  return LazyComponent;
}

/**
 * Route-level code splitting with data prefetching
 *
 * Note: Next.js automatically handles code splitting for pages in the app directory.
 * This section is kept for reference but should not be used for page components
 * that export metadata, as they must remain server components.
 *
 * For client-side route prefetching, use Next.js Link component with prefetch prop.
 */
export const routeComponents = {
  // Removed page-level lazy loading as Next.js handles this automatically
  // and page components with metadata exports must be server components
};

/**
 * Feature-level code splitting for heavy components
 */
export const featureComponents = {
  // AI Analysis Modal - heavy component with ML dependencies
  AnalysisModal: createLazyComponent(
    () => import('../../features/ai-analysis/components/AnalysisModal'),
    {
      prefetch: true,
      timeout: 15000, // Longer timeout for heavy component
    }
  ),

  // The following components are not yet implemented and are commented out
  // to prevent build errors. Uncomment when the components are created.

  // Chart components - heavy visualization library
  // ChartComponents: createLazyComponent(() => import('../../components/charts'), {
  //   prefetch: false,
  //   timeout: 10000,
  // }),

  // Advanced search with complex filtering
  // AdvancedSearch: createLazyComponent(
  //   () => import('../../features/search/components/AdvancedSearch'),
  //   { prefetch: false }
  // ),

  // Data export functionality
  // DataExport: createLazyComponent(() => import('../../features/export/components/DataExport'), {
  //   prefetch: false,
  // }),

  // Rich text editor for notes
  // RichTextEditor: createLazyComponent(() => import('../../components/editor/RichTextEditor'), {
  //   prefetch: false,
  // }),
};

/**
 * Bundle analysis utilities
 */
export class BundleAnalyzer {
  private static loadTimes: Map<string, number> = new Map();

  /**
   * Track component load times
   */
  static trackLoadTime(componentName: string, loadTime: number) {
    this.loadTimes.set(componentName, loadTime);

    // Report to analytics in production
    if (process.env.NODE_ENV === 'production') {
      // This would integrate with your analytics service
      console.log(`Component ${componentName} loaded in ${loadTime}ms`);
    }
  }

  /**
   * Get performance report
   */
  static getPerformanceReport() {
    const report = Array.from(this.loadTimes.entries())
      .map(([name, time]) => ({ name, time }))
      .sort((a, b) => b.time - a.time);

    return {
      slowestComponents: report.slice(0, 5),
      averageLoadTime: report.reduce((sum, item) => sum + item.time, 0) / report.length,
      totalComponents: report.length,
    };
  }
}

/**
 * Preload critical components
 */
export function preloadCriticalComponents() {
  if (typeof window === 'undefined') return;

  // Preload feature components likely to be used soon
  // Note: Page-level prefetching is handled by Next.js Link component
  const criticalComponents = [featureComponents.AnalysisModal];

  criticalComponents.forEach((component) => {
    if ((component as any).prefetch) {
      (component as any).prefetch();
    }
  });
}

/**
 * Dynamic import with retry logic
 */
export async function dynamicImport<T>(
  importFn: () => Promise<T>,
  retries = 3,
  delay = 1000
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i < retries; i++) {
    try {
      return await importFn();
    } catch (error) {
      lastError = error as Error;

      // Don't retry on certain errors
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        // Network error, wait and retry
        await new Promise((resolve) => setTimeout(resolve, delay * (i + 1)));
      } else {
        // Other errors, don't retry
        throw error;
      }
    }
  }

  throw lastError!;
}

/**
 * Webpack chunk loading optimization
 */
export function optimizeChunkLoading() {
  if (typeof window === 'undefined') return;

  // Prefetch webpack chunks based on user behavior
  const prefetchChunk = (chunkName: string) => {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = `/_next/static/chunks/${chunkName}`;
    document.head.appendChild(link);
  };

  // Only prefetch chunks if user is authenticated
  // This prevents unnecessary 404 errors on login page
  const hasToken = typeof window !== 'undefined' && localStorage.getItem('auth_token');

  if (hasToken) {
    // Prefetch chunks on idle
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        // Note: App Router uses different chunk structure than Pages Router
        // These prefetch attempts may not work as expected with App Router
        // Consider removing or updating to match App Router structure
        // prefetchChunk('pages/recommendations');
        // prefetchChunk('pages/subscriptions');
      });
    }
  }
}

/**
 * Component-level splitting for large feature modules
 */
export function createFeatureModule<T extends Record<string, ComponentType<any>>>(
  components: T,
  moduleName: string
): { [K in keyof T]: LazyExoticComponent<T[K]> } {
  const lazyComponents = {} as { [K in keyof T]: LazyExoticComponent<T[K]> };

  Object.entries(components).forEach(([name, component]) => {
    lazyComponents[name as keyof T] = createLazyComponent(
      () => Promise.resolve({ default: component as any }),
      {
        prefetch: false,
        timeout: 5000,
      }
    );
  });

  // Track module usage
  if (process.env.NODE_ENV === 'development') {
    console.log(
      `Created lazy module: ${moduleName} with ${Object.keys(components).length} components`
    );
  }

  return lazyComponents;
}

/**
 * Tree shaking utilities
 */
export const treeShakingHelpers = {
  /**
   * Mark functions for tree shaking
   */
  markForTreeShaking: <T extends (...args: any[]) => any>(fn: T, condition: boolean) => {
    return condition ? fn : undefined;
  },

  /**
   * Conditional imports for tree shaking
   */
  conditionalImport: async <T>(
    condition: boolean,
    importFn: () => Promise<T>
  ): Promise<T | null> => {
    return condition ? await importFn() : null;
  },

  /**
   * Dead code elimination helper
   */
  eliminateDeadCode: (code: () => any, isUsed: boolean) => {
    return isUsed ? code() : undefined;
  },
};

/**
 * Initialize code splitting optimizations
 */
export function initializeCodeSplitting() {
  if (typeof window === 'undefined') return;

  // Preload critical components
  preloadCriticalComponents();

  // Optimize chunk loading
  optimizeChunkLoading();

  // Setup performance monitoring
  const observer = new PerformanceObserver((list) => {
    list.getEntries().forEach((entry) => {
      if (entry.entryType === 'navigation') {
        const navEntry = entry as PerformanceNavigationTiming;
        console.log('Page load performance:', {
          domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
          loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
        });
      }
    });
  });

  observer.observe({ entryTypes: ['navigation'] });
}
