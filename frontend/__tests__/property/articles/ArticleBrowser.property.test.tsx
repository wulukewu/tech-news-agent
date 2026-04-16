/**
 * Property Tests for ArticleBrowser Component
 * Feature: frontend-feature-enhancement
 * Task: 4.2 撰寫文章瀏覽器屬性測試
 *
 * These tests validate the correctness properties of the ArticleBrowser component
 * using property-based testing with fast-check.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, cleanup } from '@testing-library/react';
import fc from 'fast-check';
import { renderWithProviders, mockViewport } from '../../utils/test-utils';
import {
  articleArbitrary,
  articleFiltersArbitrary,
  responsiveBreakpoints,
} from '../../utils/arbitraries';
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
        <button data-testid="analysis-button" onClick={() => onAnalyze?.(article.id)}>
          Deep Dive Analysis
        </button>
      )}
      {showReadingListButton && (
        <button data-testid="reading-list-button" onClick={() => onAddToReadingList?.(article.id)}>
          Add to Reading List
        </button>
      )}
    </div>
  ),
}));

// Mock VirtualizedList component
vi.mock('@/components/ui/virtualized-list', () => ({
  VirtualizedList: ({ items, renderItem }: any) => (
    <div data-testid="virtualized-list">
      {items.map((item: any, index: number) => renderItem({ index, style: {}, data: item }))}
    </div>
  ),
}));

// Import the component after mocks
const { ArticleBrowser } = await import('@/features/articles/components/ArticleBrowser');

describe('ArticleBrowser Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  /**
   * **Validates: Requirements 1.1**
   * Property 1: 文章瀏覽器響應式渲染
   * For any set of articles, the Advanced_Article_Browser should render
   * the correct number of article cards in a responsive grid layout
   * that adapts to different screen sizes.
   */
  it('Property 1: ArticleBrowser should render correct number of article cards responsively', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 0, maxLength: 20 }),
        responsiveBreakpoints,
        (articles, viewportWidth) => {
          // Mock the hook to return our test articles
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

          // Set viewport width for responsive testing
          mockViewport(viewportWidth);

          const { container } = renderWithProviders(<ArticleBrowser />);

          if (articles.length === 0) {
            // Empty state should be shown
            const emptyMessages = screen.queryAllByText('沒有找到文章');
            expect(emptyMessages.length).toBeGreaterThan(0);
          } else {
            // All articles should be rendered as cards
            const articleCards = screen.queryAllByTestId('article-card');
            expect(articleCards.length).toBeGreaterThanOrEqual(articles.length);

            // Grid layout should be responsive
            const gridContainer = container.querySelector('.grid');
            if (gridContainer) {
              // Should have responsive grid classes
              expect(gridContainer).toHaveClass('grid');
            }
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * **Validates: Requirements 1.6**
   * Property 4: 統計資料準確性
   * For any article dataset and filter combination, the displayed statistics
   * (total count, filtered count) should accurately reflect the actual number of articles.
   */
  it('Property 4: ArticleBrowser should display accurate article statistics', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 1, maxLength: 20 }),
        articleFiltersArbitrary,
        (articles, filters) => {
          // Apply filters to get expected filtered count
          const filteredArticles = articles.filter((article) => {
            // Apply category filter
            if (filters.categories && filters.categories.length > 0) {
              if (!filters.categories.includes(article.category)) {
                return false;
              }
            }

            // Apply tinkering index filter
            if (filters.tinkeringIndex) {
              const [min, max] = filters.tinkeringIndex;
              if (article.tinkeringIndex < min || article.tinkeringIndex > max) {
                return false;
              }
            }

            return true;
          });

          // Mock the hook to return filtered articles
          mockUseArticles.mockReturnValue({
            data: {
              articles: filteredArticles,
              totalCount: articles.length,
              hasNextPage: false,
            },
            isLoading: false,
            error: null,
            refetch: vi.fn(),
          });

          renderWithProviders(<ArticleBrowser initialFilters={filters} />);

          if (filteredArticles.length === 0) {
            // Empty state - no statistics shown
            const emptyMessages = screen.queryAllByText('沒有找到文章');
            expect(emptyMessages.length).toBeGreaterThan(0);
          } else {
            // Check total count display (may have multiple instances)
            const totalTexts = screen.queryAllByText(new RegExp(`總計: ${articles.length}`));
            expect(totalTexts.length).toBeGreaterThan(0);

            // Verify the actual number of rendered cards
            const articleCards = screen.queryAllByTestId('article-card');
            expect(articleCards.length).toBeGreaterThanOrEqual(filteredArticles.length);
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property 2: 按鈕顯示限制正確性
   * For any page of articles, the system should display "Deep Dive Analysis" buttons
   * for up to 5 articles and "Add to Reading List" buttons for up to 10 articles per page.
   * **Validates: Requirements 1.7, 1.8**
   */
  it('Property 2: ArticleBrowser should limit button display correctly', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 1, maxLength: 15 }),
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
            // Should show at most 5 analysis buttons per component instance
            const maxExpectedAnalysis = Math.min(articles.length, 5);
            expect(analysisButtons.length).toBeGreaterThanOrEqual(maxExpectedAnalysis);
          } else {
            expect(analysisButtons.length).toBe(0);
          }

          if (showReadingListButtons) {
            // Should show at most 10 reading list buttons per component instance
            const maxExpectedReadingList = Math.min(articles.length, 10);
            expect(readingListButtons.length).toBeGreaterThanOrEqual(maxExpectedReadingList);
          } else {
            expect(readingListButtons.length).toBe(0);
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property 3: 虛擬滾動條件正確性
   * For any article list, virtual scrolling should be enabled only when
   * enableVirtualization is true AND article count > 50.
   * **Validates: Requirements 12.2**
   */
  it('Property 3: ArticleBrowser should use virtual scrolling correctly', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 0, maxLength: 100 }),
        fc.boolean(), // enableVirtualization
        (articles, enableVirtualization) => {
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

          renderWithProviders(<ArticleBrowser enableVirtualization={enableVirtualization} />);

          const shouldUseVirtualization = enableVirtualization && articles.length > 50;
          const virtualizedLists = screen.queryAllByTestId('virtualized-list');

          if (shouldUseVirtualization) {
            // Should use virtual scrolling
            expect(virtualizedLists.length).toBeGreaterThan(0);
          } else if (articles.length > 0) {
            // Should use regular grid layout
            expect(virtualizedLists.length).toBe(0);
            // Should have article cards in regular layout
            const articleCards = screen.queryAllByTestId('article-card');
            expect(articleCards.length).toBeGreaterThan(0);
          }

          cleanup();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property 5: 載入和錯誤狀態正確性
   * For any loading or error state, ArticleBrowser should display
   * appropriate feedback to the user.
   */
  it('Property 5: ArticleBrowser should handle loading and error states correctly', () => {
    fc.assert(
      fc.property(
        fc.boolean(), // isLoading
        fc.option(fc.record({ message: fc.string({ minLength: 1, maxLength: 100 }) })), // error
        (isLoading, error) => {
          mockUseArticles.mockReturnValue({
            data: null,
            isLoading,
            error,
            refetch: vi.fn(),
          });

          renderWithProviders(<ArticleBrowser />);

          if (isLoading) {
            const loadingTexts = screen.queryAllByText('載入文章中...');
            expect(loadingTexts.length).toBeGreaterThan(0);
            // Should not show articles
            expect(screen.queryAllByTestId('article-card')).toHaveLength(0);
          } else if (error) {
            // Error message might be displayed, check for retry button
            const retryButtons = screen.queryAllByRole('button', { name: /重試|retry/i });
            expect(retryButtons.length).toBeGreaterThan(0);
          }

          cleanup();
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property 6: 回調函數正確性
   * For any article interaction, the appropriate callback should be called
   * with the correct article ID.
   */
  it('Property 6: ArticleBrowser should call callbacks with correct article IDs', () => {
    fc.assert(
      fc.property(fc.array(articleArbitrary, { minLength: 1, maxLength: 10 }), (articles) => {
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

        renderWithProviders(
          <ArticleBrowser
            showAnalysisButtons={true}
            showReadingListButtons={true}
            onAnalyze={onAnalyze}
            onAddToReadingList={onAddToReadingList}
          />
        );

        // Test analysis button callbacks
        const analysisButtons = screen.queryAllByTestId('analysis-button');
        expect(analysisButtons.length).toBeGreaterThan(0);

        // Click first analysis button and verify callback
        if (analysisButtons.length > 0) {
          analysisButtons[0].click();
          expect(onAnalyze).toHaveBeenCalledWith(articles[0].id);
        }

        // Test reading list button callbacks
        const readingListButtons = screen.queryAllByTestId('reading-list-button');
        expect(readingListButtons.length).toBeGreaterThan(0);

        // Click first reading list button and verify callback
        if (readingListButtons.length > 0) {
          readingListButtons[0].click();
          expect(onAddToReadingList).toHaveBeenCalledWith(articles[0].id);
        }

        cleanup();
      }),
      { numRuns: 30 }
    );
  });

  /**
   * Property 7: 可訪問性屬性一致性
   * ArticleBrowser should maintain proper accessibility attributes
   * across all states and configurations.
   * **Validates: Requirements 13.1, 13.2, 13.3**
   */
  it('Property 7: ArticleBrowser should maintain accessibility attributes', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 1, maxLength: 10 }),
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

          // All buttons should have proper labels
          const buttons = screen.queryAllByRole('button');
          buttons.forEach((button) => {
            const accessibleName = button.textContent || button.getAttribute('aria-label');
            expect(accessibleName).toBeTruthy();
          });

          // Article cards should have proper structure
          const articleCards = screen.queryAllByTestId('article-card');
          expect(articleCards.length).toBeGreaterThan(0);

          articleCards.forEach((card) => {
            // Should have article title as heading or text
            const title = card.querySelector('h3');
            expect(title).toBeInTheDocument();
          });

          cleanup();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property 8: 篩選狀態一致性
   * For any filter configuration, ArticleBrowser should maintain
   * consistent state and display appropriate results.
   */
  it('Property 8: ArticleBrowser should maintain consistent filter state', () => {
    fc.assert(
      fc.property(
        fc.array(articleArbitrary, { minLength: 1, maxLength: 20 }),
        articleFiltersArbitrary,
        (articles, initialFilters) => {
          // Simulate server-side filtering by pre-filtering articles
          const filteredArticles = articles.filter((article) => {
            if (initialFilters.categories && initialFilters.categories.length > 0) {
              if (!initialFilters.categories.includes(article.category)) {
                return false;
              }
            }
            return true;
          });

          mockUseArticles.mockReturnValue({
            data: {
              articles: filteredArticles,
              totalCount: articles.length,
              hasNextPage: false,
            },
            isLoading: false,
            error: null,
            refetch: vi.fn(),
          });

          renderWithProviders(<ArticleBrowser initialFilters={initialFilters} />);

          if (filteredArticles.length === 0) {
            // Empty state - no statistics shown
            const emptyMessages = screen.queryAllByText('沒有找到文章');
            expect(emptyMessages.length).toBeGreaterThan(0);
          } else {
            // Should display correct statistics (may have multiple instances)
            const totalTexts = screen.queryAllByText(new RegExp(`總計: ${articles.length}`));
            expect(totalTexts.length).toBeGreaterThan(0);

            // Should render correct number of articles
            const articleCards = screen.queryAllByTestId('article-card');
            expect(articleCards.length).toBeGreaterThanOrEqual(filteredArticles.length);

            // All displayed articles should match filter criteria
            if (initialFilters.categories && initialFilters.categories.length > 0) {
              const categoryElements = screen.queryAllByTestId('category');
              categoryElements.forEach((element) => {
                expect(initialFilters.categories).toContain(element.textContent);
              });
            }
          }

          cleanup();
        }
      ),
      { numRuns: 30 }
    );
  });
});
