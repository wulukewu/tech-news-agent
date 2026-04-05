'use client';

import { useState } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { EmptyState } from '@/components/EmptyState';
import { ArticleListSkeleton } from '@/components/LoadingSkeleton';
import { StatusFilterTabs } from '@/components/reading-list/StatusFilterTabs';
import { ReadingListItem } from '@/components/reading-list/ReadingListItem';
import {
  useReadingList,
  useUpdateReadingListStatus,
  useUpdateReadingListRating,
  useRemoveFromReadingList,
} from '@/lib/hooks/useReadingList';
import type { ReadingListStatus } from '@/types/readingList';
import { BookMarked, Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

/**
 * Main reading list page component
 * Validates Requirements 1.1, 1.2, 1.3, 1.5, 2.1, 2.2, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2, 8.3, 10.1, 10.2, 10.5, 12.1, 12.2, 12.3, 12.4, 12.5, 17.1, 17.3, 17.4
 */
export default function ReadingListPage() {
  const [selectedStatus, setSelectedStatus] =
    useState<ReadingListStatus | null>(null);
  const [page, setPage] = useState(1);

  // Fetch reading list data
  const { data, isLoading, isError, error, refetch } = useReadingList(
    page,
    selectedStatus,
  );

  // Mutations
  const updateStatus = useUpdateReadingListStatus();
  const updateRating = useUpdateReadingListRating();
  const removeItem = useRemoveFromReadingList();

  // Handle status filter change
  const handleStatusChange = (status: ReadingListStatus | null) => {
    setSelectedStatus(status);
    setPage(1); // Reset to first page when filter changes
  };

  // Handle load more
  const handleLoadMore = () => {
    setPage((prev) => prev + 1);
  };

  // Loading state
  if (isLoading && page === 1) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <h1 className="text-3xl font-bold mb-6">Reading List</h1>
          <ArticleListSkeleton />
        </div>
      </ProtectedRoute>
    );
  }

  // Error state
  if (isError) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <h1 className="text-3xl font-bold mb-6">Reading List</h1>
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <AlertCircle className="h-12 w-12 text-destructive" />
            <h2 className="text-xl font-semibold">
              Failed to load reading list
            </h2>
            <p className="text-muted-foreground text-center max-w-md">
              {error?.message || 'Please try again.'}
            </p>
            <button
              onClick={() => refetch()}
              className={cn(
                'px-4 py-2 rounded-md bg-primary text-primary-foreground',
                'hover:bg-primary/90 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
              )}
            >
              Retry
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  // Empty state
  if (!data || data.items.length === 0) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8 px-4 max-w-6xl">
          <h1 className="text-3xl font-bold mb-6">Reading List</h1>

          {/* Show status tabs even when empty */}
          <div className="mb-6">
            <StatusFilterTabs
              selectedStatus={selectedStatus}
              onStatusChange={handleStatusChange}
            />
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
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
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
          <StatusFilterTabs
            selectedStatus={selectedStatus}
            onStatusChange={handleStatusChange}
          />
        </div>

        {/* Reading List Items */}
        <div className="space-y-4">
          {data.items.map((item) => (
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

        {/* Load More Button */}
        {data.hasNextPage && (
          <div className="mt-8 flex justify-center">
            <button
              onClick={handleLoadMore}
              disabled={isLoading}
              className={cn(
                'inline-flex items-center gap-2 px-6 py-3 rounded-md',
                'bg-primary text-primary-foreground',
                'hover:bg-primary/90 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'font-medium',
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading more articles...
                </>
              ) : (
                'Load More'
              )}
            </button>
          </div>
        )}

        {/* Pagination info */}
        <div className="mt-4 text-center text-sm text-muted-foreground">
          Showing {data.items.length} of {data.totalCount} articles
        </div>
      </div>
    </ProtectedRoute>
  );
}
