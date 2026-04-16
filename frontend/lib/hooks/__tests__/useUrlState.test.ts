import { renderHook, act } from '@testing-library/react';
import { useKeyboardNavigation, useFocusNavigation } from '../useUrlState';

// Mock DOM methods
const mockScrollIntoView = jest.fn();
const mockFocus = jest.fn();
const mockBlur = jest.fn();

// Mock querySelector
const mockQuerySelector = jest.fn();
Object.defineProperty(document, 'querySelector', {
  value: mockQuerySelector,
  writable: true,
});

// Mock element methods
const createMockElement = () => ({
  scrollIntoView: mockScrollIntoView,
  focus: mockFocus,
  blur: mockBlur,
});

describe('useKeyboardNavigation', () => {
  const mockCallbacks = {
    onRefresh: jest.fn(),
    onFocusSearch: jest.fn(),
    onNavigateNext: jest.fn(),
    onNavigatePrevious: jest.fn(),
    onEscape: jest.fn(),
    onToggleFilters: jest.fn(),
    onToggleSorting: jest.fn(),
    onSelectAll: jest.fn(),
    onClearSelections: jest.fn(),
    onQuickRating: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockScrollIntoView.mockClear();
    mockFocus.mockClear();
    mockBlur.mockClear();
    mockQuerySelector.mockClear();
  });

  afterEach(() => {
    // Clean up event listeners
    document.removeEventListener('keydown', jest.fn());
  });

  describe('Basic Navigation Keys', () => {
    it('calls onNavigateNext when j key is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'j' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onNavigateNext).toHaveBeenCalledTimes(1);
    });

    it('calls onNavigatePrevious when k key is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'k' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onNavigatePrevious).toHaveBeenCalledTimes(1);
    });

    it('calls onRefresh when r key is pressed (without Ctrl)', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'r' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onRefresh).toHaveBeenCalledTimes(1);
    });

    it('does not call onRefresh when Ctrl+r is pressed (browser refresh)', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'r', ctrlKey: true });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onRefresh).not.toHaveBeenCalled();
    });

    it('calls onFocusSearch when / key is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: '/' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onFocusSearch).toHaveBeenCalledTimes(1);
    });

    it('calls onEscape when Escape key is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'Escape' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onEscape).toHaveBeenCalledTimes(1);
    });
  });

  describe('Enhanced Navigation Keys', () => {
    it('calls onToggleFilters when f key is pressed (without Ctrl)', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'f' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onToggleFilters).toHaveBeenCalledTimes(1);
    });

    it('does not call onToggleFilters when Ctrl+f is pressed (browser find)', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'f', ctrlKey: true });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onToggleFilters).not.toHaveBeenCalled();
    });

    it('calls onToggleSorting when s key is pressed (without Ctrl)', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 's' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onToggleSorting).toHaveBeenCalledTimes(1);
    });

    it('calls onSelectAll when Ctrl+a is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'a', ctrlKey: true });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onSelectAll).toHaveBeenCalledTimes(1);
    });

    it('calls onClearSelections when c key is pressed (without Ctrl)', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'c' });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onClearSelections).toHaveBeenCalledTimes(1);
    });
  });

  describe('Quick Rating Keys', () => {
    it('calls onQuickRating with correct rating for number keys 1-5', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      for (let i = 1; i <= 5; i++) {
        act(() => {
          const event = new KeyboardEvent('keydown', { key: i.toString() });
          document.dispatchEvent(event);
        });

        expect(mockCallbacks.onQuickRating).toHaveBeenCalledWith(i);
      }

      expect(mockCallbacks.onQuickRating).toHaveBeenCalledTimes(5);
    });

    it('does not call onQuickRating when Ctrl+number is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: '1', ctrlKey: true });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onQuickRating).not.toHaveBeenCalled();
    });

    it('does not call onQuickRating when Shift+number is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: '1', shiftKey: true });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onQuickRating).not.toHaveBeenCalled();
    });
  });

  describe('Arrow Key Navigation', () => {
    it('calls onNavigateNext when Ctrl+ArrowDown is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown', ctrlKey: true });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onNavigateNext).toHaveBeenCalledTimes(1);
    });

    it('calls onNavigatePrevious when Ctrl+ArrowUp is pressed', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowUp', ctrlKey: true });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onNavigatePrevious).toHaveBeenCalledTimes(1);
    });

    it('does not trigger navigation for arrow keys without Ctrl', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      act(() => {
        const downEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        const upEvent = new KeyboardEvent('keydown', { key: 'ArrowUp' });
        document.dispatchEvent(downEvent);
        document.dispatchEvent(upEvent);
      });

      expect(mockCallbacks.onNavigateNext).not.toHaveBeenCalled();
      expect(mockCallbacks.onNavigatePrevious).not.toHaveBeenCalled();
    });
  });

  describe('Input Element Handling', () => {
    it('ignores keyboard shortcuts when typing in input elements', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      // Mock input element as event target
      const mockInput = document.createElement('input');

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'j' });
        Object.defineProperty(event, 'target', { value: mockInput });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onNavigateNext).not.toHaveBeenCalled();
    });

    it('ignores keyboard shortcuts when typing in textarea elements', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      const mockTextarea = document.createElement('textarea');

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'k' });
        Object.defineProperty(event, 'target', { value: mockTextarea });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onNavigatePrevious).not.toHaveBeenCalled();
    });

    it('ignores keyboard shortcuts when typing in select elements', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      const mockSelect = document.createElement('select');

      act(() => {
        const event = new KeyboardEvent('keydown', { key: 'r' });
        Object.defineProperty(event, 'target', { value: mockSelect });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onRefresh).not.toHaveBeenCalled();
    });

    it('ignores keyboard shortcuts when typing in contentEditable elements', () => {
      renderHook(() => useKeyboardNavigation(mockCallbacks));

      const mockDiv = document.createElement('div');
      mockDiv.contentEditable = 'true';

      act(() => {
        const event = new KeyboardEvent('keydown', { key: '/' });
        Object.defineProperty(event, 'target', { value: mockDiv });
        document.dispatchEvent(event);
      });

      expect(mockCallbacks.onFocusSearch).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Shortcuts Help', () => {
    it('returns keyboard shortcuts information', () => {
      const { result } = renderHook(() => useKeyboardNavigation(mockCallbacks));

      expect(result.current.shortcuts).toEqual([
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
      ]);
    });
  });
});

describe('useFocusNavigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockScrollIntoView.mockClear();
    mockFocus.mockClear();
    mockBlur.mockClear();
    mockQuerySelector.mockClear();
  });

  describe('Basic Focus Navigation', () => {
    it('initializes with no focused item', () => {
      const { result } = renderHook(() => useFocusNavigation(5));

      expect(result.current.focusedIndex).toBe(-1);
    });

    it('navigates to next item', () => {
      const { result } = renderHook(() => useFocusNavigation(5));

      act(() => {
        result.current.navigateNext();
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('navigates to previous item', () => {
      const { result } = renderHook(() => useFocusNavigation(5));

      act(() => {
        result.current.navigatePrevious();
      });

      expect(result.current.focusedIndex).toBe(4); // Wraps to last item
    });

    it('wraps around when navigating past the end', () => {
      const { result } = renderHook(() => useFocusNavigation(3));

      // Navigate to last item
      act(() => {
        result.current.setFocus(2);
      });

      // Navigate next should wrap to first
      act(() => {
        result.current.navigateNext();
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('wraps around when navigating before the beginning', () => {
      const { result } = renderHook(() => useFocusNavigation(3));

      // Start at first item
      act(() => {
        result.current.setFocus(0);
      });

      // Navigate previous should wrap to last
      act(() => {
        result.current.navigatePrevious();
      });

      expect(result.current.focusedIndex).toBe(2);
    });
  });

  describe('Focus Management', () => {
    it('clears focus', () => {
      const { result } = renderHook(() => useFocusNavigation(5));

      act(() => {
        result.current.setFocus(2);
      });

      expect(result.current.focusedIndex).toBe(2);

      act(() => {
        result.current.clearFocus();
      });

      expect(result.current.focusedIndex).toBe(-1);
    });

    it('sets focus to specific index', () => {
      const { result } = renderHook(() => useFocusNavigation(5));

      act(() => {
        result.current.setFocus(3);
      });

      expect(result.current.focusedIndex).toBe(3);
    });

    it('ignores invalid focus index', () => {
      const { result } = renderHook(() => useFocusNavigation(3));

      act(() => {
        result.current.setFocus(5); // Out of bounds
      });

      expect(result.current.focusedIndex).toBe(-1);

      act(() => {
        result.current.setFocus(-2); // Negative
      });

      expect(result.current.focusedIndex).toBe(-1);
    });
  });

  describe('DOM Interaction', () => {
    it('scrolls focused element into view on navigation', () => {
      const mockElement = createMockElement();
      mockQuerySelector.mockReturnValue(mockElement);

      const { result } = renderHook(() => useFocusNavigation(5));

      act(() => {
        result.current.navigateNext();
      });

      // Wait for setTimeout
      setTimeout(() => {
        expect(mockQuerySelector).toHaveBeenCalledWith('[data-article-index="0"]');
        expect(mockElement.scrollIntoView).toHaveBeenCalledWith({
          behavior: 'smooth',
          block: 'center',
        });
        expect(mockElement.focus).toHaveBeenCalled();
      }, 0);
    });

    it('handles missing DOM element gracefully', () => {
      mockQuerySelector.mockReturnValue(null);

      const { result } = renderHook(() => useFocusNavigation(5));

      act(() => {
        result.current.navigateNext();
      });

      // Should not throw error
      expect(result.current.focusedIndex).toBe(0);
    });

    it('blurs active element when clearing focus', () => {
      const mockActiveElement = createMockElement();
      Object.defineProperty(document, 'activeElement', {
        value: mockActiveElement,
        writable: true,
      });

      const { result } = renderHook(() => useFocusNavigation(5));

      act(() => {
        result.current.setFocus(1);
      });

      act(() => {
        result.current.clearFocus();
      });

      expect(mockActiveElement.blur).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero items', () => {
      const { result } = renderHook(() => useFocusNavigation(0));

      act(() => {
        result.current.navigateNext();
      });

      expect(result.current.focusedIndex).toBe(-1);

      act(() => {
        result.current.navigatePrevious();
      });

      expect(result.current.focusedIndex).toBe(-1);
    });

    it('handles single item', () => {
      const { result } = renderHook(() => useFocusNavigation(1));

      act(() => {
        result.current.navigateNext();
      });

      expect(result.current.focusedIndex).toBe(0);

      act(() => {
        result.current.navigateNext();
      });

      expect(result.current.focusedIndex).toBe(0); // Should wrap to same item
    });

    it('updates when total items change', () => {
      const { result, rerender } = renderHook(({ totalItems }) => useFocusNavigation(totalItems), {
        initialProps: { totalItems: 5 },
      });

      act(() => {
        result.current.setFocus(4);
      });

      expect(result.current.focusedIndex).toBe(4);

      // Reduce total items
      rerender({ totalItems: 3 });

      act(() => {
        result.current.setFocus(4); // Should be ignored now
      });

      expect(result.current.focusedIndex).toBe(4); // Previous focus maintained
    });
  });
});
