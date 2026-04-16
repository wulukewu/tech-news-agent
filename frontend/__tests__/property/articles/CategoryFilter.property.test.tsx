/**
 * Property Tests for Category Filtering Components
 * Feature: frontend-feature-enhancement
 * Task: 4.4 撰寫分類篩選屬性測試
 *
 * These tests validate the correctness properties of category filtering functionality
 * using property-based testing with fast-check.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fc from 'fast-check';
import { renderWithProviders } from '../../utils/test-utils';
import { CategoryFilterMenu } from '@/features/articles/components/CategoryFilterMenu';

// Mock the useCategories hook
const mockUseCategories = vi.fn();
vi.mock('@/lib/hooks/useArticles', () => ({
  useCategories: () => mockUseCategories(),
}));

describe('Category Filter Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  /**
   * **Validates: Requirements 1.2**
   * Property 2: 分類篩選選單正確性
   * For any category distribution dataset, the Category_Filter_Menu should display
   * the correct trigger text based on selection state.
   */
  it('Property 2: CategoryFilterMenu should display correct trigger text based on selection', () => {
    fc.assert(
      fc.property(
        // Generate category arrays of various sizes
        fc
          .array(
            fc.string({ minLength: 1, maxLength: 20 }).filter((s) => s.trim().length > 0),
            { minLength: 1, maxLength: 50 }
          )
          .map((categories) => [...new Set(categories)]), // Remove duplicates
        fc.array(fc.integer({ min: 0, max: 4 }), { maxLength: 3 }), // selection indices
        (categories, selectionIndices) => {
          if (categories.length === 0) return; // Skip empty categories

          // Create selection based on indices
          const selectedCategories = selectionIndices
            .filter((index) => index < categories.length)
            .map((index) => categories[index])
            .filter((cat, index, arr) => arr.indexOf(cat) === index); // Remove duplicates

          // Mock the hook to return our test categories
          mockUseCategories.mockReturnValue({
            data: categories,
            isLoading: false,
            error: null,
          });

          const mockOnCategoryChange = vi.fn();

          renderWithProviders(
            <CategoryFilterMenu
              selectedCategories={selectedCategories}
              onCategoryChange={mockOnCategoryChange}
              maxCategories={24}
            />
          );

          // Check the trigger button exists
          const trigger = screen.getByRole('combobox');
          expect(trigger).toBeInTheDocument();

          // Verify trigger text based on selection
          if (selectedCategories.length === 0) {
            expect(trigger).toHaveTextContent('顯示全部');
          } else if (selectedCategories.length === 1) {
            expect(trigger).toHaveTextContent(selectedCategories[0]);
          } else {
            expect(trigger).toHaveTextContent(`已選擇 ${selectedCategories.length} 個項目`);
          }

          // Verify badge count if multiple selections
          if (selectedCategories.length > 0) {
            const badge = screen.getByText(selectedCategories.length.toString());
            expect(badge).toBeInTheDocument();
          }

          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Validates: Requirements 1.2**
   * Property 2 Extended: CategoryFilterMenu should display selected categories as badges
   */
  it('Property 2 Extended: CategoryFilterMenu should display selected categories as badges', () => {
    fc.assert(
      fc.property(
        // Generate categories and selections
        fc
          .array(
            fc.string({ minLength: 1, maxLength: 15 }).filter((s) => s.trim().length > 0),
            { minLength: 3, maxLength: 10 }
          )
          .map((categories) => [...new Set(categories)]), // Remove duplicates
        fc.array(fc.integer({ min: 0, max: 2 }), { minLength: 1, maxLength: 3 }), // selection indices
        (categories, selectionIndices) => {
          if (categories.length === 0) return; // Skip empty categories

          // Create selection based on indices
          const selectedCategories = selectionIndices
            .filter((index) => index < categories.length)
            .map((index) => categories[index])
            .filter((cat, index, arr) => arr.indexOf(cat) === index); // Remove duplicates

          if (selectedCategories.length === 0) return; // Skip if no selection

          // Mock the hook to return our test categories
          mockUseCategories.mockReturnValue({
            data: categories,
            isLoading: false,
            error: null,
          });

          const mockOnCategoryChange = vi.fn();

          renderWithProviders(
            <CategoryFilterMenu
              selectedCategories={selectedCategories}
              onCategoryChange={mockOnCategoryChange}
              maxCategories={24}
            />
          );

          // Verify each selected category appears as a badge
          selectedCategories.forEach((category) => {
            const badge = screen.getByText(category);
            expect(badge).toBeInTheDocument();

            // Badge should be clickable (has X icon)
            const xIcon = badge.querySelector('svg');
            expect(xIcon).toBeInTheDocument();
          });

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * **Validates: Requirements 1.5**
   * Property 3: 即時篩選功能
   * For any combination of filter parameters, the callback should be called
   * with updated selection when categories are clicked.
   */
  it('Property 3: CategoryFilterMenu should call callback with updated selection', async () => {
    fc.assert(
      fc.property(
        // Generate categories and initial selections
        fc
          .array(
            fc.string({ minLength: 1, maxLength: 15 }).filter((s) => s.trim().length > 0),
            { minLength: 3, maxLength: 8 }
          )
          .map((categories) => [...new Set(categories)]), // Remove duplicates
        fc.array(fc.integer({ min: 0, max: 2 }), { maxLength: 2 }), // indices for initial selection
        async (categories, selectionIndices) => {
          if (categories.length === 0) return; // Skip empty categories

          // Create initial selection based on indices
          const initialSelection = selectionIndices
            .filter((index) => index < categories.length)
            .map((index) => categories[index])
            .filter((cat, index, arr) => arr.indexOf(cat) === index); // Remove duplicates

          // Mock the hook to return our test categories
          mockUseCategories.mockReturnValue({
            data: categories,
            isLoading: false,
            error: null,
          });

          const mockOnCategoryChange = vi.fn();
          const user = userEvent.setup();

          renderWithProviders(
            <CategoryFilterMenu
              selectedCategories={initialSelection}
              onCategoryChange={mockOnCategoryChange}
              maxCategories={24}
            />
          );

          // Test removing a category by clicking its badge
          if (initialSelection.length > 0) {
            const categoryToRemove = initialSelection[0];
            const badge = screen.getByText(categoryToRemove);

            await user.click(badge);

            // Verify the callback was called with the category removed
            const expectedSelection = initialSelection.filter((cat) => cat !== categoryToRemove);
            expect(mockOnCategoryChange).toHaveBeenCalledWith(expectedSelection);
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * **Validates: Requirements 1.5**
   * Property 3 Extended: Real-time filtering should not cause page navigation
   */
  it('Property 3 Extended: CategoryFilterMenu interactions should not cause navigation', async () => {
    fc.assert(
      fc.property(
        // Generate categories and selections
        fc
          .array(
            fc.string({ minLength: 1, maxLength: 15 }).filter((s) => s.trim().length > 0),
            { minLength: 2, maxLength: 5 }
          )
          .map((categories) => [...new Set(categories)]), // Remove duplicates
        fc.array(fc.integer({ min: 0, max: 1 }), { minLength: 1, maxLength: 2 }), // selection indices
        async (categories, selectionIndices) => {
          if (categories.length === 0) return; // Skip empty categories

          // Create selection based on indices
          const selectedCategories = selectionIndices
            .filter((index) => index < categories.length)
            .map((index) => categories[index])
            .filter((cat, index, arr) => arr.indexOf(cat) === index); // Remove duplicates

          if (selectedCategories.length === 0) return; // Skip if no selection

          // Mock the hook to return our test categories
          mockUseCategories.mockReturnValue({
            data: categories,
            isLoading: false,
            error: null,
          });

          const mockOnCategoryChange = vi.fn();
          const user = userEvent.setup();

          // Track navigation events to ensure no page refresh occurs
          const originalLocation = window.location.href;
          let navigationOccurred = false;

          // Mock window.location to detect navigation
          const mockLocation = {
            ...window.location,
            href: originalLocation,
            assign: vi.fn(() => {
              navigationOccurred = true;
            }),
            replace: vi.fn(() => {
              navigationOccurred = true;
            }),
            reload: vi.fn(() => {
              navigationOccurred = true;
            }),
          };
          Object.defineProperty(window, 'location', {
            value: mockLocation,
            writable: true,
          });

          renderWithProviders(
            <CategoryFilterMenu
              selectedCategories={selectedCategories}
              onCategoryChange={mockOnCategoryChange}
              maxCategories={24}
            />
          );

          // Click on a category badge to remove it
          const categoryToRemove = selectedCategories[0];
          const badge = screen.getByText(categoryToRemove);

          await user.click(badge);

          // Verify no navigation occurred (no page refresh)
          expect(navigationOccurred).toBe(false);
          expect(window.location.href).toBe(originalLocation);

          // Verify the callback was still called (functionality works)
          expect(mockOnCategoryChange).toHaveBeenCalled();

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * **Validates: Requirements 1.2, 1.5**
   * Property 2 & 3 Combined: Component should handle loading and error states correctly
   */
  it('Property 2 & 3 Combined: CategoryFilterMenu should handle loading and error states', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.constant({ isLoading: true, error: null, data: null }),
          fc.constant({ isLoading: false, error: new Error('Failed to load'), data: null }),
          fc.constant({ isLoading: false, error: null, data: [] })
        ),
        (hookState) => {
          // Mock the hook to return the test state
          mockUseCategories.mockReturnValue(hookState);

          const mockOnCategoryChange = vi.fn();

          renderWithProviders(
            <CategoryFilterMenu
              selectedCategories={[]}
              onCategoryChange={mockOnCategoryChange}
              maxCategories={24}
            />
          );

          const trigger = screen.getByRole('combobox');
          expect(trigger).toBeInTheDocument();

          if (hookState.isLoading) {
            expect(trigger).toHaveTextContent('載入分類中...');
            expect(trigger).toBeDisabled();
          } else if (hookState.error) {
            expect(trigger).toHaveTextContent('載入分類失敗');
            expect(trigger).toBeDisabled();
          } else if (hookState.data && hookState.data.length === 0) {
            expect(trigger).toHaveTextContent('沒有可用的分類');
            expect(trigger).toBeDisabled();
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * **Validates: Requirements 1.2**
   * Property 2 Accessibility: Component should have proper ARIA attributes
   */
  it('Property 2 Accessibility: CategoryFilterMenu should have proper ARIA attributes', () => {
    fc.assert(
      fc.property(
        fc
          .array(
            fc.string({ minLength: 1, maxLength: 15 }).filter((s) => s.trim().length > 0),
            { minLength: 1, maxLength: 10 }
          )
          .map((categories) => [...new Set(categories)]), // Remove duplicates
        (categories) => {
          if (categories.length === 0) return; // Skip empty categories

          // Mock the hook to return our test categories
          mockUseCategories.mockReturnValue({
            data: categories,
            isLoading: false,
            error: null,
          });

          const mockOnCategoryChange = vi.fn();

          renderWithProviders(
            <CategoryFilterMenu
              selectedCategories={[]}
              onCategoryChange={mockOnCategoryChange}
              maxCategories={24}
            />
          );

          const trigger = screen.getByRole('combobox');

          // Verify ARIA attributes
          expect(trigger).toHaveAttribute('role', 'combobox');
          expect(trigger).toHaveAttribute('aria-expanded', 'false');
          expect(trigger).toHaveAttribute('aria-haspopup');

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });
});
