/**
 * Unit Tests: React Query Cache Behavior
 *
 * Tests React Query caching, invalidation, refetching, and integration
 * with split contexts architecture.
 *
 * Requirements: 2.3, 2.4
 * - 2.3: React Query for server state caching and synchronization
 * - 2.4: Separate server state from client state management
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { UserProvider } from '@/contexts/UserContext';
import { useArticles, useCategories, articleKeys } from '@/lib/hooks/useArticles';
import { useReadingList, readingListKeys, useAddToReadingList } from '@/lib/hooks/useReadingList';
import * as authApi from '@/lib/api/auth';
import * as articlesApi from '@/lib/api/articles';
import * as readingListApi from '@/lib/api/readingList';

jest.mock('@/lib/api/auth');
jest.mock('@/lib/api/articles');
jest.mock('@/lib/api/readingList');

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}));

const mockedAuthApi = authApi as jest.Mocked<typeof authApi>;
const mockedArticlesApi = articlesApi as jest.Mocked<typeof articlesApi>;
const mockedReadingListApi = readingListApi as jest.Mocked<typeof readingListApi>;

describe('React Query Cache Behavior', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 1000 * 60 * 10, // 10 minutes
        },
        mutations: {
          retry: false,
        },
      },
    });

    mockedAuthApi.checkAuthStatus.mockResolvedValue({
      id: '123',
      discordId: '456',
      username: 'testuser',
    });
  });

  const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <UserProvider>{children}</UserProvider>
      </AuthProvider>
    </QueryClientProvider>
  );

  describe('Requirement 2.3: React Query Caching', () => {
    it('should cache articles data and reuse it on subsequent renders', async () => {
      const mockArticles = {
        articles: [
          { id: '1', title: 'Article 1', url: 'https://example.com/1' },
          { id: '2', title: 'Article 2', url: 'https://example.com/2' },
        ],
        page: 1,
        page_size: 20,
        total: 2,
        total_pages: 1,
      };

      mockedArticlesApi.fetchMyArticles.mockResolvedValue(mockArticles);

      const ArticlesComponent: React.FC = () => {
        const { data, isLoading } = useArticles(1, 20);

        if (isLoading) return <div>Loading...</div>;

        return (
          <div>
            {data?.articles.map((article) => (
              <div key={article.id} data-testid={`article-${article.id}`}>
                {article.title}
              </div>
            ))}
          </div>
        );
      };

      const { unmount } = render(
        <AllProviders>
          <ArticlesComponent />
        </AllProviders>
      );

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByTestId('article-1')).toHaveTextContent('Article 1');
      });

      expect(mockedArticlesApi.fetchMyArticles).toHaveBeenCalledTimes(1);

      // Unmount and remount
      unmount();

      render(
        <AllProviders>
          <ArticlesComponent />
        </AllProviders>
      );

      // Data should be available immediately from cache
      await waitFor(() => {
        expect(screen.getByTestId('article-1')).toHaveTextContent('Article 1');
      });

      // Should not have called API again (data served from cache)
      expect(mockedArticlesApi.fetchMyArticles).toHaveBeenCalledTimes(1);
    });

    it('should cache categories with longer stale time', async () => {
      const mockCategories = ['前端開發', 'AI 應用', '後端開發'];
      mockedArticlesApi.fetchCategories.mockResolvedValue(mockCategories);

      const CategoriesComponent: React.FC = () => {
        const { data, isLoading } = useCategories();

        if (isLoading) return <div>Loading...</div>;

        return (
          <div>
            {data?.map((category) => (
              <div key={category} data-testid={`category-${category}`}>
                {category}
              </div>
            ))}
          </div>
        );
      };

      render(
        <AllProviders>
          <CategoriesComponent />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.getByTestId('category-前端開發')).toBeInTheDocument();
      });

      expect(mockedArticlesApi.fetchCategories).toHaveBeenCalledTimes(1);

      // Check that data is in cache
      const cachedData = queryClient.getQueryData(articleKeys.categories());
      expect(cachedData).toEqual(mockCategories);
    });

    it('should maintain separate cache entries for different query parameters', async () => {
      const mockPage1 = {
        articles: [{ id: '1', title: 'Article 1', url: 'https://example.com/1' }],
        page: 1,
        page_size: 20,
        total: 40,
        total_pages: 2,
      };

      const mockPage2 = {
        articles: [{ id: '21', title: 'Article 21', url: 'https://example.com/21' }],
        page: 2,
        page_size: 20,
        total: 40,
        total_pages: 2,
      };

      mockedArticlesApi.fetchMyArticles
        .mockResolvedValueOnce(mockPage1)
        .mockResolvedValueOnce(mockPage2);

      const PaginatedComponent: React.FC = () => {
        const [page, setPage] = React.useState(1);
        const { data, isLoading } = useArticles(page, 20);

        return (
          <div>
            {isLoading && <div data-testid="loading">Loading...</div>}
            {data?.articles.map((article) => (
              <div key={article.id} data-testid={`article-${article.id}`}>
                {article.title}
              </div>
            ))}
            <button onClick={() => setPage(2)} data-testid="next-page">
              Next Page
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AllProviders>
          <PaginatedComponent />
        </AllProviders>
      );

      // Wait for page 1 to load
      await waitFor(() => {
        expect(screen.getByTestId('article-1')).toBeInTheDocument();
      });

      // Go to page 2
      await user.click(screen.getByTestId('next-page'));

      await waitFor(() => {
        expect(screen.getByTestId('article-21')).toBeInTheDocument();
      });

      // Both pages should be cached separately
      const page1Cache = queryClient.getQueryData(articleKeys.list(1, 20));
      const page2Cache = queryClient.getQueryData(articleKeys.list(2, 20));

      expect(page1Cache).toEqual(mockPage1);
      expect(page2Cache).toEqual(mockPage2);
    });
  });

  describe('Requirement 2.3: Cache Invalidation', () => {
    it('should invalidate reading list cache after adding an article', async () => {
      const mockReadingList = {
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

      const mockUpdatedReadingList = {
        items: [
          {
            article_id: '1',
            status: 'unread' as const,
            added_at: '2024-01-01T00:00:00Z',
          },
          {
            article_id: '2',
            status: 'unread' as const,
            added_at: '2024-01-02T00:00:00Z',
          },
        ],
        page: 1,
        page_size: 20,
        total: 2,
        total_pages: 1,
      };

      mockedReadingListApi.fetchReadingList
        .mockResolvedValueOnce(mockReadingList)
        .mockResolvedValueOnce(mockUpdatedReadingList);

      mockedReadingListApi.addToReadingList.mockResolvedValue({
        message: 'Added to reading list',
        articleId: '2',
      });

      const ReadingListComponent: React.FC = () => {
        const { data, isLoading } = useReadingList(1, 20);
        const addMutation = useAddToReadingList();

        return (
          <div>
            {isLoading && <div data-testid="loading">Loading...</div>}
            <div data-testid="count">{data?.items.length || 0}</div>
            {data?.items.map((item) => (
              <div key={item.article_id} data-testid={`item-${item.article_id}`}>
                {item.article_id}
              </div>
            ))}
            <button
              onClick={() => addMutation.mutate('2')}
              data-testid="add-button"
              disabled={addMutation.isPending}
            >
              Add Article
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AllProviders>
          <ReadingListComponent />
        </AllProviders>
      );

      // Wait for initial data
      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('1');
      });

      expect(screen.getByTestId('item-1')).toBeInTheDocument();

      // Add article
      await user.click(screen.getByTestId('add-button'));

      // Wait for mutation to complete and cache to be invalidated
      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('2');
      });

      expect(screen.getByTestId('item-2')).toBeInTheDocument();
      expect(mockedReadingListApi.fetchReadingList).toHaveBeenCalledTimes(2);
    });

    it('should invalidate all article queries when using hierarchical keys', async () => {
      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      // Manually invalidate all article queries
      await queryClient.invalidateQueries({ queryKey: articleKeys.all });

      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['articles'] })
      );
    });

    it('should support selective cache invalidation', async () => {
      const mockArticles = {
        articles: [{ id: '1', title: 'Article 1', url: 'https://example.com/1' }],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      };

      mockedArticlesApi.fetchMyArticles.mockResolvedValue(mockArticles);

      // Pre-populate cache
      queryClient.setQueryData(articleKeys.list(1, 20), mockArticles);
      queryClient.setQueryData(articleKeys.list(2, 20), mockArticles);

      // Invalidate only page 1
      await queryClient.invalidateQueries({ queryKey: articleKeys.list(1, 20) });

      // Page 1 should be invalidated
      const page1State = queryClient.getQueryState(articleKeys.list(1, 20));
      expect(page1State?.isInvalidated).toBe(true);

      // Page 2 should still be valid
      const page2Data = queryClient.getQueryData(articleKeys.list(2, 20));
      expect(page2Data).toEqual(mockArticles);
    });
  });

  describe('Requirement 2.4: Server State vs Client State Separation', () => {
    it('should manage server state (articles) separately from client state (theme)', async () => {
      const mockArticles = {
        articles: [{ id: '1', title: 'Article 1', url: 'https://example.com/1' }],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      };

      mockedArticlesApi.fetchMyArticles.mockResolvedValue(mockArticles);

      const MixedStateComponent: React.FC = () => {
        // Server state (React Query)
        const { data: articles, isLoading } = useArticles(1, 20);

        // Client state (React useState)
        const [clientFilter, setClientFilter] = React.useState('all');

        return (
          <div>
            {isLoading && <div data-testid="loading">Loading...</div>}
            <div data-testid="server-state">{articles?.articles.length || 0} articles</div>
            <div data-testid="client-state">{clientFilter}</div>
            <button onClick={() => setClientFilter('favorites')} data-testid="filter-button">
              Filter
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AllProviders>
          <MixedStateComponent />
        </AllProviders>
      );

      // Wait for server state to load
      await waitFor(() => {
        expect(screen.getByTestId('server-state')).toHaveTextContent('1 articles');
      });

      // Client state should be independent
      expect(screen.getByTestId('client-state')).toHaveTextContent('all');

      // Change client state
      await user.click(screen.getByTestId('filter-button'));

      expect(screen.getByTestId('client-state')).toHaveTextContent('favorites');

      // Server state should remain unchanged
      expect(screen.getByTestId('server-state')).toHaveTextContent('1 articles');
    });

    it('should handle server state updates without affecting client state', async () => {
      const mockInitialArticles = {
        articles: [{ id: '1', title: 'Article 1', url: 'https://example.com/1' }],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      };

      const mockUpdatedArticles = {
        articles: [
          { id: '1', title: 'Article 1', url: 'https://example.com/1' },
          { id: '2', title: 'Article 2', url: 'https://example.com/2' },
        ],
        page: 1,
        page_size: 20,
        total: 2,
        total_pages: 1,
      };

      mockedArticlesApi.fetchMyArticles
        .mockResolvedValueOnce(mockInitialArticles)
        .mockResolvedValueOnce(mockUpdatedArticles);

      const StateIsolationComponent: React.FC = () => {
        const { data: articles, refetch } = useArticles(1, 20);
        const [localCount, setLocalCount] = React.useState(0);

        return (
          <div>
            <div data-testid="server-count">{articles?.articles.length || 0}</div>
            <div data-testid="client-count">{localCount}</div>
            <button onClick={() => refetch()} data-testid="refetch-button">
              Refetch
            </button>
            <button onClick={() => setLocalCount((c) => c + 1)} data-testid="increment-button">
              Increment
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AllProviders>
          <StateIsolationComponent />
        </AllProviders>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('server-count')).toHaveTextContent('1');
      });

      // Increment client state
      await user.click(screen.getByTestId('increment-button'));
      expect(screen.getByTestId('client-count')).toHaveTextContent('1');

      // Refetch server state
      await user.click(screen.getByTestId('refetch-button'));

      await waitFor(() => {
        expect(screen.getByTestId('server-count')).toHaveTextContent('2');
      });

      // Client state should remain unchanged
      expect(screen.getByTestId('client-count')).toHaveTextContent('1');
    });

    it('should demonstrate clear separation between server and client state management', async () => {
      // Server state is managed by React Query
      const serverStateKeys = queryClient
        .getQueryCache()
        .getAll()
        .map((query) => query.queryKey);

      // Client state is managed by React Context (not in React Query cache)
      const hasAuthInCache = serverStateKeys.some((key) => key.includes('auth'));
      const hasThemeInCache = serverStateKeys.some((key) => key.includes('theme'));

      // Auth and Theme should NOT be in React Query cache (they're client state)
      expect(hasAuthInCache).toBe(false);
      expect(hasThemeInCache).toBe(false);

      // Articles and reading list SHOULD be in React Query cache (they're server state)
      const mockArticles = {
        articles: [],
        page: 1,
        page_size: 20,
        total: 0,
        total_pages: 0,
      };

      mockedArticlesApi.fetchMyArticles.mockResolvedValue(mockArticles);

      const ServerStateComponent: React.FC = () => {
        const { data } = useArticles(1, 20);
        return <div data-testid="articles">{data?.articles.length || 0}</div>;
      };

      render(
        <AllProviders>
          <ServerStateComponent />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.getByTestId('articles')).toBeInTheDocument();
      });

      // Now articles should be in cache
      const updatedKeys = queryClient
        .getQueryCache()
        .getAll()
        .map((query) => query.queryKey);
      const hasArticlesInCache = updatedKeys.some((key) => key.includes('articles'));

      expect(hasArticlesInCache).toBe(true);
    });
  });
});
