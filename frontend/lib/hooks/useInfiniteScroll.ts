import { useEffect, useRef } from 'react';

interface UseInfiniteScrollOptions {
  onLoadMore: () => void;
  hasMore: boolean;
  loading: boolean;
  threshold?: number;
}

/**
 * Custom hook for implementing infinite scroll using Intersection Observer API
 *
 * @param onLoadMore - Callback function to load more content
 * @param hasMore - Whether there is more content to load
 * @param loading - Whether content is currently being loaded
 * @param threshold - Distance in pixels from bottom to trigger load (default: 200px)
 *
 * @returns ref - Ref to attach to the sentinel element at the bottom of the list
 *
 * @example
 * ```tsx
 * const sentinelRef = useInfiniteScroll({
 *   onLoadMore: handleLoadMore,
 *   hasMore: hasNextPage,
 *   loading: loadingMore,
 *   threshold: 200
 * });
 *
 * return (
 *   <div>
 *     {items.map(item => <Item key={item.id} {...item} />)}
 *     <div ref={sentinelRef} />
 *   </div>
 * );
 * ```
 */
export function useInfiniteScroll({
  onLoadMore,
  hasMore,
  loading,
  threshold = 200,
}: UseInfiniteScrollOptions) {
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Don't set up observer if we can't load more or are already loading
    if (!hasMore || loading) return;

    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    // Create intersection observer with threshold converted to rootMargin
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;

        // Trigger load when sentinel becomes visible
        if (entry.isIntersecting && hasMore && !loading) {
          onLoadMore();
        }
      },
      {
        root: null, // viewport
        rootMargin: `${threshold}px`, // Trigger when within threshold pixels of viewport
        threshold: 0, // Trigger as soon as any part is visible
      }
    );

    observer.observe(sentinel);

    return () => {
      observer.disconnect();
    };
  }, [onLoadMore, hasMore, loading, threshold]);

  return sentinelRef;
}
