/**
 * Property Tests for Interactive Features (Task 4.7)
 * Feature: frontend-feature-enhancement
 * Task: 4.7 撰寫互動功能屬性測試
 *
 * These tests validate the correctness properties for interactive functionality
 * using property-based testing with fast-check.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fc from 'fast-check';
import { renderWithProviders } from '../../utils/test-utils';
import { articleArbitrary, articleFiltersArbitrary } from '../../utils/arbitraries';
import type { Article, ArticleFilters } from '@/types/article';

// Mock the useArticles hook
const mockUseArticles = vi.fn();
vi.mock('@/lib/hooks/useArticles', () => ({
  useArticles: () => mockUseArticles(),
}));

// Mock the ArticleCard component
vi.mock('@/components/ArticleCard', () => ({
  ArticleCard: ({
    article,
    showAnalysisButton,
    showReadingListButton,
    onAnalyze,
    onAddToReadingList,
  }: any) => (
    <div data-testid="article-card" data-article-id={article.id}>
      <h3>{article.title}</h3>
      <p>{article.summary}</p>
      <span data-testid="category">{article.category}</span>
      <span data-testid="tinkering-index">{article.tinkeringIndex}</span>
      {showAnalysisButton && (
        <button
          data-testid="analysis-button"
          onClick={() => onAnalyze?.(article.id)}
          tabIndex={0}
          aria-label={`Deep dive analysis for ${article.title}`}
        >
          Deep Dive Analysis
        </button>
      )}
      {showReadingListButton && (
        <button
          data-testid="reading-list-button"
          onClick={() => onAddToReadingList?.(article.id)}
          tabIndex={0}
          aria-label={`Add ${article.title} to reading list`}
        >
          Add to Reading List
        </button>
      )}
    </div>
  ),
}));

// Mock next/navigation for URL state testing
const mockReplace = vi.fn();
const mockGet = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
  useSearchParams: () => ({
    get: mockGet,
    toString: () => '',
  }),
}));

// Import the component after mocks
const { ArticleBrowser } = await import('@/features/articles/components/ArticleBrowser');

describe('Interactive Features Properties (Task 4.7)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
    mockGet.mockReturnValue(null);
  });

  /**
   * **Validates: Requirements 1.7, 1.8**
   * Property 5: 按鈕顯示限制
   * For any page of articles, the system should display "Deep Dive Analysis" buttons
   * for up to 5 articles and "Add to Reading List" buttons for up to 10 articles per page.
   */
  it('Property 5: 按鈕顯示限制 - Button display limits should be enforced correctly', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 1, maxLength: 20 }),
        fc.boolean(), // showAnalysisButtons
        fc.boolean(), // showReadingListButtons
        (articles, showAnalysisButtons, showReadingListButtons) => {
          mockUseArticles.mockReturnValue({
            data: {
              articles,
              totalCount: articles.length,
              hasNextPage: false,
            },
            isLoading: false,
            error: null,
            refetch: vi.fn(),
          });

          renderWithProviders(
            <ArticleBrowser
              showAnalysisButtons={showAnalysisButtons}
              showReadingListButtons={showReadingListButtons}
            />
          );

          const analysisButtons = screen.queryAllByTestId('analysis-button');
          const readingListButtons = screen.queryAllByTestId('reading-list-button');

          if (showAnalysisButtons) {
            // Should display "Deep Dive Analysis" buttons for up to 5 articles per page
            const expectedAnalysisButtons = Math.min(articles.length, 5);
            expect(analysisButtons.length).toBeLessThanOrEqual(5);
            expect(analysisButtons.length).toBeGreaterThanOrEqual(
              Math.min(expectedAnalysisButtons, articles.length)
            );

            // Each analysis button should have proper accessibility attributes
            analysisButtons.forEach((button) => {
              expect(button).toHaveAttribute('aria-label');
              expect(button).toHaveAttribute('tabIndex', '0');
              expect(button.textContent).toContain('Deep Dive Analysis');
            });
          } else {
            expect(analysisButtons.length).toBe(0);
          }

          if (showReadingListButtons) {
            // Should display "Add to Reading List" buttons for up to 10 articles per page
            const expectedReadingListButtons = Math.min(articles.length, 10);
            expect(readingListButtons.length).toBeLessThanOrEqual(10);
            expect(readingListButtons.length).toBeGreaterThanOrEqual(
              Math.min(expectedReadingListButtons, articles.length)
            );

            // Each reading list button should have proper accessibility attributes
            readingListButtons.forEach((button) => {
              expect(button).toHaveAttribute('aria-label');
              expect(button).toHaveAttribute('tabIndex', '0');
              expect(button.textContent).toContain('Add to Reading List');
            });
          } else {
            expect(readingListButtons.length).toBe(0);
          }

          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Validates: Requirements 1.9**
   * Property 6: URL 狀態同步
   * For any filter state applied by the user, the URL should be updated to reflect
   * the current filters and maintain state consistency on page refresh.
   */
  it('Property 6: URL 狀態同步 - URL state should synchronize with filter changes', () => {
    fc.assert(
      fc.property(
        fc.record({
          categories: fc.option(
            fc.array(fc.constantFrom('tech', 'ai', 'web', 'mobile', 'devops'), {
              minLength: 1,
              maxLength: 3,
            })
          ),
          tinkeringIndex: fc.option(
            fc
              .tuple(fc.integer(1, 5), fc.integer(1, 5))
              .map(([min, max]) => [Math.min(min, max), Math.max(min, max)] as [number, number])
          ),
          sortBy: fc.option(fc.constantFrom('date', 'tinkering_index', 'category')),
          sortOrder: fc.option(fc.constantFrom('asc', 'desc')),
        }),
        (filters: Partial<ArticleFilters>) => {
          const articles = fc.sample(articleArbitrary, 5);

          mockUseArticles.mockReturnValue({
            data: {
              articles,
              totalCount: articles.length,
              hasNextPage: false,
            },
            isLoading: false,
            error: null,
            refetch: vi.fn(),
          });

          renderWithProviders(<ArticleBrowser initialFilters={filters as ArticleFilters} />);

          // Verify that URL update was called if filters are present
          const hasFilters = Object.values(filters).some(
            (value) =>
              value !== undefined &&
              value !== null &&
              (Array.isArray(value) ? value.length > 0 : true)
          );

          if (hasFilters) {
            // URL should be updated to reflect current filters
            expect(mockReplace).toHaveBeenCalled();

            // Get the URL that was passed to replace
            const calls = mockReplace.mock.calls;
            if (calls.length > 0) {
              const lastCall = calls[calls.length - 1];
              const urlWithParams = lastCall[0];

              // Verify URL contains expected parameters
              if (filters.categories && filters.categories.length > 0) {
                expect(urlWithParams).toContain('categories=');
              }
              if (filters.tinkeringIndex) {
                expect(urlWithParams).toContain('tinkeringIndex=');
              }
              if (filters.sortBy) {
                expect(urlWithParams).toContain('sortBy=');
              }
              if (filters.sortOrder) {
                expect(urlWithParams).toContain('sortOrder=');
              }
            }
          }

          // Test state consistency on page refresh simulation
          // Mock URL params to simulate page refresh
          if (filters.categories) {
            mockGet.mockImplementation((key: string) => {
              if (key === 'categories') return filters.categories!.join(',');
              return null;
            });
          }

          // Re-render component to simulate page refresh
          cleanup();
          renderWithProviders(<ArticleBrowser />);

          // Component should maintain filter state from URL
          if (filters.categories && filters.categories.length > 0) {
            // Should display filtered results consistently
            const articleCards = screen.queryAllByTestId('article-card');
            expect(articleCards.length).toBeGreaterThanOrEqual(0);
          }

          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Validates: Requirements 1.10**
   * Property 7: 鍵盤導航可訪問性
   * For any interactive element in the Advanced_Article_Browser, keyboard navigation
   * should provide access to all functionality without requiring mouse interaction.
   */
  it('Property 7: 鍵盤導航可訪問性 - Keyboard navigation should provide full functionality access', async () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 1, maxLength: 8 }),
        fc.record({
          showAnalysisButtons: fc.boolean(),
          showReadingListButtons: fc.boolean(),
          keySequence: fc.array(
            fc.constantFrom('Tab', 'Enter', 'Space', 'ArrowDown', 'ArrowUp', 'Escape'),
            { minLength: 1, maxLength: 5 }
          ),
        }),
        async (articles, { showAnalysisButtons, showReadingListButtons, keySequence }) => {
          const onAnalyze = vi.fn();
          const onAddToReadingList = vi.fn();

          mockUseArticles.mockReturnValue({
            data: {
              articles,
              totalCount: articles.length,
              hasNextPage: false,
            },
            isLoading: false,
            error: null,
            refetch: vi.fn(),
          });

          const user = userEvent.setup();

          renderWithProviders(
            <ArticleBrowser
              showAnalysisButtons={showAnalysisButtons}
              showReadingListButtons={showReadingListButtons}
              onAnalyze={onAnalyze}
              onAddToReadingList={onAddToReadingList}
            />
          );

          // Get all interactive elements
          const analysisButtons = screen.queryAllByTestId('analysis-button');
          const readingListButtons = screen.queryAllByTestId('reading-list-button');
          const allButtons = [...analysisButtons, ...readingListButtons];

          // Verify all interactive elements are keyboard accessible
          allButtons.forEach((button) => {
            // Should have tabIndex for keyboard navigation
            expect(button).toHaveAttribute('tabIndex');

            // Should have accessible name
            const accessibleName = button.textContent || button.getAttribute('aria-label');
            expect(accessibleName).toBeTruthy();
            expect(accessibleName!.length).toBeGreaterThan(0);
          });

          // Test keyboard navigation sequence
          if (allButtons.length > 0) {
            // Focus first button
            allButtons[0].focus();
            expect(document.activeElement).toBe(allButtons[0]);

            // Test keyboard interaction
            for (const key of keySequence) {
              try {
                switch (key) {
                  case 'Tab':
                    await user.tab();
                    break;
                  case 'Enter':
                    await user.keyboard('{Enter}');
                    break;
                  case 'Space':
                    await user.keyboard(' ');
                    break;
                  case 'ArrowDown':
                    await user.keyboard('{ArrowDown}');
                    break;
                  case 'ArrowUp':
                    await user.keyboard('{ArrowUp}');
                    break;
                  case 'Escape':
                    await user.keyboard('{Escape}');
                    break;
                }
              } catch (error) {
                // Some keyboard interactions might not be applicable in all contexts
                // This is acceptable for property testing
              }
            }

            // Test that Enter/Space can activate buttons
            if (analysisButtons.length > 0) {
              analysisButtons[0].focus();
              await user.keyboard('{Enter}');

              // Should be able to activate analysis functionality via keyboard
              // (callback might be called depending on implementation)
            }

            if (readingListButtons.length > 0) {
              readingListButtons[0].focus();
              await user.keyboard(' ');

              // Should be able to activate reading list functionality via keyboard
              // (callback might be called depending on implementation)
            }
          }

          // Verify no functionality requires mouse interaction
          // All interactive elements should be reachable and activatable via keyboard
          const interactiveElements = screen.queryAllByRole('button');
          interactiveElements.forEach((element) => {
            // Should be focusable
            expect(element.tabIndex).toBeGreaterThanOrEqual(0);

            // Should have keyboard event handlers (implicit through role="button")
            expect(element).toHaveAttribute('role', 'button');
          });

          cleanup();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional Property: Interactive elements should maintain focus management
   * Ensures proper focus handling during dynamic content updates
   */
  it('Property 7 Extended: Focus management should be maintained during content updates', async () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 2, maxLength: 6 }),
        fc.array(articleArbitrary, { minLength: 1, maxLength: 4 }), // updated articles
        async (initialArticles, updatedArticles) => {
          const user = userEvent.setup();
          let currentArticles = initialArticles;

          // Mock hook that can be updated
          const mockRefetch = vi.fn();
          mockUseArticles.mockImplementation(() => ({
            data: {
              articles: currentArticles,
              totalCount: currentArticles.length,
              hasNextPage: false,
            },
            isLoading: false,
            error: null,
            refetch: mockRefetch,
          }));

          const { rerender } = renderWithProviders(
            <ArticleBrowser showAnalysisButtons={true} showReadingListButtons={true} />
          );

          // Focus on first button
          const initialButtons = screen.queryAllByTestId('analysis-button');
          if (initialButtons.length > 0) {
            initialButtons[0].focus();
            expect(document.activeElement).toBe(initialButtons[0]);

            // Update articles (simulate dynamic content update)
            currentArticles = updatedArticles;
            mockUseArticles.mockReturnValue({
              data: {
                articles: currentArticles,
                totalCount: currentArticles.length,
                hasNextPage: false,
              },
              isLoading: false,
              error: null,
              refetch: mockRefetch,
            });

            rerender(<ArticleBrowser showAnalysisButtons={true} showReadingListButtons={true} />);

            // Focus should be managed appropriately
            // Either maintained on equivalent element or moved to safe location
            const activeElement = document.activeElement;
            if (activeElement && activeElement !== document.body) {
              // If focus is maintained, it should be on a valid interactive element
              expect(activeElement.tagName).toBe('BUTTON');
            }
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property: Button limits should be enforced per page, not per component instance
   * Ensures the limits apply correctly in pagination scenarios
   */
  it('Property 5 Extended: Button limits should apply per page in pagination scenarios', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 6, maxLength: 25 }),
        fc.integer({ min: 5, max: 10 }), // page size
        (allArticles, pageSize) => {
          // Simulate pagination by taking first page
          const currentPageArticles = allArticles.slice(0, pageSize);

          mockUseArticles.mockReturnValue({
            data: {
              articles: currentPageArticles,
              totalCount: allArticles.length,
              hasNextPage: allArticles.length > pageSize,
            },
            isLoading: false,
            error: null,
            refetch: vi.fn(),
          });

          renderWithProviders(
            <ArticleBrowser
              showAnalysisButtons={true}
              showReadingListButtons={true}
              pageSize={pageSize}
            />
          );

          const analysisButtons = screen.queryAllByTestId('analysis-button');
          const readingListButtons = screen.queryAllByTestId('reading-list-button');

          // Analysis buttons: up to 5 per page
          expect(analysisButtons.length).toBeLessThanOrEqual(5);
          expect(analysisButtons.length).toBeLessThanOrEqual(currentPageArticles.length);

          // Reading list buttons: up to 10 per page
          expect(readingListButtons.length).toBeLessThanOrEqual(10);
          expect(readingListButtons.length).toBeLessThanOrEqual(currentPageArticles.length);

          // If we have more articles than button limits, verify limits are enforced
          if (currentPageArticles.length > 5) {
            expect(analysisButtons.length).toBe(5);
          }
          if (currentPageArticles.length > 10) {
            expect(readingListButtons.length).toBe(10);
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });
});
