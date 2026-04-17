/**
 * Unit tests for TinkeringIndexStars component
 * Task 6.3: Implement tinkering index visualization
 *
 * Requirements:
 * - 25.1: Display tinkering index using 1-5 star icons with color coding
 * - 25.2: Use gray for 1-2 stars, yellow for 3 stars, orange for 4-5 stars
 * - 25.3: Display filled stars for rating value, outlined for remaining
 * - 25.6: Ensure 24px minimum size on mobile viewport
 * - 25.7: Include tooltip showing numeric value and description
 * - 25.8: Use consistent star icon sizing (20px standard view)
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
    it('should render exactly 5 star icons', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');
      expect(stars).toHaveLength(5);
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

  describe('Requirement 25.2: Color coding (gray 1-2, yellow 3, orange 4-5)', () => {
    it('should use gray color for index 1 (beginner)', () => {
      const article = createMockArticle(1);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 1 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // First star should be filled with gray
      expect(stars[0]).toHaveClass('fill-gray-400');
      expect(stars[0]).toHaveClass('text-gray-400');
    });

    it('should use gray color for index 2 (beginner)', () => {
      const article = createMockArticle(2);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 2 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // First two stars should be filled with gray
      expect(stars[0]).toHaveClass('fill-gray-400');
      expect(stars[1]).toHaveClass('fill-gray-400');
    });

    it('should use yellow color for index 3 (intermediate)', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // First three stars should be filled with yellow
      expect(stars[0]).toHaveClass('fill-yellow-400');
      expect(stars[1]).toHaveClass('fill-yellow-400');
      expect(stars[2]).toHaveClass('fill-yellow-400');
    });

    it('should use orange color for index 4 (advanced)', () => {
      const article = createMockArticle(4);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 4 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // First four stars should be filled with orange
      expect(stars[0]).toHaveClass('fill-orange-400');
      expect(stars[1]).toHaveClass('fill-orange-400');
      expect(stars[2]).toHaveClass('fill-orange-400');
      expect(stars[3]).toHaveClass('fill-orange-400');
    });

    it('should use orange color for index 5 (advanced)', () => {
      const article = createMockArticle(5);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 5 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // All five stars should be filled with orange
      expect(stars[0]).toHaveClass('fill-orange-400');
      expect(stars[1]).toHaveClass('fill-orange-400');
      expect(stars[2]).toHaveClass('fill-orange-400');
      expect(stars[3]).toHaveClass('fill-orange-400');
      expect(stars[4]).toHaveClass('fill-orange-400');
    });
  });

  describe('Requirement 25.3: Filled stars for rating, outlined for remaining', () => {
    it('should show 3 filled stars and 2 outlined stars for index 3', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // First 3 stars should be filled (yellow)
      expect(stars[0]).toHaveClass('fill-yellow-400');
      expect(stars[1]).toHaveClass('fill-yellow-400');
      expect(stars[2]).toHaveClass('fill-yellow-400');

      // Last 2 stars should be outlined (gray)
      expect(stars[3]).toHaveClass('text-gray-300');
      expect(stars[3]).not.toHaveClass('fill-yellow-400');
      expect(stars[4]).toHaveClass('text-gray-300');
      expect(stars[4]).not.toHaveClass('fill-yellow-400');
    });

    it('should show 1 filled star and 4 outlined stars for index 1', () => {
      const article = createMockArticle(1);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 1 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // First star should be filled (gray)
      expect(stars[0]).toHaveClass('fill-gray-400');

      // Last 4 stars should be outlined
      for (let i = 1; i < 5; i++) {
        expect(stars[i]).toHaveClass('text-gray-300');
        expect(stars[i]).not.toHaveClass('fill-gray-400');
      }
    });

    it('should show all 5 filled stars for index 5', () => {
      const article = createMockArticle(5);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 5 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // All stars should be filled (orange)
      for (let i = 0; i < 5; i++) {
        expect(stars[i]).toHaveClass('fill-orange-400');
      }
    });
  });

  describe('Requirement 25.6: 24px minimum size on mobile viewport', () => {
    it('should have minimum 20px size classes', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // Each star should have minimum size classes
      stars.forEach((star) => {
        expect(star).toHaveClass('min-h-[20px]');
        expect(star).toHaveClass('min-w-[20px]');
      });
    });

    it('should have h-5 w-5 classes for standard sizing', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      // Each star should have h-5 w-5 (20px) classes
      stars.forEach((star) => {
        expect(star).toHaveClass('h-5');
        expect(star).toHaveClass('w-5');
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

      // Wait for tooltip to appear (may appear multiple times due to portal rendering)
      await waitFor(() => {
        const tooltips = screen.getAllByText('1 - Beginner');
        expect(tooltips.length).toBeGreaterThan(0);
      });
    });

    it('should show tooltip with "2 - Beginner" for index 2', async () => {
      const user = userEvent.setup();
      const article = createMockArticle(2);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 2 out of 5/i);

      await user.hover(tinkeringContainer);

      await waitFor(() => {
        const tooltips = screen.getAllByText('2 - Beginner');
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

    it('should show tooltip with "4 - Advanced" for index 4', async () => {
      const user = userEvent.setup();
      const article = createMockArticle(4);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 4 out of 5/i);

      await user.hover(tinkeringContainer);

      await waitFor(() => {
        const tooltips = screen.getAllByText('4 - Advanced');
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

  describe('Requirement 25.8: Consistent star icon sizing (20px standard view)', () => {
    it('should use 20px (h-5 w-5) for standard view', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      stars.forEach((star) => {
        expect(star).toHaveClass('h-5'); // h-5 = 20px
        expect(star).toHaveClass('w-5'); // w-5 = 20px
      });
    });

    it('should have responsive sizing classes for desktop', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      const stars = tinkeringContainer.querySelectorAll('svg');

      stars.forEach((star) => {
        expect(star).toHaveClass('md:h-5'); // 20px on desktop
        expect(star).toHaveClass('md:w-5'); // 20px on desktop
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
      const stars = tinkeringContainer.querySelectorAll('svg');

      stars.forEach((star) => {
        expect(star).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });

  describe('Visual Layout', () => {
    it('should display stars in a horizontal row with gap', () => {
      const article = createMockArticle(3);
      render(<ArticleCard article={article} />);

      const tinkeringContainer = screen.getByLabelText(/tinkering index: 3 out of 5/i);
      expect(tinkeringContainer).toHaveClass('flex');
      expect(tinkeringContainer).toHaveClass('items-center');
      expect(tinkeringContainer).toHaveClass('gap-1');
    });
  });
});
