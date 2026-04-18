# React Query Migration Examples

This document provides practical examples of migrating existing components from direct API calls to React Query hooks.

## Example 1: Article List Component

### Before (Direct API Calls)

```tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchMyArticles } from '@/lib/api/articles';
import type { Article } from '@/types/article';

export function ArticleList() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const loadArticles = async () => {
      try {
        setLoading(true);
        const response = await fetchMyArticles(page, 20);
        setArticles(response.articles);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    loadArticles();
  }, [page]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
      <button onClick={() => setPage((p) => p - 1)} disabled={page === 1}>
        Previous
      </button>
      <button onClick={() => setPage((p) => p + 1)}>Next</button>
    </div>
  );
}
```

### After (React Query)

```tsx
'use client';

import { useState } from 'react';
import { useArticles } from '@/lib/hooks';

export function ArticleList() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useArticles(page, 20);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data.articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
      <button onClick={() => setPage((p) => p - 1)} disabled={page === 1}>
        Previous
      </button>
      <button onClick={() => setPage((p) => p + 1)} disabled={page >= data.total_pages}>
        Next
      </button>
    </div>
  );
}
```

**Benefits:**

- ✅ No manual state management for articles, loading, error
- ✅ Automatic caching - switching pages is instant
- ✅ Background refetching keeps data fresh
- ✅ Less code to maintain

## Example 2: Reading List with Add/Remove

### Before (Direct API Calls)

```tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchReadingList, addToReadingList, removeFromReadingList } from '@/lib/api/readingList';
import { toast } from 'sonner';

export function ReadingList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadReadingList = async () => {
    try {
      setLoading(true);
      const response = await fetchReadingList();
      setItems(response.items);
    } catch (error) {
      toast.error('Failed to load reading list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReadingList();
  }, []);

  const handleAdd = async (articleId: string) => {
    try {
      setActionLoading(articleId);
      await addToReadingList(articleId);
      toast.success('Added to reading list');
      // Manually refetch to update UI
      await loadReadingList();
    } catch (error) {
      toast.error('Failed to add');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRemove = async (articleId: string) => {
    try {
      setActionLoading(articleId);
      await removeFromReadingList(articleId);
      toast.success('Removed from reading list');
      // Manually refetch to update UI
      await loadReadingList();
    } catch (error) {
      toast.error('Failed to remove');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {items.map((item) => (
        <div key={item.article_id}>
          <h3>{item.article.title}</h3>
          <button
            onClick={() => handleRemove(item.article_id)}
            disabled={actionLoading === item.article_id}
          >
            {actionLoading === item.article_id ? 'Removing...' : 'Remove'}
          </button>
        </div>
      ))}
    </div>
  );
}
```

### After (React Query)

```tsx
'use client';

import { useReadingList, useAddToReadingList, useRemoveFromReadingList } from '@/lib/hooks';
import { toast } from 'sonner';

export function ReadingList() {
  const { data, isLoading } = useReadingList();
  const { mutate: addToList } = useAddToReadingList();
  const { mutate: removeFromList, isPending: isRemoving } = useRemoveFromReadingList();

  const handleAdd = (articleId: string) => {
    addToList(articleId, {
      onSuccess: () => toast.success('Added to reading list'),
      onError: () => toast.error('Failed to add'),
    });
  };

  const handleRemove = (articleId: string) => {
    removeFromList(articleId, {
      onSuccess: () => toast.success('Removed from reading list'),
      onError: () => toast.error('Failed to remove'),
    });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {data.items.map((item) => (
        <div key={item.article_id}>
          <h3>{item.article.title}</h3>
          <button onClick={() => handleRemove(item.article_id)} disabled={isRemoving}>
            {isRemoving ? 'Removing...' : 'Remove'}
          </button>
        </div>
      ))}
    </div>
  );
}
```

**Benefits:**

- ✅ Automatic cache invalidation - list updates automatically after add/remove
- ✅ No manual refetching needed
- ✅ Simpler state management
- ✅ Better error handling

## Example 3: Feed Subscription Toggle

### Before (Direct API Calls)

```tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchFeeds, toggleSubscription } from '@/lib/api/feeds';
import { toast } from 'sonner';

export function FeedList() {
  const [feeds, setFeeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<string | null>(null);

  const loadFeeds = async () => {
    try {
      setLoading(true);
      const data = await fetchFeeds();
      setFeeds(data);
    } catch (error) {
      toast.error('Failed to load feeds');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeeds();
  }, []);

  const handleToggle = async (feedId: string) => {
    try {
      setToggling(feedId);
      const response = await toggleSubscription(feedId);
      toast.success(response.subscribed ? 'Subscribed!' : 'Unsubscribed');

      // Manually update local state
      setFeeds(
        feeds.map((feed) =>
          feed.id === feedId ? { ...feed, is_subscribed: response.subscribed } : feed
        )
      );
    } catch (error) {
      toast.error('Failed to toggle subscription');
    } finally {
      setToggling(null);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {feeds.map((feed) => (
        <div key={feed.id}>
          <h3>{feed.name}</h3>
          <button onClick={() => handleToggle(feed.id)} disabled={toggling === feed.id}>
            {toggling === feed.id
              ? 'Processing...'
              : feed.is_subscribed
                ? 'Unsubscribe'
                : 'Subscribe'}
          </button>
        </div>
      ))}
    </div>
  );
}
```

### After (React Query with Optimistic Updates)

```tsx
'use client';

import { useFeeds, useToggleSubscription } from '@/lib/hooks';
import { toast } from 'sonner';

export function FeedList() {
  const { data: feeds, isLoading } = useFeeds();
  const { mutate: toggleSub, isPending } = useToggleSubscription();

  const handleToggle = (feedId: string) => {
    toggleSub(feedId, {
      onSuccess: (data) => {
        toast.success(data.subscribed ? 'Subscribed!' : 'Unsubscribed');
      },
      onError: () => {
        toast.error('Failed to toggle subscription');
      },
    });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {feeds.map((feed) => (
        <div key={feed.id}>
          <h3>{feed.name}</h3>
          <button onClick={() => handleToggle(feed.id)} disabled={isPending}>
            {isPending ? 'Processing...' : feed.is_subscribed ? 'Unsubscribe' : 'Subscribe'}
          </button>
        </div>
      ))}
    </div>
  );
}
```

**Benefits:**

- ✅ Optimistic updates - UI updates instantly
- ✅ Automatic rollback on error
- ✅ No manual state synchronization
- ✅ Cache invalidation handled automatically

## Example 4: Category Filter with Articles

### Before (Direct API Calls)

```tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchCategories, fetchMyArticles } from '@/lib/api/articles';

export function ArticlesWithFilter() {
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCategories = async () => {
      const data = await fetchCategories();
      setCategories(data);
    };
    loadCategories();
  }, []);

  useEffect(() => {
    const loadArticles = async () => {
      try {
        setLoading(true);
        const response = await fetchMyArticles(
          1,
          20,
          selectedCategories.length > 0 ? selectedCategories : undefined
        );
        setArticles(response.articles);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    loadArticles();
  }, [selectedCategories]);

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  return (
    <div>
      <div>
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => toggleCategory(category)}
            className={selectedCategories.includes(category) ? 'active' : ''}
          >
            {category}
          </button>
        ))}
      </div>
      {loading ? (
        <div>Loading articles...</div>
      ) : (
        <div>
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### After (React Query)

```tsx
'use client';

import { useState } from 'react';
import { useCategories, useArticles } from '@/lib/hooks';

export function ArticlesWithFilter() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  const { data: categories } = useCategories();
  const { data: articlesData, isLoading } = useArticles(
    1,
    20,
    selectedCategories.length > 0 ? selectedCategories : undefined
  );

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  return (
    <div>
      <div>
        {categories?.map((category) => (
          <button
            key={category}
            onClick={() => toggleCategory(category)}
            className={selectedCategories.includes(category) ? 'active' : ''}
          >
            {category}
          </button>
        ))}
      </div>
      {isLoading ? (
        <div>Loading articles...</div>
      ) : (
        <div>
          {articlesData.articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
```

**Benefits:**

- ✅ Separate queries for categories and articles
- ✅ Categories cached independently (change infrequently)
- ✅ Articles automatically refetch when filter changes
- ✅ Previous filter results cached for instant switching

## Migration Checklist

When migrating a component to React Query:

- [ ] Identify all API calls in the component
- [ ] Replace `useState` for server data with appropriate query hooks
- [ ] Remove manual `useEffect` for data fetching
- [ ] Replace mutation logic with mutation hooks
- [ ] Remove manual cache invalidation/refetching
- [ ] Update loading/error state checks to use query states
- [ ] Add toast notifications in mutation callbacks
- [ ] Test optimistic updates work correctly
- [ ] Verify cache invalidation triggers correctly
- [ ] Remove unused state management code

## Common Patterns

### Pattern 1: Dependent Queries

When one query depends on data from another:

```tsx
function ArticleDetails({ articleId }: { articleId: string }) {
  // First query
  const { data: article } = useArticle(articleId);

  // Second query depends on first
  const { data: comments } = useComments(articleId, {
    enabled: !!article, // Only run when article is loaded
  });

  return (
    <div>
      <h1>{article?.title}</h1>
      {comments?.map((comment) => (
        <Comment key={comment.id} comment={comment} />
      ))}
    </div>
  );
}
```

### Pattern 2: Infinite Scroll

For infinite scrolling lists:

```tsx
import { useInfiniteQuery } from '@tanstack/react-query';

function InfiniteArticleList() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['articles', 'infinite'],
    queryFn: ({ pageParam = 1 }) => fetchMyArticles(pageParam, 20),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.total_pages ? lastPage.page + 1 : undefined,
  });

  return (
    <div>
      {data?.pages.map((page) =>
        page.articles.map((article) => <ArticleCard key={article.id} article={article} />)
      )}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

### Pattern 3: Prefetching

Prefetch data before user navigates:

```tsx
import { useQueryClient } from '@tanstack/react-query';
import { articleKeys } from '@/lib/hooks';

function ArticleLink({ articleId }: { articleId: string }) {
  const queryClient = useQueryClient();

  const prefetchArticle = () => {
    queryClient.prefetchQuery({
      queryKey: articleKeys.detail(articleId),
      queryFn: () => fetchArticle(articleId),
    });
  };

  return (
    <Link href={`/articles/${articleId}`} onMouseEnter={prefetchArticle}>
      View Article
    </Link>
  );
}
```
