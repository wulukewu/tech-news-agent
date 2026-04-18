'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// Dynamic import for SSR safety
const VirtualizedListClient = React.lazy(() =>
  import('./virtualized-list-client').then((module) => ({ default: module.VirtualizedListClient }))
) as React.ComponentType<VirtualizedListProps<any>>;

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number | ((index: number) => number);
  renderItem: (props: {
    index: number;
    style: React.CSSProperties;
    data: T;
    isScrolling?: boolean;
  }) => React.ReactNode;
  height?: number;
  width?: string | number;
  overscan?: number;
  className?: string;
  onScroll?: (props: {
    scrollDirection: 'forward' | 'backward';
    scrollOffset: number;
    scrollUpdateWasRequested: boolean;
  }) => void;
  // Infinite loading props
  hasNextPage?: boolean;
  isNextPageLoading?: boolean;
  loadNextPage?: () => Promise<void> | void;
  threshold?: number;
}

// SSR-safe fallback component
function VirtualizedListFallback<T>({
  items,
  renderItem,
  height,
  width,
  className,
}: Pick<VirtualizedListProps<T>, 'items' | 'renderItem' | 'height' | 'width' | 'className'>) {
  return (
    <div className={cn('space-y-2', className)} style={{ height, width }}>
      {items.slice(0, 10).map((item, index) => (
        <div key={index}>{renderItem({ index, style: {}, data: item })}</div>
      ))}
      {items.length > 10 && (
        <div className="text-center text-muted-foreground">
          ... and {items.length - 10} more items
        </div>
      )}
    </div>
  );
}

/**
 * VirtualizedList - High-performance virtualized list component
 * Supports both fixed and variable item heights, with infinite loading
 * SSR-safe with fallback rendering
 */
export function VirtualizedList<T>(props: VirtualizedListProps<T>) {
  const [isClient, setIsClient] = React.useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  // Show fallback during SSR and initial client render
  if (!isClient) {
    return <VirtualizedListFallback {...props} />;
  }

  // Show virtualized list on client
  return (
    <React.Suspense fallback={<VirtualizedListFallback {...props} />}>
      <VirtualizedListClient {...props} />
    </React.Suspense>
  );
}

// Re-export other components for compatibility
export * from './virtualized-list-client';
