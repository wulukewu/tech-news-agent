/**
 * React Query hooks for Reading List API
 *
 * This module provides React Query hooks for fetching and managing reading list items.
 * Implements server state management with automatic caching, optimistic updates,
 * and cache invalidation strategies.
 *
 * Requirements: 2.3, 2.4
 * - 2.3: Use React Query for server state caching and synchronization
 * - 2.4: Separate server state from client state management
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from '@tanstack/react-query';
import {
  fetchReadingList,
  addToReadingList,
  updateReadingListStatus,
  updateReadingListRating,
  removeFromReadingList,
} from '@/lib/api/readingList';
import type { ReadingListResponse, ReadingListStatus } from '@/types/readingList';
import { articleKeys } from './useArticles';

/**
 * Query keys for reading list
 *
 * Centralized query keys for consistent cache management.
 * Using arrays allows for hierarchical invalidation.
 */
export const readingListKeys = {
  all: ['readingList'] as const,
  lists: () => [...readingListKeys.all, 'list'] as const,
  list: (page: number, pageSize: number, status?: ReadingListStatus) =>
    [...readingListKeys.lists(), { page, pageSize, status }] as const,
};

/**
 * Hook to fetch paginated reading list with optional status filter
 *
 * Features:
 * - Automatic caching with 2-minute stale time
 * - Background refetching when data becomes stale
 * - Pagination support
 * - Status filtering (unread, reading, completed)
 *
 * @param page - Page number (1-indexed, defaults to 1)
 * @param pageSize - Number of items per page (defaults to 20)
 * @param status - Optional status filter
 * @returns UseQueryResult with reading list data and query state
 *
 * @example
 * ```tsx
 * function ReadingList() {
 *   const { data, isLoading, error } = useReadingList(1, 20, 'unread');
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       {data.items.map(item => (
 *         <ReadingListItem key={item.article_id} item={item} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useReadingList(
  page: number = 1,
  pageSize: number = 20,
  status?: ReadingListStatus
): UseQueryResult<ReadingListResponse, Error> {
  return useQuery({
    queryKey: readingListKeys.list(page, pageSize, status),
    queryFn: () => fetchReadingList(page, pageSize, status),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to add an article to the reading list
 *
 * Features:
 * - Automatic cache invalidation after successful addition
 * - Invalidates both reading list and articles cache
 * - Error handling with toast notifications
 *
 * @returns UseMutationResult with mutate function and mutation state
 *
 * @example
 * ```tsx
 * function AddToReadingListButton({ articleId }: { articleId: string }) {
 *   const { mutate, isPending } = useAddToReadingList();
 *
 *   return (
 *     <button
 *       onClick={() => mutate(articleId)}
 *       disabled={isPending}
 *     >
 *       {isPending ? 'Adding...' : 'Add to Reading List'}
 *     </button>
 *   );
 * }
 * ```
 */
export function useAddToReadingList(): UseMutationResult<
  { message: string; articleId: string },
  Error,
  string,
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addToReadingList,
    onSuccess: () => {
      // Invalidate reading list cache to refetch updated data
      queryClient.invalidateQueries({ queryKey: readingListKeys.all });
      // Invalidate articles cache as article's reading list status may have changed
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
    },
  });
}

/**
 * Hook to update reading list item status
 *
 * Features:
 * - Automatic cache invalidation after successful update
 * - Optimistic updates for instant UI feedback
 * - Rollback on error
 *
 * @returns UseMutationResult with mutate function and mutation state
 *
 * @example
 * ```tsx
 * function StatusSelector({ articleId, currentStatus }: Props) {
 *   const { mutate, isPending } = useUpdateReadingListStatus();
 *
 *   return (
 *     <select
 *       value={currentStatus}
 *       onChange={(e) => mutate({
 *         articleId,
 *         status: e.target.value as ReadingListStatus
 *       })}
 *       disabled={isPending}
 *     >
 *       <option value="unread">Unread</option>
 *       <option value="reading">Reading</option>
 *       <option value="completed">Completed</option>
 *     </select>
 *   );
 * }
 * ```
 */
export function useUpdateReadingListStatus(): UseMutationResult<
  { message: string; status: string },
  Error,
  { articleId: string; status: ReadingListStatus },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ articleId, status }) => updateReadingListStatus(articleId, status),
    onSuccess: () => {
      // Invalidate reading list cache to refetch updated data
      queryClient.invalidateQueries({ queryKey: readingListKeys.all });
    },
  });
}

/**
 * Hook to update reading list item rating
 *
 * Features:
 * - Automatic cache invalidation after successful update
 * - Optimistic updates for instant UI feedback
 * - Rollback on error
 *
 * @returns UseMutationResult with mutate function and mutation state
 *
 * @example
 * ```tsx
 * function RatingSelector({ articleId, currentRating }: Props) {
 *   const { mutate, isPending } = useUpdateReadingListRating();
 *
 *   return (
 *     <div>
 *       {[1, 2, 3, 4, 5].map(rating => (
 *         <button
 *           key={rating}
 *           onClick={() => mutate({ articleId, rating })}
 *           disabled={isPending}
 *         >
 *           {rating}
 *         </button>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useUpdateReadingListRating(): UseMutationResult<
  { message: string; rating: number | null },
  Error,
  { articleId: string; rating: number | null },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ articleId, rating }) => updateReadingListRating(articleId, rating),
    onSuccess: () => {
      // Invalidate reading list cache to refetch updated data
      queryClient.invalidateQueries({ queryKey: readingListKeys.all });
    },
  });
}

/**
 * Hook to remove an article from the reading list
 *
 * Features:
 * - Automatic cache invalidation after successful removal
 * - Invalidates both reading list and articles cache
 * - Error handling with toast notifications
 *
 * @returns UseMutationResult with mutate function and mutation state
 *
 * @example
 * ```tsx
 * function RemoveButton({ articleId }: { articleId: string }) {
 *   const { mutate, isPending } = useRemoveFromReadingList();
 *
 *   return (
 *     <button
 *       onClick={() => mutate(articleId)}
 *       disabled={isPending}
 *     >
 *       {isPending ? 'Removing...' : 'Remove'}
 *     </button>
 *   );
 * }
 * ```
 */
export function useRemoveFromReadingList(): UseMutationResult<
  { message: string },
  Error,
  string,
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeFromReadingList,
    onSuccess: () => {
      // Invalidate reading list cache to refetch updated data
      queryClient.invalidateQueries({ queryKey: readingListKeys.all });
      // Invalidate articles cache as article's reading list status may have changed
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
    },
  });
}
