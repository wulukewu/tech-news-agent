'use client';

import * as React from 'react';
import { FixedSizeList as List, VariableSizeList } from 'react-window';
import InfiniteLoader from 'react-window-infinite-loader';
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
  onScroll?: (props: { scrollTop: number; scrollLeft: number }) => void;
  // Infinite loading props
  hasNextPage?: boolean;
  isNextPageLoading?: boolean;
  loadNextPage?: () => Promise<void> | void;
  threshold?: number;
}

/**
 * VirtualizedList - High-performance virtualized list component
 * Supports both fixed and variable item heights, with infinite loading
 */
export function VirtualizedList<T>({
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
  const listRef = React.useRef<any>(null);
  const isVariableHeight = typeof itemHeight === 'function';

  // For infinite loading, we need to know if an item is loaded
  const isItemLoaded = React.useCallback(
    (index: number) => {
      return !!items[index];
    },
    [items]
  );

  // Total item count including loading items
  const itemCount = hasNextPage ? items.length + 1 : items.length;

  // Item renderer that handles loading states
  const itemRenderer = React.useCallback(
    ({ index, style, isScrolling }: any) => {
      const isLoading = index >= items.length;

      if (isLoading) {
        return (
          <div style={style} className="flex items-center justify-center p-4">
            <LoadingSpinner size="sm" text="載入更多..." />
          </div>
        );
      }

      const item = items[index];
      return renderItem({ index, style, data: item, isScrolling });
    },
    [items, renderItem]
  );

  // Handle scroll events
  const handleScroll = React.useCallback(
    (props: any) => {
      onScroll?.(props);
    },
    [onScroll]
  );

  // Scroll to specific item
  const scrollToItem = React.useCallback(
    (index: number, align: 'auto' | 'smart' | 'center' | 'end' | 'start' = 'auto') => {
      listRef.current?.scrollToItem(index, align);
    },
    []
  );

  // Scroll to top
  const scrollToTop = React.useCallback(() => {
    listRef.current?.scrollTo(0);
  }, []);

  // Expose scroll methods via ref
  React.useImperativeHandle(listRef, () => ({
    scrollToItem,
    scrollToTop,
    scrollTo: (scrollTop: number) => listRef.current?.scrollTo(scrollTop),
  }));

  if (items.length === 0) {
    return (
      <div
        className={cn('flex items-center justify-center text-muted-foreground', className)}
        style={{ height, width }}
      >
        <div className="text-center">
          <p className="text-sm">沒有資料</p>
        </div>
      </div>
    );
  }

  // Render with infinite loading if needed
  if (hasNextPage && loadNextPage) {
    return (
      <div className={className}>
        <InfiniteLoader
          isItemLoaded={isItemLoaded}
          itemCount={itemCount}
          loadMoreItems={loadNextPage}
          threshold={threshold}
        >
          {({ onItemsRendered, ref }) => {
            if (isVariableHeight) {
              return (
                <VariableSizeList
                  ref={(list) => {
                    ref(list);
                    (listRef as any).current = list;
                  }}
                  height={height}
                  width={width}
                  itemCount={itemCount}
                  itemSize={itemHeight as (index: number) => number}
                  onItemsRendered={onItemsRendered}
                  onScroll={handleScroll}
                  overscanCount={overscan}
                >
                  {itemRenderer}
                </VariableSizeList>
              );
            }

            return (
              <List
                ref={(list) => {
                  ref(list);
                  (listRef as any).current = list;
                }}
                height={height}
                width={width}
                itemCount={itemCount}
                itemSize={itemHeight as number}
                onItemsRendered={onItemsRendered}
                onScroll={handleScroll}
                overscanCount={overscan}
              >
                {itemRenderer}
              </List>
            );
          }}
        </InfiniteLoader>
      </div>
    );
  }

  // Render regular virtualized list
  if (isVariableHeight) {
    return (
      <VariableSizeList
        ref={listRef}
        className={className}
        height={height}
        width={width}
        itemCount={items.length}
        itemSize={itemHeight as (index: number) => number}
        onScroll={handleScroll}
        overscanCount={overscan}
      >
        {itemRenderer}
      </VariableSizeList>
    );
  }

  return (
    <List
      ref={listRef}
      className={className}
      height={height}
      width={width}
      itemCount={items.length}
      itemSize={itemHeight as number}
      onScroll={handleScroll}
      overscanCount={overscan}
    >
      {itemRenderer}
    </List>
  );
}

// Hook for managing virtualized list state
export function useVirtualizedList<T>({
  initialItems = [],
  pageSize = 20,
  loadMore,
}: {
  initialItems?: T[];
  pageSize?: number;
  loadMore?: (page: number) => Promise<T[]>;
}) {
  const [items, setItems] = React.useState<T[]>(initialItems);
  const [isLoading, setIsLoading] = React.useState(false);
  const [hasNextPage, setHasNextPage] = React.useState(true);
  const [page, setPage] = React.useState(1);

  const loadNextPage = React.useCallback(async () => {
    if (isLoading || !hasNextPage || !loadMore) return;

    setIsLoading(true);
    try {
      const newItems = await loadMore(page);

      if (newItems.length === 0 || newItems.length < pageSize) {
        setHasNextPage(false);
      }

      setItems((prev) => [...prev, ...newItems]);
      setPage((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to load more items:', error);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, hasNextPage, loadMore, page, pageSize]);

  const reset = React.useCallback(() => {
    setItems(initialItems);
    setPage(1);
    setHasNextPage(true);
    setIsLoading(false);
  }, [initialItems]);

  return {
    items,
    isLoading,
    hasNextPage,
    loadNextPage,
    reset,
    setItems,
  };
}

// Preset list components for common use cases
interface ArticleListItemProps {
  article: any;
  style: React.CSSProperties;
  onClick?: (article: any) => void;
}

export function ArticleListItem({ article, style, onClick }: ArticleListItemProps) {
  return (
    <div
      style={style}
      className="flex items-center p-4 border-b hover:bg-accent cursor-pointer"
      onClick={() => onClick?.(article)}
    >
      <div className="flex-1 min-w-0">
        <h3 className="font-medium truncate">{article.title}</h3>
        <p className="text-sm text-muted-foreground truncate">{article.summary}</p>
        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
          <span>{article.source?.name}</span>
          <span>•</span>
          <span>{new Date(article.publishedAt).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
}

export function VirtualizedArticleList({
  articles,
  onArticleClick,
  itemHeight = 120,
  ...props
}: {
  articles: any[];
  onArticleClick?: (article: any) => void;
} & Omit<VirtualizedListProps<any>, 'items' | 'renderItem'>) {
  const renderItem = React.useCallback(
    ({ index, style, data }: any) => (
      <ArticleListItem article={data} style={style} onClick={onArticleClick} />
    ),
    [onArticleClick]
  );

  return (
    <VirtualizedList items={articles} renderItem={renderItem} itemHeight={itemHeight} {...props} />
  );
}
