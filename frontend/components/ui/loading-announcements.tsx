/**
 * Accessible Loading Announcements
 *
 * Provides ARIA live regions for screen readers to announce loading states
 * and completion states for better accessibility.
 *
 * Requirements: 12.5, 15.1, 15.5
 */

'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

interface LoadingAnnouncementProps {
  isLoading: boolean;
  loadingMessage?: string;
  completedMessage?: string;
  errorMessage?: string;
  className?: string;
}

/**
 * ARIA Live Region for Loading Announcements
 * Announces loading states to screen readers
 * Requirements: 12.5, 15.1
 */
export function LoadingAnnouncement({
  isLoading,
  loadingMessage = 'Loading content',
  completedMessage = 'Content loaded',
  errorMessage,
  className,
}: LoadingAnnouncementProps) {
  const [announcement, setAnnouncement] = useState('');
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (errorMessage) {
      setAnnouncement(errorMessage);
      setHasError(true);
    } else if (isLoading) {
      setAnnouncement(loadingMessage);
      setHasError(false);
    } else if (announcement === loadingMessage) {
      // Only announce completion if we were previously loading
      setAnnouncement(completedMessage);
      setHasError(false);

      // Clear the completion message after a short delay
      const timer = setTimeout(() => {
        setAnnouncement('');
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isLoading, loadingMessage, completedMessage, errorMessage, announcement]);

  return (
    <div className={cn('sr-only', className)} role="status" aria-live="polite" aria-atomic="true">
      {announcement}
    </div>
  );
}

/**
 * Page Loading Announcer
 * Announces page-level loading states
 * Requirements: 12.5
 */
export function PageLoadingAnnouncer({
  isLoading,
  pageName,
  className,
}: {
  isLoading: boolean;
  pageName?: string;
  className?: string;
}) {
  const loadingMessage = pageName ? `Loading ${pageName} page` : 'Loading page';
  const completedMessage = pageName ? `${pageName} page loaded` : 'Page loaded';

  return (
    <LoadingAnnouncement
      isLoading={isLoading}
      loadingMessage={loadingMessage}
      completedMessage={completedMessage}
      className={className}
    />
  );
}

/**
 * Article Loading Announcer
 * Announces article-specific loading states
 * Requirements: 12.5
 */
export function ArticleLoadingAnnouncer({
  isLoading,
  count,
  isLoadingMore = false,
  className,
}: {
  isLoading: boolean;
  count?: number;
  isLoadingMore?: boolean;
  className?: string;
}) {
  const getLoadingMessage = () => {
    if (isLoadingMore) {
      return 'Loading more articles';
    }
    return 'Loading articles';
  };

  const getCompletedMessage = () => {
    if (isLoadingMore) {
      return count ? `Loaded ${count} more articles` : 'More articles loaded';
    }
    return count ? `Loaded ${count} articles` : 'Articles loaded';
  };

  return (
    <LoadingAnnouncement
      isLoading={isLoading}
      loadingMessage={getLoadingMessage()}
      completedMessage={getCompletedMessage()}
      className={className}
    />
  );
}

/**
 * Feed Loading Announcer
 * Announces feed-specific loading states
 * Requirements: 12.5
 */
export function FeedLoadingAnnouncer({
  isLoading,
  feedName,
  operation = 'loading',
  className,
}: {
  isLoading: boolean;
  feedName?: string;
  operation?: 'loading' | 'subscribing' | 'unsubscribing' | 'updating';
  className?: string;
}) {
  const getLoadingMessage = () => {
    const action = {
      loading: 'Loading',
      subscribing: 'Subscribing to',
      unsubscribing: 'Unsubscribing from',
      updating: 'Updating',
    }[operation];

    return feedName ? `${action} ${feedName}` : `${action} feed`;
  };

  const getCompletedMessage = () => {
    const action = {
      loading: 'Loaded',
      subscribing: 'Subscribed to',
      unsubscribing: 'Unsubscribed from',
      updating: 'Updated',
    }[operation];

    return feedName ? `${action} ${feedName}` : `${action} feed`;
  };

  return (
    <LoadingAnnouncement
      isLoading={isLoading}
      loadingMessage={getLoadingMessage()}
      completedMessage={getCompletedMessage()}
      className={className}
    />
  );
}

/**
 * Reading List Loading Announcer
 * Announces reading list operations
 * Requirements: 12.5
 */
export function ReadingListAnnouncer({
  isLoading,
  operation = 'loading',
  articleTitle,
  className,
}: {
  isLoading: boolean;
  operation?: 'loading' | 'adding' | 'removing' | 'updating';
  articleTitle?: string;
  className?: string;
}) {
  const getLoadingMessage = () => {
    const action = {
      loading: 'Loading reading list',
      adding: 'Adding to reading list',
      removing: 'Removing from reading list',
      updating: 'Updating reading list item',
    }[operation];

    return articleTitle ? `${action}: ${articleTitle}` : action;
  };

  const getCompletedMessage = () => {
    const action = {
      loading: 'Reading list loaded',
      adding: 'Added to reading list',
      removing: 'Removed from reading list',
      updating: 'Reading list item updated',
    }[operation];

    return articleTitle ? `${action}: ${articleTitle}` : action;
  };

  return (
    <LoadingAnnouncement
      isLoading={isLoading}
      loadingMessage={getLoadingMessage()}
      completedMessage={getCompletedMessage()}
      className={className}
    />
  );
}

/**
 * Search Loading Announcer
 * Announces search operations
 * Requirements: 12.5
 */
export function SearchLoadingAnnouncer({
  isLoading,
  query,
  resultCount,
  className,
}: {
  isLoading: boolean;
  query?: string;
  resultCount?: number;
  className?: string;
}) {
  const loadingMessage = query ? `Searching for "${query}"` : 'Searching';

  const getCompletedMessage = () => {
    if (resultCount === 0) {
      return query ? `No results found for "${query}"` : 'No results found';
    }
    if (resultCount === 1) {
      return query ? `Found 1 result for "${query}"` : 'Found 1 result';
    }
    return query ? `Found ${resultCount} results for "${query}"` : `Found ${resultCount} results`;
  };

  return (
    <LoadingAnnouncement
      isLoading={isLoading}
      loadingMessage={loadingMessage}
      completedMessage={getCompletedMessage()}
      className={className}
    />
  );
}

/**
 * Form Loading Announcer
 * Announces form submission states
 * Requirements: 12.5
 */
export function FormLoadingAnnouncer({
  isLoading,
  formName,
  operation = 'submitting',
  className,
}: {
  isLoading: boolean;
  formName?: string;
  operation?: 'submitting' | 'saving' | 'updating' | 'deleting';
  className?: string;
}) {
  const getLoadingMessage = () => {
    const action = {
      submitting: 'Submitting',
      saving: 'Saving',
      updating: 'Updating',
      deleting: 'Deleting',
    }[operation];

    return formName ? `${action} ${formName}` : `${action} form`;
  };

  const getCompletedMessage = () => {
    const action = {
      submitting: 'Submitted',
      saving: 'Saved',
      updating: 'Updated',
      deleting: 'Deleted',
    }[operation];

    return formName ? `${action} ${formName}` : `${action} form`;
  };

  return (
    <LoadingAnnouncement
      isLoading={isLoading}
      loadingMessage={getLoadingMessage()}
      completedMessage={getCompletedMessage()}
      className={className}
    />
  );
}
