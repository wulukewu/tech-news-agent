/**
 * Loading Indicators for Async Operations
 *
 * Provides various loading indicators for different async operations:
 * - Initial page load skeletons
 * - Infinite scroll spinners
 * - Component-specific loading states
 *
 * Requirements: 12.3, 12.4, 19.3
 */

'use client';

import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ArticleGridSkeleton,
  FeedListSkeleton,
  ReadingListSkeleton,
  NavigationSkeleton,
} from '@/components/LoadingSkeleton';

interface LoadingIndicatorProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

/**
 * Spinner for infinite scroll loading
 * Shows at bottom of lists when loading more content
 * Requirements: 12.4, 19.3
 */
export function InfiniteScrollSpinner({
  className,
  size = 'md',
  text = 'Loading more...',
}: LoadingIndicatorProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <div
      className={cn('flex flex-col items-center justify-center gap-2 py-8', className)}
      role="status"
      aria-live="polite"
      aria-label="Loading more content"
    >
      <Loader2 className={cn('animate-spin text-primary', sizeClasses[size])} aria-hidden="true" />
      {text && <p className="text-sm text-muted-foreground">{text}</p>}
    </div>
  );
}

/**
 * Component-specific loading overlay
 * Shows loading state for specific components during updates
 * Requirements: 12.4
 */
export function ComponentLoadingOverlay({
  className,
  size = 'md',
  text = 'Updating...',
}: LoadingIndicatorProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <div
      className={cn(
        'absolute inset-0 flex items-center justify-center',
        'bg-background/80 backdrop-blur-sm rounded-lg z-10',
        className
      )}
      role="status"
      aria-live="polite"
      aria-label="Component updating"
    >
      <div className="flex flex-col items-center gap-2">
        <Loader2
          className={cn('animate-spin text-primary', sizeClasses[size])}
          aria-hidden="true"
        />
        {text && <p className="text-sm text-muted-foreground">{text}</p>}
      </div>
    </div>
  );
}

/**
 * Initial page load skeleton
 * Shows skeleton matching expected content layout
 * Requirements: 12.3
 */
export function InitialPageSkeleton({
  type = 'dashboard',
  showNavigation = true,
}: {
  type?: 'dashboard' | 'reading-list' | 'subscriptions';
  showNavigation?: boolean;
}) {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation skeleton */}
      {showNavigation && <NavigationSkeleton />}

      {/* Main content skeleton */}
      <main className="container mx-auto px-4 py-6">
        {type === 'dashboard' && (
          <div className="space-y-6">
            {/* Search and filters skeleton */}
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="h-10 bg-muted animate-pulse rounded-md" />
              </div>
              <div className="flex gap-2">
                <div className="h-10 w-20 bg-muted animate-pulse rounded-md" />
                <div className="h-10 w-24 bg-muted animate-pulse rounded-md" />
                <div className="h-10 w-20 bg-muted animate-pulse rounded-md" />
              </div>
            </div>

            {/* Article grid skeleton */}
            <ArticleGridSkeleton count={9} />
          </div>
        )}

        {type === 'reading-list' && <ReadingListSkeleton count={8} />}

        {type === 'subscriptions' && (
          <div className="space-y-6">
            {/* Search and bulk actions skeleton */}
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="h-10 bg-muted animate-pulse rounded-md" />
              </div>
              <div className="flex gap-2">
                <div className="h-10 w-32 bg-muted animate-pulse rounded-md" />
                <div className="h-10 w-28 bg-muted animate-pulse rounded-md" />
              </div>
            </div>

            {/* Feed categories skeleton */}
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="space-y-3">
                  {/* Category header */}
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 bg-muted animate-pulse rounded" />
                    <div className="h-6 w-32 bg-muted animate-pulse rounded" />
                  </div>
                  {/* Category feeds */}
                  <FeedListSkeleton count={4} />
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

/**
 * Button loading state
 * Shows loading spinner inside buttons during async operations
 * Requirements: 12.4
 */
export function ButtonLoadingSpinner({
  size = 'sm',
  className,
}: {
  size?: 'sm' | 'md';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
  };

  return (
    <Loader2 className={cn('animate-spin', sizeClasses[size], className)} aria-hidden="true" />
  );
}

/**
 * Card loading overlay
 * Shows loading state over individual cards during updates
 * Requirements: 12.4
 */
export function CardLoadingOverlay({
  isLoading,
  children,
  className,
}: {
  isLoading: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('relative', className)}>
      {children}
      {isLoading && <ComponentLoadingOverlay size="sm" text="Updating..." />}
    </div>
  );
}

/**
 * List loading state
 * Shows when entire lists are being refreshed
 * Requirements: 12.3, 12.4
 */
export function ListLoadingState({
  type = 'articles',
  count = 5,
}: {
  type?: 'articles' | 'feeds' | 'reading-list';
  count?: number;
}) {
  if (type === 'articles') {
    return <ArticleGridSkeleton count={count} />;
  }

  if (type === 'feeds') {
    return <FeedListSkeleton count={count} />;
  }

  if (type === 'reading-list') {
    return <ReadingListSkeleton count={count} />;
  }

  return null;
}
