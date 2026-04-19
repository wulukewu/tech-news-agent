/**
 * FeedSearch Component
 *
 * Provides search functionality across all available feeds
 *
 * Validates: Requirements 4.10
 * - THE Feed_Management_Dashboard SHALL provide search functionality across all available feeds
 */

import { useState, useMemo, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import type { Feed } from '@/types/feed';
import { useI18n } from '@/contexts/I18nContext';

export interface FeedSearchProps {
  feeds: Feed[];
  onFilteredFeedsChange: (filteredFeeds: Feed[]) => void;
  className?: string;
}

export function FeedSearch({ feeds, onFilteredFeedsChange, className = '' }: FeedSearchProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const callbackRef = useRef(onFilteredFeedsChange);
  const { t } = useI18n();

  // Keep callback ref up to date
  useEffect(() => {
    callbackRef.current = onFilteredFeedsChange;
  }, [onFilteredFeedsChange]);

  const filteredFeeds = useMemo(() => {
    if (!searchQuery.trim()) {
      return feeds;
    }

    const query = searchQuery.toLowerCase();
    return feeds.filter(
      (feed) =>
        feed.name.toLowerCase().includes(query) ||
        feed.category.toLowerCase().includes(query) ||
        feed.url.toLowerCase().includes(query) ||
        feed.description?.toLowerCase().includes(query) ||
        feed.tags?.some((tag) => tag.toLowerCase().includes(query))
    );
  }, [feeds, searchQuery]);

  // Notify parent of filtered feeds whenever they change
  useEffect(() => {
    callbackRef.current(filteredFeeds);
  }, [filteredFeeds]);

  const handleClear = () => {
    setSearchQuery('');
  };

  return (
    <div className={`relative ${className}`}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
      <Input
        type="text"
        placeholder={t('forms.placeholders.search-feed')}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="pl-9 pr-9"
      />
      {searchQuery && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClear}
          className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
        >
          <X className="w-4 h-4" />
        </Button>
      )}
      {searchQuery && (
        <div className="absolute left-0 right-0 top-full mt-1 text-xs text-muted-foreground">
          {t('forms.messages.search-results', { count: filteredFeeds.length })}
        </div>
      )}
    </div>
  );
}
