'use client';

import { useState, useEffect, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ArticleGrid } from '@/components/ArticleGrid';
import { ArticleListSkeleton } from '@/components/LoadingSkeleton';
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';
import { useScrollRestoration } from '@/lib/hooks/useScrollRestoration';
import { fetchCategories } from '@/lib/api/articles';
import { useDashboardFilters } from './hooks/useDashboardFilters';
import { useDashboardArticles } from './hooks/useDashboardArticles';
import { DashboardHeader } from './components/DashboardHeader';
import { EmptyState } from './components/EmptyState';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ViewModeSelector, type ViewMode } from './components/ViewModeSelector';
import { SortSelector, type SortOption } from './components/SortSelector';
import { CategoryFilter } from '@/components/CategoryFilter';
import { useI18n } from '@/contexts/I18nContext';

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { t } = useI18n();
  const [categories, setCategories] = useState<string[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  // Get tab from URL, default to 'all'
  const currentTab = searchParams.get('tab') || 'all';

  // View mode and sort state
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [sortOption, setSortOption] = useState<SortOption>('latest');

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

  // Handle tab change
  const handleTabChange = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('tab', value);
    router.push(`/dashboard/articles?${params.toString()}`, { scroll: false });
  };

  const filteredArticles = useMemo(() => {
    let result = articles;

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter(
        (article) =>
          article.title.toLowerCase().includes(query) ||
          article.aiSummary?.toLowerCase().includes(query) ||
          article.category.toLowerCase().includes(query)
      );
    }

    // Filter by tab
    // TODO: Implement actual filtering based on tab (recommended, subscribed, saved)
    // For now, all tabs show the same articles

    // Sort articles
    if (sortOption === 'popular') {
      // TODO: Implement popularity sorting when available
      result = [...result];
    } else if (sortOption === 'tinkering') {
      result = [...result].sort((a, b) => (b.tinkeringIndex || 0) - (a.tinkeringIndex || 0));
    } else {
      // Latest (default) - already sorted by publishedAt from API
      result = [...result];
    }

    return result;
  }, [articles, searchQuery, currentTab, sortOption]);

  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore: hasNextPage,
    loading: loadingMore,
  });

  if (loading || loadingCategories) {
    return (
      <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold">{t('pages.articles.title')}</h1>
        </header>
        <ArticleListSkeleton />
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{t('pages.articles.title')}</h1>
        <p className="text-muted-foreground">{t('pages.articles.description')}</p>
      </div>

      <Tabs value={currentTab} onValueChange={handleTabChange} className="space-y-6">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="recommended">Recommended</TabsTrigger>
          <TabsTrigger value="subscribed">Subscribed</TabsTrigger>
          <TabsTrigger value="saved">Saved</TabsTrigger>
        </TabsList>

        {/* Filters and Controls */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-wrap gap-2 items-center">
            <CategoryFilter
              categories={categories}
              selectedCategories={selectedCategories}
              onToggleCategory={toggleCategory}
              onSelectAll={selectAllCategories}
              onClearAll={deselectAllCategories}
              loading={loadingCategories}
            />
            <SortSelector value={sortOption} onChange={setSortOption} />
          </div>
          <ViewModeSelector value={viewMode} onChange={setViewMode} />
        </div>

        <TabsContent value="all" className="mt-6">
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
        </TabsContent>

        <TabsContent value="recommended" className="mt-6">
          {filteredArticles.length === 0 ? (
            <EmptyState
              searchQuery={searchQuery}
              selectedCategoriesCount={selectedCategories.length}
              onClearSearch={() => handleSearch('')}
            />
          ) : (
            <>
              <section aria-label="Recommended articles">
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
        </TabsContent>

        <TabsContent value="subscribed" className="mt-6">
          {filteredArticles.length === 0 ? (
            <EmptyState
              searchQuery={searchQuery}
              selectedCategoriesCount={selectedCategories.length}
              onClearSearch={() => handleSearch('')}
            />
          ) : (
            <>
              <section aria-label="Subscribed articles">
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
        </TabsContent>

        <TabsContent value="saved" className="mt-6">
          {filteredArticles.length === 0 ? (
            <EmptyState
              searchQuery={searchQuery}
              selectedCategoriesCount={selectedCategories.length}
              onClearSearch={() => handleSearch('')}
            />
          ) : (
            <>
              <section aria-label="Saved articles">
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
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function DashboardPage() {
  const { t } = useI18n();

  return (
    <Suspense
      fallback={
        <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
          <header className="mb-6">
            <h1 className="text-3xl font-bold">{t('pages.articles.title')}</h1>
          </header>
          <ArticleListSkeleton />
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
