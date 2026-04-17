import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

interface ScrollPosition {
  x: number;
  y: number;
}

/**
 * Custom hook for managing scroll position restoration across navigation
 *
 * Saves scroll position to sessionStorage when navigating away and restores it
 * when returning to the page. Handles both programmatic navigation and browser
 * back/forward buttons.
 *
 * @param key - Unique key for storing scroll position (default: pathname)
 * @param enabled - Whether scroll restoration is enabled (default: true)
 *
 * @example
 * ```tsx
 * function DashboardPage() {
 *   useScrollRestoration('dashboard');
 *
 *   return <div>...</div>;
 * }
 * ```
 */
export function useScrollRestoration(key?: string, enabled: boolean = true) {
  const pathname = usePathname();
  const storageKey = key || `scroll-position-${pathname}`;
  const isRestoringRef = useRef(false);

  // Save scroll position before navigating away
  useEffect(() => {
    if (!enabled) return;

    const saveScrollPosition = () => {
      const position: ScrollPosition = {
        x: window.scrollX,
        y: window.scrollY,
      };

      try {
        sessionStorage.setItem(storageKey, JSON.stringify(position));
      } catch (error) {
        // Silently fail if sessionStorage is unavailable
      }
    };

    // Save on route change (before unload)
    window.addEventListener('beforeunload', saveScrollPosition);

    // Save periodically while scrolling (for SPA navigation)
    let scrollTimeout: NodeJS.Timeout;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(saveScrollPosition, 100);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('beforeunload', saveScrollPosition);
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(scrollTimeout);
    };
  }, [storageKey, enabled]);

  // Restore scroll position on mount
  useEffect(() => {
    if (!enabled || isRestoringRef.current) return;

    const restoreScrollPosition = () => {
      try {
        const savedPosition = sessionStorage.getItem(storageKey);

        if (savedPosition) {
          const position: ScrollPosition = JSON.parse(savedPosition);

          // Use requestAnimationFrame to ensure DOM is ready
          requestAnimationFrame(() => {
            window.scrollTo({
              left: position.x,
              top: position.y,
              behavior: 'instant' as ScrollBehavior,
            });

            isRestoringRef.current = true;
          });
        }
      } catch (error) {
        // Silently fail if sessionStorage is unavailable
      }
    };

    // Restore after a short delay to ensure content is loaded
    const timeoutId = setTimeout(restoreScrollPosition, 100);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [storageKey, enabled]);

  // Handle browser back/forward navigation
  useEffect(() => {
    if (!enabled) return;

    const handlePopState = () => {
      // Restore scroll position on back/forward navigation
      const savedPosition = sessionStorage.getItem(storageKey);

      if (savedPosition) {
        try {
          const position: ScrollPosition = JSON.parse(savedPosition);

          // Delay restoration to ensure page is rendered
          setTimeout(() => {
            window.scrollTo({
              left: position.x,
              top: position.y,
              behavior: 'instant' as ScrollBehavior,
            });
          }, 50);
        } catch (error) {
          // Silently fail if sessionStorage is unavailable
        }
      }
    };

    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [storageKey, enabled]);
}

/**
 * Clear saved scroll position for a specific key
 *
 * @param key - Storage key to clear
 */
export function clearScrollPosition(key: string) {
  try {
    sessionStorage.removeItem(`scroll-position-${key}`);
  } catch (error) {
    // Silently fail if sessionStorage is unavailable
  }
}

/**
 * Get saved scroll position for a specific key
 *
 * @param key - Storage key to retrieve
 * @returns Saved scroll position or null
 */
export function getScrollPosition(key: string): ScrollPosition | null {
  try {
    const saved = sessionStorage.getItem(`scroll-position-${key}`);
    return saved ? JSON.parse(saved) : null;
  } catch (error) {
    // Silently fail if sessionStorage is unavailable
    return null;
  }
}
