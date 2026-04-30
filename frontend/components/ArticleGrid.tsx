'use client';

import { ArticleCard } from '@/components/ArticleCard';
import type { Article } from '@/types/article';

interface ArticleGridProps {
  articles: Article[];
  /** Show analysis button on cards */
  showAnalysisButton?: boolean;
  /** Show reading list button on cards */
  showReadingListButton?: boolean;
  /** Callback when analysis is requested */
  onAnalyze?: (articleId: string) => void;
  /** Callback when article is added to reading list */
  onAddToReadingList?: (articleId: string) => void;
  /** View mode for articles display */
  viewMode?: 'card' | 'list' | 'compact';
}

/**
 * ArticleGrid Component
 *
 * Responsive grid layout for displaying articles:
 * - Mobile (< 768px): 1 column, full width
 * - Tablet (768px-1024px): 2 columns
 * - Desktop (1024px+): 3 columns
 * - Maximum container width: 1400px (max-w-7xl)
 * - Gap spacing: 16px (gap-4)
 *
 * Requirements:
 * - 1.4: Single column layout on mobile viewport
 * - 1.5: Two-column grid on tablet viewport
 * - 1.6: Three-column grid on desktop viewport with max 1400px width
 * - 1.7: Consistent 16px gap spacing between grid items
 */
export function ArticleGrid({
  articles,
  showAnalysisButton = false,
  showReadingListButton = true,
  onAnalyze,
  onAddToReadingList,
  viewMode = 'card',
}: ArticleGridProps) {
  // Different layouts based on view mode
  const getGridClasses = () => {
    switch (viewMode) {
      case 'list':
        return 'flex flex-col gap-4';
      case 'compact':
        return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3';
      case 'card':
      default:
        return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4';
    }
  };

  const getArticleLayout = () => {
    switch (viewMode) {
      case 'list':
        return 'desktop';
      case 'compact':
      case 'card':
      default:
        return 'mobile';
    }
  };

  return (
    <div className={getGridClasses()} role="list" aria-label="Articles grid">
      {articles.map((article) => (
        <div key={article.id} role="listitem">
          <ArticleCard
            article={article}
            showAnalysisButton={showAnalysisButton}
            showReadingListButton={showReadingListButton}
            onAnalyze={onAnalyze}
            onAddToReadingList={onAddToReadingList}
            layout={getArticleLayout()}
          />
        </div>
      ))}
    </div>
  );
}
