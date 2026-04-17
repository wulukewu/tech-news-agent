'use client';

import { useState, useEffect, useMemo, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { ArticleGrid } from '@/components/ArticleGrid';
import { ArticleListSkeleton } from '@/components/LoadingSkeleton';
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';
import { useScrollRestoration } from '@/lib/hooks/useScrollRestoration';
import { fetchCategories } from '@/lib/api/articles';
import { useDashboardFilters } from './hooks/useDashboardFilters';
import { useDashboardArticles } from './hooks/useDashboardArticles';
import { DashboardHeader } from './components/DashboardHeader';
import { EmptyState } from './components/EmptyState';

function DashboardContent() {
  const searchParams = useSearchParams();
  const [categories, setCategories] = useState<string[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  useScrollRestoration('dashboard');

  const {
    selectedCategories,
    setSelectedCategories,
    searchQuery,
    toggleCategory,
    selectAllCategories,
    deselectAllCategories,
    handleSearch,
  } = useDashboardFilters({ categories });

  const { articles, loading, loadingMore, hasNextPage, handleLoadMore } = useDashboardArticles({
    selectedCategories,
    loadingCategories,
  });

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const cats = await fetchCategories();
        setCategories(cats || []);

        const categoriesParam = searchParams.get('categories');
        if (categoriesParam) {
          const urlCategories = categoriesParam.split(',').filter(Boolean);
          const validCategories = urlCategories.filter((cat) => (cats || []).includes(cat));
          setSelectedCategories(validCategories.length > 0 ? validCategories : cats || []);
        } else {
          setSelectedCategories(cats || []);
        }
      } catch (error) {
        setCategories([]);
        setSelectedCategories([]);
      } finally {
        setLoadingCategories(false);
      }
    };

    loadCategories();
  }, [searchParams, setSelectedCategories]);

  const filteredArticles = useMemo(() => {
    if (!searchQuery.trim()) return articles;
    const query = searchQuery.toLowerCase().trim();
    return articles.filter(
      (article) =>
        article.title.toLowerCase().includes(query) ||
        article.aiSummary?.toLowerCase().includes(query) ||
        article.category.toLowerCase().includes(query)
    );
  }, [articles, searchQuery]);

  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore: hasNextPage,
    loading: loadingMore,
  });

  if (loading || loadingCategories) {
    return (
      <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold">Your Articles</h1>
        </header>
        <ArticleListSkeleton />
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
      <DashboardHeader
        categories={categories}
        selectedCategories={selectedCategories}
        searchQuery={searchQuery}
        articlesCount={filteredArticles.length}
        loadingCategories={loadingCategories}
        onSearch={handleSearch}
        onToggleCategory={toggleCategory}
        onSelectAll={selectAllCategories}
        onClearAll={deselectAllCategories}
      />

      {filteredArticles.length === 0 ? (
        <EmptyState
          searchQuery={searchQuery}
          selectedCategoriesCount={selectedCategories.length}
          onClearSearch={() => handleSearch('')}
        />
      ) : (
        <>
          <section aria-label="Article list">
            <ArticleGrid articles={filteredArticles} />
          </section>

          {hasNextPage && <div ref={sentinelRef} className="h-px" aria-hidden="true" />}

          {loadingMore && (
            <div className="flex justify-center py-8" role="status" aria-live="polite">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              <span className="sr-only">Loading more articles...</span>
            </div>
          )}

          {!hasNextPage && filteredArticles.length > 0 && (
            <div className="text-center py-8 text-muted-foreground" role="status">
              No more articles
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <Suspense
        fallback={
          <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
            <header className="mb-6">
              <h1 className="text-3xl font-bold">Your Articles</h1>
            </header>
            <ArticleListSkeleton />
          </div>
        }
      >
        <DashboardContent />
      </Suspense>
    </ProtectedRoute>
  );
}
