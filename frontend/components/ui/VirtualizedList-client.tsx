'use client';

import { useRef, useMemo, useCallback, useEffect, useImperativeHandle, forwardRef } from 'react';
// Temporarily disabled react-window imports to fix SSR build issues
// import { FixedSizeList as List, VariableSizeList } from 'react-window';
import { cn } from '@/lib/utils';

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

// Item renderer for fixed size list
const FixedSizeItemRenderer = ({ index, style, data }: any) => {
  const { items, renderItem, itemData } = data;
  const item = items[index];
  return <div style={style}>{renderItem({ index, style: {}, data: item, itemData })}</div>;
};

// Item renderer for variable size list
const VariableSizeItemRenderer = ({ index, style, data, isScrolling }: any) => {
  const { items, renderItem, itemData } = data;
  const item = items[index];
  return (
    <div style={style}>{renderItem({ index, style: {}, data: item, isScrolling, itemData })}</div>
  );
};

/**
 * VirtualizedListClient Component - Client-side only implementation
 * TEMPORARILY DISABLED: react-window imports removed to fix SSR build issues
 */
export const VirtualizedListClient = forwardRef<any, VirtualizedListProps<any>>(
  function VirtualizedListClient<T>(
    {
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
    }: VirtualizedListProps<T>,
    ref: React.Ref<any>
  ) {
    // Temporary fallback implementation
    return (
      <div className={cn('virtualized-list space-y-2', className)} style={{ height, width }}>
        <div className="text-center text-muted-foreground p-4">
          Virtual scrolling temporarily disabled for SSR compatibility
        </div>
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
);
