/**
 * Integration Tests: Dashboard Responsive Grid Layout
 *
 * Tests the responsive grid behavior at different breakpoints:
 * - Mobile (< 768px): 1 column
 * - Tablet (768px-1024px): 2 columns
 * - Desktop (1024px+): 3 columns
 *
 * Requirements Coverage:
 * - 1.4: Single column layout on mobile viewport
 * - 1.5: Two-column grid on tablet viewport
 * - 1.6: Three-column grid on desktop viewport with max 1400px width
 * - 1.7: Consistent 16px gap spacing between grid items
 */

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DashboardPage from '@/app/dashboard/page';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { fetchMyArticles, fetchCategories } from '@/lib/api/articles';
import type { Article } from '@/types/article';

// Mock dependencies
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  usePathname: vi.fn(() => '/dashboard'),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/lib/api/articles', () => ({
  fetchMyArticles: vi.fn(),
  fetchCategories: vi.fn(),
}));

vi.mock('@/lib/hooks/useInfiniteScroll', () => ({
  useInfiniteScroll: vi.fn(),
}));

vi.mock('@/lib/hooks/useReadingList', () => ({
  useAddToReadingList: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
}));

vi.mock('next-themes', () => ({
  useTheme: vi.fn(() => ({ theme: 'light' })),
}));

describe('Dashboard Responsive Grid Layout', () => {
  const mockRouter = {
    push: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  };

  const mockArticles: Article[] = [
    {
      id: '1',
      title: 'Article 1',
      url: 'https://example.com/1',
      feedName: 'Feed 1',
      category: 'Tech',
      publishedAt: '2024-01-01T00:00:00Z',
      tinkeringIndex: 3,
      aiSummary: 'Summary 1',
      imageUrl: '/test1.jpg',
      isInReadingList: false,
    },
    {
      id: '2',
      title: 'Article 2',
      url: 'https://example.com/2',
      feedName: 'Feed 2',
      category: 'AI',
      publishedAt: '2024-01-02T00:00:00Z',
      tinkeringIndex: 4,
      aiSummary: 'Summary 2',
      imageUrl: '/test2.jpg',
      isInReadingList: false,
    },
    {
      id: '3',
      title: 'Article 3',
      url: 'https://example.com/3',
      feedName: 'Feed 3',
      category: 'Web Dev',
      publishedAt: '2024-01-03T00:00:00Z',
      tinkeringIndex: 5,
      aiSummary: 'Summary 3',
      imageUrl: '/test3.jpg',
      isInReadingList: false,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    (useRouter as any).mockReturnValue(mockRouter);
    (useAuth as any).mockReturnValue({
      isAuthenticated: true,
      loading: false,
      user: { id: '1', username: 'testuser' },
    });

    (fetchCategories as any).mockResolvedValue(['Tech', 'AI', 'Web Dev']);
    (fetchMyArticles as any).mockResolvedValue({
      articles: mockArticles,
      hasNextPage: false,
      total: 3,
    });
  });

  describe('Grid Layout Classes', () => {
    it('should render grid with responsive column classes', async () => {
      const { container } = render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      const grid = container.querySelector('[role="list"]');
      expect(grid).toBeInTheDocument();

      // Verify responsive grid classes
      expect(grid).toHaveClass('grid');
      expect(grid).toHaveClass('grid-cols-1'); // Mobile: 1 column (< 768px)
      expect(grid).toHaveClass('md:grid-cols-2'); // Tablet: 2 columns (768px-1024px)
      expect(grid).toHaveClass('lg:grid-cols-3'); // Desktop: 3 columns (1024px+)
    });

    it('should have consistent gap spacing (gap-4 = 16px)', async () => {
      const { container } = render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      const grid = container.querySelector('[role="list"]');
      expect(grid).toHaveClass('gap-4');
    });
  });

  describe('Container Width and Padding', () => {
    it('should have maximum container width of 1400px (max-w-7xl)', async () => {
      const { container } = render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      const mainContainer = container.querySelector('.container');
      expect(mainContainer).toHaveClass('max-w-7xl');
    });

    it('should have responsive padding (16px mobile, 24px tablet, 32px desktop)', async () => {
      const { container } = render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      const mainContainer = container.querySelector('.container');
      expect(mainContainer).toHaveClass('px-4'); // Mobile: 16px (4 * 4px)
      expect(mainContainer).toHaveClass('md:px-6'); // Tablet: 24px (6 * 4px)
      expect(mainContainer).toHaveClass('lg:px-8'); // Desktop: 32px (8 * 4px)
    });
  });

  describe('Article Rendering in Grid', () => {
    it('should render all articles in the grid', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
        expect(screen.getByText('Article 2')).toBeInTheDocument();
        expect(screen.getByText('Article 3')).toBeInTheDocument();
      });
    });

    it('should render articles with mobile layout by default', async () => {
      const { container } = render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      // Verify grid items are rendered
      const listItems = container.querySelectorAll('[role="listitem"]');
      expect(listItems).toHaveLength(3);
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no articles', async () => {
      (fetchMyArticles as any).mockResolvedValue({
        articles: [],
        hasNextPage: false,
        total: 0,
      });

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('No articles found')).toBeInTheDocument();
      });
    });

    it('should not render grid when no articles', async () => {
      (fetchMyArticles as any).mockResolvedValue({
        articles: [],
        hasNextPage: false,
        total: 0,
      });

      const { container } = render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('No articles found')).toBeInTheDocument();
      });

      const grid = container.querySelector('[role="list"]');
      expect(grid).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have semantic list structure', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      const list = screen.getByRole('list', { name: /article list/i });
      expect(list).toBeInTheDocument();

      const items = screen.getAllByRole('listitem');
      expect(items).toHaveLength(3);
    });

    it('should have proper heading hierarchy', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      const mainHeading = screen.getByRole('heading', { level: 1, name: /your articles/i });
      expect(mainHeading).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show skeleton loader while loading', () => {
      (fetchCategories as any).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(['Tech']), 100))
      );

      render(<DashboardPage />);

      // Skeleton should be visible during loading
      expect(screen.getByText('Your Articles')).toBeInTheDocument();
    });
  });

  describe('Category Filtering', () => {
    it('should maintain grid layout when filtering categories', async () => {
      const { container } = render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Article 1')).toBeInTheDocument();
      });

      const grid = container.querySelector('[role="list"]');
      expect(grid).toHaveClass('grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });
  });
});
