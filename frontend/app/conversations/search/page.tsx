'use client';
import { logger } from '@/lib/utils/logger';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { formatDistanceToNow } from 'date-fns';
import {
  Search,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Globe,
  Hash,
  Clock,
  MessageSquare,
  SlidersHorizontal,
  X,
  ChevronDown,
  ChevronUp,
  Star,
} from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { searchConversations, type ConversationSummary } from '@/lib/api/conversations';
import { useI18n } from '@/contexts/I18nContext';

// ─── Types ────────────────────────────────────────────────────────────────────

type PlatformFilter = 'all' | 'web' | 'discord';

// ─── Highlight helper ─────────────────────────────────────────────────────────

function HighlightedText({ text, query }: { text: string; query: string }) {
  if (!query.trim()) return <span>{text}</span>;

  const terms = query
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));

  if (terms.length === 0) return <span>{text}</span>;

  const pattern = new RegExp(`(${terms.join('|')})`, 'gi');
  const parts = text.split(pattern);

  return (
    <span>
      {parts.map((part, i) =>
        pattern.test(part) ? (
          <mark key={i} className="bg-yellow-200 dark:bg-yellow-800/60 rounded-sm px-0.5">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
}

// ─── Search Result Card ───────────────────────────────────────────────────────

function SearchResultCard({
  conversation,
  query,
}: {
  conversation: ConversationSummary;
  query: string;
}) {
  const router = useRouter();
  const { t } = useI18n();

  let timeDisplay = '';
  try {
    const date = new Date(conversation.last_message_at);
    if (!isNaN(date.getTime())) {
      timeDisplay = formatDistanceToNow(date, { addSuffix: true });
    }
  } catch {
    timeDisplay = '';
  }

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => router.push(`/conversations/${conversation.id}`)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          router.push(`/conversations/${conversation.id}`);
        }
      }}
      aria-label={t('chat.search-open-aria', { title: conversation.title })}
      className={cn(
        'group flex flex-col gap-2 rounded-lg border bg-card p-4',
        'cursor-pointer transition-all duration-200',
        'hover:shadow-md hover:border-primary/40',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'
      )}
    >
      {/* Title row */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="flex-1 text-sm font-semibold leading-snug group-hover:text-primary transition-colors line-clamp-2">
          <HighlightedText text={conversation.title} query={query} />
        </h3>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {conversation.is_favorite && (
            <Star
              className="h-3.5 w-3.5 text-yellow-500 fill-current"
              aria-label={t('chat.search-result-favorited-aria')}
            />
          )}
          {conversation.platform === 'discord' ? (
            <Badge
              variant="secondary"
              className="text-xs bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 border-0 flex items-center gap-1"
            >
              <Hash className="h-3 w-3" aria-hidden="true" />
              Discord
            </Badge>
          ) : (
            <Badge
              variant="secondary"
              className="text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-0 flex items-center gap-1"
            >
              <Globe className="h-3 w-3" aria-hidden="true" />
              Web
            </Badge>
          )}
        </div>
      </div>

      {/* Summary snippet */}
      {conversation.summary && (
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
          <HighlightedText text={conversation.summary} query={query} />
        </p>
      )}

      {/* Tags */}
      {conversation.tags && conversation.tags.length > 0 && (
        <div className="flex flex-wrap gap-1" aria-label={t('chat.search-result-tags-aria')}>
          {conversation.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-muted text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground mt-auto">
        <span className="flex items-center gap-1">
          <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
          {conversation.message_count}
        </span>
        {timeDisplay && (
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" aria-hidden="true" />
            {timeDisplay}
          </span>
        )}
      </div>
    </article>
  );
}

// ─── Advanced Filters Panel ───────────────────────────────────────────────────

interface FiltersState {
  platform: PlatformFilter;
  is_favorite: boolean | undefined;
  is_archived: boolean | undefined;
}

function AdvancedFilters({
  filters,
  onChange,
  onReset,
}: {
  filters: FiltersState;
  onChange: (f: Partial<FiltersState>) => void;
  onReset: () => void;
}) {
  const { t } = useI18n();
  const hasActiveFilters =
    filters.platform !== 'all' ||
    filters.is_favorite !== undefined ||
    filters.is_archived !== undefined;

  return (
    <div className="rounded-lg border bg-muted/30 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">{t('chat.search-advanced-title')}</h3>
        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer flex items-center gap-1"
            aria-label={t('chat.search-reset-aria')}
          >
            <X className="h-3 w-3" aria-hidden="true" />
            {t('chat.search-reset-label')}
          </button>
        )}
      </div>

      {/* Platform */}
      <div>
        <label className="text-xs text-muted-foreground mb-2 block">
          {t('chat.search-platform-label')}
        </label>
        <div role="group" aria-label={t('chat.search-platform-aria')} className="flex gap-2">
          {(['all', 'web', 'discord'] as PlatformFilter[]).map((p) => (
            <button
              key={p}
              onClick={() => onChange({ platform: p })}
              aria-pressed={filters.platform === p}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
                filters.platform === p
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
              )}
            >
              {p === 'all' ? t('chat.search-platform-all') : p === 'web' ? 'Web' : 'Discord'}
            </button>
          ))}
        </div>
      </div>

      {/* Status */}
      <div>
        <label className="text-xs text-muted-foreground mb-2 block">
          {t('chat.search-status-label')}
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() =>
              onChange({ is_favorite: filters.is_favorite === true ? undefined : true })
            }
            aria-pressed={filters.is_favorite === true}
            className={cn(
              'px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer flex items-center gap-1',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
              filters.is_favorite === true
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'
                : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
            )}
          >
            <Star className="h-3 w-3" aria-hidden="true" />
            {t('chat.search-status-favorite')}
          </button>
          <button
            onClick={() =>
              onChange({ is_archived: filters.is_archived === true ? undefined : true })
            }
            aria-pressed={filters.is_archived === true}
            className={cn(
              'px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
              filters.is_archived === true
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
            )}
          >
            {t('chat.search-status-archived')}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page Content ────────────────────────────────────────────────────────

const DEFAULT_FILTERS: FiltersState = {
  platform: 'all',
  is_favorite: undefined,
  is_archived: undefined,
};

function ConversationSearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t } = useI18n();

  const initialQuery = searchParams?.get('q') ?? '';

  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);
  const [results, setResults] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FiltersState>(DEFAULT_FILTERS);

  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Debounce query
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  // Run search when debounced query or filters change
  const runSearch = useCallback(async () => {
    if (!debouncedQuery.trim()) {
      setResults([]);
      setHasSearched(false);
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const apiFilters: Parameters<typeof searchConversations>[1] = {
        limit: 30,
      };
      if (filters.platform !== 'all') apiFilters.platform = filters.platform;
      if (filters.is_favorite !== undefined) apiFilters.is_favorite = filters.is_favorite;
      if (filters.is_archived !== undefined) apiFilters.is_archived = filters.is_archived;

      const response = await searchConversations(debouncedQuery, apiFilters);
      setResults(response.items);
    } catch (err) {
      console.error('Search failed:', err);
      setError(t('chat.error-load-failed'));
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, filters]);

  useEffect(() => {
    runSearch();
  }, [runSearch]);

  const handleFilterChange = (partial: Partial<FiltersState>) => {
    setFilters((prev) => ({ ...prev, ...partial }));
  };

  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS);
  };

  const handleClearSearch = () => {
    setQuery('');
    setDebouncedQuery('');
    setResults([]);
    setHasSearched(false);
    inputRef.current?.focus();
  };

  const hasActiveFilters =
    filters.platform !== 'all' ||
    filters.is_favorite !== undefined ||
    filters.is_archived !== undefined;

  return (
    <div className="container mx-auto py-8 px-4 max-w-3xl">
      {/* Header */}
      <header className="flex items-center gap-3 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/conversations')}
          className="cursor-pointer"
          aria-label={t('chat.search-back-aria')}
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        </Button>
        <h1 className="text-2xl font-bold">{t('chat.search-page-title')}</h1>
      </header>

      {/* Search input */}
      <div className="relative mb-3">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
          aria-hidden="true"
        />
        <label htmlFor="search-input" className="sr-only">
          {t('chat.search-label')}
        </label>
        <Input
          id="search-input"
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('chat.search-input-placeholder')}
          className="pl-9 pr-9"
          aria-label={t('chat.search-input-aria')}
        />
        {query && (
          <button
            onClick={handleClearSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            aria-label={t('chat.search-clear-aria')}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Filter toggle */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setShowFilters((v) => !v)}
          className={cn(
            'flex items-center gap-1.5 text-sm transition-colors cursor-pointer',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 rounded',
            hasActiveFilters
              ? 'text-primary font-medium'
              : 'text-muted-foreground hover:text-foreground'
          )}
          aria-expanded={showFilters}
          aria-controls="advanced-filters"
        >
          <SlidersHorizontal className="h-3.5 w-3.5" aria-hidden="true" />
          {t('chat.search-advanced-toggle')}
          {hasActiveFilters && (
            <span className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-primary text-primary-foreground text-xs">
              !
            </span>
          )}
          {showFilters ? (
            <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
          )}
        </button>

        {hasSearched && !loading && (
          <p className="text-xs text-muted-foreground" aria-live="polite">
            {results.length > 0
              ? t('chat.search-results-count', { count: results.length })
              : t('chat.search-no-results-text')}
          </p>
        )}
      </div>

      {/* Advanced filters panel */}
      {showFilters && (
        <div id="advanced-filters" className="mb-4">
          <AdvancedFilters
            filters={filters}
            onChange={handleFilterChange}
            onReset={handleResetFilters}
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 mb-4 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div
          role="status"
          aria-label={t('chat.search-loading-aria')}
          className="flex justify-center py-12"
        >
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden="true" />
          <span className="sr-only">{t('chat.search-loading-sr')}</span>
        </div>
      ) : !hasSearched ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Search className="h-10 w-10 text-muted-foreground/40 mb-4" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">{t('chat.search-empty-hint')}</p>
          <p className="text-xs text-muted-foreground mt-1">{t('chat.search-empty-hint-sub')}</p>
        </div>
      ) : results.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Search className="h-10 w-10 text-muted-foreground/40 mb-4" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">
            {t('chat.search-no-match', { query: debouncedQuery })}
          </p>
          <p className="text-xs text-muted-foreground mt-1">{t('chat.search-no-match-sub')}</p>
        </div>
      ) : (
        <div role="list" aria-label={t('chat.search-results-aria')} className="space-y-3">
          {results.map((conv) => (
            <div key={conv.id} role="listitem">
              <SearchResultCard conversation={conv} query={debouncedQuery} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Page Export ──────────────────────────────────────────────────────────────

export default function ConversationSearchPage() {
  return (
    <ProtectedRoute>
      <ConversationSearchContent />
    </ProtectedRoute>
  );
}
