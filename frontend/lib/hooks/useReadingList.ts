import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchReadingList,
  addToReadingList,
  updateReadingListStatus,
  updateReadingListRating,
  removeFromReadingList,
} from '@/lib/api/readingList';
import type { ReadingListStatus } from '@/types/readingList';
import { toast } from 'sonner';

/**
 * Hook to fetch reading list with pagination and filtering
 * Validates Requirements 1.1, 2.2, 9.1, 9.2
 */
export function useReadingList(
  page: number = 1,
  status?: ReadingListStatus | null,
) {
  return useQuery({
    queryKey: ['readingList', page, status],
    queryFn: () => fetchReadingList(page, 20, status || undefined),
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
}

/**
 * Hook to add article to reading list
 * Validates Requirements 4.1, 4.3, 4.4, 4.5, 9.5
 */
export function useAddToReadingList() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (articleId: string) => addToReadingList(articleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['readingList'] });
      toast.success('Added to reading list');
    },
    onError: (error: Error) => {
      if (
        error.message.includes('already exists') ||
        error.message.includes('409')
      ) {
        toast.error('Article already in reading list');
      } else {
        toast.error('Failed to add to reading list');
      }
    },
  });
}

/**
 * Hook to update reading list item status
 * Validates Requirements 5.1, 5.2, 5.4, 5.5, 9.5
 */
export function useUpdateReadingListStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      articleId,
      status,
    }: {
      articleId: string;
      status: ReadingListStatus;
    }) => updateReadingListStatus(articleId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['readingList'] });
      toast.success('Status updated');
    },
    onError: () => {
      toast.error('Failed to update status');
    },
  });
}

/**
 * Hook to update reading list item rating with optimistic updates
 * Validates Requirements 6.4, 6.5, 6.6, 9.5
 */
export function useUpdateReadingListRating() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      articleId,
      rating,
    }: {
      articleId: string;
      rating: number | null;
    }) => updateReadingListRating(articleId, rating),
    onMutate: async ({ articleId, rating }) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ['readingList'] });
      const previousData = queryClient.getQueryData(['readingList']);

      queryClient.setQueriesData({ queryKey: ['readingList'] }, (old: any) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.map((item: any) =>
            item.articleId === articleId ? { ...item, rating } : item,
          ),
        };
      });

      return { previousData };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(['readingList'], context.previousData);
      }
      toast.error('Failed to update rating');
    },
    onSuccess: () => {
      toast.success('Rating updated');
    },
  });
}

/**
 * Hook to remove article from reading list
 * Validates Requirements 7.1, 7.3, 7.4, 7.5, 9.5
 */
export function useRemoveFromReadingList() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (articleId: string) => removeFromReadingList(articleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['readingList'] });
      toast.success('Removed from reading list');
    },
    onError: () => {
      toast.error('Failed to remove from reading list');
    },
  });
}
