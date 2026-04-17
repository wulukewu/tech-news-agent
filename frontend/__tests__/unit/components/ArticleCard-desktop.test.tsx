/**
 * Unit tests for ArticleCard component - Desktop Horizontal Layout
 * Task 6.2: Create desktop horizontal layout for article card
 *
 * Requirements Coverage:
 * - 6.1: Display title, source, category, published date, tinkering index, summary
 * - 6.3: Use horizontal layout with image thumbnail on desktop
 * - 6.5: Hover effects (shadow elevation, subtle transform)
 * - 6.7: Truncate long titles to 3 lines on desktop
 * - 6.8: Display category badge with consistent color mapping
 */

import {
  renderWithProviders as render,
  screen,
  fireEvent,
  waitFor,
} from '@/__tests__/utils/test-utils';
import { ArticleCard } from '@/components/ArticleCard';
import type { Article } from '@/types/article';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';

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

describe('ArticleCard - Desktop Horizontal Layout', () => {
  const mockArticle: Article = {
    id: 'article-1',
    title:
      'Test Article Title for Desktop Layout with Very Long Title That Should Be Truncated to Three Lines Maximum',
    url: 'https://example.com/article',
    feedName: 'Tech Blog',
    category: 'Technology',
    publishedAt: new Date('2024-01-01').toISOString(),
    tinkeringIndex: 4,
    aiSummary:
      'This is a test article summary that is quite long and should be expandable when it exceeds 200 characters. '.repeat(
        3
      ),
  };

  describe('Layout Structure', () => {
    it('should render desktop horizontal layout when layout prop is "desktop"', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();

      // Desktop layout should have horizontal flex container
      const card = article.querySelector('.flex.gap-4');
      expect(card).toBeInTheDocument();
    });

    it('should position image on left side with 200x150 dimensions', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const image = screen.getByRole('img', { name: mockArticle.title });
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('width', '200');
      expect(image).toHaveAttribute('height', '150');

      // Image container should have fixed width and height
      const imageContainer = image.closest('.w-48.h-32');
      expect(imageContainer).toBeInTheDocument();
    });

    it('should position content on right side of image', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      // Content container should have flex-1 to take remaining space
      const article = screen.getByRole('article');
      const contentContainer = article.querySelector('.flex-1.flex-col');
      expect(contentContainer).toBeInTheDocument();
    });
  });

  describe('Title Truncation', () => {
    it('should apply line-clamp-3 for title truncation on desktop', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const titleLink = screen.getByRole('link', { name: new RegExp(mockArticle.title, 'i') });
      const titleElement = titleLink.querySelector('h3');
      expect(titleElement).toHaveClass('line-clamp-3');
    });

    it('should display full title for short titles', () => {
      const shortTitleArticle = {
        ...mockArticle,
        title: 'Short Title',
      };
      render(<ArticleCard article={shortTitleArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Short Title')).toBeInTheDocument();
    });
  });

  describe('Hover Effects', () => {
    it('should have hover shadow elevation class', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      const card = article.querySelector('.hover\\:shadow-lg');
      expect(card).toBeInTheDocument();
    });

    it('should have hover transform class for subtle elevation', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      const card = article.querySelector('.hover\\:-translate-y-1');
      expect(card).toBeInTheDocument();
    });

    it('should have transition-all class for smooth animations', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      const card = article.querySelector('.transition-all');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Share Button', () => {
    it('should display share button in top-right corner', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const shareButton = screen.getByRole('button', { name: /share article/i });
      expect(shareButton).toBeInTheDocument();
    });

    it('should have minimum 44px touch target for share button', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const shareButton = screen.getByRole('button', { name: /share article/i });
      expect(shareButton).toHaveClass('min-h-[44px]');
      expect(shareButton).toHaveClass('min-w-[44px]');
    });

    it('should have cursor-pointer class for share button', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const shareButton = screen.getByRole('button', { name: /share article/i });
      expect(shareButton).toHaveClass('cursor-pointer');
    });

    it('should copy link to clipboard when share is not supported', async () => {
      // Mock clipboard API
      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        clipboard: {
          writeText: writeTextMock,
        },
        share: undefined,
      });

      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const shareButton = screen.getByRole('button', { name: /share article/i });
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(writeTextMock).toHaveBeenCalledWith(mockArticle.url);
      });
    });
  });

  describe('Metadata Display', () => {
    it('should display source, category badge, and date in horizontal row', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Tech Blog')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();

      const timeElement = screen.getByRole('time');
      expect(timeElement).toBeInTheDocument();
    });

    it('should use gap-3 spacing between metadata items', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      const metadataContainer = article.querySelector('.flex.items-center.gap-3');
      expect(metadataContainer).toBeInTheDocument();
    });
  });

  describe('Tinkering Index Visualization', () => {
    it('should display tinkering index with star icons', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const tinkeringBadge = screen.getByLabelText(/tinkering index: 4 out of 5/i);
      expect(tinkeringBadge).toBeInTheDocument();
    });

    it('should use correct color coding for tinkering index', () => {
      // Test advanced level (4-5 stars) - orange
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const tinkeringBadge = screen.getByLabelText(/tinkering index: 4 out of 5 - advanced/i);
      expect(tinkeringBadge).toBeInTheDocument();
    });
  });

  describe('Summary Display', () => {
    it('should display AI summary with line-clamp-2', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const summary = screen.getByText(/this is a test article summary/i);
      expect(summary).toBeInTheDocument();
      expect(summary).toHaveClass('line-clamp-2');
    });

    it('should show "Read more" button for long summaries', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const readMoreButton = screen.getByRole('button', { name: /read more/i });
      expect(readMoreButton).toBeInTheDocument();
    });

    it('should expand summary when "Read more" is clicked', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const summary = screen.getByText(/this is a test article summary/i);
      expect(summary).toHaveClass('line-clamp-2');

      const readMoreButton = screen.getByRole('button', { name: /read more/i });
      fireEvent.click(readMoreButton);

      // Summary should expand - check for !line-clamp-none class
      expect(summary).toHaveClass('!line-clamp-none');
      expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('should display "Add to reading list" and "Mark as read" buttons', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('button', { name: /add to reading list/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /mark as read/i })).toBeInTheDocument();
    });

    it('should have minimum 44px touch targets for action buttons', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const addToReadingListButton = screen.getByRole('button', { name: /add to reading list/i });
      expect(addToReadingListButton).toHaveClass('min-h-[44px]');
      expect(addToReadingListButton).toHaveClass('min-w-[44px]');

      const markAsReadButton = screen.getByRole('button', { name: /mark as read/i });
      expect(markAsReadButton).toHaveClass('min-h-[44px]');
      expect(markAsReadButton).toHaveClass('min-w-[44px]');
    });

    it('should have cursor-pointer class for action buttons', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const addToReadingListButton = screen.getByRole('button', { name: /add to reading list/i });
      expect(addToReadingListButton).toHaveClass('cursor-pointer');

      const markAsReadButton = screen.getByRole('button', { name: /mark as read/i });
      expect(markAsReadButton).toHaveClass('cursor-pointer');
    });
  });

  describe('3-Column Grid Optimization', () => {
    it('should use flex layout that works well in grid', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      const card = article.querySelector('.flex.gap-4');
      expect(card).toBeInTheDocument();
    });

    it('should have proper spacing with gap-2 for content', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      const contentContainer = article.querySelector('.flex-1.flex-col.gap-2');
      expect(contentContainer).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for icon-only buttons', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const shareButton = screen.getByRole('button', { name: /share article/i });
      expect(shareButton).toHaveAttribute('aria-label', 'Share article');
    });

    it('should have semantic HTML structure', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();

      const heading = screen.getByRole('heading', { level: 3 });
      expect(heading).toBeInTheDocument();

      const timeElement = screen.getByRole('time');
      expect(timeElement).toBeInTheDocument();
    });

    it('should have proper link attributes for external links', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const titleLink = screen.getByRole('link', { name: new RegExp(mockArticle.title, 'i') });
      expect(titleLink).toHaveAttribute('target', '_blank');
      expect(titleLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Category Badge', () => {
    it('should display category badge with semantic colors', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const categoryBadge = screen.getByText('Technology');
      expect(categoryBadge).toBeInTheDocument();
    });

    it('should use consistent badge styling', () => {
      render(<ArticleCard article={mockArticle} layout="desktop" />, {
        wrapper: createWrapper(),
      });

      const categoryBadge = screen.getByText('Technology');
      // Badge should be a span or div with proper styling
      expect(categoryBadge.tagName).toMatch(/SPAN|DIV/i);
    });
  });
});
