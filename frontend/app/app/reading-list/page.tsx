'use client';

import { useState, useCallback } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { EmptyState } from '@/components/EmptyState';
import { ArticleListSkeleton } from '@/components/LoadingSkeleton';
import { StatusFilterTabs } from '@/components/reading-list/StatusFilterTabs';
import { ReadingListItem } from '@/components/reading-list/ReadingListItem';
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';
import { useReadingListArticles } from '@/lib/hooks/useReadingListArticles';
import {
  useUpdateReadingListStatus,
  useUpdateReadingListRating,
  useRemoveFromReadingList,
} from '@/lib/hooks/useReadingList';
import type { ReadingListStatus } from '@/types/readingList';
import { BookMarked, CheckSquare, Square, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { useI18n } from '@/contexts/I18nContext';

/**
 * Main reading list page component
 * Validates Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.8
 */
export default function ReadingListPage() {
  const { t } = useI18n();
  const [selectedStatus, setSelectedStatus] = useState<ReadingListStatus | null>(null);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);

  // Use infinite scroll hook for articles
  const { articles, loading, loadingMore, hasNextPage, totalCount, handleLoadMore } =
    useReadingListArticles({ selectedStatus });

  // Mutations
  const updateStatus = useUpdateReadingListStatus();
  const updateRating = useUpdateReadingListRating();
  const removeItem = useRemoveFromReadingList();

  // Handle status filter change
  const handleStatusChange = useCallback((status: ReadingListStatus | null) => {
    setSelectedStatus(status);
    setSelectedItems(new Set()); // Clear selection when changing status
  }, []);

  // Handle item selection
  const toggleItemSelection = (articleId: string) => {
    setSelectedItems((prev) => {
      const next = new Set(prev);
      if (next.has(articleId)) {
        next.delete(articleId);
      } else {
        next.add(articleId);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedItems(new Set(articles.map((item) => item.articleId)));
  };

  const deselectAll = () => {
    setSelectedItems(new Set());
  };

  // Batch operations
  const handleBatchMarkAsRead = async () => {
    for (const articleId of selectedItems) {
      await updateStatus.mutateAsync({ articleId, status: 'Read' });
    }
    setSelectedItems(new Set());
    setIsSelectionMode(false);
  };

  const handleBatchRemove = async () => {
    for (const articleId of selectedItems) {
      await removeItem.mutateAsync(articleId);
    }
    setSelectedItems(new Set());
    setIsSelectionMode(false);
  };

  // Infinite scroll sentinel
  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore: hasNextPage,
    loading: loadingMore,
  });

  // Loading state
  if (loading) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <h1 className="text-3xl font-bold mb-6">{t('reading-list-page.loading-title')}</h1>
          <ArticleListSkeleton />
        </div>
      </ProtectedRoute>
    );
  }

  if (!articles || articles.length === 0) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <h1 className="text-3xl font-bold mb-6">{t('reading-list-page.title')}</h1>

          <div className="mb-6">
            <StatusFilterTabs selectedStatus={selectedStatus} onStatusChange={handleStatusChange} />
          </div>

          <EmptyState
            title={t('reading-list-page.empty-title')}
            description={t('reading-list-page.empty-description')}
            icon={<BookMarked className="h-12 w-12" />}
            action={
              <Link
                href="/dashboard/articles"
                className={cn(
                  'inline-flex items-center px-4 py-2 rounded-md',
                  'bg-primary text-primary-foreground',
                  'hover:bg-primary/90 transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2'
                )}
              >
                {t('reading-list-page.browse-articles')}
              </Link>
            }
          />
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">{t('reading-list-page.title')}</h1>
          {articles && articles.length > 0 && (
            <Button
              variant="outline"
              onClick={() => {
                setIsSelectionMode(!isSelectionMode);
                setSelectedItems(new Set());
              }}
            >
              {isSelectionMode
                ? t('reading-list-page.cancel-button')
                : t('reading-list-page.select-button')}
            </Button>
          )}
        </div>

        {/* Status Filter Tabs */}
        <div className="mb-6">
          <StatusFilterTabs selectedStatus={selectedStatus} onStatusChange={handleStatusChange} />
        </div>

        {/* Batch Actions Bar */}
        {isSelectionMode && articles && articles.length > 0 && (
          <div className="mb-4 p-4 bg-muted rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectedItems.size === articles.length ? deselectAll : selectAll}
              >
                {selectedItems.size === articles.length ? (
                  <>
                    <CheckSquare className="h-4 w-4 mr-2" />
                    {t('reading-list-page.deselect-all')}
                  </>
                ) : (
                  <>
                    <Square className="h-4 w-4 mr-2" />
                    {t('reading-list-page.select-all')}
                  </>
                )}
              </Button>
              <span className="text-sm text-muted-foreground">
                {t('reading-list-page.selected-count', { count: selectedItems.size })}
              </span>
            </div>
            {selectedItems.size > 0 && (
              <div className="flex items-center gap-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleBatchMarkAsRead}
                  disabled={updateStatus.isPending}
                >
                  {t('reading-list-page.batch-mark-read')}
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleBatchRemove}
                  disabled={removeItem.isPending}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  {t('reading-list-page.batch-remove')}
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Reading List Items */}
        <div className="space-y-4">
          {articles.map((item) => (
            <div key={item.articleId} className="flex items-start gap-3">
              {isSelectionMode && (
                <Checkbox
                  checked={selectedItems.has(item.articleId)}
                  onCheckedChange={() => toggleItemSelection(item.articleId)}
                  className="mt-6"
                />
              )}
              <div className="flex-1">
                <ReadingListItem
                  item={item}
                  onStatusChange={(articleId, status) => {
                    updateStatus.mutate({ articleId, status });
                  }}
                  onRatingChange={(articleId, rating) => {
                    updateRating.mutate({ articleId, rating });
                  }}
                  onRemove={(articleId) => {
                    removeItem.mutate(articleId);
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Infinite scroll sentinel */}
        {hasNextPage && <div ref={sentinelRef} className="h-px" aria-hidden="true" />}

        {/* Loading indicator for infinite scroll */}
        {loadingMore && (
          <div className="flex justify-center py-8" role="status" aria-live="polite">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <span className="sr-only">{t('reading-list-page.loading-more-sr')}</span>
          </div>
        )}

        {!hasNextPage && articles.length > 0 && (
          <div className="text-center py-8 text-muted-foreground" role="status">
            {t('reading-list-page.no-more-articles')}
          </div>
        )}

        {/* Pagination info */}
        <div className="mt-4 text-center text-sm text-muted-foreground">
          {t('reading-list-page.showing-count', { shown: articles.length, total: totalCount })}
        </div>
      </div>
    </ProtectedRoute>
  );
}
