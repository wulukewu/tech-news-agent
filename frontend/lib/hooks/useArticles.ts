/**
 * React Query hooks for Articles API
 *
 * This module provides React Query hooks for fetching and managing articles.
 * Implements server state management with automatic caching, background refetching,
 * and cache invalidation.
 *
 * Requirements: 2.3, 2.4
 * - 2.3: Use React Query for server state caching and synchronization
 * - 2.4: Separate server state from client state management
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { fetchMyArticles, fetchCategories } from '@/lib/api/articles';
import type { ArticleListResponse } from '@/types/article';

/**
 * Query keys for articles
 *
 * Centralized query keys for consistent cache management.
 * Using arrays allows for hierarchical invalidation.
 */
export const articleKeys = {
  all: ['articles'] as const,
  lists: () => [...articleKeys.all, 'list'] as const,
  list: (page: number, pageSize: number, categories?: string[]) =>
    [...articleKeys.lists(), { page, pageSize, categories }] as const,
  categories: () => [...articleKeys.all, 'categories'] as const,
};

/**
 * Hook to fetch paginated articles with optional category filtering
 *
 * Features:
 * - Automatic caching with 5-minute stale time
 * - Background refetching when data becomes stale
 * - Pagination support
 * - Category filtering
 *
 * @param page - Page number (1-indexed, defaults to 1)
 * @param pageSize - Number of articles per page (defaults to 20)
 * @param categories - Array of categories to filter by (optional)
 * @returns UseQueryResult with articles data and query state
 *
 * @example
 * ```tsx
 * function ArticleList() {
 *   const { data, isLoading, error } = useArticles(1, 20, ['前端開發']);
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       {data.articles.map(article => (
 *         <ArticleCard key={article.id} article={article} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useArticles(
  page: number = 1,
  pageSize: number = 20,
  categories?: string[]
): UseQueryResult<ArticleListResponse, Error> {
  return useQuery({
    queryKey: articleKeys.list(page, pageSize, categories),
    queryFn: () => fetchMyArticles(page, pageSize, categories),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  });
}

/**
 * Hook to fetch available article categories
 *
 * Features:
 * - Automatic caching with 30-minute stale time (categories change infrequently)
 * - Background refetching when data becomes stale
 *
 * @returns UseQueryResult with categories array and query state
 *
 * @example
 * ```tsx
 * function CategoryFilter() {
 *   const { data: categories, isLoading } = useCategories();
 *
 *   if (isLoading) return <div>Loading categories...</div>;
 *
 *   return (
 *     <select>
 *       {categories?.map(category => (
 *         <option key={category} value={category}>
 *           {category}
 *         </option>
 *       ))}
 *     </select>
 *   );
 * }
 * ```
 */
export function useCategories(): UseQueryResult<string[], Error> {
  return useQuery({
    queryKey: articleKeys.categories(),
    queryFn: fetchCategories,
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
  });
}
