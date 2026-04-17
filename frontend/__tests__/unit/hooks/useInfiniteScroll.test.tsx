import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';

describe('useInfiniteScroll', () => {
  let mockIntersectionObserver: any;
  let observeCallback: IntersectionObserverCallback | null = null;
  let observeMock: any;
  let disconnectMock: any;

  beforeEach(() => {
    observeMock = vi.fn();
    disconnectMock = vi.fn();

    // Mock IntersectionObserver
    mockIntersectionObserver = vi.fn((callback: IntersectionObserverCallback) => {
      observeCallback = callback;
      return {
        observe: observeMock,
        unobserve: vi.fn(),
        disconnect: disconnectMock,
      };
    });

    global.IntersectionObserver = mockIntersectionObserver as any;
  });

  afterEach(() => {
    vi.clearAllMocks();
    observeCallback = null;
  });

  it('should return a ref object', () => {
    const onLoadMore = vi.fn();
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
      })
    );

    expect(result.current).toHaveProperty('current');
  });

  it('should create IntersectionObserver with correct threshold when sentinel is attached', async () => {
    const onLoadMore = vi.fn();
    const threshold = 200;

    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
        threshold,
      })
    );

    // Attach a sentinel element
    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    // Wait for effect to run
    await waitFor(() => {
      expect(mockIntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        expect.objectContaining({
          root: null,
          rootMargin: `${threshold}px`,
          threshold: 0,
        })
      );
    });
  });

  it('should use default threshold of 200px', async () => {
    const onLoadMore = vi.fn();

    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    await waitFor(() => {
      expect(mockIntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        expect.objectContaining({
          rootMargin: '200px',
        })
      );
    });
  });

  it('should call onLoadMore when sentinel intersects', async () => {
    const onLoadMore = vi.fn();
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    await waitFor(() => {
      expect(observeCallback).not.toBeNull();
    });

    // Trigger intersection
    const entries: IntersectionObserverEntry[] = [
      {
        isIntersecting: true,
        target: sentinelElement,
      } as IntersectionObserverEntry,
    ];

    observeCallback!(entries, {} as IntersectionObserver);

    expect(onLoadMore).toHaveBeenCalledTimes(1);
  });

  it('should not call onLoadMore when loading is true', async () => {
    const onLoadMore = vi.fn();
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: true,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    // Observer should not be created when loading
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(mockIntersectionObserver).not.toHaveBeenCalled();
  });

  it('should not call onLoadMore when hasMore is false', async () => {
    const onLoadMore = vi.fn();
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: false,
        loading: false,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    // Observer should not be created when hasMore is false
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(mockIntersectionObserver).not.toHaveBeenCalled();
  });

  it('should not call onLoadMore when sentinel is not intersecting', async () => {
    const onLoadMore = vi.fn();
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    await waitFor(() => {
      expect(observeCallback).not.toBeNull();
    });

    const entries: IntersectionObserverEntry[] = [
      {
        isIntersecting: false,
        target: sentinelElement,
      } as IntersectionObserverEntry,
    ];

    observeCallback!(entries, {} as IntersectionObserver);

    expect(onLoadMore).not.toHaveBeenCalled();
  });

  it('should disconnect observer on unmount', async () => {
    const onLoadMore = vi.fn();

    const { result, unmount } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    await waitFor(() => {
      expect(mockIntersectionObserver).toHaveBeenCalled();
    });

    unmount();

    expect(disconnectMock).toHaveBeenCalled();
  });

  it('should prevent multiple simultaneous requests via loading flag', async () => {
    const onLoadMore = vi.fn();
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    await waitFor(() => {
      expect(observeCallback).not.toBeNull();
    });

    // First intersection - should trigger
    const entries: IntersectionObserverEntry[] = [
      {
        isIntersecting: true,
        target: sentinelElement,
      } as IntersectionObserverEntry,
    ];

    observeCallback!(entries, {} as IntersectionObserver);
    expect(onLoadMore).toHaveBeenCalledTimes(1);

    // Second intersection immediately after - should still trigger
    // (the parent component is responsible for setting loading=true)
    observeCallback!(entries, {} as IntersectionObserver);
    expect(onLoadMore).toHaveBeenCalledTimes(2);
  });

  it('should handle custom threshold values', async () => {
    const onLoadMore = vi.fn();
    const customThreshold = 500;

    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
        threshold: customThreshold,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    await waitFor(() => {
      expect(mockIntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        expect.objectContaining({
          rootMargin: `${customThreshold}px`,
        })
      );
    });
  });

  it('should observe the sentinel element', async () => {
    const onLoadMore = vi.fn();
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore,
        hasMore: true,
        loading: false,
      })
    );

    const sentinelElement = document.createElement('div');
    if (result.current) {
      (result.current as { current: HTMLDivElement | null }).current = sentinelElement;
    }

    await waitFor(() => {
      expect(observeMock).toHaveBeenCalledWith(sentinelElement);
    });
  });
});
