import { renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  useScrollRestoration,
  clearScrollPosition,
  getScrollPosition,
} from '@/lib/hooks/useScrollRestoration';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/dashboard'),
}));

describe('useScrollRestoration', () => {
  let mockSessionStorage: { [key: string]: string };

  beforeEach(() => {
    // Mock sessionStorage
    mockSessionStorage = {};

    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn((key: string) => mockSessionStorage[key] || null),
        setItem: vi.fn((key: string, value: string) => {
          mockSessionStorage[key] = value;
        }),
        removeItem: vi.fn((key: string) => {
          delete mockSessionStorage[key];
        }),
        clear: vi.fn(() => {
          mockSessionStorage = {};
        }),
      },
      writable: true,
    });

    // Mock window.scrollTo
    window.scrollTo = vi.fn();

    // Mock window scroll position
    Object.defineProperty(window, 'scrollX', { value: 0, writable: true });
    Object.defineProperty(window, 'scrollY', { value: 0, writable: true });

    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  describe('useScrollRestoration', () => {
    it('should save scroll position on scroll event', () => {
      renderHook(() => useScrollRestoration('test-page'));

      // Simulate scroll
      Object.defineProperty(window, 'scrollX', { value: 100, writable: true });
      Object.defineProperty(window, 'scrollY', { value: 500, writable: true });

      window.dispatchEvent(new Event('scroll'));

      // Fast-forward timers to trigger debounced save
      vi.advanceTimersByTime(150);

      expect(window.sessionStorage.setItem).toHaveBeenCalledWith(
        'scroll-position-test-page',
        JSON.stringify({ x: 100, y: 500 })
      );
    });

    it('should save scroll position on beforeunload', () => {
      renderHook(() => useScrollRestoration('test-page'));

      Object.defineProperty(window, 'scrollX', { value: 200, writable: true });
      Object.defineProperty(window, 'scrollY', { value: 800, writable: true });

      window.dispatchEvent(new Event('beforeunload'));

      expect(window.sessionStorage.setItem).toHaveBeenCalledWith(
        'scroll-position-test-page',
        JSON.stringify({ x: 200, y: 800 })
      );
    });

    it('should restore scroll position on mount', () => {
      // Set up saved position
      mockSessionStorage['scroll-position-test-page'] = JSON.stringify({ x: 150, y: 600 });

      renderHook(() => useScrollRestoration('test-page'));

      // Fast-forward to trigger restoration
      vi.advanceTimersByTime(150);

      // Run pending animation frames
      vi.runAllTimers();

      expect(window.scrollTo).toHaveBeenCalledWith({
        left: 150,
        top: 600,
        behavior: 'instant',
      });
    });

    it('should not restore scroll position when no saved position exists', () => {
      renderHook(() => useScrollRestoration('test-page'));

      vi.advanceTimersByTime(150);
      vi.runAllTimers();

      expect(window.scrollTo).not.toHaveBeenCalled();
    });

    it('should handle popstate event for browser back/forward', () => {
      mockSessionStorage['scroll-position-test-page'] = JSON.stringify({ x: 100, y: 400 });

      renderHook(() => useScrollRestoration('test-page'));

      // Simulate browser back/forward
      window.dispatchEvent(new Event('popstate'));

      vi.advanceTimersByTime(100);

      expect(window.scrollTo).toHaveBeenCalledWith({
        left: 100,
        top: 400,
        behavior: 'instant',
      });
    });

    it('should not save or restore when enabled is false', () => {
      mockSessionStorage['scroll-position-test-page'] = JSON.stringify({ x: 100, y: 400 });

      renderHook(() => useScrollRestoration('test-page', false));

      // Try to trigger restoration
      vi.advanceTimersByTime(150);
      vi.runAllTimers();

      expect(window.scrollTo).not.toHaveBeenCalled();

      // Try to trigger save
      Object.defineProperty(window, 'scrollY', { value: 500, writable: true });
      window.dispatchEvent(new Event('scroll'));
      vi.advanceTimersByTime(150);

      expect(window.sessionStorage.setItem).not.toHaveBeenCalled();
    });

    it('should use pathname as default key', () => {
      renderHook(() => useScrollRestoration());

      Object.defineProperty(window, 'scrollY', { value: 300, writable: true });
      window.dispatchEvent(new Event('beforeunload'));

      expect(window.sessionStorage.setItem).toHaveBeenCalledWith(
        'scroll-position-/dashboard',
        expect.any(String)
      );
    });

    it('should clean up event listeners on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() => useScrollRestoration('test-page'));

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('popstate', expect.any(Function));
    });

    it('should handle sessionStorage errors gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      // Mock sessionStorage to throw error
      (window.sessionStorage.setItem as any).mockImplementation(() => {
        throw new Error('Storage quota exceeded');
      });

      renderHook(() => useScrollRestoration('test-page'));

      Object.defineProperty(window, 'scrollY', { value: 500, writable: true });
      window.dispatchEvent(new Event('beforeunload'));

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Failed to save scroll position:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('clearScrollPosition', () => {
    it('should remove scroll position from sessionStorage', () => {
      mockSessionStorage['scroll-position-test-page'] = JSON.stringify({ x: 100, y: 400 });

      clearScrollPosition('test-page');

      expect(window.sessionStorage.removeItem).toHaveBeenCalledWith('scroll-position-test-page');
      expect(mockSessionStorage['scroll-position-test-page']).toBeUndefined();
    });

    it('should handle errors gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      (window.sessionStorage.removeItem as any).mockImplementation(() => {
        throw new Error('Storage error');
      });

      clearScrollPosition('test-page');

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Failed to clear scroll position:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('getScrollPosition', () => {
    it('should retrieve saved scroll position', () => {
      mockSessionStorage['scroll-position-test-page'] = JSON.stringify({ x: 150, y: 600 });

      const position = getScrollPosition('test-page');

      expect(position).toEqual({ x: 150, y: 600 });
    });

    it('should return null when no position is saved', () => {
      const position = getScrollPosition('test-page');

      expect(position).toBeNull();
    });

    it('should handle errors gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      (window.sessionStorage.getItem as any).mockImplementation(() => {
        throw new Error('Storage error');
      });

      const position = getScrollPosition('test-page');

      expect(position).toBeNull();
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Failed to get scroll position:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });

    it('should handle invalid JSON gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      mockSessionStorage['scroll-position-test-page'] = 'invalid json';

      const position = getScrollPosition('test-page');

      expect(position).toBeNull();
      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });
  });
});
