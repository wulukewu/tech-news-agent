'use client';
import { logger } from '@/lib/utils/logger';

import {
  Check,
  Archive,
  Trash2,
  Loader2,
  ExternalLink,
  RotateCcw,
  ArchiveRestore,
  Cpu,
  Sparkles,
  Lightbulb,
} from 'lucide-react';
import { TinkeringIndexStars } from '@/components/TinkeringIndexStars';
import { formatDistanceToNow, format, isAfter, subDays } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import type {
  ReadingListItem as ReadingListItemType,
  ReadingListStatus,
} from '@/types/readingList';
import { TINKERING_INDEX_LEVELS } from '@/lib/constants';
import { RatingSelector } from './RatingSelector';
import { useState } from 'react';
import { useI18n } from '@/contexts/I18nContext';

interface ReadingListItemProps {
  item: ReadingListItemType;
  onStatusChange: (articleId: string, status: ReadingListStatus) => void;
  onRatingChange: (articleId: string, rating: number | null) => void;
  onRemove: (articleId: string) => void;
}

/**
 * Card component displaying a single reading list item with actions
 * Validates Requirements 1.4, 5.1, 5.2, 5.3, 6.1, 6.4, 7.1, 7.2, 11.1, 11.2, 15.1, 15.2, 15.3, 16.1, 16.2, 16.4, 16.5, 17.1, 17.4, 18.3
 */
export function ReadingListItem({
  item,
  onStatusChange,
  onRatingChange,
  onRemove,
}: ReadingListItemProps) {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [isSummaryExpanded, setIsSummaryExpanded] = useState(false);
  const { t, locale } = useI18n();
  const dateFnsLocale = locale === 'zh-TW' ? zhTW : enUS;

  const handleStatusChange = async (status: ReadingListStatus) => {
    if (!item.articleId) {
      console.error('Cannot update status: article_id is undefined');
      return;
    }
    setLoadingAction('status');
    try {
      await onStatusChange(item.articleId, status);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleRemove = async () => {
    if (!item.articleId) {
      console.error('Cannot remove article: article_id is undefined');
      return;
    }
    setLoadingAction('remove');
    try {
      await onRemove(item.articleId);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleRatingChange = async (rating: number | null) => {
    if (!item.articleId) {
      console.error('Cannot update rating: article_id is undefined');
      return;
    }
    setLoadingAction('rating');
    try {
      await onRatingChange(item.articleId, rating);
    } finally {
      setLoadingAction(null);
    }
  };

  // Format date - handle invalid dates gracefully
  let dateDisplay = t('reading-list-item.recently-added');
  try {
    const addedDate = new Date(item.addedAt);
    if (!isNaN(addedDate.getTime())) {
      const sevenDaysAgo = subDays(new Date(), 7);
      dateDisplay = isAfter(addedDate, sevenDaysAgo)
        ? formatDistanceToNow(addedDate, { addSuffix: true, locale: dateFnsLocale })
        : format(addedDate, locale === 'zh-TW' ? 'yyyy年M月d日' : 'MMM d, yyyy', {
            locale: dateFnsLocale,
          });
    }
  } catch (error) {
    console.error('Error formatting date:', error);
  }

  // Status badge colors
  const statusColors = {
    Unread: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    Read: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    Archived: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  };

  // Sanitize URL
  const sanitizeUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.href;
    } catch {
      return '#';
    }
  };

  const isLoading = loadingAction !== null;

  return (
    <article
      className={cn(
        'bg-card border border-border rounded-lg p-4 md:p-6',
        'transition-all duration-300 hover:shadow-md hover:-translate-y-1 hover:scale-[1.01]',
        'group cursor-pointer',
        'motion-reduce:transition-none'
      )}
    >
      {/* Title and URL */}
      <div className="mb-3">
        <a
          href={sanitizeUrl(item.url)}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            'text-xl font-semibold text-foreground hover:text-primary',
            'line-clamp-2 transition-colors duration-200',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded',
            'inline-flex items-center gap-2 group-hover:text-primary'
          )}
        >
          {item.title}
          <ExternalLink className="h-4 w-4 flex-shrink-0 transition-transform duration-200 group-hover:scale-[1.05]" />
        </a>
      </div>

      {item.actionableTakeaway && (
        <div className="mb-4 flex items-start gap-2 rounded-lg bg-amber-500/5 dark:bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-xs text-amber-800 dark:text-amber-300 font-medium leading-relaxed transition-all duration-300 hover:bg-amber-500/10 hover:border-amber-500/30">
          <Lightbulb className="h-4 w-4 flex-shrink-0 text-amber-500 animate-pulse" />
          <div>
            <span className="font-bold mr-1">{t('article-card.takeaway-prefix')}：</span>
            <span className="font-normal italic">{item.actionableTakeaway}</span>
          </div>
        </div>
      )}

      {/* Metadata row */}
      <div className="flex flex-wrap items-center gap-2 mb-4 text-sm">
        {/* Category badge */}
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-secondary text-secondary-foreground font-medium transition-all duration-300 hover:scale-[1.02] cursor-default">
          {item.category}
        </span>

        {/* Tinkering Index (Technical Depth) Badge - WITHOUT EMOJIS */}
        {item.tinkeringIndex !== undefined && item.tinkeringIndex !== null && (
          <TinkeringIndexStars index={item.tinkeringIndex} />
        )}

        {/* Source badge - WITHOUT EMOJIS */}
        {item.source && (
          <span
            className={cn(
              'inline-flex items-center px-2.5 py-0.5 rounded-full font-medium text-xs',
              item.source === 'discord'
                ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
            )}
          >
            {item.source === 'discord' ? 'Discord' : 'Web'}
          </span>
        )}

        {/* Status badge */}
        <span
          className={cn(
            'inline-flex items-center px-2.5 py-0.5 rounded-full font-medium',
            statusColors[item.status]
          )}
        >
          {t('reading-list-item.status-label', { status: item.status })}
        </span>

        {/* Added date */}
        <span className="text-muted-foreground">
          {t('reading-list-item.added-date', { date: dateDisplay })}
        </span>
      </div>

      {/* AI Summary Section - WITHOUT EMOJIS */}
      {item.aiSummary && (
        <div className="mt-4 mb-5 border border-border/60 rounded-lg bg-muted/30 dark:bg-muted/10 p-4 transition-all duration-300 hover:bg-muted/40 hover:border-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider inline-flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-primary animate-pulse" />
              {t('reading-list-item.ai-insight-title', { defaultValue: 'Agent 智慧導讀' })}
            </span>
            <button
              onClick={() => setIsSummaryExpanded(!isSummaryExpanded)}
              className="text-xs text-primary hover:text-primary/80 hover:underline focus:outline-none transition-colors"
            >
              {isSummaryExpanded
                ? t('buttons.collapse', { defaultValue: '收起摘要' })
                : t('buttons.expand', { defaultValue: '展開摘要' })}
            </button>
          </div>
          <p
            className={cn(
              'text-sm text-foreground/85 leading-relaxed transition-all duration-300',
              !isSummaryExpanded && 'line-clamp-2'
            )}
          >
            {item.aiSummary}
          </p>
        </div>
      )}

      {/* Rating and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Rating */}
        <div className="flex items-center gap-2">
          <RatingSelector
            rating={item.rating}
            onChange={handleRatingChange}
            disabled={isLoading}
            size="md"
          />
          {loadingAction === 'rating' && (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Status change buttons - show different buttons based on current status */}
          {item.status === 'Unread' && (
            <button
              onClick={() => handleStatusChange('Read')}
              disabled={isLoading}
              aria-label="Mark as read"
              className={cn(
                'inline-flex items-center gap-2 px-3 py-2 rounded-md',
                'bg-primary text-primary-foreground',
                'hover:bg-primary/90 hover:scale-[1.02] active:scale-95',
                'transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'text-sm font-medium',
                'motion-reduce:transition-none'
              )}
            >
              {loadingAction === 'status' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4 transition-transform duration-300 hover:scale-[1.05]" />
              )}
              <span className="hidden sm:inline">{t('buttons.mark-as-read')}</span>
            </button>
          )}

          {item.status === 'Read' && (
            <button
              onClick={() => handleStatusChange('Unread')}
              disabled={isLoading}
              aria-label={t('reading-list-item.mark-as-unread-aria')}
              className={cn(
                'inline-flex items-center gap-2 px-3 py-2 rounded-md',
                'bg-primary text-primary-foreground',
                'hover:bg-primary/90 hover:scale-[1.02] active:scale-95',
                'transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'text-sm font-medium',
                'motion-reduce:transition-none'
              )}
            >
              {loadingAction === 'status' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCcw className="h-4 w-4 transition-transform duration-300 hover:scale-[1.05]" />
              )}
              <span className="hidden sm:inline">
                {t('reading-list-item.mark-as-unread-label')}
              </span>
            </button>
          )}

          {item.status === 'Archived' && (
            <button
              onClick={() => handleStatusChange('Unread')}
              disabled={isLoading}
              aria-label={t('reading-list-item.unarchive-aria')}
              className={cn(
                'inline-flex items-center gap-2 px-3 py-2 rounded-md',
                'bg-primary text-primary-foreground',
                'hover:bg-primary/90 hover:scale-[1.02] active:scale-95',
                'transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'text-sm font-medium',
                'motion-reduce:transition-none'
              )}
            >
              {loadingAction === 'status' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArchiveRestore className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{t('reading-list-item.unarchive-label')}</span>
            </button>
          )}

          {/* Archive button - only show if not already archived */}
          {item.status !== 'Archived' && (
            <button
              onClick={() => handleStatusChange('Archived')}
              disabled={isLoading}
              aria-label={t('reading-list-item.archive-aria')}
              className={cn(
                'inline-flex items-center gap-2 px-3 py-2 rounded-md',
                'bg-secondary text-secondary-foreground',
                'hover:bg-secondary/80 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'text-sm font-medium',
                'motion-reduce:transition-none'
              )}
            >
              {loadingAction === 'status' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Archive className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{t('reading-list-item.archive-label')}</span>
            </button>
          )}

          {/* Remove */}
          <button
            onClick={handleRemove}
            disabled={isLoading}
            aria-label={t('reading-list-item.remove-aria')}
            className={cn(
              'inline-flex items-center gap-2 px-3 py-2 rounded-md',
              'bg-destructive text-destructive-foreground',
              'hover:bg-destructive/90 transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-destructive focus:ring-offset-2',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'text-sm font-medium',
              'motion-reduce:transition-none'
            )}
          >
            {loadingAction === 'remove' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">{t('buttons.remove')}</span>
          </button>
        </div>
      </div>
    </article>
  );
}
