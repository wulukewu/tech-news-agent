/**
 * ArticleBrowser Component Unit Tests
 *
 * Tests the core functionality of the ArticleBrowser component including:
 * - Responsive grid layout rendering
 * - Virtual scrolling integration
 * - Button limit enforcement (5 analysis, 10 reading list)
 * - Statistics display accuracy
 * - Loading and error states
 *
 * Requirements: 1.1, 12.2
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithQueryClient } from '@/__tests__/utils/render';
import { ArticleBrowser } from '@/features/articles/components/ArticleBrowser';
import { createMockArticles } from '@/__tests__/utils/arbitraries';
import type { Article } from '@/types/article';

// Mock the hooks
vi.mock('@/lib/hooks/useArticles', () => ({
  useArticles: vi.fn(),
}));

// Mock the ArticleCard component
vi.mock('@/components/ArticleCard', () => ({
  ArticleCard: ({
    article,
    showAnalysisButton,
    showReadingListButton,
    onAnalyze,
    onAddToReadingList,
  }: any) => (
    <div data-testid="article-card" data-article-id={article.id}>
      <h3>{article.title}</h3>
      <p>{article.category}</p>
      {showAnalysisButton && (
        <button data-testid="analysis-button" onClick={() => onAnalyze?.(article.id)}>
          Deep Dive Analysis
        </button>
      )}
      {showReadingListButton && (
        <button data-testid="reading-list-button" onClick={() => onAddToReadingList?.(article.id)}>
          Add to Reading List
        </button>
      )}
    </div>
  ),
}));

// Mock the VirtualizedList component
vi.mock('@/components/ui/virtualized-list', () => ({
  VirtualizedList: ({ items, renderItem }: any) => (
    <div data-testid="virtualized-list">
      {items.map((item: any, index: number) => (
        <div key={item.id}>{renderItem({ index, style: {}, data: item })}</div>
      ))}
    </div>
  ),
}));

import { useArticles } from '@/lib/hooks/useArticles';

const mockUseArticles = useArticles as any;

describe('ArticleBrowser', () => {
  const mockArticles: Article[] = [
    {
      id: '1',
      title: 'Test Article 1',
      url: 'https://example.com/1',
      feedName: 'Test Feed',
      category: 'tech',
      publishedAt: '2024-01-01T00:00:00Z',
      tinkeringIndex: 4,
      aiSummary: 'Test summary 1',
      isInReadingList: false,
    },
    {
      id: '2',
      title: 'Test Article 2',
      url: 'https://example.com/2',
      feedName: 'Test Feed',
      category: 'ai',
      publishedAt: '2024-01-02T00:00:00Z',
      tinkeringIndex: 3,
      aiSummary: 'Test summary 2',
      isInReadingList: true,
    },
  ];

  const mockArticleData = {
    articles: mockArticles,
    page: 1,
    pageSize: 20,
    totalCount: 2,
    hasNextPage: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseArticles.mockReturnValue({
      data: mockArticleData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  describe('Basic Rendering', () => {
    it('should render articles in a responsive grid layout', () => {
      renderWithQueryClient(<ArticleBrowser />);

      // Check that articles are rendered
      expect(screen.getAllByTestId('article-card')).toHaveLength(2);
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      expect(screen.getByText('Test Article 2')).toBeInTheDocument();
    });

    it('should display article statistics correctly', () => {
      renderWithQueryClient(<ArticleBrowser />);

      // Check statistics display
      expect(screen.getByText('總計: 2')).toBeInTheDocument();
    });

    it('should show filtered count when filters are applied', () => {
      const filteredData = {
        ...mockArticleData,
        totalCount: 10,
      };

      mockUseArticles.mockReturnValue({
        data: filteredData,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithQueryClient(<ArticleBrowser initialFilters={{ category: 'tech' }} />);

      expect(screen.getByText('總計: 10')).toBeInTheDocument();
      expect(screen.getByText('篩選後: 2')).toBeInTheDocument();
    });
  });

  describe('Button Limits', () => {
    it('should show analysis buttons for maximum 5 articles per page', () => {
      const manyArticles = createMockArticles(10);
      mockUseArticles.mockReturnValue({
        data: { ...mockArticleData, articles: manyArticles },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithQueryClient(<ArticleBrowser showAnalysisButtons={true} />);

      const analysisButtons = screen.getAllByTestId('analysis-button');
      expect(analysisButtons).toHaveLength(5);
    });

    it('should show reading list buttons for maximum 10 articles per page', () => {
      const manyArticles = createMockArticles(15);
      mockUseArticles.mockReturnValue({
        data: { ...mockArticleData, articles: manyArticles },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithQueryClient(<ArticleBrowser showReadingListButtons={true} />);

      const readingListButtons = screen.getAllByTestId('reading-list-button');
      expect(readingListButtons).toHaveLength(10);
    });

    it('should not show buttons when disabled', () => {
      renderWithQueryClient(
        <ArticleBrowser showAnalysisButtons={false} showReadingListButtons={false} />
      );

      expect(screen.queryByTestId('analysis-button')).not.toBeInTheDocument();
      expect(screen.queryByTestId('reading-list-button')).not.toBeInTheDocument();
    });
  });

  describe('Virtual Scrolling', () => {
    it('should use virtual scrolling when enabled and articles > 50', () => {
      const manyArticles = createMockArticles(60);
      mockUseArticles.mockReturnValue({
        data: { ...mockArticleData, articles: manyArticles },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithQueryClient(<ArticleBrowser enableVirtualization={true} />);

      expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
    });

    it('should use regular grid when virtualization disabled or articles <= 50', () => {
      renderWithQueryClient(<ArticleBrowser enableVirtualization={true} />);

      expect(screen.queryByTestId('virtualized-list')).not.toBeInTheDocument();
      expect(screen.getAllByTestId('article-card')).toHaveLength(2);
    });
  });

  describe('Loading and Error States', () => {
    it('should show loading spinner when loading', () => {
      mockUseArticles.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithQueryClient(<ArticleBrowser />);

      expect(screen.getByText('載入文章中...')).toBeInTheDocument();
    });

    it('should show error message when error occurs', () => {
      const mockError = new Error('Failed to fetch articles');
      mockUseArticles.mockReturnValue({
        data: null,
        isLoading: false,
        error: mockError,
        refetch: vi.fn(),
      });

      renderWithQueryClient(<ArticleBrowser />);

      expect(screen.getByText('發生錯誤')).toBeInTheDocument();
    });

    it('should show empty state when no articles', () => {
      mockUseArticles.mockReturnValue({
        data: { ...mockArticleData, articles: [] },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithQueryClient(<ArticleBrowser />);

      expect(screen.getByText('沒有找到文章')).toBeInTheDocument();
    });
  });

  describe('Callbacks', () => {
    it('should call onAnalyze when analysis button is clicked', async () => {
      const user = userEvent.setup();
      const onAnalyze = vi.fn();

      renderWithQueryClient(<ArticleBrowser showAnalysisButtons={true} onAnalyze={onAnalyze} />);

      const analysisButton = screen.getAllByTestId('analysis-button')[0];
      await user.click(analysisButton);

      expect(onAnalyze).toHaveBeenCalledWith('1');
    });

    it('should call onAddToReadingList when reading list button is clicked', async () => {
      const user = userEvent.setup();
      const onAddToReadingList = vi.fn();

      renderWithQueryClient(
        <ArticleBrowser showReadingListButtons={true} onAddToReadingList={onAddToReadingList} />
      );

      const readingListButton = screen.getAllByTestId('reading-list-button')[0];
      await user.click(readingListButton);

      expect(onAddToReadingList).toHaveBeenCalledWith('1');
    });
  });

  describe('Filtering', () => {
    it('should apply tinkering index filters correctly', () => {
      renderWithQueryClient(
        <ArticleBrowser
          initialFilters={{
            minTinkeringIndex: 4,
            maxTinkeringIndex: 5,
          }}
        />
      );

      // Only article with tinkeringIndex 4 should be shown
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      expect(screen.queryByText('Test Article 2')).not.toBeInTheDocument();
      expect(screen.getByText('篩選後: 1')).toBeInTheDocument();
    });
  });
});
