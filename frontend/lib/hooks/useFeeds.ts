/**
 * React Query hooks for Feeds and Subscriptions API
 *
 * This module provides React Query hooks for fetching feeds and managing subscriptions.
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
import { fetchFeeds, toggleSubscription } from '@/lib/api/feeds';
import type { Feed, SubscriptionToggleResponse } from '@/types/feed';
import { articleKeys } from './useArticles';

/**
 * Query keys for feeds and subscriptions
 *
 * Centralized query keys for consistent cache management.
 * Using arrays allows for hierarchical invalidation.
 */
export const feedKeys = {
  all: ['feeds'] as const,
  lists: () => [...feedKeys.all, 'list'] as const,
  list: () => [...feedKeys.lists()] as const,
};

/**
 * Hook to fetch all available feeds
 *
 * Features:
 * - Automatic caching with 10-minute stale time (feeds change infrequently)
 * - Background refetching when data becomes stale
 * - Includes subscription status for each feed
 *
 * @returns UseQueryResult with feeds array and query state
 *
 * @example
 * ```tsx
 * function FeedList() {
 *   const { data: feeds, isLoading, error } = useFeeds();
 *
 *   if (isLoading) return <div>Loading feeds...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       {feeds?.map(feed => (
 *         <FeedCard key={feed.id} feed={feed} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useFeeds(): UseQueryResult<Feed[], Error> {
  return useQuery({
    queryKey: feedKeys.list(),
    queryFn: fetchFeeds,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}

/**
 * Hook to toggle subscription status for a feed
 *
 * Features:
 * - Automatic cache invalidation after successful toggle
 * - Invalidates both feeds and articles cache (new articles may appear)
 * - Optimistic updates for instant UI feedback
 * - Error handling with rollback
 *
 * @returns UseMutationResult with mutate function and mutation state
 *
 * @example
 * ```tsx
 * function SubscribeButton({ feedId, isSubscribed }: Props) {
 *   const { mutate, isPending } = useToggleSubscription();
 *
 *   return (
 *     <button
 *       onClick={() => mutate(feedId)}
 *       disabled={isPending}
 *     >
 *       {isPending
 *         ? 'Processing...'
 *         : isSubscribed
 *         ? 'Unsubscribe'
 *         : 'Subscribe'}
 *     </button>
 *   );
 * }
 * ```
 */
export function useToggleSubscription(): UseMutationResult<
  SubscriptionToggleResponse,
  Error,
  string,
  { previousFeeds: Feed[] | undefined }
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: toggleSubscription,
    // Optimistic update: immediately update UI before server responds
    onMutate: async (feedId) => {
      // Cancel any outgoing refetches to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: feedKeys.list() });

      // Snapshot the previous value
      const previousFeeds = queryClient.getQueryData<Feed[]>(feedKeys.list());

      // Optimistically update the cache
      queryClient.setQueryData<Feed[]>(feedKeys.list(), (old) => {
        if (!old) return old;
        return old.map((feed) =>
          feed.id === feedId ? { ...feed, is_subscribed: !feed.is_subscribed } : feed
        );
      });

      // Return context with previous value for rollback
      return { previousFeeds };
    },
    // On error, rollback to previous value
    onError: (err, feedId, context) => {
      if (context?.previousFeeds) {
        queryClient.setQueryData(feedKeys.list(), context.previousFeeds);
      }
    },
    // Always refetch after error or success to ensure cache is in sync
    onSettled: () => {
      // Invalidate feeds cache to refetch updated data
      queryClient.invalidateQueries({ queryKey: feedKeys.all });
      // Invalidate articles cache as new articles may appear from subscribed feeds
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
    },
  });
}
