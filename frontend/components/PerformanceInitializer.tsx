/**
 * Performance Initialization Component
 * Requirements: 12.1, 12.8, 12.9
 *
 * This component initializes all performance monitoring and optimization
 * features when the app loads.
 */

'use client';
import { logger } from '@/lib/utils/logger';

import { useEffect } from 'react';
import { initializePerformanceMonitoring } from '@/lib/utils/performance-monitoring';
import { initializeErrorTracking } from '@/lib/utils/error-tracking';
import { initializeBundleOptimization } from '@/lib/utils/bundle-optimization';
import { initializeCodeSplitting } from '@/lib/utils/code-splitting';

/**
 * Performance Initializer Component
 */
export function PerformanceInitializer() {
  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;

    let performanceMonitor: any = null;
    let errorTracker: any = null;

    const initializePerformanceFeatures = async () => {
      try {
        // Initialize performance monitoring
        performanceMonitor = initializePerformanceMonitoring();

        // Initialize error tracking
        errorTracker = initializeErrorTracking();

        // Initialize bundle optimization
        initializeBundleOptimization();

        // Initialize code splitting optimizations
        initializeCodeSplitting();

        // Log initialization in development
        if (process.env.NODE_ENV === 'development') {
          logger.debug('🚀 Performance optimizations initialized');
        }

        // Report initialization to analytics
        if (performanceMonitor) {
          // This would integrate with your analytics service
          logger.debug('📊 Performance monitoring active');
        }
      } catch (error) {
        console.error('Failed to initialize performance features:', error);

        // Report initialization failure
        if (errorTracker) {
          errorTracker.captureError(error, 'performance', 'high', ['initialization']);
        }
      }
    };

    // Initialize with a small delay to not block initial render
    const timeoutId = setTimeout(initializePerformanceFeatures, 100);

    // Cleanup function
    return () => {
      clearTimeout(timeoutId);

      if (performanceMonitor?.cleanup) {
        performanceMonitor.cleanup();
      }
    };
  }, []);

  // This component doesn't render anything
  return null;
}

/**
 * Service Worker Registration Component
 */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const registerServiceWorker = async () => {
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/',
          });

          // Handle service worker updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // New service worker is available
                  logger.debug('New service worker available');

                  // Optionally show update notification to user
                  if (window.confirm('A new version is available. Reload to update?')) {
                    window.location.reload();
                  }
                }
              });
            }
          });

          // Log successful registration
          if (process.env.NODE_ENV === 'development') {
            logger.debug('✅ Service Worker registered successfully');
          }
        } catch (error) {
          console.error('Service Worker registration failed:', error);
        }
      }
    };

    // Register service worker after page load
    if (document.readyState === 'complete') {
      registerServiceWorker();
    } else {
      window.addEventListener('load', registerServiceWorker);
    }
  }, []);

  return null;
}

/**
 * Critical Resource Preloader
 */
export function CriticalResourcePreloader() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const preloadCriticalResources = () => {
      // Helper function to check if resource exists before preloading
      const preloadIfExists = async (url: string, as: string, type?: string) => {
        try {
          const response = await fetch(url, { method: 'HEAD' });
          if (response.ok) {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = url;
            link.as = as;
            if (type) link.type = type;
            if (as === 'font') link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
          }
        } catch (error) {
          // Silently fail - resource doesn't exist
          if (process.env.NODE_ENV === 'development') {
            console.debug(`Skipping preload for missing resource: ${url}`);
          }
        }
      };

      // Only preload fonts if using Next.js font optimization
      // Comment out font preloads since we should use Next.js font optimization
      // const fontPreloads = ['/fonts/inter-var.woff2', '/fonts/inter-var-italic.woff2'];
      // fontPreloads.forEach((fontUrl) => preloadIfExists(fontUrl, 'font', 'font/woff2'));

      // Only preload images that exist
      // Comment out until icons are generated
      // const imagePreloads = ['/icons/icon-192x192.png', '/images/logo.svg'];
      // imagePreloads.forEach((imageUrl) => preloadIfExists(imageUrl, 'image'));

      // Only prefetch authenticated pages if user has a token
      // This prevents unnecessary API calls on the login page
      const hasToken = localStorage.getItem('auth_token');

      if (hasToken) {
        // Prefetch likely next pages with correct app paths
        const prefetchUrls = ['/app/articles', '/app/recommendations', '/app/reading-list'];

        prefetchUrls.forEach((url) => {
          const link = document.createElement('link');
          link.rel = 'prefetch';
          link.href = url;
          document.head.appendChild(link);
        });
      }
    };

    // Preload resources when idle
    if ('requestIdleCallback' in window) {
      requestIdleCallback(preloadCriticalResources);
    } else {
      setTimeout(preloadCriticalResources, 1000);
    }
  }, []);

  return null;
}

/**
 * Performance Budget Monitor
 */
export function PerformanceBudgetMonitor() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const monitorPerformanceBudget = () => {
      // Monitor bundle size
      if ('performance' in window && 'getEntriesByType' in performance) {
        const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

        let totalJSSize = 0;
        let totalCSSSize = 0;
        let totalImageSize = 0;

        resources.forEach((resource) => {
          const size = resource.transferSize || 0;

          if (resource.name.includes('.js')) {
            totalJSSize += size;
          } else if (resource.name.includes('.css')) {
            totalCSSSize += size;
          } else if (resource.name.match(/\.(jpg|jpeg|png|gif|webp|avif|svg)$/)) {
            totalImageSize += size;
          }
        });

        // Performance budget thresholds (in bytes)
        const budgets = {
          js: 500 * 1024, // 500KB
          css: 100 * 1024, // 100KB
          images: 1000 * 1024, // 1MB
        };

        // Check budget violations
        const violations = [];
        if (totalJSSize > budgets.js) {
          violations.push(
            `JavaScript: ${(totalJSSize / 1024).toFixed(0)}KB (budget: ${budgets.js / 1024}KB)`
          );
        }
        if (totalCSSSize > budgets.css) {
          violations.push(
            `CSS: ${(totalCSSSize / 1024).toFixed(0)}KB (budget: ${budgets.css / 1024}KB)`
          );
        }
        if (totalImageSize > budgets.images) {
          violations.push(
            `Images: ${(totalImageSize / 1024).toFixed(0)}KB (budget: ${budgets.images / 1024}KB)`
          );
        }

        if (violations.length > 0 && process.env.NODE_ENV === 'development') {
          logger.warn('⚠️ Performance budget violations:', violations);
        }

        // Log budget status in development
        if (process.env.NODE_ENV === 'development') {
          logger.debug('📊 Performance Budget Status:', {
            javascript: `${(totalJSSize / 1024).toFixed(0)}KB / ${budgets.js / 1024}KB`,
            css: `${(totalCSSSize / 1024).toFixed(0)}KB / ${budgets.css / 1024}KB`,
            images: `${(totalImageSize / 1024).toFixed(0)}KB / ${budgets.images / 1024}KB`,
          });
        }
      }
    };

    // Monitor budget after page load
    window.addEventListener('load', () => {
      setTimeout(monitorPerformanceBudget, 2000);
    });
  }, []);

  return null;
}

/**
 * Combined Performance Provider
 */
export function PerformanceProvider() {
  return (
    <>
      <PerformanceInitializer />
      <ServiceWorkerRegistration />
      <CriticalResourcePreloader />
      <PerformanceBudgetMonitor />
    </>
  );
}
