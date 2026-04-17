import { useState, useEffect, useCallback } from 'react';
import { fetchReadingList } from '@/lib/api/readingList';
import { toast } from '@/lib/toast';
import type { ReadingListItem, ReadingListStatus } from '@/types/readingList';

interface UseReadingListArticlesProps {
  selectedStatus: ReadingListStatus | null;
}

/**
 * Hook for managing reading list articles with infinite scroll
 *
 * Features:
 * - Infinite scroll pagination
 * - Status filtering
 * - Loading states
 * - Error handling
 *
 * @param selectedStatus - Optional status filter
 * @returns Reading list state and handlers
 */
export function useReadingListArticles({ selectedStatus }: UseReadingListArticlesProps) {
  const [articles, setArticles] = useState<ReadingListItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const loadArticles = useCallback(
    async (pageNum: number, append: boolean = false) => {
      try {
        if (append) {
          setLoadingMore(true);
        } else {
          setLoading(true);
        }

        const data = await fetchReadingList(pageNum, 20, selectedStatus || undefined);

        if (append) {
          setArticles((prev) => [...prev, ...(data?.items || [])]);
        } else {
          setArticles(data?.items || []);
        }

        setHasNextPage(data?.hasNextPage || false);
        setTotalCount(data?.totalCount || 0);
        setPage(pageNum);
      } catch (error) {
        toast.error('Failed to load reading list');
        if (!append) {
          setArticles([]);
          setTotalCount(0);
        }
        setHasNextPage(false);
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [selectedStatus]
  );

  const handleLoadMore = () => {
    if (!loadingMore && hasNextPage) {
      loadArticles(page + 1, true);
    }
  };

  // Reset and reload when status filter changes
  useEffect(() => {
    setPage(1);
    loadArticles(1);
  }, [selectedStatus, loadArticles]);

  return {
    articles,
    loading,
    loadingMore,
    hasNextPage,
    totalCount,
    handleLoadMore,
    refetch: () => loadArticles(1),
  };
}
