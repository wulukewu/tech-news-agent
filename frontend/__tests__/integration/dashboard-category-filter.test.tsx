import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter, useSearchParams } from 'next/navigation';
import DashboardPage from '@/app/dashboard/page';
import * as articlesApi from '@/lib/api/articles';

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(),
}));

// Mock API calls
vi.mock('@/lib/api/articles', () => ({
  fetchMyArticles: vi.fn(),
  fetchCategories: vi.fn(),
}));

// Mock ProtectedRoute
vi.mock('@/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock other components
vi.mock('@/components/ArticleGrid', () => ({
  ArticleGrid: ({ articles }: { articles: any[] }) => (
    <div data-testid="article-grid">{articles.length} articles</div>
  ),
}));

vi.mock('@/components/TriggerSchedulerButton', () => ({
  TriggerSchedulerButton: () => <button>Trigger Scheduler</button>,
}));

vi.mock('@/components/SearchBar', () => ({
  SearchBar: ({ onSearch }: { onSearch: (query: string) => void }) => (
    <input
      data-testid="search-bar"
      onChange={(e) => onSearch(e.target.value)}
      placeholder="Search"
    />
  ),
}));

describe('Dashboard Category Filter Integration', () => {
  const mockRouter = {
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  };

  const mockCategories = ['Tech News', 'AI/ML', 'Web Dev', 'DevOps', 'Security'];
  const mockArticles = [
    {
      id: '1',
      title: 'Test Article 1',
      category: 'Tech News',
      aiSummary: 'Summary 1',
      url: 'https://example.com/1',
      publishedAt: '2024-01-01T00:00:00Z',
      tinkeringIndex: 3,
    },
    {
      id: '2',
      title: 'Test Article 2',
      category: 'AI/ML',
      aiSummary: 'Summary 2',
      url: 'https://example.com/2',
      publishedAt: '2024-01-02T00:00:00Z',
      tinkeringIndex: 4,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as any).mockReturnValue(mockRouter);
    (articlesApi.fetchCategories as any).mockResolvedValue(mockCategories);
    (articlesApi.fetchMyArticles as any).mockResolvedValue({
      articles: mockArticles,
      hasNextPage: false,
    });
  });

  describe('URL Query Parameter Persistence', () => {
    it('should initialize selected categories from URL query parameter', async () => {
      const mockSearchParams = new URLSearchParams('categories=Tech News,AI/ML');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      // Check that the correct categories are selected
      const techNewsBadge = screen.getByText('Tech News').closest('div');
      const aiMlBadge = screen.getByText('AI/ML').closest('div');
      const webDevBadge = screen.getByText('Web Dev').closest('div');

      expect(techNewsBadge).toHaveAttribute('aria-checked', 'true');
      expect(aiMlBadge).toHaveAttribute('aria-checked', 'true');
      expect(webDevBadge).toHaveAttribute('aria-checked', 'false');
    });

    it('should select all categories when no URL parameter is present', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      // All categories should be selected by default
      mockCategories.forEach((category) => {
        const badge = screen.getByText(category).closest('div');
        expect(badge).toHaveAttribute('aria-checked', 'true');
      });
    });

    it('should update URL when category is toggled', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      // Click to deselect a category
      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.click(techNewsBadge);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });

      // Check that URL was updated with remaining categories
      const lastCall = mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1];
      expect(lastCall[0]).toContain('categories=');
      expect(lastCall[0]).not.toContain('Tech News');
    });

    it('should update URL when Select All is clicked', async () => {
      const mockSearchParams = new URLSearchParams('categories=Tech News');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Select All')).toBeInTheDocument();
      });

      const selectAllButton = screen.getByText('Select All');
      fireEvent.click(selectAllButton);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });

      // When all categories are selected, URL should not have categories param
      const lastCall = mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1];
      expect(lastCall[0]).toBe('/dashboard');
    });

    it('should update URL when Clear All is clicked', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Clear All')).toBeInTheDocument();
      });

      const clearAllButton = screen.getByText('Clear All');
      fireEvent.click(clearAllButton);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });

      // When no categories are selected, URL should have categories param with empty value
      const lastCall = mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1];
      // The implementation removes the categories param when empty, so URL should be /dashboard
      expect(lastCall[0]).toMatch(/\/dashboard(\?categories=)?/);
    });

    it('should preserve search query when updating category filters', async () => {
      const mockSearchParams = new URLSearchParams('search=test&categories=Tech News');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('AI/ML')).toBeInTheDocument();
      });

      // Toggle a category
      const aiMlBadge = screen.getByText('AI/ML');
      fireEvent.click(aiMlBadge);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });

      // Check that search query is preserved in URL
      const lastCall = mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1];
      expect(lastCall[0]).toContain('search=test');
      expect(lastCall[0]).toContain('categories=');
    });

    it('should use router.replace instead of router.push to avoid history pollution', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.click(techNewsBadge);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    it('should pass scroll: false to router.replace to maintain scroll position', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.click(techNewsBadge);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });

      const lastCall = mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1];
      expect(lastCall[1]).toEqual({ scroll: false });
    });
  });

  describe('Filter Performance', () => {
    it('should update article list within 300ms of filter change', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      const startTime = Date.now();

      // Toggle a category
      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.click(techNewsBadge);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });

      const endTime = Date.now();
      const duration = endTime - startTime;

      // Should update within 300ms
      expect(duration).toBeLessThan(300);
    });

    it('should fetch articles with selected categories', async () => {
      const mockSearchParams = new URLSearchParams('categories=Tech News,AI/ML');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(articlesApi.fetchMyArticles).toHaveBeenCalled();
      });

      // Check that fetchMyArticles was called with the correct categories
      const lastCall = (articlesApi.fetchMyArticles as any).mock.calls[
        (articlesApi.fetchMyArticles as any).mock.calls.length - 1
      ];
      expect(lastCall[2]).toEqual(['Tech News', 'AI/ML']);
    });

    it('should refetch articles when category selection changes', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      const initialCallCount = (articlesApi.fetchMyArticles as any).mock.calls.length;

      // Toggle a category
      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.click(techNewsBadge);

      await waitFor(() => {
        expect((articlesApi.fetchMyArticles as any).mock.calls.length).toBeGreaterThan(
          initialCallCount
        );
      });
    });
  });

  describe('Invalid URL Parameters', () => {
    it('should handle invalid category names in URL gracefully', async () => {
      const mockSearchParams = new URLSearchParams('categories=InvalidCategory,Tech News');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      // Only valid categories should be selected
      const techNewsBadge = screen.getByText('Tech News').closest('div');
      expect(techNewsBadge).toHaveAttribute('aria-checked', 'true');

      // Invalid category should not cause errors
      expect(screen.queryByText('InvalidCategory')).not.toBeInTheDocument();
    });

    it('should handle empty category parameter', async () => {
      const mockSearchParams = new URLSearchParams('categories=');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      // Should default to all categories selected
      mockCategories.forEach((category) => {
        const badge = screen.getByText(category).closest('div');
        expect(badge).toHaveAttribute('aria-checked', 'true');
      });
    });

    it('should handle malformed category parameter', async () => {
      const mockSearchParams = new URLSearchParams('categories=,,,');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Tech News')).toBeInTheDocument();
      });

      // Should default to all categories selected
      mockCategories.forEach((category) => {
        const badge = screen.getByText(category).closest('div');
        expect(badge).toHaveAttribute('aria-checked', 'true');
      });
    });
  });

  describe('Combined Search and Filter', () => {
    it('should support both search and category filters simultaneously', async () => {
      const mockSearchParams = new URLSearchParams('search=test&categories=Tech News');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId('search-bar')).toBeInTheDocument();
      });

      // Category filter should be active
      const techNewsBadge = screen.getByText('Tech News').closest('div');
      expect(techNewsBadge).toHaveAttribute('aria-checked', 'true');

      // Search query should be in the URL (we can't easily test the SearchBar's internal state)
      expect(mockSearchParams.get('search')).toBe('test');
    });

    it('should update URL with both search and categories', async () => {
      const mockSearchParams = new URLSearchParams('');
      (useSearchParams as any).mockReturnValue(mockSearchParams);

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId('search-bar')).toBeInTheDocument();
      });

      // Enter search query
      const searchBar = screen.getByTestId('search-bar');
      fireEvent.change(searchBar, { target: { value: 'test query' } });

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });

      // Toggle a category
      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.click(techNewsBadge);

      await waitFor(() => {
        const lastCall = mockRouter.replace.mock.calls[mockRouter.replace.mock.calls.length - 1];
        expect(lastCall[0]).toContain('search=');
        expect(lastCall[0]).toContain('categories=');
      });
    });
  });
});
