'use client';
import { logger } from '@/lib/utils/logger';

import * as React from 'react';
import { cn } from '@/lib/utils';

// Dynamic import for SSR safety
const VirtualizedListClient = React.lazy(() =>
  import('./VirtualizedList-client').then((module) => ({ default: module.VirtualizedListClient }))
) as React.ComponentType<VirtualizedListProps<any>>;

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number | ((index: number) => number);
  renderItem: (props: { index: number; style: React.CSSProperties; data: T }) => React.ReactNode;
  height?: number;
  width?: string | number;
  overscan?: number;
  className?: string;
  onScroll?: (props: {
    scrollDirection: 'forward' | 'backward';
    scrollOffset: number;
    scrollUpdateWasRequested: boolean;
  }) => void;
  onItemsRendered?: (props: {
    overscanStartIndex: number;
    overscanStopIndex: number;
    visibleStartIndex: number;
    visibleStopIndex: number;
  }) => void;
  scrollToIndex?: number;
  scrollToAlignment?: 'auto' | 'smart' | 'center' | 'end' | 'start';
  initialScrollOffset?: number;
  useIsScrolling?: boolean;
  itemData?: any;
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
 * VirtualizedList Component - SSR-safe wrapper
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

/**
 * Hook for virtualized list performance monitoring
 */
export function useVirtualizedListPerformance(itemCount: number) {
  const renderCount = React.useRef(0);
  const lastRenderTime = React.useRef(0);

  React.useEffect(() => {
    renderCount.current += 1;
    const now = performance.now();

    if (lastRenderTime.current > 0) {
      const timeDiff = now - lastRenderTime.current;
      if (timeDiff > 16.67) {
        // More than one frame
        logger.warn(`VirtualizedList render took ${timeDiff.toFixed(2)}ms for ${itemCount} items`);
      }
    }

    lastRenderTime.current = now;
  });

  return {
    renderCount: renderCount.current,
    lastRenderTime: lastRenderTime.current,
  };
}

/**
 * Optimized article list component using virtualization
 */
export function VirtualizedArticleList<T>({
  articles,
  itemHeight,
  renderArticle,
  ...props
}: Omit<VirtualizedListProps<T>, 'items' | 'renderItem'> & {
  articles: T[];
  renderArticle: (article: T, index: number) => React.ReactNode;
}) {
  const renderItem = React.useCallback(
    ({ index, style, data }: { index: number; style: React.CSSProperties; data: T }) => (
      <div style={style}>{renderArticle(data, index)}</div>
    ),
    [renderArticle]
  );

  return (
    <VirtualizedList items={articles} renderItem={renderItem} itemHeight={itemHeight} {...props} />
  );
}
