/**
 * Virtualized List Component for Performance Optimization
 * Requirements: 12.2
 *
 * This component provides efficient rendering of large lists by only
 * rendering visible items, significantly improving performance.
 */

'use client';

import { FixedSizeList as List, VariableSizeList } from 'react-window';
import { forwardRef, useMemo, useCallback, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

/**
 * Props for VirtualizedList component
 */
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

/**
 * Item renderer wrapper for fixed size list
 */
const FixedSizeItemRenderer = <T,>({
  index,
  style,
  data,
  isScrolling,
}: {
  index: number;
  style: React.CSSProperties;
  data: {
    items: T[];
    renderItem: VirtualizedListProps<T>['renderItem'];
    itemData?: any;
  };
  isScrolling?: boolean;
}) => {
  const { items, renderItem, itemData } = data;
  const item = items[index];

  if (!item) {
    return (
      <div style={style} className="flex items-center justify-center text-gray-400">
        Loading...
      </div>
    );
  }

  return <div style={style}>{renderItem({ index, style: {}, data: item, isScrolling })}</div>;
};

/**
 * Item renderer wrapper for variable size list
 */
const VariableSizeItemRenderer = <T,>({
  index,
  style,
  data,
  isScrolling,
}: {
  index: number;
  style: React.CSSProperties;
  data: {
    items: T[];
    renderItem: VirtualizedListProps<T>['renderItem'];
    itemData?: any;
  };
  isScrolling?: boolean;
}) => {
  const { items, renderItem, itemData } = data;
  const item = items[index];

  if (!item) {
    return (
      <div style={style} className="flex items-center justify-center text-gray-400">
        Loading...
      </div>
    );
  }

  return <div style={style}>{renderItem({ index, style: {}, data: item, isScrolling })}</div>;
};

/**
 * VirtualizedList Component
 */
export function VirtualizedList<T>({
  items,
  itemHeight,
  renderItem,
  height = 400,
  width = '100%',
  overscan = 5,
  className,
  onScroll,
  onItemsRendered,
  scrollToIndex,
  scrollToAlignment = 'auto',
  initialScrollOffset = 0,
  useIsScrolling = false,
  itemData,
}: VirtualizedListProps<T>) {
  const listRef = useRef<any>(null);

  // Determine if we need variable or fixed size list
  const isVariableSize = typeof itemHeight === 'function';

  // Memoize item data to prevent unnecessary re-renders
  const memoizedItemData = useMemo(
    () => ({
      items,
      renderItem,
      itemData,
    }),
    [items, renderItem, itemData]
  );

  // Handle scroll to index
  useEffect(() => {
    if (scrollToIndex !== undefined && listRef.current) {
      listRef.current.scrollToItem(scrollToIndex, scrollToAlignment);
    }
  }, [scrollToIndex, scrollToAlignment]);

  // Performance monitoring
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      const startTime = performance.now();

      return () => {
        const renderTime = performance.now() - startTime;
        if (renderTime > 16) {
          // More than one frame
          console.warn(
            `VirtualizedList render took ${renderTime.toFixed(2)}ms for ${items.length} items`
          );
        }
      };
    }
  }, [items.length]);

  // Scroll handler with performance optimization
  const handleScroll = useCallback(
    (props: any) => {
      // Throttle scroll events for performance
      if (onScroll) {
        requestAnimationFrame(() => {
          onScroll(props);
        });
      }
    },
    [onScroll]
  );

  // Items rendered handler
  const handleItemsRendered = useCallback(
    (props: any) => {
      if (onItemsRendered) {
        onItemsRendered(props);
      }

      // Performance monitoring in development
      if (process.env.NODE_ENV === 'development') {
        const visibleCount = props.visibleStopIndex - props.visibleStartIndex + 1;
        const overscanCount = props.overscanStopIndex - props.overscanStartIndex + 1;

        console.log(
          `VirtualizedList: ${visibleCount} visible, ${overscanCount} total rendered out of ${items.length} items`
        );
      }
    },
    [onItemsRendered, items.length]
  );

  // Empty state
  if (items.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 rounded-lg',
          className
        )}
        style={{ height, width }}
      >
        <div className="text-center">
          <div className="text-lg font-medium">No items to display</div>
          <div className="text-sm text-gray-400 mt-1">The list is empty</div>
        </div>
      </div>
    );
  }

  // Render variable size list
  if (isVariableSize) {
    return (
      <div className={cn('virtualized-list', className)}>
        <VariableSizeList
          ref={listRef}
          height={height}
          width={width}
          itemCount={items.length}
          itemSize={itemHeight as (index: number) => number}
          itemData={memoizedItemData as any}
          overscanCount={overscan}
          onScroll={handleScroll}
          onItemsRendered={handleItemsRendered}
          initialScrollOffset={initialScrollOffset}
          useIsScrolling={useIsScrolling}
        >
          {VariableSizeItemRenderer as any}
        </VariableSizeList>
      </div>
    );
  }

  // Render fixed size list
  return (
    <div className={cn('virtualized-list', className)}>
      <List
        ref={listRef}
        height={height}
        width={width}
        itemCount={items.length}
        itemSize={itemHeight as number}
        itemData={memoizedItemData as any}
        overscanCount={overscan}
        onScroll={handleScroll}
        onItemsRendered={handleItemsRendered}
        initialScrollOffset={initialScrollOffset}
        useIsScrolling={useIsScrolling}
      >
        {FixedSizeItemRenderer as any}
      </List>
    </div>
  );
}

/**
 * Specialized virtualized list for articles
 */
export function VirtualizedArticleList<T extends { id: string; title: string }>({
  articles,
  renderArticle,
  ...props
}: Omit<VirtualizedListProps<T>, 'items' | 'renderItem'> & {
  articles: T[];
  renderArticle: (article: T, index: number) => React.ReactNode;
}) {
  const renderItem = useCallback(
    ({ index, style, data }: { index: number; style: React.CSSProperties; data: T }) => (
      <div style={style} key={data.id}>
        {renderArticle(data, index)}
      </div>
    ),
    [renderArticle]
  );

  return <VirtualizedList items={articles} renderItem={renderItem} {...props} />;
}

/**
 * Hook for virtualized list performance monitoring
 */
export function useVirtualizedListPerformance(itemCount: number) {
  const renderCount = useRef(0);
  const lastRenderTime = useRef(0);

  useEffect(() => {
    renderCount.current += 1;
    lastRenderTime.current = performance.now();
  });

  const getPerformanceStats = useCallback(
    () => ({
      renderCount: renderCount.current,
      lastRenderTime: lastRenderTime.current,
      itemCount,
      averageRenderTime: lastRenderTime.current / renderCount.current,
    }),
    [itemCount]
  );

  return { getPerformanceStats };
}
