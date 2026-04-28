/**
 * Unit tests for React Query hooks
 *
 * Tests the React Query hooks for articles, reading list, and feeds.
 * Validates cache invalidation strategies and optimistic updates.
 *
 * Requirements: 2.3, 2.4
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useArticles,
  useCategories,
  useReadingList,
  useAddToReadingList,
  useUpdateReadingListStatus,
  useRemoveFromReadingList,
  useFeeds,
  useToggleSubscription,
} from '@/lib/hooks';
import * as articlesApi from '@/lib/api/articles';
import * as readingListApi from '@/lib/api/readingList';
import * as feedsApi from '@/lib/api/feeds';

// Mock API modules
vi.mock('@/lib/api/articles');
vi.mock('@/lib/api/readingList');
vi.mock('@/lib/api/feeds');

const mockedArticlesApi = articlesApi as jest.Mocked<typeof articlesApi>;
const mockedReadingListApi = readingListApi as jest.Mocked<typeof readingListApi>;
const mockedFeedsApi = feedsApi as jest.Mocked<typeof feedsApi>;

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries for tests
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('React Query Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useArticles', () => {
    it('should fetch articles successfully', async () => {
      const mockData = {
        articles: [{ id: '1', title: 'Test Article', url: 'https://test.com' }],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      };

      mockedArticlesApi.fetchMyArticles.mockResolvedValue(mockData);

      const { result } = renderHook(() => useArticles(1, 20), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockData);
      expect(mockedArticlesApi.fetchMyArticles).toHaveBeenCalledWith(1, 20, undefined);
    });

    it('should fetch articles with category filter', async () => {
      const mockData = {
        articles: [],
        page: 1,
        page_size: 20,
        total: 0,
        total_pages: 0,
      };

      mockedArticlesApi.fetchMyArticles.mockResolvedValue(mockData);

      const { result } = renderHook(() => useArticles(1, 20, ['前端開發']), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedArticlesApi.fetchMyArticles).toHaveBeenCalledWith(1, 20, ['前端開發']);
    });

    it('should handle fetch error', async () => {
      const mockError = new Error('Failed to fetch articles');
      mockedArticlesApi.fetchMyArticles.mockRejectedValue(mockError);

      const { result } = renderHook(() => useArticles(1, 20), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('useCategories', () => {
    it('should fetch categories successfully', async () => {
      const mockCategories = ['前端開發', 'AI 應用', '後端開發'];
      mockedArticlesApi.fetchCategories.mockResolvedValue(mockCategories);

      const { result } = renderHook(() => useCategories(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockCategories);
      expect(mockedArticlesApi.fetchCategories).toHaveBeenCalledTimes(1);
    });
  });

  describe('useReadingList', () => {
    it('should fetch reading list successfully', async () => {
      const mockData = {
        items: [
          {
            article_id: '1',
            status: 'unread' as const,
            added_at: '2024-01-01T00:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      };

      mockedReadingListApi.fetchReadingList.mockResolvedValue(mockData);

      const { result } = renderHook(() => useReadingList(1, 20), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockData);
      expect(mockedReadingListApi.fetchReadingList).toHaveBeenCalledWith(1, 20, undefined);
    });

    it('should fetch reading list with status filter', async () => {
      const mockData = {
        items: [],
        page: 1,
        page_size: 20,
        total: 0,
        total_pages: 0,
      };

      mockedReadingListApi.fetchReadingList.mockResolvedValue(mockData);

      const { result } = renderHook(() => useReadingList(1, 20, 'unread'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedReadingListApi.fetchReadingList).toHaveBeenCalledWith(1, 20, 'unread');
    });
  });

  describe('useAddToReadingList', () => {
    it('should add article to reading list', async () => {
      const mockResponse = {
        message: 'Added to reading list',
        articleId: '123',
      };

      mockedReadingListApi.addToReadingList.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAddToReadingList(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('123');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(mockedReadingListApi.addToReadingList).toHaveBeenCalledWith('123', expect.anything());
    });

    it('should handle add error', async () => {
      const mockError = new Error('Failed to add');
      mockedReadingListApi.addToReadingList.mockRejectedValue(mockError);

      const { result } = renderHook(() => useAddToReadingList(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('123');

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('useUpdateReadingListStatus', () => {
    it('should update reading list status', async () => {
      const mockResponse = {
        message: 'Status updated',
        status: 'reading',
      };

      mockedReadingListApi.updateReadingListStatus.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useUpdateReadingListStatus(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ articleId: '123', status: 'reading' });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(mockedReadingListApi.updateReadingListStatus).toHaveBeenCalledWith('123', 'reading');
    });
  });

  describe('useRemoveFromReadingList', () => {
    it('should remove article from reading list', async () => {
      const mockResponse = { message: 'Removed from reading list' };
      mockedReadingListApi.removeFromReadingList.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useRemoveFromReadingList(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('123');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(mockedReadingListApi.removeFromReadingList).toHaveBeenCalledWith(
        '123',
        expect.anything()
      );
    });
  });

  describe('useFeeds', () => {
    it('should fetch feeds successfully', async () => {
      const mockFeeds = [
        {
          id: '1',
          name: 'Test Feed',
          url: 'https://test.com/feed',
          is_subscribed: true,
        },
      ];

      mockedFeedsApi.fetchFeeds.mockResolvedValue(mockFeeds);

      const { result } = renderHook(() => useFeeds(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockFeeds);
      expect(mockedFeedsApi.fetchFeeds).toHaveBeenCalledTimes(1);
    });
  });

  describe('useToggleSubscription', () => {
    it('should toggle subscription successfully', async () => {
      const mockResponse = {
        feed_id: '123',
        subscribed: true,
        message: 'Subscribed successfully',
      };

      mockedFeedsApi.toggleSubscription.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useToggleSubscription(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('123');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(mockedFeedsApi.toggleSubscription).toHaveBeenCalledWith('123', expect.anything());
    });

    it('should handle toggle error', async () => {
      const mockError = new Error('Failed to toggle subscription');
      mockedFeedsApi.toggleSubscription.mockRejectedValue(mockError);

      const { result } = renderHook(() => useToggleSubscription(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('123');

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('Cache Invalidation', () => {
    it('should invalidate reading list cache after adding article', async () => {
      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      mockedReadingListApi.addToReadingList.mockResolvedValue({
        message: 'Added',
        articleId: '123',
      });

      const { result } = renderHook(() => useAddToReadingList(), { wrapper });

      result.current.mutate('123');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Should invalidate both reading list and articles cache
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['readingList'] })
      );
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['articles'] })
      );
    });

    it('should invalidate feeds cache after toggling subscription', async () => {
      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      );

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      mockedFeedsApi.toggleSubscription.mockResolvedValue({
        feed_id: '123',
        subscribed: true,
        message: 'Subscribed',
      });

      const { result } = renderHook(() => useToggleSubscription(), { wrapper });

      result.current.mutate('123');

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Should invalidate both feeds and articles cache
      expect(invalidateSpy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['feeds'] }));
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['articles'] })
      );
    });
  });
});
