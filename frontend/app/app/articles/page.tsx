'use client';

import { useState, useEffect, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ArticleGrid } from '@/components/ArticleGrid';
import { ArticleListSkeleton } from '@/components/LoadingSkeleton';
import { useInfiniteScroll } from '@/lib/hooks/useInfiniteScroll';
import { useScrollRestoration } from '@/lib/hooks/useScrollRestoration';
import { fetchCategories } from '@/lib/api/articles';
import { fetchReadingList } from '@/lib/api/readingList';
import { useDashboardFilters } from './hooks/useDashboardFilters';
import { useDashboardArticles } from './hooks/useDashboardArticles';
import { EmptyState } from './components/EmptyState';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ViewModeSelector, type ViewMode } from './components/ViewModeSelector';
import { SortSelector, type SortOption } from './components/SortSelector';
import { CategoryFilter } from '@/components/CategoryFilter';
import { SearchBar } from '@/components/SearchBar';
import { useI18n } from '@/contexts/I18nContext';
import type { Article } from '@/types/article';

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { t } = useI18n();
  const [categories, setCategories] = useState<string[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [savedArticles, setSavedArticles] = useState<Article[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(false);

  // Get tab from URL, default to 'all'
  const currentTab = searchParams.get('tab') || 'all';

  // View mode and sort state
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [sortOption, setSortOption] = useState<SortOption>('latest');

  const handleAnalyze = (articleId: string) => {
    router.push(`/app/chat?articleId=${articleId}`);
  };

  useScrollRestoration('dashboard');

  const {
    selectedCategories,
    setSelectedCategories,
    searchQuery,
    toggleCategory,
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
    router.push(`/app/articles?${params.toString()}`, { scroll: false });

    // Load saved articles when switching to saved tab
    if (value === 'saved' && savedArticles.length === 0) {
      setLoadingSaved(true);
      fetchReadingList(1, 50)
        .then((data) => {
          // Map reading list items to Article shape for display
          const mapped: Article[] = data.items.map((item) => ({
            id: item.articleId,
            title: item.title,
            url: item.url,
            feedName: '',
            category: item.category,
            publishedAt: item.addedAt,
            tinkeringIndex: 0,
            aiSummary: null,
            isInReadingList: true,
          }));
          setSavedArticles(mapped);
        })
        .catch(() => setSavedArticles([]))
        .finally(() => setLoadingSaved(false));
    }
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
    if (currentTab === 'saved') {
      // Show saved articles from reading list
      result = savedArticles;
    } else if (currentTab === 'recommended') {
      // Show articles with high tinkering index (>= 7)
      result = result.filter((article) => (article.tinkeringIndex || 0) >= 7);
    }
    // 'all' and 'subscribed' tabs show everything (no additional filtering)

    // Sort articles
    if (sortOption === 'popular') {
      // Sort by a combination of tinkering index and recency
      result = [...result].sort((a, b) => {
        const timeA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
        const timeB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
        const scoreA = (a.tinkeringIndex || 0) * 10 + timeB / 1000000;
        const scoreB = (b.tinkeringIndex || 0) * 10 + timeA / 1000000;
        return scoreB - scoreA;
      });
    } else if (sortOption === 'tinkering') {
      result = [...result].sort((a, b) => (b.tinkeringIndex || 0) - (a.tinkeringIndex || 0));
    } else {
      // Latest (default) - already sorted by publishedAt from API
      result = [...result];
    }

    return result;
  }, [articles, savedArticles, searchQuery, currentTab, sortOption]);

  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore: hasNextPage,
    loading: loadingMore,
  });

  return (
    <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{t('pages.articles.title')}</h1>
        <p className="text-muted-foreground">{t('pages.articles.description')}</p>
      </div>

      <Tabs value={currentTab} onValueChange={handleTabChange} className="space-y-6">
        {/* Filters and Controls */}
        <div className="space-y-2">
          <SearchBar onSearch={handleSearch} placeholder="Search articles..." />
          <div className="flex items-center gap-2">
            <TabsList>
              <TabsTrigger value="all">{t('ui.all')}</TabsTrigger>
              <TabsTrigger value="saved">{t('ui.saved')}</TabsTrigger>
              <TabsTrigger value="recommended">{t('ui.recommended')}</TabsTrigger>
            </TabsList>
            <div className="flex items-center gap-2 ml-auto">
              <SortSelector value={sortOption} onChange={setSortOption} />
              <ViewModeSelector value={viewMode} onChange={setViewMode} />
            </div>
          </div>
          <CategoryFilter
            categories={categories}
            selectedCategories={selectedCategories}
            onToggleCategory={toggleCategory}
            onClearAll={deselectAllCategories}
            loading={loadingCategories}
          />
        </div>

        <TabsContent value="all" className="mt-6">
          {loading ? (
            <ArticleListSkeleton />
          ) : filteredArticles.length === 0 ? (
            <EmptyState
              searchQuery={searchQuery}
              selectedCategoriesCount={selectedCategories.length}
              onClearSearch={() => handleSearch('')}
              hasNoSubscriptions={articles.length === 0 && !loading}
            />
          ) : (
            <>
              <section aria-label={t('articles-page.article-list-aria')}>
                <ArticleGrid
                  articles={filteredArticles}
                  viewMode={viewMode}
                  showAnalysisButton
                  onAnalyze={handleAnalyze}
                />
              </section>

              {hasNextPage && <div ref={sentinelRef} className="h-px" aria-hidden="true" />}

              {loadingMore && (
                <div className="flex justify-center py-8" role="status" aria-live="polite">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  <span className="sr-only">{t('articles-page.loading-more-sr')}</span>
                </div>
              )}

              {!hasNextPage && filteredArticles.length > 0 && (
                <div className="text-center py-8 text-muted-foreground" role="status">
                  {t('articles-page.no-more-articles')}
                </div>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="saved" className="mt-6">
          {loadingSaved ? (
            <ArticleListSkeleton />
          ) : savedArticles.length === 0 ? (
            <section className="flex flex-col items-center justify-center min-h-[40vh] text-center gap-4">
              <p className="text-xl font-semibold">{t('articles-page.no-saved-articles')}</p>
              <p className="text-muted-foreground">{t('articles-page.save-articles-hint')}</p>
            </section>
          ) : (
            <section aria-label={t('articles-page.saved-aria')}>
              <ArticleGrid articles={savedArticles} viewMode={viewMode} />
            </section>
          )}
        </TabsContent>

        <TabsContent value="recommended" className="mt-6">
          {loading ? (
            <ArticleListSkeleton />
          ) : filteredArticles.length === 0 ? (
            <section className="flex flex-col items-center justify-center min-h-[40vh] text-center gap-4">
              <p className="text-xl font-semibold">{t('articles-page.no-recommended-articles')}</p>
              <p className="text-muted-foreground">{t('articles-page.no-recommended-hint')}</p>
            </section>
          ) : (
            <section aria-label={t('articles-page.recommended-aria')}>
              <ArticleGrid
                articles={filteredArticles}
                viewMode={viewMode}
                showAnalysisButton
                onAnalyze={handleAnalyze}
              />
            </section>
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
