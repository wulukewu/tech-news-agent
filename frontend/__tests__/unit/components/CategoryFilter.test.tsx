import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CategoryFilter } from '@/components/CategoryFilter';

describe('CategoryFilter', () => {
  const mockCategories = ['Tech News', 'AI/ML', 'Web Dev', 'DevOps', 'Security'];
  const mockOnToggleCategory = vi.fn();
  const mockOnSelectAll = vi.fn();
  const mockOnClearAll = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render all categories as badges', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      mockCategories.forEach((category) => {
        expect(screen.getByText(category)).toBeInTheDocument();
      });
    });

    it('should render Select All and Clear All buttons', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      expect(screen.getByText('Select All')).toBeInTheDocument();
      expect(screen.getByText('Clear All')).toBeInTheDocument();
    });

    it('should not render when categories array is empty', () => {
      const { container } = render(
        <CategoryFilter
          categories={[]}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('should render loading skeleton when loading is true', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
          loading={true}
        />
      );

      // Check for loading skeleton elements
      const skeletons = screen
        .getAllByRole('generic')
        .filter((el) => el.className.includes('animate-pulse'));
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Selection State', () => {
    it('should show selected categories with default variant', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={['Tech News', 'AI/ML']}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const techNewsBadge = screen.getByText('Tech News').closest('div');
      const aiMlBadge = screen.getByText('AI/ML').closest('div');
      const webDevBadge = screen.getByText('Web Dev').closest('div');

      // Selected badges should have aria-checked="true"
      expect(techNewsBadge).toHaveAttribute('aria-checked', 'true');
      expect(aiMlBadge).toHaveAttribute('aria-checked', 'true');
      expect(webDevBadge).toHaveAttribute('aria-checked', 'false');
    });

    it('should disable Select All button when all categories are selected', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={mockCategories}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const selectAllButton = screen.getByText('Select All');
      expect(selectAllButton).toBeDisabled();
    });

    it('should disable Clear All button when no categories are selected', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const clearAllButton = screen.getByText('Clear All');
      expect(clearAllButton).toBeDisabled();
    });
  });

  describe('Interactions', () => {
    it('should call onToggleCategory when a badge is clicked', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={['Tech News']}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const aiMlBadge = screen.getByText('AI/ML');
      fireEvent.click(aiMlBadge);

      expect(mockOnToggleCategory).toHaveBeenCalledWith('AI/ML');
      expect(mockOnToggleCategory).toHaveBeenCalledTimes(1);
    });

    it('should call onSelectAll when Select All button is clicked', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={['Tech News']}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const selectAllButton = screen.getByText('Select All');
      fireEvent.click(selectAllButton);

      expect(mockOnSelectAll).toHaveBeenCalledTimes(1);
    });

    it('should call onClearAll when Clear All button is clicked', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={['Tech News', 'AI/ML']}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const clearAllButton = screen.getByText('Clear All');
      fireEvent.click(clearAllButton);

      expect(mockOnClearAll).toHaveBeenCalledTimes(1);
    });
  });

  describe('Keyboard Navigation', () => {
    it('should call onToggleCategory when Enter key is pressed on a badge', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.keyDown(techNewsBadge, { key: 'Enter', code: 'Enter' });

      expect(mockOnToggleCategory).toHaveBeenCalledWith('Tech News');
    });

    it('should call onToggleCategory when Space key is pressed on a badge', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const aiMlBadge = screen.getByText('AI/ML');
      fireEvent.keyDown(aiMlBadge, { key: ' ', code: 'Space' });

      expect(mockOnToggleCategory).toHaveBeenCalledWith('AI/ML');
    });

    it('should not call onToggleCategory for other keys', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.keyDown(techNewsBadge, { key: 'a', code: 'KeyA' });

      expect(mockOnToggleCategory).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes on badges', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={['Tech News']}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const techNewsBadge = screen.getByText('Tech News').closest('div');
      expect(techNewsBadge).toHaveAttribute('role', 'checkbox');
      expect(techNewsBadge).toHaveAttribute('aria-checked', 'true');
      expect(techNewsBadge).toHaveAttribute('aria-label', 'Filter by Tech News');
      expect(techNewsBadge).toHaveAttribute('tabIndex', '0');
    });

    it('should have proper ARIA label on container', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const container = screen.getByRole('group');
      expect(container).toHaveAttribute('aria-label', 'Category filters');
    });

    it('should be keyboard focusable', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      mockCategories.forEach((category) => {
        const badge = screen.getByText(category).closest('div');
        expect(badge).toHaveAttribute('tabIndex', '0');
      });
    });
  });

  describe('Responsive Design', () => {
    it('should have horizontal scroll container classes', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const container = screen.getByRole('group');
      expect(container.className).toContain('overflow-x-auto');
      expect(container.className).toContain('scrollbar-hide');
      expect(container.className).toContain('snap-x');
    });

    it('should have minimum touch target size on badges', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      mockCategories.forEach((category) => {
        const badge = screen.getByText(category).closest('div');
        expect(badge?.className).toContain('min-h-[44px]');
      });
    });

    it('should prevent text wrapping on badges', () => {
      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      mockCategories.forEach((category) => {
        const badge = screen.getByText(category).closest('div');
        expect(badge?.className).toContain('whitespace-nowrap');
      });
    });
  });

  describe('Performance', () => {
    it('should update within 300ms of filter change', async () => {
      const startTime = Date.now();

      render(
        <CategoryFilter
          categories={mockCategories}
          selectedCategories={[]}
          onToggleCategory={mockOnToggleCategory}
          onSelectAll={mockOnSelectAll}
          onClearAll={mockOnClearAll}
        />
      );

      const techNewsBadge = screen.getByText('Tech News');
      fireEvent.click(techNewsBadge);

      const endTime = Date.now();
      const duration = endTime - startTime;

      // The component should respond immediately (< 300ms)
      expect(duration).toBeLessThan(300);
      expect(mockOnToggleCategory).toHaveBeenCalled();
    });
  });
});
