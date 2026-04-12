'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { ArticleCard } from '@/components/ArticleCard';
import { ArticleListSkeleton } from '@/components/LoadingSkeleton';
import { TriggerSchedulerButton } from '@/components/TriggerSchedulerButton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';
import { fetchMyArticles, fetchCategories } from '@/lib/api/articles';
import { toast } from '@/lib/toast';
import type { Article } from '@/types/article';

export default function DashboardPage() {
  const router = useRouter();
  const [articles, setArticles] = useState<Article[]>([]);
  const [page, setPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  // Category filter state
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  // Load categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const cats = await fetchCategories();
        setCategories(cats || []);
        // Initially select all categories
        setSelectedCategories(cats || []);
      } catch (error) {
        console.error('Failed to load categories:', error);
        setCategories([]);
        setSelectedCategories([]);
      } finally {
        setLoadingCategories(false);
      }
    };

    loadCategories();
  }, []);

  const loadArticles = async (pageNum: number, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }

      const data = await fetchMyArticles(
        pageNum,
        20,
        selectedCategories.length > 0 ? selectedCategories : undefined
      );

      if (append) {
        setArticles((prev) => [...prev, ...(data?.articles || [])]);
      } else {
        setArticles(data?.articles || []);
      }

      setHasNextPage(data?.hasNextPage || false);
      setPage(pageNum);
    } catch (error) {
      toast.error('Failed to load articles');
      console.error('Failed to load articles:', error);
      setArticles([]);
      setHasNextPage(false);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // Reload articles when selected categories change
  useEffect(() => {
    if (!loadingCategories) {
      loadArticles(1);
    }
  }, [selectedCategories, loadingCategories]);

  const handleLoadMore = () => {
    if (!loadingMore && hasNextPage) {
      loadArticles(page + 1, true);
    }
  };

  // Infinite scroll
  useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore: hasNextPage,
    loading: loadingMore,
  });

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) => {
      if (prev.includes(category)) {
        return prev.filter((c) => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  const selectAllCategories = () => {
    setSelectedCategories(categories);
  };

  const deselectAllCategories = () => {
    setSelectedCategories([]);
  };

  if (loading || loadingCategories) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8 px-4">
          <header className="mb-6">
            <h1 className="text-3xl font-bold">Your Articles</h1>
          </header>
          <ArticleListSkeleton />
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8 px-4">
        <header className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold">Your Articles</h1>
            <div className="flex gap-2">
              <TriggerSchedulerButton />
              <Button variant="outline" onClick={() => router.push('/subscriptions')}>
                管理訂閱
              </Button>
            </div>
          </div>

          {/* Category Filter */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Filter by category:</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAllCategories}
                className="h-7 text-xs"
              >
                Select All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={deselectAllCategories}
                className="h-7 text-xs"
              >
                Clear All
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {categories?.map((category) => {
                const isSelected = selectedCategories.includes(category);
                return (
                  <Badge
                    key={category}
                    variant={isSelected ? 'default' : 'outline'}
                    className="cursor-pointer transition-colors"
                    onClick={() => toggleCategory(category)}
                  >
                    {category}
                  </Badge>
                );
              })}
            </div>
          </div>
        </header>

        {articles?.length === 0 ? (
          <section className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <h2 className="text-2xl font-bold mb-2">No articles found</h2>
            <p className="text-muted-foreground mb-6">
              {selectedCategories.length === 0
                ? 'Please select at least one category to view articles'
                : 'No articles available for the selected categories'}
            </p>
          </section>
        ) : (
          <>
            <section className="space-y-4" aria-label="Article list">
              {articles?.map((article) => <ArticleCard key={article.id} article={article} />)}
            </section>

            {loadingMore && (
              <div className="flex justify-center py-8" role="status" aria-live="polite">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                <span className="sr-only">Loading more articles...</span>
              </div>
            )}

            {!hasNextPage && articles?.length > 0 && (
              <div className="text-center py-8 text-muted-foreground" role="status">
                No more articles
              </div>
            )}
          </>
        )}
      </div>
    </ProtectedRoute>
  );
}
