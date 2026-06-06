'use client';
import { logger } from '@/lib/utils/logger';

import { useState, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';
import {
  BookmarkPlus,
  BookmarkCheck,
  Star,
  Loader2,
  CheckCircle,
  Lightbulb,
  Sparkles,
  Cpu,
} from 'lucide-react';
import Image from 'next/image';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn, getCategoryBadgeStyles } from '@/lib/utils';
import type { Article } from '@/types/article';
import { useAddToReadingList, useUpdateReadingListStatus } from '@/lib/hooks/useReadingList';
import { toast } from '@/lib/toast';
import { useTheme } from 'next-themes';
import { useI18n } from '@/contexts/I18nContext';
import { TinkeringIndexStars } from '@/components/TinkeringIndexStars';

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
  /** Layout variant - mobile (vertical), desktop (horizontal), or compact (dense) */
  layout?: 'mobile' | 'desktop' | 'compact';
  /** Hide all action buttons (useful on landing page) */
  hideActions?: boolean;
}

export function ArticleCard({
  article,
  showAnalysisButton = false,
  showReadingListButton = true,
  onAnalyze,
  onAddToReadingList,
  layout = 'mobile',
  hideActions = false,
}: ArticleCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAdded, setIsAdded] = useState(article.isInReadingList);
  const isRead = article.readStatus === 'read';
  const [isReadState, setIsReadState] = useState(isRead);
  const addToReadingList = useAddToReadingList();
  const updateStatus = useUpdateReadingListStatus();
  const { theme } = useTheme();
  const { t, locale } = useI18n();
  const dateFnsLocale = locale === 'zh-TW' ? zhTW : enUS;

  // Swipe gesture states
  const [touchStart, setTouchStart] = useState({ x: 0, y: 0 });
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isSwiping, setIsSwiping] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);

  useEffect(() => {
    setIsReadState(article.readStatus === 'read');
  }, [article.readStatus]);

  useEffect(() => {
    setIsAdded(article.isInReadingList);
  }, [article.isInReadingList]);

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

  const handleMarkAsRead = async () => {
    if (!article.id) {
      console.error('Cannot mark as read: article.id is undefined');
      toast.error(t('errors.invalid-input'));
      return;
    }

    try {
      if (isReadState || isRead) return;

      await updateStatus.mutateAsync({ articleId: article.id, status: 'Read' });
      setIsReadState(true);
      toast.success(t('success.article-marked-read'));
    } catch (error) {
      console.error('Failed to mark as read, attempting to add first:', error);
      try {
        await addToReadingList.mutateAsync(article.id);
        setIsAdded(true);
        await updateStatus.mutateAsync({ articleId: article.id, status: 'Read' });
        setIsReadState(true);
        toast.success(t('success.article-marked-read'));
      } catch (err) {
        console.error('Failed to mark as read on fallback:', err);
        toast.error(t('errors.server-error'));
      }
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    if (hideActions) return;
    const touch = e.touches[0];
    setTouchStart({ x: touch.clientX, y: touch.clientY });
    setIsSwiping(false);
    setSwipeDirection(null);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (hideActions) return;
    if (touchStart.x === 0) return;

    const touch = e.touches[0];
    const diffX = touch.clientX - touchStart.x;
    const diffY = touch.clientY - touchStart.y;

    if (!isSwiping) {
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 10) {
        setIsSwiping(true);
      } else {
        return;
      }
    }

    const constrainedOffset = Math.max(-120, Math.min(120, diffX));
    setSwipeOffset(constrainedOffset);
    setSwipeDirection(constrainedOffset > 0 ? 'right' : constrainedOffset < 0 ? 'left' : null);
  };

  const handleTouchEnd = async () => {
    if (hideActions) return;
    setTouchStart({ x: 0, y: 0 });
    setIsSwiping(false);

    if (Math.abs(swipeOffset) > 80) {
      if (swipeDirection === 'right' && !isAdded) {
        await handleAddToReadingList();
      } else if (swipeDirection === 'left' && !(isReadState || isRead)) {
        await handleMarkAsRead();
      }
    }

    setSwipeOffset(0);
    setSwipeDirection(null);
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
      <article className="h-full relative overflow-hidden rounded-xl select-none touch-pan-y">
        {/* Swipe action background indicators */}
        {swipeOffset !== 0 && (
          <div className="absolute inset-0 flex items-center justify-between rounded-xl overflow-hidden pointer-events-none">
            {swipeOffset > 0 && (
              <div
                className="absolute inset-0 bg-gradient-to-r from-emerald-500 via-emerald-500/80 to-transparent flex items-center pl-6 text-white font-semibold"
                style={{ opacity: Math.min(1, swipeOffset / 80) }}
              >
                <div className="flex flex-col items-start gap-1">
                  <BookmarkPlus className="h-5 w-5 animate-bounce" />
                  <span className="text-[10px] uppercase font-bold tracking-wider">
                    {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                  </span>
                </div>
              </div>
            )}
            {swipeOffset < 0 && (
              <div
                className="absolute inset-0 bg-gradient-to-l from-sky-600 via-sky-600/80 to-transparent flex items-center justify-end pr-6 text-white font-semibold"
                style={{ opacity: Math.min(1, Math.abs(swipeOffset) / 80) }}
              >
                <div className="flex flex-col items-end gap-1">
                  <CheckCircle className="h-5 w-5 animate-pulse" />
                  <span className="text-[10px] uppercase font-bold tracking-wider">
                    {isReadState || isRead ? t('buttons.read') : t('buttons.mark-as-read')}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        <div
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          style={{
            transform: `translateX(${swipeOffset}px)`,
            transition: isSwiping ? 'none' : 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          className="h-full w-full relative z-10"
        >
          <Card
            className={cn(
              'h-full flex flex-col group transition-all duration-300 cursor-pointer overflow-hidden hover:shadow-md hover:border-muted-foreground/20 hover:bg-muted/5',
              (isReadState || isRead) && 'opacity-60 border-l-4 border-l-green-500'
            )}
          >
            <CardContent className="p-0 h-full flex flex-col justify-between">
              {/* Top part: Image + Content */}
              <div className="flex flex-col">
                {/* Image - Only show if imageUrl exists */}
                {article.imageUrl && (
                  <div className="relative w-full aspect-video overflow-hidden">
                    <Image
                      src={article.imageUrl}
                      alt={article.title}
                      width={400}
                      height={225}
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
                      sizes="(max-width: 768px) 100vw, 400px"
                      priority={false}
                      onError={(e) => {
                        e.currentTarget.parentElement!.style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  </div>
                )}

                {/* Content container with padding */}
                <div className="p-4 flex flex-col gap-3">
                  {/* Title with line-clamp-2 truncation */}
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline group-hover:text-primary transition-colors duration-200"
                  >
                    <h3 className="text-base font-semibold line-clamp-2 leading-snug">
                      {article.title}
                    </h3>
                  </a>

                  {article.actionableTakeaway && (
                    <div className="relative overflow-hidden rounded-r-xl rounded-l-md border border-amber-500/10 border-l-4 border-l-amber-500 bg-gradient-to-r from-amber-500/5 to-yellow-500/5 dark:from-amber-500/10 dark:to-yellow-500/5 p-3 text-xs transition-all duration-300 hover:shadow-[0_2px_8px_rgba(245,158,11,0.06)] hover:border-amber-500/20">
                      <div className="flex items-center gap-1.5 font-semibold text-amber-700 dark:text-amber-300 mb-1.5">
                        <Lightbulb className="h-3.5 w-3.5 text-amber-500 flex-shrink-0 animate-pulse" />
                        <span>{t('article-card.takeaway-prefix')}</span>
                      </div>
                      <p className="text-amber-800/90 dark:text-amber-200/90 leading-relaxed font-normal italic">
                        "{article.actionableTakeaway}"
                      </p>
                    </div>
                  )}

                  {/* Metadata row: source, category badge, date */}
                  <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    {article.feedName && <span className="truncate">{article.feedName}</span>}
                    {article.feedName && <span aria-hidden="true">•</span>}
                    <Badge
                      variant="secondary"
                      style={categoryStyles}
                      className="transition-all duration-300 hover:scale-[1.02] cursor-default"
                    >
                      {article.category}
                    </Badge>
                    <span aria-hidden="true">•</span>
                    <time dateTime={article.publishedAt || undefined}>{formattedDate}</time>
                  </div>

                  {/* Tinkering Index with star icons (1-5) */}
                  <TinkeringIndexStars index={article.tinkeringIndex} />

                  {/* Agent Insight Panel (Task 10.3) */}
                  {article.aiSummary && (
                    <div className="relative overflow-hidden rounded-r-xl rounded-l-md border border-border/60 border-l-4 border-l-primary bg-gradient-to-r from-primary/5 to-violet-500/5 dark:from-primary/10 dark:to-violet-500/5 p-3.5 transition-all duration-300 hover:shadow-[0_2px_10px_rgba(99,102,241,0.06)] hover:border-primary/20">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-primary inline-flex items-center gap-1.5 uppercase tracking-wider">
                          <Sparkles className="h-3.5 w-3.5 text-primary animate-pulse" />
                          {t('reading-list-item.ai-insight-title' as any)}
                        </span>
                        {shouldShowReadMore && (
                          <button
                            onClick={() => setIsExpanded(!isExpanded)}
                            className="text-xs font-semibold text-primary/80 hover:text-primary hover:underline focus:outline-none transition-colors cursor-pointer"
                            aria-expanded={isExpanded}
                          >
                            {isExpanded ? t('buttons.collapse' as any) : t('buttons.expand' as any)}
                          </button>
                        )}
                      </div>
                      <p
                        className={cn(
                          'text-sm text-foreground/90 leading-relaxed font-normal transition-all duration-300',
                          !isExpanded && shouldShowReadMore && 'line-clamp-2',
                          isExpanded && '!line-clamp-none'
                        )}
                      >
                        {article.aiSummary}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom part: Action buttons pushed to bottom using mt-auto */}
              {!hideActions && (
                <div className="p-4 pt-0 mt-auto flex flex-col gap-2">
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
                        className="flex-1 min-h-[44px] min-w-[44px] transition-all duration-300 hover:scale-[1.02] active:scale-95"
                      >
                        {addToReadingList.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : isAdded ? (
                          <BookmarkCheck className="h-4 w-4 mr-2 text-green-600 animate-in zoom-in-50 duration-300" />
                        ) : (
                          <BookmarkPlus className="h-4 w-4 mr-2 transition-transform duration-200 group-hover:scale-[1.05]" />
                        )}
                        <span className="text-sm">
                          {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                        </span>
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      onClick={handleMarkAsRead}
                      disabled={updateStatus.isPending || isReadState || isRead}
                      aria-label={t('article-card.mark-as-read-aria')}
                      className="flex-1 min-h-[44px] min-w-[44px] transition-all duration-300 hover:scale-[1.02] active:scale-95"
                    >
                      {updateStatus.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : isReadState || isRead ? (
                        <CheckCircle className="h-4 w-4 mr-2 text-green-600 animate-in zoom-in-50 duration-300" />
                      ) : (
                        <CheckCircle className="h-4 w-4 mr-2 transition-transform duration-200 group-hover:scale-[1.05]" />
                      )}
                      <span className="text-sm">
                        {isReadState || isRead ? t('buttons.read') : t('buttons.mark-as-read')}
                      </span>
                    </Button>
                  </div>

                  {/* Optional analysis button */}
                  {showAnalysisButton && (
                    <Button
                      variant="default"
                      onClick={handleAnalyze}
                      aria-label={t('article-card.deep-dive-aria')}
                      className="w-full min-h-[44px] transition-all duration-300 hover:scale-[1.02] active:scale-95 hover:shadow-md"
                    >
                      {t('article-card.deep-dive-label')}
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </article>
    );
  }

  // Compact layout (for fast scanning)
  if (layout === 'compact') {
    return (
      <article className="relative overflow-hidden rounded-xl select-none touch-pan-y">
        {/* Swipe action background indicators */}
        {swipeOffset !== 0 && (
          <div className="absolute inset-0 flex items-center justify-between rounded-xl overflow-hidden pointer-events-none">
            {swipeOffset > 0 && (
              <div
                className="absolute inset-0 bg-gradient-to-r from-emerald-500 via-emerald-500/80 to-transparent flex items-center pl-6 text-white font-semibold"
                style={{ opacity: Math.min(1, swipeOffset / 80) }}
              >
                <div className="flex flex-col items-start gap-1">
                  <BookmarkPlus className="h-5 w-5 animate-bounce" />
                  <span className="text-[10px] uppercase font-bold tracking-wider">
                    {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                  </span>
                </div>
              </div>
            )}
            {swipeOffset < 0 && (
              <div
                className="absolute inset-0 bg-gradient-to-l from-sky-600 via-sky-600/80 to-transparent flex items-center justify-end pr-6 text-white font-semibold"
                style={{ opacity: Math.min(1, Math.abs(swipeOffset) / 80) }}
              >
                <div className="flex flex-col items-end gap-1">
                  <CheckCircle className="h-5 w-5 animate-pulse" />
                  <span className="text-[10px] uppercase font-bold tracking-wider">
                    {isReadState || isRead ? t('buttons.read') : t('buttons.mark-as-read')}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        <div
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          style={{
            transform: `translateX(${swipeOffset}px)`,
            transition: isSwiping ? 'none' : 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          className="w-full relative z-10"
        >
          <Card
            className={cn(
              'group transition-all duration-300 cursor-pointer overflow-hidden bg-card border border-border/60 p-3 hover:shadow-sm hover:border-border hover:bg-muted/10',
              (isReadState || isRead) && 'opacity-60 border-l-4 border-l-green-500'
            )}
          >
            <CardContent className="p-0 flex items-center justify-between gap-4">
              {/* Left part: Title, Category badge, published date */}
              <div className="flex flex-col gap-1.5 min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    variant="secondary"
                    style={categoryStyles}
                    className="px-1.5 py-0 rounded text-[10px] font-semibold tracking-wider transition-all duration-300 hover:scale-[1.02] cursor-default"
                  >
                    {article.category}
                  </Badge>
                  {article.feedName && (
                    <span className="text-xs text-muted-foreground truncate max-w-[120px]">
                      {article.feedName}
                    </span>
                  )}
                  <span aria-hidden="true" className="text-xs text-muted-foreground/40">
                    •
                  </span>
                  <time
                    dateTime={article.publishedAt || undefined}
                    className="text-xs text-muted-foreground"
                  >
                    {formattedDate}
                  </time>
                </div>

                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline group-hover:text-primary transition-colors duration-200 truncate block"
                >
                  <h4 className="text-sm font-semibold truncate leading-snug">{article.title}</h4>
                </a>

                {/* Tiny line of summary or takeaway context with expand/collapse */}
                {article.actionableTakeaway ? (
                  <div className="flex items-start gap-2 text-xs w-full">
                    <p
                      className={cn(
                        'text-amber-600 dark:text-amber-400 font-medium italic transition-all duration-200',
                        !isExpanded ? 'truncate flex-1' : 'whitespace-pre-wrap break-words flex-1'
                      )}
                    >
                      {article.actionableTakeaway}
                    </p>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setIsExpanded(!isExpanded);
                      }}
                      className="text-[10px] font-semibold text-amber-600/70 hover:text-amber-600 dark:text-amber-400/70 dark:hover:text-amber-400 hover:underline transition-colors flex-shrink-0"
                    >
                      {isExpanded ? t('buttons.collapse' as any) : t('buttons.expand' as any)}
                    </button>
                  </div>
                ) : article.aiSummary ? (
                  <div className="flex items-start gap-2 text-xs w-full">
                    <p
                      className={cn(
                        'text-muted-foreground transition-all duration-200',
                        !isExpanded ? 'truncate flex-1' : 'whitespace-pre-wrap break-words flex-1'
                      )}
                    >
                      {article.aiSummary}
                    </p>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setIsExpanded(!isExpanded);
                      }}
                      className="text-[10px] font-semibold text-muted-foreground/60 hover:text-primary hover:underline transition-colors flex-shrink-0"
                    >
                      {isExpanded ? t('buttons.collapse' as any) : t('buttons.expand' as any)}
                    </button>
                  </div>
                ) : null}
              </div>

              {/* Right part: Minimal icon action buttons */}
              {!hideActions && (
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  {showReadingListButton && (
                    <TooltipProvider delayDuration={300}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={handleAddToReadingList}
                            disabled={addToReadingList.isPending || isAdded}
                            aria-label={
                              isAdded
                                ? t('article-card.added-to-reading-list-aria')
                                : t('article-card.add-to-reading-list-aria')
                            }
                            className="h-8 w-8 min-h-[32px] min-w-[32px] transition-all duration-200 hover:scale-[1.05]"
                          >
                            {addToReadingList.isPending ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : isAdded ? (
                              <BookmarkCheck className="h-3.5 w-3.5 text-green-600 animate-in zoom-in-50 duration-300" />
                            ) : (
                              <BookmarkPlus className="h-3.5 w-3.5" />
                            )}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent side="top">
                          <p className="text-xs">
                            {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}

                  <TooltipProvider delayDuration={300}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={handleMarkAsRead}
                          disabled={updateStatus.isPending || isReadState || isRead}
                          aria-label={t('article-card.mark-as-read-aria')}
                          className="h-8 w-8 min-h-[32px] min-w-[32px] transition-all duration-200 hover:scale-[1.05]"
                        >
                          {updateStatus.isPending ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : isReadState || isRead ? (
                            <CheckCircle className="h-3.5 w-3.5 text-green-600 animate-in zoom-in-50 duration-300" />
                          ) : (
                            <CheckCircle className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="text-xs">
                          {isReadState || isRead ? t('buttons.read') : t('buttons.mark-as-read')}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>

                  {showAnalysisButton && (
                    <TooltipProvider delayDuration={300}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={handleAnalyze}
                            aria-label={t('article-card.deep-dive-aria')}
                            className="h-8 w-8 min-h-[32px] min-w-[32px] transition-all duration-200 hover:scale-[1.05]"
                          >
                            <Sparkles className="h-3.5 w-3.5 text-primary" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent side="top">
                          <p className="text-xs">{t('article-card.deep-dive-label')}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </article>
    );
  }

  // Desktop horizontal layout (Task 6.2)
  return (
    <article className="relative overflow-hidden rounded-xl select-none touch-pan-y">
      {/* Swipe action background indicators */}
      {swipeOffset !== 0 && (
        <div className="absolute inset-0 flex items-center justify-between rounded-xl overflow-hidden pointer-events-none">
          {swipeOffset > 0 && (
            <div
              className="absolute inset-0 bg-gradient-to-r from-emerald-500 via-emerald-500/80 to-transparent flex items-center pl-6 text-white font-semibold"
              style={{ opacity: Math.min(1, swipeOffset / 80) }}
            >
              <div className="flex flex-col items-start gap-1">
                <BookmarkPlus className="h-5 w-5 animate-bounce" />
                <span className="text-[10px] uppercase font-bold tracking-wider">
                  {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                </span>
              </div>
            </div>
          )}
          {swipeOffset < 0 && (
            <div
              className="absolute inset-0 bg-gradient-to-l from-sky-600 via-sky-600/80 to-transparent flex items-center justify-end pr-6 text-white font-semibold"
              style={{ opacity: Math.min(1, Math.abs(swipeOffset) / 80) }}
            >
              <div className="flex flex-col items-end gap-1">
                <CheckCircle className="h-5 w-5 animate-pulse" />
                <span className="text-[10px] uppercase font-bold tracking-wider">
                  {isReadState || isRead ? t('buttons.read') : t('buttons.mark-as-read')}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      <div
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{
          transform: `translateX(${swipeOffset}px)`,
          transition: isSwiping ? 'none' : 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
        className="w-full relative z-10"
      >
        <Card
          className={cn(
            'group transition-all duration-300 cursor-pointer overflow-hidden hover:shadow-md hover:border-muted-foreground/20 hover:bg-muted/5',
            (isReadState || isRead) && 'opacity-60 border-l-4 border-l-green-500'
          )}
        >
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
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
                    sizes="176px"
                    priority={false}
                    onError={(e) => {
                      e.currentTarget.parentElement!.style.display = 'none';
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-r from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
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
                    className="hover:underline flex-1 group-hover:text-primary transition-colors duration-200"
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
                    className="min-h-[44px] min-w-[44px] cursor-pointer transition-all duration-300 hover:scale-[1.05]"
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

                {article.actionableTakeaway && (
                  <div className="relative overflow-hidden rounded-r-xl rounded-l-md border border-amber-500/10 border-l-4 border-l-amber-500 bg-gradient-to-r from-amber-500/5 to-yellow-500/5 dark:from-amber-500/10 dark:to-yellow-500/5 p-3 text-xs transition-all duration-300 hover:shadow-[0_2px_8px_rgba(245,158,11,0.06)] hover:border-amber-500/20">
                    <div className="flex items-center gap-1.5 font-semibold text-amber-700 dark:text-amber-300 mb-1.5">
                      <Lightbulb className="h-3.5 w-3.5 text-amber-500 flex-shrink-0 animate-pulse" />
                      <span>{t('article-card.takeaway-prefix')}</span>
                    </div>
                    <p className="text-amber-800/90 dark:text-amber-200/90 leading-relaxed font-normal italic">
                      "{article.actionableTakeaway}"
                    </p>
                  </div>
                )}

                {/* Metadata row: source, category badge, date */}
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  {article.feedName && <span className="truncate">{article.feedName}</span>}
                  {article.feedName && <span aria-hidden="true">•</span>}
                  <Badge
                    variant="secondary"
                    style={categoryStyles}
                    className="transition-all duration-300 hover:scale-[1.02] cursor-default"
                  >
                    {article.category}
                  </Badge>
                  <span aria-hidden="true">•</span>
                  <time dateTime={article.publishedAt || undefined}>{formattedDate}</time>
                </div>

                {/* Tinkering Index with star icons */}
                <TinkeringIndexStars index={article.tinkeringIndex} />

                {/* Agent Insight Panel (Task 10.3) */}
                {article.aiSummary && (
                  <div className="relative overflow-hidden rounded-r-xl rounded-l-md border border-border/60 border-l-4 border-l-primary bg-gradient-to-r from-primary/5 to-violet-500/5 dark:from-primary/10 dark:to-violet-500/5 p-3.5 transition-all duration-300 hover:shadow-[0_2px_10px_rgba(99,102,241,0.06)] hover:border-primary/20">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-primary inline-flex items-center gap-1.5 uppercase tracking-wider">
                        <Sparkles className="h-3.5 w-3.5 text-primary animate-pulse" />
                        {t('reading-list-item.ai-insight-title' as any)}
                      </span>
                      {shouldShowReadMore && (
                        <button
                          onClick={() => setIsExpanded(!isExpanded)}
                          className="text-xs font-semibold text-primary/80 hover:text-primary hover:underline focus:outline-none transition-colors cursor-pointer"
                          aria-expanded={isExpanded}
                        >
                          {isExpanded ? t('buttons.collapse' as any) : t('buttons.expand' as any)}
                        </button>
                      )}
                    </div>
                    <p
                      className={cn(
                        'text-sm text-foreground/90 leading-relaxed font-normal transition-all duration-300',
                        !isExpanded && shouldShowReadMore && 'line-clamp-2',
                        isExpanded && '!line-clamp-none'
                      )}
                    >
                      {article.aiSummary}
                    </p>
                  </div>
                )}

                {/* Action buttons */}
                {!hideActions && (
                  <>
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
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                          ) : isAdded ? (
                            <BookmarkCheck className="h-4 w-4 mr-2 text-green-600 animate-in zoom-in-50 duration-300" />
                          ) : (
                            <BookmarkPlus className="h-4 w-4 mr-2" />
                          )}
                          <span className="text-sm">
                            {isAdded ? t('buttons.saved') : t('buttons.read-later')}
                          </span>
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleMarkAsRead}
                        disabled={updateStatus.isPending || isReadState || isRead}
                        aria-label={t('article-card.mark-as-read-aria')}
                        className="min-h-[44px] min-w-[44px] cursor-pointer animate-in fade-in"
                      >
                        {updateStatus.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : isReadState || isRead ? (
                          <CheckCircle className="h-4 w-4 mr-2 text-green-600 animate-in zoom-in-50 duration-300" />
                        ) : (
                          <CheckCircle className="h-4 w-4 mr-2" />
                        )}
                        <span className="text-sm">
                          {isReadState || isRead ? t('buttons.read') : t('buttons.mark-as-read')}
                        </span>
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
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </article>
  );
}
