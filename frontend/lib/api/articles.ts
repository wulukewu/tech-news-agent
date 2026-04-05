import { apiClient } from './client';
import type { Article, ArticleListResponse } from '@/types/article';

/**
 * Articles API functions
 *
 * Validates Requirements 7.5, 10.2:
 * - 7.5: THE API client SHALL provide fetchMyArticles(page, pageSize) function
 * - 10.2: THE page SHALL fetch articles from GET /api/articles/me endpoint
 */

/**
 * Fetch all available article categories
 *
 * @returns Promise resolving to array of category names
 */
export async function fetchCategories(): Promise<string[]> {
  const response = await apiClient.get<{ categories: string[] }>(
    '/api/articles/categories',
  );
  return response.categories;
}

/**
 * Fetch articles with optional category filtering
 *
 * @param page - Page number (1-indexed, defaults to 1)
 * @param pageSize - Number of articles per page (defaults to 20)
 * @param categories - Array of categories to filter by (optional)
 * @returns Promise resolving to ArticleListResponse with articles and pagination metadata
 *
 * @example
 * ```typescript
 * // Fetch all articles
 * const response = await fetchMyArticles();
 *
 * // Fetch articles filtered by categories
 * const response = await fetchMyArticles(1, 20, ['前端開發', 'AI 應用']);
 * ```
 */
export async function fetchMyArticles(
  page: number = 1,
  pageSize: number = 20,
  categories?: string[],
): Promise<ArticleListResponse> {
  let url = `/api/articles/me?page=${page}&page_size=${pageSize}`;

  if (categories && categories.length > 0) {
    url += `&categories=${encodeURIComponent(categories.join(','))}`;
  }

  return apiClient.get<ArticleListResponse>(url);
}
