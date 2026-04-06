import { apiClient } from './client';
import type {
  ReadingListResponse,
  ReadingListStatus,
} from '@/types/readingList';

/**
 * Fetch reading list with pagination and optional status filter
 * Validates Requirements 1.1, 2.2, 3.1
 */
export async function fetchReadingList(
  page: number = 1,
  pageSize: number = 20,
  status?: ReadingListStatus,
): Promise<ReadingListResponse> {
  let url = `/api/reading-list?page=${page}&page_size=${pageSize}`;
  if (status) {
    url += `&status=${status}`;
  }
  return apiClient.get<ReadingListResponse>(url);
}

/**
 * Add article to reading list
 * Validates Requirements 4.1
 */
export async function addToReadingList(
  articleId: string,
): Promise<{ message: string; articleId: string }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  return apiClient.post('/api/reading-list', { article_id: articleId });
}

/**
 * Update reading list item status
 * Validates Requirements 5.1
 */
export async function updateReadingListStatus(
  articleId: string,
  status: ReadingListStatus,
): Promise<{ message: string; status: string }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  return apiClient.patch(`/api/reading-list/${articleId}/status`, { status });
}

/**
 * Update reading list item rating
 * Validates Requirements 6.1
 */
export async function updateReadingListRating(
  articleId: string,
  rating: number | null,
): Promise<{ message: string; rating: number | null }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  return apiClient.patch(`/api/reading-list/${articleId}/rating`, { rating });
}

/**
 * Remove article from reading list
 * Validates Requirements 7.1
 */
export async function removeFromReadingList(
  articleId: string,
): Promise<{ message: string }> {
  if (!articleId || articleId === 'undefined') {
    throw new Error('Invalid article_id: must be a valid UUID');
  }
  return apiClient.delete(`/api/reading-list/${articleId}`);
}
