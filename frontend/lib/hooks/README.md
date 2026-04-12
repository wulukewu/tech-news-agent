# React Query Hooks

This directory contains React Query hooks for managing server state in the Tech News Agent application.

## Overview

React Query (TanStack Query) is used to manage server state separately from client state. It provides:

- **Automatic caching**: Data is cached and reused across components
- **Background refetching**: Data is automatically refreshed in the background
- **Cache invalidation**: Smart cache invalidation strategies keep data in sync
- **Optimistic updates**: UI updates immediately before server confirms
- **Error handling**: Built-in error handling and retry logic

## Architecture

```
Server State (React Query)          Client State (React Context)
├── Articles                        ├── Authentication status
├── Reading List                    ├── User profile
├── Feeds                           ├── Theme preferences
└── Subscriptions                   └── UI state (modals, etc.)
```

## Available Hooks

### Articles

#### `useArticles(page, pageSize, categories?)`

Fetches paginated articles with optional category filtering.

```tsx
import { useArticles } from '@/lib/hooks';

function ArticleList() {
  const { data, isLoading, error } = useArticles(1, 20, ['前端開發']);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data.articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
      <Pagination currentPage={data.page} totalPages={data.total_pages} />
    </div>
  );
}
```

#### `useCategories()`

Fetches available article categories.

```tsx
import { useCategories } from '@/lib/hooks';

function CategoryFilter() {
  const { data: categories, isLoading } = useCategories();

  if (isLoading) return <div>Loading...</div>;

  return (
    <select>
      {categories?.map((category) => (
        <option key={category} value={category}>
          {category}
        </option>
      ))}
    </select>
  );
}
```

### Reading List

#### `useReadingList(page, pageSize, status?)`

Fetches paginated reading list with optional status filter.

```tsx
import { useReadingList } from '@/lib/hooks';

function ReadingList() {
  const { data, isLoading } = useReadingList(1, 20, 'unread');

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {data.items.map((item) => (
        <ReadingListItem key={item.article_id} item={item} />
      ))}
    </div>
  );
}
```

#### `useAddToReadingList()`

Adds an article to the reading list.

```tsx
import { useAddToReadingList } from '@/lib/hooks';
import { toast } from 'sonner';

function AddButton({ articleId }: { articleId: string }) {
  const { mutate, isPending } = useAddToReadingList();

  const handleAdd = () => {
    mutate(articleId, {
      onSuccess: () => {
        toast.success('Added to reading list');
      },
      onError: (error) => {
        toast.error(`Failed to add: ${error.message}`);
      },
    });
  };

  return (
    <button onClick={handleAdd} disabled={isPending}>
      {isPending ? 'Adding...' : 'Add to Reading List'}
    </button>
  );
}
```

#### `useUpdateReadingListStatus()`

Updates the status of a reading list item.

```tsx
import { useUpdateReadingListStatus } from '@/lib/hooks';

function StatusSelector({ articleId, currentStatus }: Props) {
  const { mutate, isPending } = useUpdateReadingListStatus();

  return (
    <select
      value={currentStatus}
      onChange={(e) =>
        mutate({
          articleId,
          status: e.target.value as ReadingListStatus,
        })
      }
      disabled={isPending}
    >
      <option value="unread">Unread</option>
      <option value="reading">Reading</option>
      <option value="completed">Completed</option>
    </select>
  );
}
```

#### `useUpdateReadingListRating()`

Updates the rating of a reading list item.

```tsx
import { useUpdateReadingListRating } from '@/lib/hooks';

function RatingSelector({ articleId, currentRating }: Props) {
  const { mutate, isPending } = useUpdateReadingListRating();

  return (
    <div>
      {[1, 2, 3, 4, 5].map((rating) => (
        <button
          key={rating}
          onClick={() => mutate({ articleId, rating })}
          disabled={isPending}
          className={currentRating === rating ? 'active' : ''}
        >
          ★
        </button>
      ))}
    </div>
  );
}
```

#### `useRemoveFromReadingList()`

Removes an article from the reading list.

```tsx
import { useRemoveFromReadingList } from '@/lib/hooks';
import { toast } from 'sonner';

function RemoveButton({ articleId }: { articleId: string }) {
  const { mutate, isPending } = useRemoveFromReadingList();

  const handleRemove = () => {
    mutate(articleId, {
      onSuccess: () => {
        toast.success('Removed from reading list');
      },
      onError: (error) => {
        toast.error(`Failed to remove: ${error.message}`);
      },
    });
  };

  return (
    <button onClick={handleRemove} disabled={isPending}>
      {isPending ? 'Removing...' : 'Remove'}
    </button>
  );
}
```

### Feeds and Subscriptions

#### `useFeeds()`

Fetches all available feeds with subscription status.

```tsx
import { useFeeds } from '@/lib/hooks';

function FeedList() {
  const { data: feeds, isLoading } = useFeeds();

  if (isLoading) return <div>Loading...</div>;

  return <div>{feeds?.map((feed) => <FeedCard key={feed.id} feed={feed} />)}</div>;
}
```

#### `useToggleSubscription()`

Toggles subscription status for a feed.

```tsx
import { useToggleSubscription } from '@/lib/hooks';
import { toast } from 'sonner';

function SubscribeButton({ feedId, isSubscribed }: Props) {
  const { mutate, isPending } = useToggleSubscription();

  const handleToggle = () => {
    mutate(feedId, {
      onSuccess: (data) => {
        toast.success(data.subscribed ? 'Subscribed!' : 'Unsubscribed');
      },
      onError: (error) => {
        toast.error(`Failed: ${error.message}`);
      },
    });
  };

  return (
    <button onClick={handleToggle} disabled={isPending}>
      {isPending ? 'Processing...' : isSubscribed ? 'Unsubscribe' : 'Subscribe'}
    </button>
  );
}
```

## Cache Invalidation Strategies

### Automatic Invalidation

Mutations automatically invalidate related queries:

- **Adding to reading list**: Invalidates reading list and articles cache
- **Removing from reading list**: Invalidates reading list and articles cache
- **Updating reading list status/rating**: Invalidates reading list cache
- **Toggling subscription**: Invalidates feeds and articles cache

### Manual Invalidation

You can manually invalidate queries when needed:

```tsx
import { useQueryClient } from '@tanstack/react-query';
import { articleKeys, readingListKeys, feedKeys } from '@/lib/hooks';

function RefreshButton() {
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    // Invalidate all article queries
    queryClient.invalidateQueries({ queryKey: articleKeys.all });

    // Invalidate specific article list
    queryClient.invalidateQueries({
      queryKey: articleKeys.list(1, 20, ['前端開發']),
    });

    // Invalidate all reading list queries
    queryClient.invalidateQueries({ queryKey: readingListKeys.all });

    // Invalidate all feed queries
    queryClient.invalidateQueries({ queryKey: feedKeys.all });
  };

  return <button onClick={handleRefresh}>Refresh All</button>;
}
```

## Query Keys

Query keys are centralized for consistent cache management:

```typescript
// Article keys
articleKeys.all; // ['articles']
articleKeys.lists(); // ['articles', 'list']
articleKeys.list(1, 20, ['前端開發']); // ['articles', 'list', { page: 1, pageSize: 20, categories: ['前端開發'] }]
articleKeys.categories(); // ['articles', 'categories']

// Reading list keys
readingListKeys.all; // ['readingList']
readingListKeys.lists(); // ['readingList', 'list']
readingListKeys.list(1, 20, 'unread'); // ['readingList', 'list', { page: 1, pageSize: 20, status: 'unread' }]

// Feed keys
feedKeys.all; // ['feeds']
feedKeys.lists(); // ['feeds', 'list']
feedKeys.list(); // ['feeds', 'list']
```

## Configuration

Default React Query configuration (in `QueryProvider.tsx`):

```typescript
{
  queries: {
    staleTime: 60 * 1000,           // 1 minute
    gcTime: 5 * 60 * 1000,          // 5 minutes
    retry: 2,                        // Retry 2 times
    refetchOnWindowFocus: true,      // Refetch on window focus
    refetchOnReconnect: true,        // Refetch on reconnect
    refetchOnMount: true,            // Refetch on mount
  },
  mutations: {
    retry: 1,                        // Retry mutations once
  },
}
```

Individual hooks can override these defaults:

```typescript
export function useArticles(page, pageSize, categories) {
  return useQuery({
    queryKey: articleKeys.list(page, pageSize, categories),
    queryFn: () => fetchMyArticles(page, pageSize, categories),
    staleTime: 5 * 60 * 1000, // Override: 5 minutes
    gcTime: 10 * 60 * 1000, // Override: 10 minutes
  });
}
```

## Best Practices

### 1. Use Query Hooks for Server State

✅ **Do**: Use React Query hooks for data from the server

```tsx
const { data: articles } = useArticles(1, 20);
```

❌ **Don't**: Use useState for server data

```tsx
const [articles, setArticles] = useState([]);
useEffect(() => {
  fetchArticles().then(setArticles);
}, []);
```

### 2. Use Context for Client State

✅ **Do**: Use React Context for UI state

```tsx
const { theme, setTheme } = useTheme();
```

❌ **Don't**: Use React Query for UI state

```tsx
// Don't do this
const { data: theme } = useQuery(['theme'], () => localStorage.getItem('theme'));
```

### 3. Handle Loading and Error States

✅ **Do**: Handle all query states

```tsx
const { data, isLoading, error } = useArticles();

if (isLoading) return <LoadingSkeleton />;
if (error) return <ErrorMessage error={error} />;
return <ArticleList articles={data.articles} />;
```

### 4. Use Optimistic Updates for Better UX

✅ **Do**: Use optimistic updates for instant feedback

```tsx
const { mutate } = useToggleSubscription();
// Optimistic update is handled in the hook
```

### 5. Invalidate Related Queries

✅ **Do**: Invalidate related queries after mutations

```tsx
// Automatically handled in mutation hooks
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: readingListKeys.all });
  queryClient.invalidateQueries({ queryKey: articleKeys.all });
};
```

## Debugging

### React Query DevTools

DevTools are available in development mode. Press the React Query icon in the bottom-right corner to open.

Features:

- View all queries and their states
- Inspect query data and metadata
- Manually trigger refetches
- View query timelines

### Logging

Enable query logging in development:

```tsx
import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  logger: {
    log: console.log,
    warn: console.warn,
    error: console.error,
  },
});
```

## Migration Guide

### Before (Direct API Calls)

```tsx
function ArticleList() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMyArticles()
      .then(setArticles)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{/* render articles */}</div>;
}
```

### After (React Query)

```tsx
function ArticleList() {
  const { data, isLoading, error } = useArticles(1, 20);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{/* render articles */}</div>;
}
```

Benefits:

- ✅ Automatic caching
- ✅ Background refetching
- ✅ No manual state management
- ✅ Automatic error handling
- ✅ Shared state across components

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 2.3**: React Query is used for server state caching and synchronization
- **Requirement 2.4**: Server state is separated from client state management
- **Requirement 1.1**: Unified API client is used for all requests
- **Requirement 1.2**: Consistent error handling across all API requests
- **Requirement 1.3**: Request/response interceptors are supported
- **Requirement 1.4**: Type-safe API client methods with generics
