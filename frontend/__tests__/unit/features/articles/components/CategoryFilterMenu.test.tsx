/**
 * CategoryFilterMenu Component Unit Tests
 *
 * Tests the functionality of the CategoryFilterMenu component including:
 * - Multi-select category filtering
 * - Search functionality
 * - Show all/show less toggle
 * - Real-time filtering
 * - Accessibility features
 *
 * Requirements: 1.2, 1.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, mockViewport } from '@/__tests__/utils/test-utils';
import { CategoryFilterMenu } from '@/features/articles/components/CategoryFilterMenu';
import type { CategoryOption } from '@/features/articles/components/CategoryFilterMenu';

describe('CategoryFilterMenu', () => {
  const mockCategories: CategoryOption[] = [
    { value: 'tech', label: 'Technology', count: 150 },
    { value: 'ai', label: 'Artificial Intelligence', count: 120 },
    { value: 'web', label: 'Web Development', count: 100 },
    { value: 'mobile', label: 'Mobile Development', count: 80 },
    { value: 'data', label: 'Data Science', count: 75 },
    { value: 'security', label: 'Cybersecurity', count: 60 },
    { value: 'cloud', label: 'Cloud Computing', count: 55 },
    { value: 'devops', label: 'DevOps', count: 50 },
    { value: 'blockchain', label: 'Blockchain', count: 45 },
    { value: 'iot', label: 'Internet of Things', count: 40 },
  ];

  const mockOnSelectionChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render with placeholder when no categories selected', () => {
      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
          placeholder="選擇分類..."
        />
      );

      expect(screen.getByText('選擇分類...')).toBeInTheDocument();
    });

    it('should display selected count when multiple categories selected', () => {
      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech', 'ai']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('已選擇 2 個分類')).toBeInTheDocument();
    });

    it('should display single category name when one selected', () => {
      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      expect(screen.getByText('Technology')).toBeInTheDocument();
    });
  });

  describe('Dropdown Interaction', () => {
    it('should open dropdown when trigger is clicked', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('Technology')).toBeInTheDocument();
        expect(screen.getByText('150')).toBeInTheDocument(); // Count badge
      });
    });

    it('should display categories sorted by count in descending order', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        const categoryItems = screen.getAllByRole('option');
        // First item should be Technology (highest count: 150)
        expect(categoryItems[0]).toHaveTextContent('Technology');
        expect(categoryItems[0]).toHaveTextContent('150');
      });
    });
  });

  describe('Category Selection', () => {
    it('should handle single category selection', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('Technology')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Technology'));

      expect(mockOnSelectionChange).toHaveBeenCalledWith(['tech']);
    });

    it('should handle multiple category selection', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('Artificial Intelligence')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Artificial Intelligence'));

      expect(mockOnSelectionChange).toHaveBeenCalledWith(['tech', 'ai']);
    });

    it('should handle category deselection', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech', 'ai']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('Technology')).toBeInTheDocument();
      });

      // Click already selected category to deselect
      await user.click(screen.getByText('Technology'));

      expect(mockOnSelectionChange).toHaveBeenCalledWith(['ai']);
    });
  });

  describe('Search Functionality', () => {
    it('should filter categories based on search query', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
          searchable={true}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('搜尋分類...')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('搜尋分類...');
      await user.type(searchInput, 'AI');

      await waitFor(() => {
        expect(screen.getByText('Artificial Intelligence')).toBeInTheDocument();
        expect(screen.queryByText('Technology')).not.toBeInTheDocument();
      });
    });

    it('should show "no results" message when search yields no matches', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
          searchable={true}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('搜尋分類...')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('搜尋分類...');
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText('找不到相關分類')).toBeInTheDocument();
      });
    });

    it('should not show search input when searchable is false', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
          searchable={false}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('搜尋分類...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Show All Functionality', () => {
    it('should show "Show All" button when categories exceed maxVisible', async () => {
      const user = userEvent.setup();
      const manyCategories = Array.from({ length: 30 }, (_, i) => ({
        value: `cat${i}`,
        label: `Category ${i}`,
        count: 100 - i,
      }));

      renderWithProviders(
        <CategoryFilterMenu
          categories={manyCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
          maxVisible={5}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('顯示全部 (30)')).toBeInTheDocument();
      });
    });

    it('should expand to show all categories when "Show All" is clicked', async () => {
      const user = userEvent.setup();
      const manyCategories = Array.from({ length: 10 }, (_, i) => ({
        value: `cat${i}`,
        label: `Category ${i}`,
        count: 100 - i,
      }));

      renderWithProviders(
        <CategoryFilterMenu
          categories={manyCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
          maxVisible={5}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('顯示全部 (10)')).toBeInTheDocument();
      });

      await user.click(screen.getByText('顯示全部 (10)'));

      await waitFor(() => {
        expect(screen.getByText('顯示較少')).toBeInTheDocument();
        // Should now show all categories
        expect(screen.getByText('Category 9')).toBeInTheDocument();
      });
    });
  });

  describe('Clear All Functionality', () => {
    it('should show clear all button when categories are selected', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech', 'ai']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('清除全部')).toBeInTheDocument();
        expect(screen.getByText('已選擇 2 個分類')).toBeInTheDocument();
      });
    });

    it('should clear all selections when clear all button is clicked', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech', 'ai']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));

      await waitFor(() => {
        expect(screen.getByText('清除全部')).toBeInTheDocument();
      });

      await user.click(screen.getByText('清除全部'));

      expect(mockOnSelectionChange).toHaveBeenCalledWith([]);
    });
  });

  describe('Selected Categories Display', () => {
    it('should display selected categories as badges below the trigger', () => {
      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech', 'ai']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      // Should show badges for selected categories
      expect(screen.getByText('Technology')).toBeInTheDocument();
      expect(screen.getByText('Artificial Intelligence')).toBeInTheDocument();
    });

    it('should allow removing categories by clicking on badges', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={['tech', 'ai']}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      // Click on the Technology badge to remove it
      const techBadge = screen.getByText('Technology');
      await user.click(techBadge);

      expect(mockOnSelectionChange).toHaveBeenCalledWith(['ai']);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-expanded', 'false');
    });

    it('should update aria-expanded when opened', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      await waitFor(() => {
        expect(trigger).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      renderWithProviders(
        <CategoryFilterMenu
          categories={mockCategories}
          selectedCategories={[]}
          onSelectionChange={mockOnSelectionChange}
          disabled={true}
        />
      );

      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeDisabled();
    });
  });
});
