/**
 * Unit tests for TinkeringIndexStars component
 * Unified card layout visual verification
 *
 * Requirements:
 * - 25.1: Display tinkering index using 1-5 star icons with color coding
 * - 25.2: Use dynamic colored CPU badge (green for 1-2, blue for 3, purple for 4-5)
 * - 25.3: Display filled stars for rating value, outlined for remaining
 * - 25.6: Ensure responsive sizing with delicate stars
 * - 25.7: Include tooltip showing numeric value and description
 * - 25.8: Use consistent star icon sizing (14px delicate view)
 */

import { renderWithProviders as render, screen, waitFor } from '@/__tests__/utils/test-utils';
import userEvent from '@testing-library/user-event';
import { ArticleCard } from '@/components/ArticleCard';
import type { Article } from '@/types/article';

describe('TinkeringIndexStars', () => {
  const createMockArticle = (tinkeringIndex: number): Article => ({
    id: 'test-article',
    title: 'Test Article',
    url: 'https://example.com',
    feedName: 'Test Feed',
    category: 'Technology',
    publishedAt: new Date().toISOString(),
    tinkeringIndex,
    aiSummary: 'Test summary',
  });

  describe('Requirement 25.1: Display 1-5 star icons with color coding', () => {
    it('should render CPU badge and exactly 5 star icons', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const svgs = tinkeringContainer.querySelectorAll('svg');
      // 1 CPU icon + 5 stars = 6 SVGs
      expect(svgs).toHaveLength(6);
    });

    it('should render stars for index 1', () => {
      const article = createMockArticle(1);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 1 out of 5/i);
      expect(tinkeringContainer).toBeInTheDocument();
    });

    it('should render stars for index 5', () => {
      const article = createMockArticle(5);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 5 out of 5/i);
      expect(tinkeringContainer).toBeInTheDocument();
    });

    it('should clamp index below 1 to 1', () => {
      const article = createMockArticle(0);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 1 out of 5/i);
      expect(tinkeringContainer).toBeInTheDocument();
    });

    it('should clamp index above 5 to 5', () => {
      const article = createMockArticle(10);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 5 out of 5/i);
      expect(tinkeringContainer).toBeInTheDocument();
    });
  });

  describe('Requirement 25.2: Color coding CPU Badge (green 1-2, blue 3, purple 4-5)', () => {
    it('should use green color class for index 1', () => {
      const article = createMockArticle(1);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 1 out of 5/i);
      const cpuBadge = tinkeringContainer.querySelector('span');
      expect(cpuBadge).toHaveClass('bg-green-100');
      expect(cpuBadge).toHaveClass('text-green-800');
    });

    it('should use green color class for index 2', () => {
      const article = createMockArticle(2);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 2 out of 5/i);
      const cpuBadge = tinkeringContainer.querySelector('span');
      expect(cpuBadge).toHaveClass('bg-green-100');
    });

    it('should use blue color class for index 3', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const cpuBadge = tinkeringContainer.querySelector('span');
      expect(cpuBadge).toHaveClass('bg-blue-100');
      expect(cpuBadge).toHaveClass('text-blue-800');
    });

    it('should use purple color class for index 4', () => {
      const article = createMockArticle(4);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 4 out of 5/i);
      const cpuBadge = tinkeringContainer.querySelector('span');
      expect(cpuBadge).toHaveClass('bg-purple-100');
      expect(cpuBadge).toHaveClass('text-purple-800');
    });

    it('should use purple color class for index 5', () => {
      const article = createMockArticle(5);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 5 out of 5/i);
      const cpuBadge = tinkeringContainer.querySelector('span');
      expect(cpuBadge).toHaveClass('bg-purple-100');
    });
  });

  describe('Requirement 25.3: Filled stars for rating, outlined for remaining', () => {
    it('should show 3 filled stars and 2 outlined stars for index 3', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const svgs = Array.from(tinkeringContainer.querySelectorAll('svg')).slice(1);

      // First 3 stars should be filled
      expect(svgs[0]).toHaveClass('fill-foreground/45');
      expect(svgs[1]).toHaveClass('fill-foreground/45');
      expect(svgs[2]).toHaveClass('fill-foreground/45');

      // Last 2 stars should be outlined
      expect(svgs[3]).toHaveClass('text-muted-foreground/20');
      expect(svgs[3]).not.toHaveClass('fill-foreground/45');
      expect(svgs[4]).toHaveClass('text-muted-foreground/20');
      expect(svgs[4]).not.toHaveClass('fill-foreground/45');
    });

    it('should show 1 filled star and 4 outlined stars for index 1', () => {
      const article = createMockArticle(1);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 1 out of 5/i);
      const svgs = Array.from(tinkeringContainer.querySelectorAll('svg')).slice(1);

      // First star should be filled
      expect(svgs[0]).toHaveClass('fill-foreground/45');

      // Last 4 stars should be outlined
      for (let i = 1; i < 5; i++) {
        expect(svgs[i]).toHaveClass('text-muted-foreground/20');
        expect(svgs[i]).not.toHaveClass('fill-foreground/45');
      }
    });

    it('should show all 5 filled stars for index 5', () => {
      const article = createMockArticle(5);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 5 out of 5/i);
      const svgs = Array.from(tinkeringContainer.querySelectorAll('svg')).slice(1);

      // All stars should be filled
      for (let i = 0; i < 5; i++) {
        expect(svgs[i]).toHaveClass('fill-foreground/45');
      }
    });
  });

  describe('Requirement 25.6: Delicate size sizing layout', () => {
    it('should have h-3.5 w-3.5 standard delicate sizing classes', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const svgs = Array.from(tinkeringContainer.querySelectorAll('svg')).slice(1);

      svgs.forEach((star) => {
        expect(star).toHaveClass('h-3.5');
        expect(star).toHaveClass('w-3.5');
      });
    });
  });

  describe('Requirement 25.7: Tooltip showing numeric value and description', () => {
    it('should show tooltip with "1 - Beginner" for index 1', async () => {
      const user = userEvent.setup();
      const article = createMockArticle(1);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 1 out of 5/i);

      // Hover over the stars
      await user.hover(tinkeringContainer);

      // Wait for tooltip to appear
      await waitFor(() => {
        const tooltips = screen.getAllByText('1 - Beginner');
        expect(tooltips.length).toBeGreaterThan(0);
      });
    });

    it('should show tooltip with "3 - Intermediate" for index 3', async () => {
      const user = userEvent.setup();
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);

      await user.hover(tinkeringContainer);

      await waitFor(() => {
        const tooltips = screen.getAllByText('3 - Intermediate');
        expect(tooltips.length).toBeGreaterThan(0);
      });
    });

    it('should show tooltip with "5 - Advanced" for index 5', async () => {
      const user = userEvent.setup();
      const article = createMockArticle(5);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 5 out of 5/i);

      await user.hover(tinkeringContainer);

      await waitFor(() => {
        const tooltips = screen.getAllByText('5 - Advanced');
        expect(tooltips.length).toBeGreaterThan(0);
      });
    });

    it('should have cursor-help class to indicate tooltip availability', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      expect(tinkeringContainer).toHaveClass('cursor-help');
    });
  });

  describe('Requirement 25.8: Consistent delicate sizing', () => {
    it('should have responsive sizing min-h and min-w classes', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const svgs = Array.from(tinkeringContainer.querySelectorAll('svg')).slice(1);

      svgs.forEach((star) => {
        expect(star).toHaveClass('min-h-[14px]');
        expect(star).toHaveClass('min-w-[14px]');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA label with index and description', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(
        'Tinkering index: 3 out of 5 - Intermediate'
      );
      expect(tinkeringContainer).toBeInTheDocument();
    });

    it('should have role="img" for screen readers', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      expect(tinkeringContainer).toHaveAttribute('role', 'img');
    });

    it('should have aria-hidden="true" on individual star icons', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const svgs = Array.from(tinkeringContainer.querySelectorAll('svg')).slice(1);

      svgs.forEach((star) => {
        expect(star).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });

  describe('Visual Layout', () => {
    it('should display in a flex row with gap', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      expect(tinkeringContainer).toHaveClass('flex');
      expect(tinkeringContainer).toHaveClass('items-center');
      expect(tinkeringContainer).toHaveClass('gap-2');
    });
  });
});
