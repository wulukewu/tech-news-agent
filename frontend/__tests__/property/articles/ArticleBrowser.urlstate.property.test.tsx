/**
 * Property tests for ArticleBrowser URL state management
 *
 * Tests the correctness properties for task 4.6:
 * - Property 6: URL 狀態同步
 * - Property 7: 鍵盤導航可訪問性
 *
 * Requirements: 1.9, 1.10
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import fc from 'fast-check';
import { useUrlState, useKeyboardNavigation, useFocusNavigation } from '@/lib/hooks/useUrlState';
import type { ArticleFilters } from '@/types/article';

// Mock next/navigation
const mockReplace = vi.fn();
const mockGet = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
  useSearchParams: () => ({
    get: mockGet,
  }),
}));

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    pathname: '/articles',
    search: '',
  },
  writable: true,
});

describe('ArticleBrowser URL State Management Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockReturnValue(null);
    window.location.search = '';
  });

  /**
   * Property 6: URL 狀態同步
   * For any filter state applied by the user, the URL should be updated
   * to reflect the current filters and maintain state consistency on page refresh.
   *
   * Validates: Requirements 1.9
   */
  it('should maintain URL state consistency for any filter combination', () => {
    fc.assert(
      fc.property(
        fc.record({
          categories: fc.option(
            fc.array(fc.constantFrom('tech', 'ai', 'web', 'mobile'), { minLength: 1, maxLength: 3 })
          ),
          minTinkeringIndex: fc.option(fc.integer({ min: 1, max: 5 })),
          maxTinkeringIndex: fc.option(fc.integer({ min: 1, max: 5 })),
          sortBy: fc.option(fc.constantFrom('date', 'tinkering_index', 'category')),
          sortOrder: fc.option(fc.constantFrom('asc', 'desc')),
        }),
        (filters: Partial<ArticleFilters>) => {
          // Ensure min <= max for tinkering index
          if (filters.minTinkeringIndex && filters.maxTinkeringIndex) {
            if (filters.minTinkeringIndex > filters.maxTinkeringIndex) {
              [filters.minTinkeringIndex, filters.maxTinkeringIndex] = [
                filters.maxTinkeringIndex,
                filters.minTinkeringIndex,
              ];
            }
          }

          const { result } = renderHook(() => useUrlState());

          // Simulate updating URL with filters
          result.current.updateUrl(filters as ArticleFilters);

          // Verify that updateUrl was called (router.replace should be called)
          if (
            Object.keys(filters).some((key) => filters[key as keyof ArticleFilters] !== undefined)
          ) {
            expect(mockReplace).toHaveBeenCalled();

            // Get the URL that was passed to replace
            const lastCall = mockReplace.mock.calls[mockReplace.mock.calls.length - 1];
            const urlWithParams = lastCall[0];

            // Verify URL contains expected parameters
            if (filters.categories && filters.categories.length > 0) {
              expect(urlWithParams).toContain('categories=');
            }
            if (filters.minTinkeringIndex) {
              expect(urlWithParams).toContain('minTinkering=');
            }
            if (filters.maxTinkeringIndex) {
              expect(urlWithParams).toContain('maxTinkering=');
            }
            if (filters.sortBy) {
              expect(urlWithParams).toContain('sortBy=');
            }
            if (filters.sortOrder) {
              expect(urlWithParams).toContain('sortOrder=');
            }
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property 7: 鍵盤導航可訪問性
   * For any interactive element in the Advanced_Article_Browser, keyboard navigation
   * should provide access to all functionality without requiring mouse interaction.
   *
   * Validates: Requirements 1.10
   */
  it('should handle keyboard navigation events correctly', () => {
    fc.assert(
      fc.property(
        fc.record({
          totalItems: fc.integer({ min: 0, max: 100 }),
          keyEvents: fc.array(
            fc.constantFrom('j', 'k', 'r', '/', 'escape', 'arrowdown', 'arrowup'),
            { minLength: 1, maxLength: 10 }
          ),
        }),
        ({ totalItems, keyEvents }) => {
          const mockCallbacks = {
            onRefresh: vi.fn(),
            onFocusSearch: vi.fn(),
            onNavigateNext: vi.fn(),
            onNavigatePrevious: vi.fn(),
            onEscape: vi.fn(),
          };

          // Test keyboard navigation hook
          renderHook(() => useKeyboardNavigation(mockCallbacks));

          // Test focus navigation hook
          const { result: focusResult } = renderHook(() => useFocusNavigation(totalItems));

          // Simulate keyboard events
          keyEvents.forEach((key) => {
            const event = new KeyboardEvent('keydown', { key });
            document.dispatchEvent(event);
          });

          // Test focus navigation methods
          if (totalItems > 0) {
            focusResult.current.navigateNext();
            expect(focusResult.current.focusedIndex).toBeGreaterThanOrEqual(0);
            expect(focusResult.current.focusedIndex).toBeLessThan(totalItems);

            focusResult.current.navigatePrevious();
            expect(focusResult.current.focusedIndex).toBeGreaterThanOrEqual(0);
            expect(focusResult.current.focusedIndex).toBeLessThan(totalItems);

            focusResult.current.clearFocus();
            expect(focusResult.current.focusedIndex).toBe(-1);
          }

          // Verify keyboard callbacks were called appropriately
          const refreshCount = keyEvents.filter((k) => k === 'r').length;
          const searchCount = keyEvents.filter((k) => k === '/').length;
          const escapeCount = keyEvents.filter((k) => k === 'escape').length;

          expect(mockCallbacks.onRefresh).toHaveBeenCalledTimes(refreshCount);
          expect(mockCallbacks.onFocusSearch).toHaveBeenCalledTimes(searchCount);
          expect(mockCallbacks.onEscape).toHaveBeenCalledTimes(escapeCount);
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property: Focus navigation bounds checking
   * For any total item count, focus navigation should never exceed array bounds
   * and should handle edge cases (empty lists, single items) correctly.
   */
  it('should maintain focus navigation within bounds', () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: 1000 }), (totalItems) => {
        const { result } = renderHook(() => useFocusNavigation(totalItems));

        // Test multiple navigation operations
        for (let i = 0; i < 10; i++) {
          result.current.navigateNext();
          if (totalItems > 0) {
            expect(result.current.focusedIndex).toBeGreaterThanOrEqual(0);
            expect(result.current.focusedIndex).toBeLessThan(totalItems);
          } else {
            expect(result.current.focusedIndex).toBe(-1);
          }

          result.current.navigatePrevious();
          if (totalItems > 0) {
            expect(result.current.focusedIndex).toBeGreaterThanOrEqual(0);
            expect(result.current.focusedIndex).toBeLessThan(totalItems);
          } else {
            expect(result.current.focusedIndex).toBe(-1);
          }
        }

        // Test direct focus setting
        if (totalItems > 0) {
          const randomIndex = Math.floor(Math.random() * totalItems);
          result.current.setFocus(randomIndex);
          expect(result.current.focusedIndex).toBe(randomIndex);

          // Test out-of-bounds focus setting
          result.current.setFocus(totalItems + 10);
          expect(result.current.focusedIndex).toBe(randomIndex); // Should not change

          result.current.setFocus(-5);
          expect(result.current.focusedIndex).toBe(randomIndex); // Should not change
        }

        // Test clear focus
        result.current.clearFocus();
        expect(result.current.focusedIndex).toBe(-1);
      }),
      { numRuns: 50 }
    );
  });
});
