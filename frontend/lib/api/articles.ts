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
  const response = await apiClient.get<{ success: boolean; data: { categories: string[] } }>(
    '/api/articles/categories'
  );
  return response.data.data.categories;
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
  categories?: string[]
): Promise<ArticleListResponse> {
  let url = `/api/articles/me?page=${page}&page_size=${pageSize}`;

  if (categories && categories.length > 0) {
    url += `&categories=${encodeURIComponent(categories.join(','))}`;
  }

  const response = await apiClient.get<{
    success: boolean;
    data: Array<{
      id: string;
      title: string;
      url: string;
      publishedAt: string | null;
      tinkeringIndex: number;
      aiSummary: string | null;
      actionableTakeaway?: string | null;
      feedName: string;
      category: string;
      isInReadingList: boolean;
    }>;
    pagination: {
      total_count: number;
      page: number;
      page_size: number;
      total_pages: number;
      has_next: boolean;
      has_previous: boolean;
    };
  }>(url);

  // Transform backend response to frontend format
  return {
    articles: response.data.data.map((article) => ({
      id: article.id,
      title: article.title,
      url: article.url,
      feedName: article.feedName,
      category: article.category,
      publishedAt: article.publishedAt,
      tinkeringIndex: article.tinkeringIndex,
      aiSummary: article.aiSummary,
      actionableTakeaway: article.actionableTakeaway,
      isInReadingList: article.isInReadingList,
    })),
    page: response.data.pagination.page,
    pageSize: response.data.pagination.page_size,
    totalCount: response.data.pagination.total_count,
    hasNextPage: response.data.pagination.has_next,
  };
}

/**
 * Fetch public recommended articles (for homepage live feed)
 *
 * @param limit - Number of articles to fetch (defaults to 3)
 * @returns Promise resolving to an array of Article items
 */
export async function fetchPublicRecommendedArticles(limit: number = 3): Promise<Article[]> {
  try {
    const response = await apiClient.get<{
      success: boolean;
      data: Array<{
        id: string;
        title: string;
        url: string;
        published_at: string | null;
        tinkering_index: number;
        ai_summary: string | null;
        actionable_takeaway?: string | null;
        feed_name: string;
        category: string;
        is_in_reading_list: boolean;
      }>;
    }>(`/api/articles/public/recommended?limit=${limit}`);

    return response.data.data.map((article) => ({
      id: article.id,
      title: article.title,
      url: article.url,
      feedName: article.feed_name,
      category: article.category,
      publishedAt: article.published_at,
      tinkeringIndex: article.tinkering_index,
      aiSummary: article.ai_summary,
      actionableTakeaway: article.actionable_takeaway,
      isInReadingList: article.is_in_reading_list,
    }));
  } catch (error) {
    console.error('Failed to fetch public recommended articles:', error);
    return [];
  }
}

/**
 * Fetch a single article by its ID
 *
 * @param id - Article ID (UUID)
 * @returns Promise resolving to the Article
 */
export async function fetchArticle(id: string): Promise<Article> {
  const response = await apiClient.get<{
    success: boolean;
    data: {
      id: string;
      title: string;
      url: string;
      imageUrl?: string | null;
      publishedAt: string | null;
      tinkeringIndex: number;
      aiSummary: string | null;
      actionableTakeaway?: string | null;
      feedName: string;
      category: string;
      isInReadingList: boolean;
      readStatus?: string | null;
    };
  }>(`/api/articles/${id}`);

  const article = response.data.data;
  return {
    id: article.id,
    title: article.title,
    url: article.url,
    imageUrl: article.imageUrl,
    feedName: article.feedName,
    category: article.category,
    publishedAt: article.publishedAt,
    tinkeringIndex: article.tinkeringIndex,
    aiSummary: article.aiSummary,
    actionableTakeaway: article.actionableTakeaway,
    isInReadingList: article.isInReadingList,
    readStatus: article.readStatus,
  };
}
