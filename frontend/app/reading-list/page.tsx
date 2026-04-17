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
import { BookMarked } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

/**
 * Main reading list page component
 * Validates Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.8
 */
export default function ReadingListPage() {
  const [selectedStatus, setSelectedStatus] = useState<ReadingListStatus | null>(null);

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
  }, []);

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
          <h1 className="text-3xl font-bold mb-6">Reading List</h1>
          <ArticleListSkeleton />
        </div>
      </ProtectedRoute>
    );
  }

  // Empty state
  if (!articles || articles.length === 0) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <h1 className="text-3xl font-bold mb-6">Reading List</h1>

          {/* Show status tabs even when empty */}
          <div className="mb-6">
            <StatusFilterTabs selectedStatus={selectedStatus} onStatusChange={handleStatusChange} />
          </div>

          <EmptyState
            title="Your reading list is empty"
            description="Start adding articles from your dashboard to build your reading collection"
            icon={<BookMarked className="h-12 w-12" />}
            action={
              <Link
                href="/dashboard"
                className={cn(
                  'inline-flex items-center px-4 py-2 rounded-md',
                  'bg-primary text-primary-foreground',
                  'hover:bg-primary/90 transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2'
                )}
              >
                Browse Articles
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
        <h1 className="text-3xl font-bold mb-6">Reading List</h1>

        {/* Status Filter Tabs */}
        <div className="mb-6">
          <StatusFilterTabs selectedStatus={selectedStatus} onStatusChange={handleStatusChange} />
        </div>

        {/* Reading List Items */}
        <div className="space-y-4">
          {articles.map((item) => (
            <ReadingListItem
              key={item.articleId}
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
          ))}
        </div>

        {/* Infinite scroll sentinel */}
        {hasNextPage && <div ref={sentinelRef} className="h-px" aria-hidden="true" />}

        {/* Loading indicator for infinite scroll */}
        {loadingMore && (
          <div className="flex justify-center py-8" role="status" aria-live="polite">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <span className="sr-only">Loading more articles...</span>
          </div>
        )}

        {/* No more articles indicator */}
        {!hasNextPage && articles.length > 0 && (
          <div className="text-center py-8 text-muted-foreground" role="status">
            No more articles
          </div>
        )}

        {/* Pagination info */}
        <div className="mt-4 text-center text-sm text-muted-foreground">
          Showing {articles.length} of {totalCount} articles
        </div>
      </div>
    </ProtectedRoute>
  );
}
