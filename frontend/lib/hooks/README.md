# Custom Hooks Documentation

## useInfiniteScroll

A custom hook for implementing infinite scroll functionality using the Intersection Observer API.

### Features

- ✅ Uses Intersection Observer API (modern, performant)
- ✅ Configurable threshold distance (default: 200px)
- ✅ Prevents multiple simultaneous requests via loading flag
- ✅ Automatic cleanup on unmount
- ✅ TypeScript support

### Usage

```tsx
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';

function ArticleList() {
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleLoadMore = async () => {
    setLoading(true);
    try {
      const data = await fetchArticles(page + 1);
      setArticles((prev) => [...prev, ...data.articles]);
      setHasMore(data.hasNextPage);
      setPage(page + 1);
    } finally {
      setLoading(false);
    }
  };

  // Get ref for sentinel element
  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore,
    loading,
    threshold: 200, // Optional, defaults to 200px
  });

  return (
    <div>
      {articles.map((article) => (
        <ArticleCard key={article.id} {...article} />
      ))}

      {/* Sentinel element - triggers load when visible */}
      {hasMore && <div ref={sentinelRef} className="h-px" />}

      {loading && <LoadingSpinner />}
      {!hasMore && <div>No more articles</div>}
    </div>
  );
}
```

### Parameters

| Parameter    | Type         | Required | Default | Description                                    |
| ------------ | ------------ | -------- | ------- | ---------------------------------------------- |
| `onLoadMore` | `() => void` | Yes      | -       | Callback function to load more content         |
| `hasMore`    | `boolean`    | Yes      | -       | Whether there is more content to load          |
| `loading`    | `boolean`    | Yes      | -       | Whether content is currently being loaded      |
| `threshold`  | `number`     | No       | `200`   | Distance in pixels from bottom to trigger load |

### Returns

Returns a `ref` object that should be attached to a sentinel element at the bottom of your list.

### How It Works

1. The hook creates an Intersection Observer that watches a sentinel element
2. When the sentinel comes within `threshold` pixels of the viewport, it triggers `onLoadMore`
3. The observer is automatically disabled when `loading` is true or `hasMore` is false
4. The observer is cleaned up when the component unmounts

### Requirements Met

- ✅ **19.1**: Uses Intersection Observer for bottom detection
- ✅ **19.2**: Triggers load when within 200px of bottom (configurable)
- ✅ **19.4**: Prevents multiple simultaneous requests via loading flag

---

## useScrollRestoration

A custom hook for managing scroll position restoration across navigation.

### Features

- ✅ Saves scroll position to sessionStorage
- ✅ Restores scroll position on navigation back
- ✅ Handles browser back/forward buttons
- ✅ Configurable enable/disable
- ✅ Automatic cleanup

### Usage

```tsx
import { useScrollRestoration } from '@/lib/hooks/useScrollRestoration';

function DashboardPage() {
  // Enable scroll restoration for this page
  useScrollRestoration('dashboard');

  return <div>...</div>;
}

// Or use pathname as key (default)
function ArticlesPage() {
  useScrollRestoration(); // Uses pathname as key

  return <div>...</div>;
}

// Disable scroll restoration
function NoScrollPage() {
  useScrollRestoration('no-scroll', false);

  return <div>...</div>;
}
```

### Parameters

| Parameter | Type      | Required | Default    | Description                            |
| --------- | --------- | -------- | ---------- | -------------------------------------- |
| `key`     | `string`  | No       | `pathname` | Unique key for storing scroll position |
| `enabled` | `boolean` | No       | `true`     | Whether scroll restoration is enabled  |

### Utility Functions

#### clearScrollPosition

Clears saved scroll position for a specific key.

```tsx
import { clearScrollPosition } from '@/lib/hooks/useScrollRestoration';

clearScrollPosition('dashboard');
```

#### getScrollPosition

Retrieves saved scroll position for a specific key.

```tsx
import { getScrollPosition } from '@/lib/hooks/useScrollRestoration';

const position = getScrollPosition('dashboard');
// Returns: { x: number, y: number } | null
```

### How It Works

1. **On Scroll**: Debounces and saves current scroll position to sessionStorage
2. **On Navigation Away**: Saves scroll position before leaving the page
3. **On Mount**: Restores saved scroll position after a short delay
4. **On Browser Back/Forward**: Restores scroll position from sessionStorage

### Requirements Met

- ✅ **19.6**: Maintains scroll position on navigation back
- ✅ **19.8**: Handles scroll restoration on browser back/forward

---

## Implementation Notes

### Why Intersection Observer?

The previous implementation used scroll events with throttling. The new implementation uses Intersection Observer because:

1. **Better Performance**: Intersection Observer is handled by the browser's rendering engine, not JavaScript
2. **No Throttling Needed**: The browser automatically optimizes intersection calculations
3. **More Accurate**: Detects visibility changes precisely
4. **Modern Standard**: Recommended by web performance best practices

### Scroll Restoration Strategy

The scroll restoration hook uses sessionStorage instead of localStorage because:

1. **Session-Specific**: Scroll positions are only relevant within the same browser session
2. **Automatic Cleanup**: sessionStorage is cleared when the tab/window is closed
3. **No Quota Issues**: Less likely to hit storage limits

### Testing Strategy

Due to the complexity of testing hooks that interact with browser APIs (IntersectionObserver, sessionStorage, scroll events), we focus on:

1. **Integration Tests**: Test the hooks in actual component contexts
2. **E2E Tests**: Test the complete user flow with real browser interactions
3. **Manual Testing**: Verify behavior across different browsers and devices

---

## Browser Support

### Intersection Observer

- ✅ Chrome 51+
- ✅ Firefox 55+
- ✅ Safari 12.1+
- ✅ Edge 15+

For older browsers, consider adding a polyfill:

```bash
npm install intersection-observer
```

```tsx
// In your app entry point
if (typeof window !== 'undefined' && !('IntersectionObserver' in window)) {
  import('intersection-observer');
}
```

### sessionStorage

- ✅ All modern browsers
- ✅ IE 8+

---

## Examples

### Dashboard with Infinite Scroll and Scroll Restoration

```tsx
'use client';

import { useState, useEffect } from 'react';
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';
import { useScrollRestoration } from '@/lib/hooks/useScrollRestoration';

export default function DashboardPage() {
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  // Enable scroll restoration
  useScrollRestoration('dashboard');

  // Load initial articles
  useEffect(() => {
    loadArticles(1);
  }, []);

  const loadArticles = async (pageNum, append = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }

      const data = await fetchMyArticles(pageNum, 20);

      if (append) {
        setArticles((prev) => [...prev, ...data.articles]);
      } else {
        setArticles(data.articles);
      }

      setHasNextPage(data.hasNextPage);
      setPage(pageNum);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasNextPage) {
      loadArticles(page + 1, true);
    }
  };

  // Get sentinel ref for infinite scroll
  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore: hasNextPage,
    loading: loadingMore,
  });

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <div>
      <ArticleGrid articles={articles} />

      {/* Sentinel element for intersection observer */}
      {hasNextPage && <div ref={sentinelRef} className="h-px" aria-hidden="true" />}

      {loadingMore && <LoadingSpinner />}
      {!hasNextPage && articles.length > 0 && <div>No more articles</div>}
    </div>
  );
}
```

---

## Troubleshooting

### Infinite scroll not triggering

1. **Check sentinel element**: Make sure the sentinel element is rendered when `hasMore` is true
2. **Check loading state**: Ensure `loading` is set to `false` after data loads
3. **Check hasMore state**: Verify `hasMore` is `true` when there's more content
4. **Check browser support**: Verify IntersectionObserver is supported

### Scroll position not restoring

1. **Check sessionStorage**: Verify sessionStorage is enabled in the browser
2. **Check key**: Ensure you're using the same key for save and restore
3. **Check timing**: The restoration happens after a 100ms delay to ensure content is loaded
4. **Check navigation**: Scroll restoration only works within the same browser session

### Performance issues

1. **Reduce threshold**: Lower the threshold value to trigger loading closer to the bottom
2. **Increase page size**: Load more items per page to reduce the number of requests
3. **Optimize rendering**: Use virtualization for very long lists (react-window, react-virtual)

---

## Related

- [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
- [sessionStorage API](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage)
- [React Hooks](https://react.dev/reference/react)
