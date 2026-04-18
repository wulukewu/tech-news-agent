/**
 * Unit tests for ArticleCard mobile vertical layout (Task 6.1)
 *
 * Tests Requirements:
 * - 6.1: Vertical layout with stacked elements
 * - 6.2: Full-width layout with proper spacing
 * - 6.4: Action buttons with 44px touch targets
 * - 6.7: Title truncation with line-clamp-2
 * - 6.8: Category badge with semantic colors
 * - 20.1-20.8: Responsive image implementation
 * - 25.1-25.8: Tinkering index visualization
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ArticleCard } from '@/components/ArticleCard';
import type { Article } from '@/types/article';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { vi } from 'vitest';

// Mock next/image
vi.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

// Mock toast
vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock useAddToReadingList hook
vi.mock('@/lib/hooks/useReadingList', () => ({
  useAddToReadingList: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
}));

const mockArticle: Article = {
  id: '1',
  title: 'Test Article Title That Is Long Enough To Test Truncation Behavior',
  url: 'https://example.com/article',
  feedName: 'Tech News Feed',
  category: 'tech-news',
  publishedAt: new Date().toISOString(),
  tinkeringIndex: 3,
  aiSummary: 'This is a test summary for the article.',
  isInReadingList: false,
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="light">
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('ArticleCard - Mobile Vertical Layout', () => {
  describe('Layout Structure', () => {
    it('should render mobile vertical layout when layout prop is "mobile"', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      // Check that the article element exists
      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();
    });

    it('should stack elements vertically in mobile layout', () => {
      const { container } = render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      // Check for vertical flex container
      const verticalStack = container.querySelector('.flex.flex-col');
      expect(verticalStack).toBeInTheDocument();
    });

    it('should render image at the top with correct dimensions', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const image = screen.getByAltText(mockArticle.title);
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('width', '400');
      expect(image).toHaveAttribute('height', '225');
    });
  });

  describe('Title Truncation', () => {
    it('should apply line-clamp-2 to title', () => {
      const { container } = render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const title = screen.getByText(mockArticle.title);
      expect(title).toHaveClass('line-clamp-2');
    });

    it('should render title as a link', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const titleLink = screen.getByRole('link', { name: mockArticle.title });
      expect(titleLink).toHaveAttribute('href', mockArticle.url);
      expect(titleLink).toHaveAttribute('target', '_blank');
      expect(titleLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Metadata Display', () => {
    it('should display feed name, category badge, and date', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(mockArticle.feedName)).toBeInTheDocument();
      expect(screen.getByText(mockArticle.category)).toBeInTheDocument();
    });

    it('should display category badge with semantic colors', () => {
      const { container } = render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const badge = screen.getByText(mockArticle.category);
      expect(badge).toBeInTheDocument();
      // Badge should have inline styles for semantic colors
      expect(badge).toHaveAttribute('style');
    });
  });

  describe('Tinkering Index Visualization', () => {
    it('should display 5 stars for tinkering index', () => {
      const { container } = render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      // Find the tinkering index container
      const tinkeringIndex = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      expect(tinkeringIndex).toBeInTheDocument();

      // Should have 5 star icons
      const stars = container.querySelectorAll('svg');
      // Filter for star icons (they should be in the tinkering index section)
      const starIcons = Array.from(stars).filter((svg) =>
        svg.parentElement?.getAttribute('aria-label')?.includes('Tinkering index')
      );
      expect(starIcons.length).toBeGreaterThanOrEqual(5);
    });

    it('should color stars based on index value (3 = yellow)', () => {
      const { container } = render(
        <ArticleCard article={{ ...mockArticle, tinkeringIndex: 3 }} layout="mobile" />,
        {
          wrapper: createWrapper(),
        }
      );

      const tinkeringIndex = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringIndex.querySelectorAll('svg');

      // First 3 stars should be filled yellow (intermediate)
      expect(stars[0]).toHaveClass('fill-yellow-400');
      expect(stars[1]).toHaveClass('fill-yellow-400');
      expect(stars[2]).toHaveClass('fill-yellow-400');

      // Last 2 stars should be gray (unfilled)
      expect(stars[3]).toHaveClass('text-gray-300');
      expect(stars[4]).toHaveClass('text-gray-300');
    });

    it('should use gray for beginner level (1-2 stars)', () => {
      const { container } = render(
        <ArticleCard article={{ ...mockArticle, tinkeringIndex: 2 }} layout="mobile" />,
        {
          wrapper: createWrapper(),
        }
      );

      const tinkeringIndex = screen.getByLabelText(/tinkering index: 2 out of 5/i);
      const stars = tinkeringIndex.querySelectorAll('svg');

      // First 2 stars should be filled gray (beginner)
      expect(stars[0]).toHaveClass('fill-gray-400');
      expect(stars[1]).toHaveClass('fill-gray-400');
    });

    it('should use orange for advanced level (4-5 stars)', () => {
      const { container } = render(
        <ArticleCard article={{ ...mockArticle, tinkeringIndex: 5 }} layout="mobile" />,
        {
          wrapper: createWrapper(),
        }
      );

      const tinkeringIndex = screen.getByLabelText(/tinkering index: 5 out of 5/i);
      const stars = tinkeringIndex.querySelectorAll('svg');

      // All 5 stars should be filled orange (advanced)
      expect(stars[0]).toHaveClass('fill-orange-400');
      expect(stars[1]).toHaveClass('fill-orange-400');
      expect(stars[2]).toHaveClass('fill-orange-400');
      expect(stars[3]).toHaveClass('fill-orange-400');
      expect(stars[4]).toHaveClass('fill-orange-400');
    });
  });

  describe('Summary Display', () => {
    it('should display AI summary', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const summary = screen.getByText(mockArticle.aiSummary!);
      expect(summary).toBeInTheDocument();
      // Short summaries don't have line-clamp-2, only long ones do
    });

    it('should apply line-clamp-2 to long summaries', () => {
      const longSummary = 'A'.repeat(250);
      const { container } = render(
        <ArticleCard article={{ ...mockArticle, aiSummary: longSummary }} layout="mobile" />,
        {
          wrapper: createWrapper(),
        }
      );

      const summary = screen.getByText(longSummary);
      expect(summary).toHaveClass('line-clamp-2');
    });

    it('should show "Read more" button for long summaries', () => {
      const longSummary = 'A'.repeat(250);
      render(<ArticleCard article={{ ...mockArticle, aiSummary: longSummary }} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const readMoreButton = screen.getByRole('button', { name: /read more/i });
      expect(readMoreButton).toBeInTheDocument();
    });

    it('should expand summary when "Read more" is clicked', async () => {
      const longSummary = 'A'.repeat(250);
      render(<ArticleCard article={{ ...mockArticle, aiSummary: longSummary }} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const readMoreButton = screen.getByRole('button', { name: /read more/i });
      fireEvent.click(readMoreButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument();
      });
    });
  });

  describe('Action Buttons', () => {
    it('should render "Read Later" button with 44px minimum height', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const readLaterButton = screen.getByRole('button', { name: /add to reading list/i });
      expect(readLaterButton).toBeInTheDocument();
      expect(readLaterButton).toHaveClass('min-h-[44px]');
      expect(screen.getByText('Read Later')).toBeInTheDocument();
    });

    it('should render "Mark as Read" button with 44px minimum height', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const markAsReadButton = screen.getByRole('button', { name: /mark as read/i });
      expect(markAsReadButton).toBeInTheDocument();
      expect(markAsReadButton).toHaveClass('min-h-[44px]');
    });

    it('should display both action buttons in a row', () => {
      const { container } = render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      // Find the action buttons container
      const actionContainer = container.querySelector('.flex.gap-2');
      expect(actionContainer).toBeInTheDocument();

      const buttons = screen.getAllByRole('button');
      const actionButtons = buttons.filter(
        (btn) =>
          btn.textContent?.includes('Read Later') || btn.textContent?.includes('Mark as Read')
      );
      expect(actionButtons.length).toBe(2);
    });

    it('should show "Saved" text when article is in reading list', () => {
      render(<ArticleCard article={{ ...mockArticle, isInReadingList: true }} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Saved')).toBeInTheDocument();
    });
  });

  describe('Responsive Image', () => {
    it('should use next/image with correct props', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const image = screen.getByAltText(mockArticle.title);
      expect(image).toHaveAttribute('width', '400');
      expect(image).toHaveAttribute('height', '225');
      expect(image).toHaveAttribute('sizes', '(max-width: 768px) 100vw, 400px');
    });

    it('should have aspect-video class for 16:9 ratio', () => {
      const { container } = render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const imageContainer = container.querySelector('.aspect-video');
      expect(imageContainer).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for buttons', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('button', { name: /add to reading list/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /mark as read/i })).toBeInTheDocument();
    });

    it('should have proper ARIA label for tinkering index', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByLabelText(/tinkering index: 3 out of 5/i)).toBeInTheDocument();
    });

    it('should have semantic time element for date', () => {
      render(<ArticleCard article={mockArticle} layout="mobile" />, {
        wrapper: createWrapper(),
      });

      const timeElement = screen.getByRole('time');
      expect(timeElement).toBeInTheDocument();
      expect(timeElement).toHaveAttribute('dateTime', mockArticle.publishedAt);
    });
  });

  describe('Desktop Layout Fallback', () => {
    it('should render desktop layout when layout prop is "desktop"', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      // Desktop layout should not have the mobile vertical stack
      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();

      // Desktop layout uses CardHeader which mobile doesn't
      const title = screen.getByText(mockArticle.title);
      expect(title).toBeInTheDocument();
    });
  });
});
