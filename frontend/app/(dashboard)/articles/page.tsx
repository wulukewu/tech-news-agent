'use client';

import { ArticleBrowser } from '@/features/articles/components/ArticleBrowser';
import { MobileArticleBrowser } from '@/features/articles/components/MobileArticleBrowser';
import { useUrlState } from '@/lib/hooks/useUrlState';
import { useResponsiveLayout } from '@/hooks/useResponsiveLayout';
import { useState, Suspense } from 'react';
import type { ArticleFilters } from '@/types/article';

function ArticlesPageContent() {
  const { initialFilters, updateUrl, isInitialized } = useUrlState();
  const { isMobile } = useResponsiveLayout();
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);

  const handleAnalyze = (articleId: string) => {
    setSelectedArticleId(articleId);
    setAnalysisModalOpen(true);
    // TODO: Implement AI analysis modal in future tasks
  };

  const handleAddToReadingList = (articleId: string) => {
    // TODO: Implement reading list functionality
  };

  const handleFiltersChange = (filters: ArticleFilters) => {
    updateUrl(filters);
  };

  // Don't render until URL state is initialized to prevent hydration mismatch
  if (!isInitialized) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">文章瀏覽</h1>
            <p className="text-muted-foreground text-sm sm:text-base">
              探索最新的技術文章和深度分析
            </p>
          </div>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header - responsive text sizes */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">文章瀏覽</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            探索最新的技術文章和深度分析
            {!isMobile && ' • 使用 j/k 鍵導航，r 鍵重新整理'}
          </p>
        </div>
      </div>

      {/* Conditional rendering based on device type */}
      {isMobile ? (
        <MobileArticleBrowser
          articles={[]} // TODO: Pass actual articles from ArticleBrowser
          onRefresh={async () => {
            // TODO: Implement refresh functionality
          }}
          onFilterToggle={() => {
            // TODO: Implement mobile filter toggle
          }}
          onSearchToggle={() => {
            // TODO: Implement mobile search toggle
          }}
          className="h-[calc(100vh-200px)]"
        />
      ) : (
        <ArticleBrowser
          initialFilters={initialFilters}
          showAnalysisButtons={true}
          showReadingListButtons={true}
          onAnalyze={handleAnalyze}
          onAddToReadingList={handleAddToReadingList}
          onFiltersChange={handleFiltersChange}
          enableVirtualization={true}
        />
      )}

      {/* TODO: Add AI Analysis Modal in future tasks */}
      {analysisModalOpen && selectedArticleId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background p-4 sm:p-6 rounded-lg max-w-2xl w-full">
            <h2 className="text-lg sm:text-xl font-semibold mb-4">AI 深度分析</h2>
            <p className="text-muted-foreground mb-4 text-sm sm:text-base">
              文章 ID: {selectedArticleId}
            </p>
            <p className="text-xs sm:text-sm text-muted-foreground mb-4">
              AI 分析功能將在後續任務中實作
            </p>
            <button
              onClick={() => setAnalysisModalOpen(false)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 touch-target text-sm sm:text-base"
            >
              關閉
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ArticlesPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">文章瀏覽</h1>
              <p className="text-muted-foreground text-sm sm:text-base">
                探索最新的技術文章和深度分析
              </p>
            </div>
          </div>
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </div>
      }
    >
      <ArticlesPageContent />
    </Suspense>
  );
}
