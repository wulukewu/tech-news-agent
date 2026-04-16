/**
 * Code Splitting Utilities
 * Requirements: 12.4
 *
 * This module provides utilities for implementing code splitting at route and component levels.
 * It uses React.lazy() and Next.js dynamic imports for optimal bundle size management.
 */

'use client';

import dynamic from 'next/dynamic';
import { ComponentType, lazy, Suspense } from 'react';

/**
 * Loading component for lazy-loaded components
 */
export function LoadingFallback({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex items-center justify-center min-h-[200px]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}

/**
 * Skeleton loading component for better UX
 */
export function SkeletonFallback() {
  return (
    <div className="space-y-4 p-4">
      <div className="h-8 bg-muted animate-pulse rounded" />
      <div className="h-4 bg-muted animate-pulse rounded w-3/4" />
      <div className="h-4 bg-muted animate-pulse rounded w-1/2" />
    </div>
  );
}

/**
 * Wrapper for React.lazy with automatic Suspense boundary
 */
export function lazyWithSuspense<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  fallback: React.ReactNode = <LoadingFallback />
) {
  const LazyComponent = lazy(importFn);

  return function LazyComponentWithSuspense(props: React.ComponentProps<T>) {
    return (
      <Suspense fallback={fallback}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

/**
 * Next.js dynamic import with loading state
 */
export function dynamicWithLoading<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options?: {
    loading?: () => JSX.Element;
    ssr?: boolean;
  }
) {
  return dynamic(importFn, {
    loading: options?.loading,
    ssr: options?.ssr ?? true,
  });
}

/**
 * Route-level code splitting helper
 * Use this for entire page components
 */
export function createLazyRoute<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  pageName: string
) {
  return dynamicWithLoading(importFn, {
    loading: () => <LoadingFallback message={`Loading ${pageName}...`} />,
    ssr: true,
  });
}

/**
 * Component-level code splitting helper
 * Use this for heavy components that aren't immediately needed
 */
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options?: {
    fallback?: JSX.Element;
    ssr?: boolean;
  }
) {
  return dynamicWithLoading(importFn, {
    loading: options?.fallback ? () => options.fallback! : undefined,
    ssr: options?.ssr ?? false, // Components usually don't need SSR
  });
}

/**
 * Preload a lazy component
 * Call this when you know the user will need the component soon
 */
export function preloadComponent(importFn: () => Promise<any>) {
  // Trigger the import but don't wait for it
  importFn().catch((err) => {
    console.warn('Failed to preload component:', err);
  });
}

/**
 * Prefetch a route
 * Use this for likely navigation targets
 */
export function prefetchRoute(href: string) {
  if (typeof window !== 'undefined') {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = href;
    document.head.appendChild(link);
  }
}

/**
 * Bundle size monitoring utility
 */
export function logBundleSize(componentName: string, startTime: number) {
  if (process.env.NODE_ENV === 'development') {
    const loadTime = performance.now() - startTime;
    console.log(`[Code Splitting] ${componentName} loaded in ${loadTime.toFixed(2)}ms`);
  }
}
