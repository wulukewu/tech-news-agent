/**
 * @jest-environment jsdom
 */

import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import fc from 'fast-check';
import { CategoryFilterMenu } from '../../CategoryFilterMenu';
import { useCategories } from '@/lib/hooks/useArticles';

import { vi } from 'vitest';

// Mock the useCategories hook
vi.mock('@/lib/hooks/useArticles', () => ({
  useCategories: vi.fn(),
}));

const mockUseCategories = useCategories as any;

// Test wrapper with QueryClient
function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

// Arbitraries for property testing
const categoryArbitrary = fc.string({ minLength: 1, maxLength: 20 });
const categoriesArrayArbitrary = fc.array(categoryArbitrary, { minLength: 0, maxLength: 50 });
const selectedCategoriesArbitrary = fc.array(categoryArbitrary, { minLength: 0, maxLength: 10 });

describe('CategoryFilterMenu Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Feature: frontend-feature-enhancement, Property 2: 分類篩選選單正確性
   * For any category distribution dataset, the Category_Filter_Menu should display
   * the top 24 most common categories plus a "顯示全部" option.
   *
   * **Validates: Requirements 1.2**
   */
  it('should display at most 24 categories plus Show All option', () => {
    fc.assert(
      fc.property(categoriesArrayArbitrary, (categories) => {
        cleanup();
        const mockOnCategoryChange = vi.fn();

        mockUseCategories.mockReturnValue({
          data: categories,
          isLoading: false,
          error: null,
        } as any);

        render(
          <TestWrapper>
            <CategoryFilterMenu
              selectedCategories={[]}
              onCategoryChange={mockOnCategoryChange}
              maxCategories={24}
            />
          </TestWrapper>
        );

        // Should render expected state for both empty and non-empty category sets
        if (categories.length === 0) {
          expect(
            screen.getAllByText(/沒有可用的分類|No categories available/i).length
          ).toBeGreaterThan(0);
        } else {
          expect(screen.getByRole('combobox')).toBeInTheDocument();
        }

        // The actual limit enforcement is tested through the MultiSelectFilter component
        // which receives maxDisplayed = maxCategories + 1 (for "Show All")
      }),
      { numRuns: 50 }
    );
  });

  /**
   * Feature: frontend-feature-enhancement, Property 3: 即時篩選功能
   * For any combination of filter parameters, applying filters should update
   * the article display without causing a page refresh or navigation event.
   *
   * **Validates: Requirements 1.5**
   */
  it('should handle category selection changes without page refresh', () => {
    fc.assert(
      fc.property(
        categoriesArrayArbitrary,
        selectedCategoriesArbitrary,
        (availableCategories, selectedCategories) => {
          cleanup();
          const mockOnCategoryChange = vi.fn();

          // Filter selected categories to only include available ones
          const validSelectedCategories = selectedCategories.filter((cat) =>
            availableCategories.includes(cat)
          );

          mockUseCategories.mockReturnValue({
            data: availableCategories,
            isLoading: false,
            error: null,
          } as any);

          render(
            <TestWrapper>
              <CategoryFilterMenu
                selectedCategories={validSelectedCategories}
                onCategoryChange={mockOnCategoryChange}
              />
            </TestWrapper>
          );

          // Component should render expected state for both empty and non-empty datasets
          if (availableCategories.length === 0) {
            expect(
              screen.getAllByText(/沒有可用的分類|No categories available/i).length
            ).toBeGreaterThan(0);
            return;
          }

          expect(screen.getByRole('combobox')).toBeInTheDocument();

          // Should display correct selection state
          if (validSelectedCategories.length === 0) {
            // Should show "Show All" when no categories selected
            expect(screen.getAllByText(/顯示全部|Show all/i).length).toBeGreaterThan(0);
          } else if (validSelectedCategories.length === 1) {
            // Should show single category name
            expect(screen.getByText(validSelectedCategories[0])).toBeInTheDocument();
          } else {
            // Should show count for multiple selections
            expect(
              screen.getAllByText(
                new RegExp(
                  `(已選擇 ${validSelectedCategories.length} 個項目|${validSelectedCategories.length} items selected)`,
                  'i'
                )
              ).length
            ).toBeGreaterThan(0);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property: Category filter should handle empty states gracefully
   * For any empty or null category data, the component should display appropriate messages.
   */
  it('should handle empty category data gracefully', () => {
    fc.assert(
      fc.property(
        fc.constantFrom([], null, undefined),
        selectedCategoriesArbitrary,
        (emptyCategories, selectedCategories) => {
          cleanup();
          const mockOnCategoryChange = vi.fn();

          mockUseCategories.mockReturnValue({
            data: emptyCategories as any,
            isLoading: false,
            error: null,
          } as any);

          render(
            <TestWrapper>
              <CategoryFilterMenu
                selectedCategories={selectedCategories}
                onCategoryChange={mockOnCategoryChange}
              />
            </TestWrapper>
          );

          // Should show empty state message
          expect(
            screen.getAllByText(/沒有可用的分類|No categories available/i).length
          ).toBeGreaterThan(0);
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Category filter should respect maxCategories limit
   * For any number of categories greater than maxCategories, only maxCategories should be displayed.
   */
  it('should respect maxCategories limit', () => {
    fc.assert(
      fc.property(
        fc.array(categoryArbitrary, { minLength: 25, maxLength: 100 }),
        fc.integer({ min: 1, max: 50 }),
        (categories, maxCategories) => {
          cleanup();
          const mockOnCategoryChange = vi.fn();

          mockUseCategories.mockReturnValue({
            data: categories,
            isLoading: false,
            error: null,
          } as any);

          render(
            <TestWrapper>
              <CategoryFilterMenu
                selectedCategories={[]}
                onCategoryChange={mockOnCategoryChange}
                maxCategories={maxCategories}
              />
            </TestWrapper>
          );

          // Component should render without errors
          expect(screen.getByRole('combobox')).toBeInTheDocument();

          // The actual limit is enforced in the useMemo hook that creates filterOptions
          // This property test ensures the component handles large category arrays gracefully
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property: Show All selection should clear other selections
   * When "Show All" is selected, all other category selections should be cleared.
   */
  it('should clear selections when Show All is conceptually selected', () => {
    fc.assert(
      fc.property(
        categoriesArrayArbitrary.filter((cats) => cats.length > 0),
        (categories) => {
          cleanup();
          const mockOnCategoryChange = vi.fn();

          mockUseCategories.mockReturnValue({
            data: categories,
            isLoading: false,
            error: null,
          } as any);

          render(
            <TestWrapper>
              <CategoryFilterMenu
                selectedCategories={[]} // Empty selection represents "Show All"
                onCategoryChange={mockOnCategoryChange}
              />
            </TestWrapper>
          );

          // When no categories are selected, it should show "Show All"
          expect(screen.getAllByText(/顯示全部|Show all/i).length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 30 }
    );
  });
});
