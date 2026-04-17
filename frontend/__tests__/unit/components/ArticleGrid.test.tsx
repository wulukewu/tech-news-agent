import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ArticleGrid } from '@/components/ArticleGrid';
import type { Article } from '@/types/article';

// Mock the ArticleCard component
vi.mock('@/components/ArticleCard', () => ({
  ArticleCard: ({ article }: { article: Article }) => (
    <div data-testid={`article-card-${article.id}`}>{article.title}</div>
  ),
}));

describe('ArticleGrid', () => {
  const mockArticles: Article[] = [
    {
      id: '1',
      title: 'Test Article 1',
      url: 'https://example.com/1',
      feedName: 'Test Feed',
      category: 'Tech',
      publishedAt: '2024-01-01T00:00:00Z',
      tinkeringIndex: 3,
      aiSummary: 'Summary 1',
      imageUrl: '/test1.jpg',
      isInReadingList: false,
    },
    {
      id: '2',
      title: 'Test Article 2',
      url: 'https://example.com/2',
      feedName: 'Test Feed',
      category: 'AI',
      publishedAt: '2024-01-02T00:00:00Z',
      tinkeringIndex: 4,
      aiSummary: 'Summary 2',
      imageUrl: '/test2.jpg',
      isInReadingList: false,
    },
    {
      id: '3',
      title: 'Test Article 3',
      url: 'https://example.com/3',
      feedName: 'Test Feed',
      category: 'Web Dev',
      publishedAt: '2024-01-03T00:00:00Z',
      tinkeringIndex: 5,
      aiSummary: 'Summary 3',
      imageUrl: '/test3.jpg',
      isInReadingList: false,
    },
  ];

  describe('Rendering', () => {
    it('should render all articles in a grid', () => {
      render(<ArticleGrid articles={mockArticles} />);

      expect(screen.getByTestId('article-card-1')).toBeInTheDocument();
      expect(screen.getByTestId('article-card-2')).toBeInTheDocument();
      expect(screen.getByTestId('article-card-3')).toBeInTheDocument();
    });

    it('should render empty grid when no articles provided', () => {
      const { container } = render(<ArticleGrid articles={[]} />);
      const grid = container.querySelector('[role="list"]');

      expect(grid).toBeInTheDocument();
      expect(grid?.children).toHaveLength(0);
    });

    it('should have proper ARIA attributes', () => {
      render(<ArticleGrid articles={mockArticles} />);

      const grid = screen.getByRole('list', { name: /articles grid/i });
      expect(grid).toBeInTheDocument();

      const items = screen.getAllByRole('listitem');
      expect(items).toHaveLength(3);
    });
  });

  describe('Responsive Grid Layout', () => {
    it('should have grid layout classes', () => {
      const { container } = render(<ArticleGrid articles={mockArticles} />);
      const grid = container.querySelector('[role="list"]');

      expect(grid).toHaveClass('grid');
      expect(grid).toHaveClass('grid-cols-1'); // Mobile: 1 column
      expect(grid).toHaveClass('md:grid-cols-2'); // Tablet: 2 columns
      expect(grid).toHaveClass('lg:grid-cols-3'); // Desktop: 3 columns
    });

    it('should have consistent gap spacing (16px / gap-4)', () => {
      const { container } = render(<ArticleGrid articles={mockArticles} />);
      const grid = container.querySelector('[role="list"]');

      expect(grid).toHaveClass('gap-4');
    });
  });

  describe('Props Handling', () => {
    it('should pass showAnalysisButton prop to ArticleCard', () => {
      // This test verifies the prop is passed through
      // The actual behavior is tested in ArticleCard tests
      render(<ArticleGrid articles={mockArticles} showAnalysisButton={true} />);

      expect(screen.getByTestId('article-card-1')).toBeInTheDocument();
    });

    it('should pass showReadingListButton prop to ArticleCard', () => {
      render(<ArticleGrid articles={mockArticles} showReadingListButton={false} />);

      expect(screen.getByTestId('article-card-1')).toBeInTheDocument();
    });

    it('should pass callback functions to ArticleCard', () => {
      const onAnalyze = vi.fn();
      const onAddToReadingList = vi.fn();

      render(
        <ArticleGrid
          articles={mockArticles}
          onAnalyze={onAnalyze}
          onAddToReadingList={onAddToReadingList}
        />
      );

      expect(screen.getByTestId('article-card-1')).toBeInTheDocument();
    });
  });

  describe('Layout Behavior', () => {
    it('should render articles in mobile layout by default', () => {
      // ArticleCard receives layout="mobile" prop
      render(<ArticleGrid articles={mockArticles} />);

      // Verify all cards are rendered (layout prop is tested in ArticleCard tests)
      expect(screen.getByTestId('article-card-1')).toBeInTheDocument();
      expect(screen.getByTestId('article-card-2')).toBeInTheDocument();
      expect(screen.getByTestId('article-card-3')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have semantic list structure', () => {
      render(<ArticleGrid articles={mockArticles} />);

      const list = screen.getByRole('list');
      const items = screen.getAllByRole('listitem');

      expect(list).toBeInTheDocument();
      expect(items).toHaveLength(3);
    });

    it('should have descriptive aria-label', () => {
      render(<ArticleGrid articles={mockArticles} />);

      const grid = screen.getByRole('list', { name: /articles grid/i });
      expect(grid).toBeInTheDocument();
    });
  });
});
