'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { ArticleFilters } from '@/types/article';

/**
 * Hook for managing URL state synchronization with article filters
 *
 * Features:
 * - Syncs filter state with URL search parameters
 * - Maintains filter state on page refresh
 * - Provides clean URL updates without page reload
 * - Handles encoding/decoding of complex filter objects
 *
 * Requirements:
 * - 1.9: URL state synchronization for filter persistence
 */
export function useUrlState() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isInitialized, setIsInitialized] = useState(false);

  // Parse filters from URL search parameters
  const parseFiltersFromUrl = useCallback((): ArticleFilters => {
    const filters: ArticleFilters = {};

    // Parse categories (comma-separated)
    const categoriesParam = searchParams.get('categories');
    if (categoriesParam) {
      filters.categories = categoriesParam.split(',').filter(Boolean);
    }

    // Parse tinkering index range
    const minTinkeringIndex = searchParams.get('minTinkering');
    const maxTinkeringIndex = searchParams.get('maxTinkering');
    if (minTinkeringIndex) {
      const parsed = parseInt(minTinkeringIndex, 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed <= 5) {
        filters.minTinkeringIndex = parsed;
      }
    }
    if (maxTinkeringIndex) {
      const parsed = parseInt(maxTinkeringIndex, 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed <= 5) {
        filters.maxTinkeringIndex = parsed;
      }
    }

    // Parse sorting
    const sortBy = searchParams.get('sortBy');
    const sortOrder = searchParams.get('sortOrder');
    if (sortBy && ['date', 'tinkering_index', 'category'].includes(sortBy)) {
      filters.sortBy = sortBy as 'date' | 'tinkering_index' | 'category';
    }
    if (sortOrder && ['asc', 'desc'].includes(sortOrder)) {
      filters.sortOrder = sortOrder as 'asc' | 'desc';
    }

    // Parse date range (ISO strings)
    const startDate = searchParams.get('startDate');
    const endDate = searchParams.get('endDate');
    if (startDate) {
      const parsed = new Date(startDate);
      if (!isNaN(parsed.getTime())) {
        filters.startDate = parsed;
      }
    }
    if (endDate) {
      const parsed = new Date(endDate);
      if (!isNaN(parsed.getTime())) {
        filters.endDate = parsed;
      }
    }

    // Parse sources (comma-separated)
    const sourcesParam = searchParams.get('sources');
    if (sourcesParam) {
      filters.sources = sourcesParam.split(',').filter(Boolean);
    }

    return filters;
  }, [searchParams]);

  // Update URL with new filters
  const updateUrl = useCallback(
    (filters: ArticleFilters) => {
      const params = new URLSearchParams();

      // Add categories
      if (filters.categories && filters.categories.length > 0) {
        params.set('categories', filters.categories.join(','));
      }

      // Add tinkering index range
      if (filters.minTinkeringIndex !== undefined && filters.minTinkeringIndex !== null) {
        params.set('minTinkering', filters.minTinkeringIndex.toString());
      }
      if (filters.maxTinkeringIndex !== undefined && filters.maxTinkeringIndex !== null) {
        params.set('maxTinkering', filters.maxTinkeringIndex.toString());
      }

      // Add sorting
      if (filters.sortBy) {
        params.set('sortBy', filters.sortBy);
      }
      if (filters.sortOrder) {
        params.set('sortOrder', filters.sortOrder);
      }

      // Add date range
      if (filters.startDate) {
        params.set('startDate', filters.startDate.toISOString());
      }
      if (filters.endDate) {
        params.set('endDate', filters.endDate.toISOString());
      }

      // Add sources
      if (filters.sources && filters.sources.length > 0) {
        params.set('sources', filters.sources.join(','));
      }

      // Update URL without page reload
      const newUrl = params.toString() ? `?${params.toString()}` : '';
      const currentPath = window.location.pathname;

      // Only update if the URL actually changed
      if (window.location.search !== newUrl) {
        router.replace(`${currentPath}${newUrl}`, { scroll: false });
      }
    },
    [router]
  );

  // Get initial filters from URL on mount
  const [initialFilters, setInitialFilters] = useState<ArticleFilters>({});

  useEffect(() => {
    if (!isInitialized) {
      const filters = parseFiltersFromUrl();
      setInitialFilters(filters);
      setIsInitialized(true);
    }
  }, [parseFiltersFromUrl, isInitialized]);

  return {
    initialFilters: isInitialized ? initialFilters : {},
    updateUrl,
    isInitialized,
  };
}

/**
 * Hook for managing enhanced keyboard navigation in article browser
 *
 * Enhanced Features for Task 12.2:
 * - j/k navigation between articles
 * - r for refresh
 * - / for search focus
 * - Escape to clear focus
 * - Arrow keys for navigation
 * - f for toggle filters
 * - s for toggle sorting
 * - a for select all (when applicable)
 * - c for clear selections
 * - 1-5 for quick rating
 *
 * Requirements:
 * - 1.10: Keyboard navigation support for all interactive elements
 * - 7.7: Keyboard shortcuts (j/k navigation, r refresh)
 */
export function useKeyboardNavigation({
  onRefresh,
  onFocusSearch,
  onNavigateNext,
  onNavigatePrevious,
  onEscape,
  onToggleFilters,
  onToggleSorting,
  onSelectAll,
  onClearSelections,
  onQuickRating,
}: {
  onRefresh?: () => void;
  onFocusSearch?: () => void;
  onNavigateNext?: () => void;
  onNavigatePrevious?: () => void;
  onEscape?: () => void;
  onToggleFilters?: () => void;
  onToggleSorting?: () => void;
  onSelectAll?: () => void;
  onClearSelections?: () => void;
  onQuickRating?: (rating: number) => void;
}) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't handle keyboard shortcuts when user is typing in an input
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        event.target instanceof HTMLSelectElement ||
        (event.target as HTMLElement)?.contentEditable === 'true'
      ) {
        return;
      }

      // Handle modifier key combinations
      const isCtrlOrCmd = event.ctrlKey || event.metaKey;
      const isShift = event.shiftKey;

      switch (event.key.toLowerCase()) {
        case 'j':
          event.preventDefault();
          onNavigateNext?.();
          break;
        case 'k':
          event.preventDefault();
          onNavigatePrevious?.();
          break;
        case 'r':
          if (!isCtrlOrCmd) {
            // Avoid conflict with browser refresh
            event.preventDefault();
            onRefresh?.();
          }
          break;
        case '/':
          event.preventDefault();
          onFocusSearch?.();
          break;
        case 'escape':
          event.preventDefault();
          onEscape?.();
          break;
        case 'f':
          if (!isCtrlOrCmd) {
            event.preventDefault();
            onToggleFilters?.();
          }
          break;
        case 's':
          if (!isCtrlOrCmd) {
            event.preventDefault();
            onToggleSorting?.();
          }
          break;
        case 'a':
          if (isCtrlOrCmd) {
            event.preventDefault();
            onSelectAll?.();
          }
          break;
        case 'c':
          if (!isCtrlOrCmd) {
            event.preventDefault();
            onClearSelections?.();
          }
          break;
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
          if (!isCtrlOrCmd && !isShift) {
            event.preventDefault();
            const rating = parseInt(event.key, 10);
            onQuickRating?.(rating);
          }
          break;
        case 'arrowdown':
          if (isCtrlOrCmd) {
            event.preventDefault();
            onNavigateNext?.();
          }
          break;
        case 'arrowup':
          if (isCtrlOrCmd) {
            event.preventDefault();
            onNavigatePrevious?.();
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [
    onRefresh,
    onFocusSearch,
    onNavigateNext,
    onNavigatePrevious,
    onEscape,
    onToggleFilters,
    onToggleSorting,
    onSelectAll,
    onClearSelections,
    onQuickRating,
  ]);

  // Return keyboard shortcut help
  return {
    shortcuts: [
      { key: 'j', description: '下一篇文章' },
      { key: 'k', description: '上一篇文章' },
      { key: 'r', description: '重新整理' },
      { key: '/', description: '聚焦搜尋' },
      { key: 'f', description: '切換篩選器' },
      { key: 's', description: '切換排序' },
      { key: 'Ctrl+A', description: '全選' },
      { key: 'c', description: '清除選擇' },
      { key: '1-5', description: '快速評分' },
      { key: 'Esc', description: '清除焦點' },
    ],
  };
}

/**
 * Hook for managing focus navigation between article cards
 *
 * Features:
 * - Track currently focused article
 * - Navigate between articles with keyboard
 * - Scroll focused article into view
 * - Handle focus management for accessibility
 *
 * Requirements:
 * - 1.10: Keyboard navigation support for all interactive elements
 */
export function useFocusNavigation(totalItems: number) {
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);

  const navigateNext = useCallback(() => {
    if (totalItems === 0) return;

    setFocusedIndex((prev) => {
      const next = prev === -1 ? 0 : prev < totalItems - 1 ? prev + 1 : 0;

      // Scroll the focused element into view
      setTimeout(() => {
        const element = document.querySelector(`[data-article-index="${next}"]`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          (element as HTMLElement).focus();
        }
      }, 0);

      return next;
    });
  }, [totalItems]);

  const navigatePrevious = useCallback(() => {
    if (totalItems === 0) return;

    setFocusedIndex((prev) => {
      const next = prev === -1 ? totalItems - 1 : prev > 0 ? prev - 1 : totalItems - 1;

      // Scroll the focused element into view
      setTimeout(() => {
        const element = document.querySelector(`[data-article-index="${next}"]`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          (element as HTMLElement).focus();
        }
      }, 0);

      return next;
    });
  }, [totalItems]);

  const clearFocus = useCallback(() => {
    setFocusedIndex(-1);
    // Remove focus from any focused element
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
  }, []);

  const setFocus = useCallback(
    (index: number) => {
      if (index >= 0 && index < totalItems) {
        setFocusedIndex(index);
      }
    },
    [totalItems]
  );

  return {
    focusedIndex,
    navigateNext,
    navigatePrevious,
    clearFocus,
    setFocus,
  };
}
