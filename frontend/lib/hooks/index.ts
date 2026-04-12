/**
 * React Query Hooks - Centralized Export
 *
 * This module exports all React Query hooks for server state management.
 * Provides a single import point for all query hooks throughout the application.
 *
 * Requirements: 2.3, 2.4
 * - 2.3: Use React Query for server state caching and synchronization
 * - 2.4: Separate server state from client state management
 */

// Article hooks
export { useArticles, useCategories, articleKeys } from './useArticles';

// Reading list hooks
export {
  useReadingList,
  useAddToReadingList,
  useUpdateReadingListStatus,
  useUpdateReadingListRating,
  useRemoveFromReadingList,
  readingListKeys,
} from './useReadingList';

// Feed and subscription hooks
export { useFeeds, useToggleSubscription, feedKeys } from './useFeeds';

/**
 * Query key utilities
 *
 * Centralized query keys for cache invalidation across the application.
 * Use these when you need to manually invalidate or refetch queries.
 *
 * @example
 * ```tsx
 * import { useQueryClient } from '@tanstack/react-query';
 * import { articleKeys, readingListKeys } from '@/lib/hooks';
 *
 * function RefreshButton() {
 *   const queryClient = useQueryClient();
 *
 *   const handleRefresh = () => {
 *     // Invalidate all article queries
 *     queryClient.invalidateQueries({ queryKey: articleKeys.all });
 *     // Invalidate all reading list queries
 *     queryClient.invalidateQueries({ queryKey: readingListKeys.all });
 *   };
 *
 *   return <button onClick={handleRefresh}>Refresh</button>;
 * }
 * ```
 */
