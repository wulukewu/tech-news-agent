'use client';

import * as React from 'react';
// Temporarily disabled react-window imports to fix SSR build issues
// import { FixedSizeList as List, VariableSizeList } from 'react-window';
// import InfiniteLoader from 'react-window-infinite-loader';
import { cn } from '@/lib/utils';
import { LoadingSpinner } from './loading-spinner';

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

/**
 * VirtualizedListClient - Client-side only virtualized list component
 * This component uses react-window which requires browser APIs
 * TEMPORARILY DISABLED: react-window imports removed to fix SSR build issues
 */
export function VirtualizedListClient<T>({
  items,
  itemHeight,
  renderItem,
  height = 600,
  width = '100%',
  overscan = 5,
  className,
  onScroll,
  hasNextPage = false,
  isNextPageLoading = false,
  loadNextPage,
  threshold = 15,
}: VirtualizedListProps<T>) {
  // Temporary fallback implementation
  return (
    <div className={cn('space-y-2', className)} style={{ height, width }}>
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
