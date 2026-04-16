'use client';

import React, { useState, useRef, useCallback } from 'react';
import { ChevronLeft, ChevronRight, Filter, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { PullToRefresh } from '@/components/ui/pull-to-refresh';
import { useTouchGestures } from '@/hooks/useTouchGestures';
import { ArticleCard } from '@/components/ArticleCard';
import { Article } from '@/types/article';

interface MobileArticleBrowserProps {
  articles: Article[];
  onRefresh?: () => Promise<void>;
  onLoadMore?: () => void;
  onFilterToggle?: () => void;
  onSearchToggle?: () => void;
  isLoading?: boolean;
  hasMore?: boolean;
  className?: string;
}

/**
 * Mobile-optimized article browser with swipe navigation and pull-to-refresh
 * Provides touch-friendly interface for browsing articles on mobile devices
 */
export function MobileArticleBrowser({
  articles,
  onRefresh,
  onLoadMore,
  onFilterToggle,
  onSearchToggle,
  isLoading = false,
  hasMore = false,
  className,
}: MobileArticleBrowserProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle swipe gestures for article navigation
  const { attachGestures } = useTouchGestures({
    onSwipeLeft: useCallback(() => {
      if (currentIndex < articles.length - 1) {
        setCurrentIndex(currentIndex + 1);
      }
    }, [currentIndex, articles.length]),
    onSwipeRight: useCallback(() => {
      if (currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
      }
    }, [currentIndex]),
    threshold: 50,
  });

  // Attach gestures to container
  React.useEffect(() => {
    const cleanup = attachGestures(containerRef.current);
    return cleanup;
  }, [attachGestures]);

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < articles.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleRefresh = async () => {
    if (onRefresh) {
      await onRefresh();
      setCurrentIndex(0); // Reset to first article after refresh
    }
  };

  if (articles.length === 0) {
    return (
      <div className={cn('flex flex-col items-center justify-center p-8 text-center', className)}>
        <div className="text-muted-foreground mb-4">
          <Search className="h-12 w-12 mx-auto mb-2" />
          <p className="text-lg font-medium">No articles found</p>
          <p className="text-sm">Try adjusting your filters or refresh to see new content</p>
        </div>
        {onRefresh && (
          <Button onClick={handleRefresh} disabled={isLoading}>
            Refresh
          </Button>
        )}
      </div>
    );
  }

  const currentArticle = articles[currentIndex];

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Mobile header with controls */}
      <div className="flex items-center justify-between p-4 border-b bg-background/95 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onFilterToggle}
            className="touch-target"
            aria-label="Toggle filters"
          >
            <Filter className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onSearchToggle}
            className="touch-target"
            aria-label="Toggle search"
          >
            <Search className="h-5 w-5" />
          </Button>
        </div>

        {/* Article counter */}
        <div className="text-sm text-muted-foreground">
          {currentIndex + 1} of {articles.length}
        </div>

        {/* Navigation controls */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className="touch-target"
            aria-label="Previous article"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleNext}
            disabled={currentIndex === articles.length - 1}
            className="touch-target"
            aria-label="Next article"
          >
            <ChevronRight className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Article content with pull-to-refresh */}
      <PullToRefresh
        onRefresh={handleRefresh}
        disabled={!onRefresh || isLoading}
        className="flex-1"
      >
        <div
          ref={containerRef}
          className="relative overflow-hidden"
          style={{ height: 'calc(100vh - 120px)' }}
        >
          {/* Swipe indicator */}
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
            <div className="flex items-center gap-1 bg-background/80 backdrop-blur px-3 py-1 rounded-full text-xs text-muted-foreground">
              <ChevronLeft className="h-3 w-3" />
              <span>Swipe to navigate</span>
              <ChevronRight className="h-3 w-3" />
            </div>
          </div>

          {/* Article cards container */}
          <div
            className="flex transition-transform duration-300 ease-out h-full"
            style={{
              transform: `translateX(-${currentIndex * 100}%)`,
              width: `${articles.length * 100}%`,
            }}
          >
            {articles.map((article, index) => (
              <div
                key={article.id}
                className="w-full flex-shrink-0 p-4 overflow-y-auto"
                style={{ width: `${100 / articles.length}%` }}
              >
                <ArticleCard
                  article={article}
                  showAnalysisButton={true}
                  showReadingListButton={true}
                  className="h-full"
                />
              </div>
            ))}
          </div>
        </div>
      </PullToRefresh>

      {/* Load more indicator */}
      {hasMore && currentIndex >= articles.length - 3 && (
        <div className="p-4 text-center border-t">
          <Button
            onClick={onLoadMore}
            disabled={isLoading}
            variant="outline"
            className="w-full touch-target"
          >
            {isLoading ? 'Loading...' : 'Load More Articles'}
          </Button>
        </div>
      )}

      {/* Pagination dots */}
      <div className="flex justify-center items-center gap-1 p-4 bg-background/95 backdrop-blur border-t">
        {articles.slice(0, Math.min(articles.length, 10)).map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={cn(
              'w-2 h-2 rounded-full transition-all duration-200 touch-target',
              index === currentIndex
                ? 'bg-primary scale-125'
                : 'bg-muted-foreground/30 hover:bg-muted-foreground/50'
            )}
            aria-label={`Go to article ${index + 1}`}
          />
        ))}
        {articles.length > 10 && (
          <span className="text-xs text-muted-foreground ml-2">+{articles.length - 10} more</span>
        )}
      </div>
    </div>
  );
}
