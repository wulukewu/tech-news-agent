'use client';

import {
  Check,
  Archive,
  Trash2,
  Loader2,
  ExternalLink,
  RotateCcw,
  ArchiveRestore,
} from 'lucide-react';
import { formatDistanceToNow, format, isAfter, subDays } from 'date-fns';
import { cn } from '@/lib/utils';
import type {
  ReadingListItem as ReadingListItemType,
  ReadingListStatus,
} from '@/types/readingList';
import { RatingSelector } from './RatingSelector';
import { useState } from 'react';

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
  let dateDisplay = 'Recently added';
  try {
    const addedDate = new Date(item.addedAt);
    if (!isNaN(addedDate.getTime())) {
      const sevenDaysAgo = subDays(new Date(), 7);
      dateDisplay = isAfter(addedDate, sevenDaysAgo)
        ? formatDistanceToNow(addedDate, { addSuffix: true })
        : format(addedDate, 'MMM d, yyyy');
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
        'transition-shadow duration-200 hover:shadow-lg',
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
            'line-clamp-2 transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded',
            'inline-flex items-center gap-2'
          )}
        >
          {item.title}
          <ExternalLink className="h-4 w-4 flex-shrink-0" />
        </a>
      </div>

      {/* Metadata row */}
      <div className="flex flex-wrap items-center gap-2 mb-4 text-sm">
        {/* Category badge */}
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-secondary text-secondary-foreground font-medium">
          {item.category}
        </span>

        {/* Status badge */}
        <span
          className={cn(
            'inline-flex items-center px-2.5 py-0.5 rounded-full font-medium',
            statusColors[item.status]
          )}
        >
          Status: {item.status}
        </span>

        {/* Added date */}
        <span className="text-muted-foreground">Added {dateDisplay}</span>
      </div>

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
                'hover:bg-primary/90 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'text-sm font-medium',
                'motion-reduce:transition-none'
              )}
            >
              {loadingAction === 'status' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">Mark as Read</span>
            </button>
          )}

          {item.status === 'Read' && (
            <button
              onClick={() => handleStatusChange('Unread')}
              disabled={isLoading}
              aria-label="Mark as unread"
              className={cn(
                'inline-flex items-center gap-2 px-3 py-2 rounded-md',
                'bg-primary text-primary-foreground',
                'hover:bg-primary/90 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'text-sm font-medium',
                'motion-reduce:transition-none'
              )}
            >
              {loadingAction === 'status' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCcw className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">Mark as Unread</span>
            </button>
          )}

          {item.status === 'Archived' && (
            <button
              onClick={() => handleStatusChange('Unread')}
              disabled={isLoading}
              aria-label="Unarchive"
              className={cn(
                'inline-flex items-center gap-2 px-3 py-2 rounded-md',
                'bg-primary text-primary-foreground',
                'hover:bg-primary/90 transition-colors',
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
              <span className="hidden sm:inline">Unarchive</span>
            </button>
          )}

          {/* Archive button - only show if not already archived */}
          {item.status !== 'Archived' && (
            <button
              onClick={() => handleStatusChange('Archived')}
              disabled={isLoading}
              aria-label="Archive"
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
              <span className="hidden sm:inline">Archive</span>
            </button>
          )}

          {/* Remove */}
          <button
            onClick={handleRemove}
            disabled={isLoading}
            aria-label="Remove from list"
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
            <span className="hidden sm:inline">Remove</span>
          </button>
        </div>
      </div>
    </article>
  );
}
