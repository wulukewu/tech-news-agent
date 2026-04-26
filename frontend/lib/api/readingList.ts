import { apiClient } from './client';
import { logger } from '@/lib/utils/logger';
import type { ReadingListResponse, ReadingListStatus } from '@/types/readingList';

/**
 * Fetch reading list with pagination and optional status filter
 * Validates Requirements 1.1, 2.2, 3.1
 */
export async function fetchReadingList(
  page: number = 1,
  pageSize: number = 20,
  status?: ReadingListStatus
): Promise<ReadingListResponse> {
  let url = `/api/reading-list?page=${page}&page_size=${pageSize}`;
  if (status) {
    url += `&status=${status}`;
  }

  const response = await apiClient.get<{
    success: boolean;
    data: Array<{
      articleId: string;
      title: string;
      url: string;
      category: string;
      status: ReadingListStatus;
      rating: number | null;
      addedAt: string;
      updatedAt: string;
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

  // Validate response structure
  const responseData = response.data;
  if (!responseData.data || !Array.isArray(responseData.data)) {
    console.error('Invalid reading list response:', responseData);
    throw new Error('Invalid response format from reading list API');
  }

  // Transform backend response to frontend format
  return {
    items: responseData.data.map((item) => ({
      articleId: item.articleId,
      title: item.title,
      url: item.url,
      category: item.category,
      status: item.status,
      rating: item.rating,
      addedAt: item.addedAt,
      updatedAt: item.updatedAt,
    })),
    page: responseData.pagination.page,
    pageSize: responseData.pagination.page_size,
    totalCount: responseData.pagination.total_count,
    hasNextPage: responseData.pagination.has_next,
  };
}

/**
 * Add article to reading list
 * Validates Requirements 4.1
 */
export async function addToReadingList(
  articleId: string
): Promise<{ message: string; articleId: string }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  const response = await apiClient.post<{
    success: boolean;
    data: { message: string; article_id: string };
  }>('/api/reading-list', { article_id: articleId });

  return {
    message: response.data.data.message,
    articleId: response.data.data.article_id,
  };
}

/**
 * Update reading list item status
 * Validates Requirements 5.1
 */
export async function updateReadingListStatus(
  articleId: string,
  status: ReadingListStatus
): Promise<{ message: string; status: string }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  const response = await apiClient.patch<{
    success: boolean;
    data: { message: string; status: string };
  }>(`/api/reading-list/${articleId}/status`, { status });

  return response.data.data;
}

/**
 * Update reading list item rating
 * Validates Requirements 6.1
 */
export async function updateReadingListRating(
  articleId: string,
  rating: number | null
): Promise<{ message: string; rating: number | null }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  const response = await apiClient.patch<{
    success: boolean;
    data: { message: string; rating: number | null };
  }>(`/api/reading-list/${articleId}/rating`, { rating });

  return response.data.data;
}

/**
 * Remove article from reading list
 * Validates Requirements 7.1
 */
export async function removeFromReadingList(articleId: string): Promise<{ message: string }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  const response = await apiClient.delete<{
    success: boolean;
    data: { message: string };
  }>(`/api/reading-list/${articleId}`);

  return response.data.data;
}
