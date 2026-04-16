'use client';

import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useArticles } from '@/lib/hooks/useArticles';
import { ArticleCard } from '@/components/ArticleCard';
import { VirtualizedList } from '@/components/ui/virtualized-list';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { CategoryFilterMenu } from './CategoryFilterMenu';
import { TinkeringIndexFilter } from './TinkeringIndexFilter';
import { SortingControls, type SortField, type SortOrder } from './SortingControls';
import { useKeyboardNavigation, useFocusNavigation } from '@/lib/hooks/useUrlState';
import { cn } from '@/lib/utils';
import type { Article, ArticleFilters } from '@/types/article';

interface ArticleBrowserProps {
  /** Initial filter state for the browser */
  initialFilters?: ArticleFilters;
  /** Number of articles per page */
  pageSize?: number;
  /** Enable virtual scrolling for large lists */
  enableVirtualization?: boolean;
  /** Custom CSS classes */
  className?: string;
  /** Show analysis buttons (max 5 per page) */
  showAnalysisButtons?: boolean;
  /** Show reading list buttons (max 10 per page) */
  showReadingListButtons?: boolean;
  /** Show category filter menu */
  showCategoryFilter?: boolean;
  /** Show tinkering index filter */
  showTinkeringIndexFilter?: boolean;
  /** Show sorting controls */
  showSortingControls?: boolean;
  /** Callback when analysis is requested */
  onAnalyze?: (articleId: string) => void;
  /** Callback when article is added to reading list */
  onAddToReadingList?: (articleId: string) => void;
  /** Callback when filters change (for URL state management) */
  onFiltersChange?: (filters: ArticleFilters) => void;
}

/**
 * ArticleBrowser - Core component for browsing articles
 *
 * Features:
 * - Responsive grid layout that adapts to different screen sizes
 * - Virtual scrolling support for large article lists
 * - Integration with existing ArticleCard component
 * - Configurable button limits (analysis: 5, reading list: 10)
 * - Category filtering with multi-select menu
 * - Tinkering index filtering with 1-5 star range selection
 * - Sorting functionality (date, technical depth, category)
 * - Article statistics display (total count, filtered count)
 * - Real-time filtering without page refresh
 * - URL state synchronization for filter persistence
 *
 * Requirements:
 * - 1.1: Advanced_Article_Browser SHALL display articles in responsive grid layout
 * - 1.2: Category_Filter_Menu with up to 24 most common categories plus "顯示全部" option
 * - 1.3: Tinkering_Index_Filter with options for different technical depth levels (1-5 stars)
 * - 1.4: Sorting options by published date, tinkering index, and category
 * - 1.5: Support real-time filtering without page refresh
 * - 1.6: Display article statistics (total count, filtered count)
 * - 12.2: Performance optimization with virtual scrolling for large lists
 */
export function ArticleBrowser({
  initialFilters,
  pageSize = 20,
  enableVirtualization = false,
  className,
  showAnalysisButtons = true,
  showReadingListButtons = true,
  showCategoryFilter = true,
  showTinkeringIndexFilter = true,
  showSortingControls = true,
  onAnalyze,
  onAddToReadingList,
  onFiltersChange,
}: ArticleBrowserProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<ArticleFilters>(initialFilters || {});
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Update filters when initialFilters change
  useEffect(() => {
    if (initialFilters) {
      setFilters(initialFilters);
    }
  }, [initialFilters]);

  // Notify parent component when filters change (for URL state management)
  useEffect(() => {
    onFiltersChange?.(filters);
  }, [filters, onFiltersChange]);

  // Handle category filter changes
  const handleCategoryChange = useCallback(
    (categories: string[]) => {
      const newFilters = {
        ...filters,
        categories: categories.length > 0 ? categories : undefined,
      };
      setFilters(newFilters);
      setCurrentPage(1); // Reset to first page when filters change
    },
    [filters]
  );

  // Handle tinkering index filter changes
  const handleTinkeringIndexChange = useCallback(
    (minValue?: number, maxValue?: number) => {
      const newFilters = {
        ...filters,
        minTinkeringIndex: minValue,
        maxTinkeringIndex: maxValue,
      };
      setFilters(newFilters);
      setCurrentPage(1); // Reset to first page when filters change
    },
    [filters]
  );

  // Handle sorting changes
  const handleSortingChange = useCallback(
    (sortBy: SortField, sortOrder: SortOrder) => {
      const newFilters = {
        ...filters,
        sortBy,
        sortOrder,
      };
      setFilters(newFilters);
      setCurrentPage(1); // Reset to first page when sorting changes
    },
    [filters]
  );

  // Fetch articles using the existing hook with category filtering
  const {
    data: articleData,
    isLoading,
    error,
    refetch,
  } = useArticles(currentPage, pageSize, filters.categories);

  // Apply client-side filtering and sorting
  const filteredAndSortedArticles = useMemo(() => {
    if (!articleData?.articles) return [];

    let filtered = articleData.articles.filter((article) => {
      // Apply tinkering index filter
      if (filters.minTinkeringIndex && article.tinkeringIndex < filters.minTinkeringIndex) {
        return false;
      }
      if (filters.maxTinkeringIndex && article.tinkeringIndex > filters.maxTinkeringIndex) {
        return false;
      }
      return true;
    });

    // Apply sorting
    if (filters.sortBy) {
      filtered = [...filtered].sort((a, b) => {
        let comparison = 0;

        switch (filters.sortBy) {
          case 'date': {
            const dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
            const dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
            comparison = dateA - dateB;
            break;
          }
          case 'tinkering_index':
            comparison = a.tinkeringIndex - b.tinkeringIndex;
            break;
          case 'category':
            comparison = a.category.localeCompare(b.category);
            break;
        }

        return filters.sortOrder === 'desc' ? -comparison : comparison;
      });
    }

    return filtered;
  }, [articleData?.articles, filters]);

  // Calculate button limits per page
  const articlesWithButtons = useMemo(() => {
    return filteredAndSortedArticles.map((article, index) => ({
      ...article,
      showAnalysisButton: showAnalysisButtons && index < 5, // Max 5 analysis buttons per page
      showReadingListButton: showReadingListButtons && index < 10, // Max 10 reading list buttons per page
    }));
  }, [filteredAndSortedArticles, showAnalysisButtons, showReadingListButtons]);

  // Focus navigation for keyboard accessibility
  const { focusedIndex, navigateNext, navigatePrevious, clearFocus } = useFocusNavigation(
    articlesWithButtons.length
  );

  // Keyboard navigation setup
  useKeyboardNavigation({
    onRefresh: () => refetch(),
    onFocusSearch: () => searchInputRef.current?.focus(),
    onNavigateNext: navigateNext,
    onNavigatePrevious: navigatePrevious,
    onEscape: clearFocus,
  });

  // Handle analysis button click
  const handleAnalyze = useCallback(
    (articleId: string) => {
      onAnalyze?.(articleId);
    },
    [onAnalyze]
  );

  // Handle add to reading list
  const handleAddToReadingList = useCallback(
    (articleId: string) => {
      onAddToReadingList?.(articleId);
    },
    [onAddToReadingList]
  );

  // Render article card for virtualized list
  const renderArticleCard = useCallback(
    ({
      index,
      style,
      data,
    }: {
      index: number;
      style: React.CSSProperties;
      data: Article & { showAnalysisButton?: boolean; showReadingListButton?: boolean };
    }) => (
      <div style={style} className="p-2">
        <div
          data-article-index={index}
          tabIndex={focusedIndex === index ? 0 : -1}
          className={cn(
            'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-lg',
            focusedIndex === index && 'ring-2 ring-primary ring-offset-2'
          )}
        >
          <ArticleCard
            article={data}
            showAnalysisButton={data.showAnalysisButton}
            showReadingListButton={data.showReadingListButton}
            onAnalyze={handleAnalyze}
            onAddToReadingList={handleAddToReadingList}
          />
        </div>
      </div>
    ),
    [handleAnalyze, handleAddToReadingList, focusedIndex]
  );

  // Loading state
  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center py-12', className)}>
        <LoadingSpinner size="lg" text="載入文章中..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={cn('py-12', className)}>
        <ErrorMessage
          message={error.message || '載入文章時發生錯誤'}
          onRetry={() => refetch()}
          type="error"
        />
      </div>
    );
  }

  // Empty state
  if (!filteredAndSortedArticles.length) {
    return (
      <div className={cn('flex items-center justify-center py-12', className)}>
        <div className="text-center">
          <p className="text-lg font-medium text-muted-foreground">沒有找到文章</p>
          <p className="text-sm text-muted-foreground mt-2">
            {filters.categories?.length ||
            filters.minTinkeringIndex ||
            filters.maxTinkeringIndex ||
            filters.sortBy
              ? '請嘗試調整篩選條件'
              : '目前沒有可用的文章'}
          </p>
        </div>
      </div>
    );
  }

  // Statistics display
  const totalCount = articleData?.totalCount || 0;
  const filteredCount = filteredAndSortedArticles.length;

  return (
    <div className={cn('space-y-6', className)} role="main" aria-label="文章瀏覽器">
      {/* Keyboard Navigation Help */}
      <div className="sr-only" aria-live="polite">
        使用 j/k 鍵導航文章，r 鍵重新整理，/ 鍵聚焦搜尋，Escape 鍵清除焦點
      </div>

      {/* Filter Section */}
      {(showCategoryFilter || showTinkeringIndexFilter || showSortingControls) && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Category Filter */}
            {showCategoryFilter && (
              <div className="space-y-2">
                <CategoryFilterMenu
                  selectedCategories={filters.categories || []}
                  onCategoryChange={handleCategoryChange}
                  className="w-full"
                />
              </div>
            )}

            {/* Tinkering Index Filter */}
            {showTinkeringIndexFilter && (
              <div className="space-y-2">
                <TinkeringIndexFilter
                  minValue={filters.minTinkeringIndex}
                  maxValue={filters.maxTinkeringIndex}
                  onMinChange={(value) =>
                    handleTinkeringIndexChange(value, filters.maxTinkeringIndex)
                  }
                  onMaxChange={(value) =>
                    handleTinkeringIndexChange(filters.minTinkeringIndex, value)
                  }
                />
              </div>
            )}

            {/* Sorting Controls */}
            {showSortingControls && (
              <div className="space-y-2">
                <SortingControls
                  sortBy={filters.sortBy || 'date'}
                  sortOrder={filters.sortOrder || 'desc'}
                  onSortByChange={(field) =>
                    handleSortingChange(field, filters.sortOrder || 'desc')
                  }
                  onSortOrderChange={(order) =>
                    handleSortingChange(filters.sortBy || 'date', order)
                  }
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Article Statistics */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="text-sm text-muted-foreground" role="status" aria-live="polite">
          <span className="font-medium">總計: {totalCount}</span>
          {filteredCount !== totalCount && (
            <>
              <span className="mx-2">•</span>
              <span className="font-medium">篩選後: {filteredCount}</span>
            </>
          )}
          {showAnalysisButtons && (
            <>
              <span className="mx-2">•</span>
              <span className="text-xs">深度分析按鈕: 最多 5 個</span>
            </>
          )}
          {showReadingListButtons && (
            <>
              <span className="mx-2">•</span>
              <span className="text-xs">閱讀清單按鈕: 最多 10 個</span>
            </>
          )}
        </div>

        {/* Active Filters Summary */}
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          {filters.categories && filters.categories.length > 0 && (
            <span className="bg-muted px-2 py-1 rounded">
              分類: {filters.categories.join(', ')}
            </span>
          )}
          {(filters.minTinkeringIndex || filters.maxTinkeringIndex) && (
            <span className="bg-muted px-2 py-1 rounded">
              深度: {filters.minTinkeringIndex || 1}-{filters.maxTinkeringIndex || 5} 星
            </span>
          )}
          {filters.sortBy && (
            <span className="bg-muted px-2 py-1 rounded">
              排序:{' '}
              {filters.sortBy === 'date'
                ? '日期'
                : filters.sortBy === 'tinkering_index'
                  ? '深度'
                  : '分類'}
              {filters.sortOrder === 'desc' ? ' ↓' : ' ↑'}
            </span>
          )}
        </div>
      </div>

      {/* Article Grid */}
      {enableVirtualization && filteredAndSortedArticles.length > 50 ? (
        // Virtual scrolling for large lists
        <VirtualizedList
          items={articlesWithButtons}
          itemHeight={280} // Approximate height of ArticleCard
          renderItem={renderArticleCard}
          height={600}
          className="border rounded-lg"
          aria-label="文章列表"
        />
      ) : (
        // Regular responsive grid layout
        <div
          className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
          role="grid"
          aria-label="文章列表"
        >
          {articlesWithButtons.map((article, index) => (
            <div
              key={article.id}
              data-article-index={index}
              tabIndex={focusedIndex === index ? 0 : -1}
              className={cn(
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-lg',
                focusedIndex === index && 'ring-2 ring-primary ring-offset-2'
              )}
              role="gridcell"
              aria-label={`文章: ${article.title}`}
            >
              <ArticleCard
                article={article}
                showAnalysisButton={article.showAnalysisButton}
                showReadingListButton={article.showReadingListButton}
                onAnalyze={handleAnalyze}
                onAddToReadingList={handleAddToReadingList}
              />
            </div>
          ))}
        </div>
      )}

      {/* Pagination Info */}
      {articleData?.hasNextPage && (
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            第 {currentPage} 頁，共 {Math.ceil(totalCount / pageSize)} 頁
          </p>
        </div>
      )}
    </div>
  );
}

// Export additional types for external use
export type { ArticleBrowserProps };
export { CategoryFilterMenu } from './CategoryFilterMenu';
export { TinkeringIndexFilter } from './TinkeringIndexFilter';
export { SortingControls } from './SortingControls';
