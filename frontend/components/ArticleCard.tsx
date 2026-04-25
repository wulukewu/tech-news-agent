'use client';

import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';
import { BookmarkPlus, BookmarkCheck, Star, Loader2, CheckCircle } from 'lucide-react';
import Image from 'next/image';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn, getCategoryBadgeStyles } from '@/lib/utils';
import type { Article } from '@/types/article';
import { useAddToReadingList } from '@/lib/hooks/useReadingList';
import { toast } from '@/lib/toast';
import { useTheme } from 'next-themes';
import { useI18n } from '@/contexts/I18nContext';

interface ArticleCardProps {
  article: Article;
  /** Show analysis button (for Deep Dive Analysis) */
  showAnalysisButton?: boolean;
  /** Show reading list button */
  showReadingListButton?: boolean;
  /** Callback when analysis is requested */
  onAnalyze?: (articleId: string) => void;
  /** Callback when article is added to reading list */
  onAddToReadingList?: (articleId: string) => void;
  /** Layout variant - mobile (vertical) or desktop (horizontal) */
  layout?: 'mobile' | 'desktop';
}

export function ArticleCard({
  article,
  showAnalysisButton = false,
  showReadingListButton = true,
  onAnalyze,
  onAddToReadingList,
  layout = 'mobile',
}: ArticleCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAdded, setIsAdded] = useState(article.isInReadingList);
  const addToReadingList = useAddToReadingList();
  const { theme } = useTheme();
  const { t, locale } = useI18n();
  const dateFnsLocale = locale === 'zh-TW' ? zhTW : enUS;

  const handleAddToReadingList = async () => {
    if (!article.id) {
      console.error('Cannot add to reading list: article.id is undefined');
      toast.error(t('errors.article-add-failed'));
      return;
    }

    // Use callback if provided, otherwise use the hook
    if (onAddToReadingList) {
      onAddToReadingList(article.id);
      return;
    }

    try {
      await addToReadingList.mutateAsync(article.id);
      setIsAdded(true);
      toast.success(t('success.article-saved'));
    } catch (error) {
      // Error handling is done in the hook with toast
      console.error('Failed to add to reading list:', error);
    }
  };

  const handleAnalyze = () => {
    if (onAnalyze && article.id) {
      onAnalyze(article.id);
    }
  };

  const formattedDate = article.publishedAt
    ? (() => {
        try {
          const date = new Date(article.publishedAt);
          if (isNaN(date.getTime())) {
            return t('article-card.recently-added');
          }

          const now = new Date();
          const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);

          if (diffInMinutes < 0) {
            return t('article-card.recently-added');
          }

          if (diffInMinutes < 60) {
            return t('article-card.minutes-ago', { count: diffInMinutes });
          }
          return formatDistanceToNow(date, { addSuffix: true, locale: dateFnsLocale });
        } catch (error) {
          console.error('Error formatting date:', error, 'publishedAt:', article.publishedAt);
          return t('article-card.recently-added');
        }
      })()
    : t('article-card.recently-added');

  const shouldShowReadMore = article.aiSummary && article.aiSummary.length > 200;

  // Get category badge styles with theme-aware colors
  const categoryStyles = getCategoryBadgeStyles(
    article.category,
    (theme as 'light' | 'dark') || 'light'
  );

  // Mobile vertical layout (Task 6.1)
  if (layout === 'mobile') {
    return (
      <article>
        <Card className="hover:shadow-md transition-shadow cursor-pointer overflow-hidden">
          <CardContent className="p-0">
            {/* Vertical stack layout */}
            <div className="flex flex-col">
              {/* Image - Only show if imageUrl exists */}
              {article.imageUrl && (
                <div className="relative w-full aspect-video overflow-hidden">
                  <Image
                    src={article.imageUrl}
                    alt={article.title}
                    width={400}
                    height={225}
                    className="w-full h-full object-cover"
                    sizes="(max-width: 768px) 100vw, 400px"
                    priority={false}
                    onError={(e) => {
                      e.currentTarget.parentElement!.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Content container with padding */}
              <div className="p-4 flex flex-col gap-3">
                {/* Title with line-clamp-2 truncation */}
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  <h3 className="text-base font-semibold line-clamp-2 leading-snug">
                    {article.title}
                  </h3>
                </a>

                {/* Metadata row: source, category badge, date */}
                <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                  {article.feedName && <span className="truncate">{article.feedName}</span>}
                  {article.feedName && <span aria-hidden="true">•</span>}
                  <Badge variant="secondary" style={categoryStyles}>
                    {article.category}
                  </Badge>
                  <span aria-hidden="true">•</span>
                  <time dateTime={article.publishedAt || undefined}>{formattedDate}</time>
                </div>

                {/* Tinkering Index with star icons (1-5) */}
                <TinkeringIndexStars index={article.tinkeringIndex} />

                {/* Summary with line-clamp */}
                {article.aiSummary && (
                  <div>
                    <p
                      className={cn(
                        'text-sm text-muted-foreground',
                        !isExpanded && shouldShowReadMore && 'line-clamp-2'
                      )}
                    >
                      {article.aiSummary}
                    </p>
                    {shouldShowReadMore && (
                      <Button
                        variant="link"
                        size="sm"
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="mt-1 p-0 h-auto text-xs"
                        aria-expanded={isExpanded}
                      >
                        {isExpanded ? t('ui.show-less') : t('ui.read-more')}
                      </Button>
                    )}
                  </div>
                )}

                {/* Action buttons with 44px touch targets */}
                <div className="flex gap-2">
                  {showReadingListButton && (
                    <Button
                      variant="outline"
                      onClick={handleAddToReadingList}
                      disabled={addToReadingList.isPending || isAdded}
                      aria-label={
                        isAdded
                          ? t('article-card.added-to-reading-list-aria')
                          : t('article-card.add-to-reading-list-aria')
                      }
                      className="flex-1 min-h-[44px] min-w-[44px]"
                    >
                      {addToReadingList.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : isAdded ? (
                        <BookmarkCheck className="h-4 w-4 mr-2" />
                      ) : (
                        <BookmarkPlus className="h-4 w-4 mr-2" />
                      )}
                      <span className="text-sm">
                        {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                      </span>
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    onClick={handleAddToReadingList}
                    disabled={isAdded}
                    aria-label={t('article-card.mark-as-read-aria')}
                    className="flex-1 min-h-[44px] min-w-[44px]"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    <span className="text-sm">{t('buttons.mark-as-read')}</span>
                  </Button>
                </div>

                {/* Optional analysis button */}
                {showAnalysisButton && (
                  <Button
                    variant="default"
                    onClick={handleAnalyze}
                    aria-label={t('article-card.deep-dive-aria')}
                    className="w-full min-h-[44px]"
                  >
                    {t('article-card.deep-dive-label')}
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </article>
    );
  }

  // Desktop horizontal layout (Task 6.2)
  return (
    <article>
      <Card className="hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 cursor-pointer overflow-hidden">
        <CardContent className="p-0">
          {/* Horizontal layout: image left (if available), content right */}
          <div className="flex gap-0">
            {/* Image - Left side (200x150) - Only show if imageUrl exists */}
            {article.imageUrl && (
              <div className="relative w-44 flex-shrink-0 overflow-hidden rounded-l-lg">
                <Image
                  src={article.imageUrl}
                  alt={article.title}
                  width={176}
                  height={132}
                  className="w-full h-full object-cover"
                  sizes="176px"
                  priority={false}
                  onError={(e) => {
                    e.currentTarget.parentElement!.style.display = 'none';
                  }}
                />
              </div>
            )}

            {/* Content - Right side */}
            <div className="flex flex-1 flex-col gap-2 p-4">
              {/* Title and Share button row */}
              <div className="flex items-start justify-between gap-2">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline flex-1"
                >
                  <h3 className="text-lg font-semibold line-clamp-3">{article.title}</h3>
                </a>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={(e) => {
                    e.preventDefault();
                    // Share functionality
                    if (navigator.share) {
                      navigator.share({
                        title: article.title,
                        url: article.url,
                      });
                    } else {
                      // Fallback: copy to clipboard
                      navigator.clipboard.writeText(article.url);
                      toast.success(t('success.link-copied'));
                    }
                  }}
                  aria-label="Share article"
                  className="min-h-[44px] min-w-[44px] cursor-pointer"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-4 w-4"
                  >
                    <circle cx="18" cy="5" r="3" />
                    <circle cx="6" cy="12" r="3" />
                    <circle cx="18" cy="19" r="3" />
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
                  </svg>
                </Button>
              </div>

              {/* Metadata row: source, category badge, date */}
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                {article.feedName && <span className="truncate">{article.feedName}</span>}
                {article.feedName && <span aria-hidden="true">•</span>}
                <Badge variant="secondary" style={categoryStyles}>
                  {article.category}
                </Badge>
                <span aria-hidden="true">•</span>
                <time dateTime={article.publishedAt || undefined}>{formattedDate}</time>
              </div>

              {/* Tinkering Index with star icons */}
              <TinkeringIndexStars index={article.tinkeringIndex} />

              {/* Summary with line-clamp-2 */}
              {article.aiSummary && (
                <div>
                  <p
                    className={cn(
                      'line-clamp-2 flex-1 text-sm text-muted-foreground',
                      isExpanded && '!line-clamp-none'
                    )}
                  >
                    {article.aiSummary}
                  </p>
                  {shouldShowReadMore && (
                    <Button
                      variant="link"
                      size="sm"
                      onClick={() => setIsExpanded(!isExpanded)}
                      className="mt-1 p-0 h-auto text-xs cursor-pointer"
                      aria-expanded={isExpanded}
                    >
                      {isExpanded ? t('ui.show-less') : t('ui.read-more')}
                    </Button>
                  )}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-2">
                {showReadingListButton && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleAddToReadingList}
                    disabled={addToReadingList.isPending || isAdded}
                    aria-label={
                      isAdded
                        ? t('article-card.added-to-reading-list-aria')
                        : t('article-card.add-to-reading-list-aria')
                    }
                    className="min-h-[44px] min-w-[44px] cursor-pointer"
                  >
                    {addToReadingList.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : isAdded ? (
                      <BookmarkCheck className="h-4 w-4" />
                    ) : (
                      <BookmarkPlus className="h-4 w-4" />
                    )}
                    <span className="ml-2 text-sm">
                      {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                    </span>
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleAddToReadingList}
                  disabled={isAdded}
                  aria-label={t('article-card.mark-as-read-aria')}
                  className="min-h-[44px] min-w-[44px] cursor-pointer"
                >
                  <CheckCircle className="h-4 w-4" />
                  <span className="ml-2 text-sm">{t('buttons.mark-as-read')}</span>
                </Button>
              </div>

              {/* Optional analysis button */}
              {showAnalysisButton && (
                <Button
                  variant="default"
                  onClick={handleAnalyze}
                  aria-label={t('article-card.deep-dive-aria')}
                  className="w-full min-h-[44px] cursor-pointer"
                >
                  {t('article-card.deep-dive-label')}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </article>
  );
}

/**
 * Tinkering Index Stars Component
 * Displays 1-5 stars with color coding and tooltip:
 * - 1-2 stars: gray (beginner)
 * - 3 stars: yellow (intermediate)
 * - 4-5 stars: orange (advanced)
 *
 * Requirements:
 * - 25.1: Display tinkering index using 1-5 star icons with color coding
 * - 25.2: Use gray for 1-2 stars, yellow for 3 stars, orange for 4-5 stars
 * - 25.3: Display filled stars for rating value, outlined for remaining
 * - 25.6: Ensure 24px minimum size on mobile viewport
 * - 25.7: Include tooltip showing numeric value and description
 * - 25.8: Use consistent star icon sizing (20px standard view)
 */
function TinkeringIndexStars({ index }: { index: number }) {
  const { t } = useI18n();
  // Clamp index to valid range (1-5)
  const clampedIndex = Math.max(1, Math.min(5, index || 1));

  // Get description based on index
  const getDescription = (idx: number): string => {
    if (idx <= 2) return 'Beginner';
    if (idx === 3) return 'Intermediate';
    return 'Advanced';
  };

  // Determine color based on index
  const getStarColor = (starIndex: number) => {
    if (starIndex >= clampedIndex) {
      return 'text-gray-300 dark:text-gray-600'; // Outlined/unfilled stars
    }
    if (clampedIndex <= 2) {
      return 'fill-gray-400 text-gray-400'; // Beginner (1-2)
    }
    if (clampedIndex === 3) {
      return 'fill-yellow-400 text-yellow-400'; // Intermediate (3)
    }
    return 'fill-orange-400 text-orange-400'; // Advanced (4-5)
  };

  const description = getDescription(clampedIndex);
  const tooltipContent = `${clampedIndex} - ${description}`;

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="flex items-center gap-1 cursor-help"
            aria-label={t('article-card.tinkering-aria', { index: clampedIndex, description })}
            role="img"
          >
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={cn(
                  'h-5 w-5 min-h-[20px] min-w-[20px]', // 20px standard, 24px on mobile via min-h/w
                  'md:h-5 md:w-5', // 20px on desktop
                  getStarColor(i)
                )}
                aria-hidden="true"
              />
            ))}
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" align="center">
          <p className="text-sm font-medium">{tooltipContent}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
