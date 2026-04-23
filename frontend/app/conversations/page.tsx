'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useI18n } from '@/contexts/I18nContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { ConversationCard } from '@/components/chat/ConversationCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { getConversations, type ConversationSummary } from '@/lib/api/conversations';
import {
  MessageSquare,
  Plus,
  Search,
  Loader2,
  AlertCircle,
  Inbox,
  Globe,
  Hash,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

type FilterTab = 'all' | 'favorites' | 'archived';
type PlatformFilter = 'all' | 'web' | 'discord';

// ─── Constants ────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20;

const FILTER_TABS: { id: FilterTab }[] = [{ id: 'all' }, { id: 'favorites' }, { id: 'archived' }];

const PLATFORM_FILTERS: { id: PlatformFilter }[] = [
  { id: 'all' },
  { id: 'web' },
  { id: 'discord' },
];

// ─── Empty State ──────────────────────────────────────────────────────────────

function EmptyState({
  tab,
  searchQuery,
  onNewConversation,
}: {
  tab: FilterTab;
  searchQuery: string;
  onNewConversation: () => void;
}) {
  const { t } = useI18n();

  let message: string;
  if (searchQuery) {
    message = t('chat.empty-no-match', { query: searchQuery });
  } else if (tab === 'favorites') {
    message = t('chat.empty-no-favorites');
  } else if (tab === 'archived') {
    message = t('chat.empty-no-archived');
  } else {
    message = t('chat.empty-no-conversations');
  }

  let description: string | null = null;
  if (searchQuery) {
    description = t('chat.empty-try-different');
  } else if (tab === 'all') {
    description = t('chat.empty-start-first');
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="h-14 w-14 rounded-full bg-muted flex items-center justify-center mb-4">
        <Inbox className="h-7 w-7 text-muted-foreground" aria-hidden="true" />
      </div>
      <p className="text-base font-medium text-foreground mb-1">{message}</p>
      {description && <p className="text-sm text-muted-foreground mb-6">{description}</p>}
      {tab === 'all' && !searchQuery && (
        <Button onClick={onNewConversation} className="cursor-pointer">
          <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          {t('chat.new-conversation')}
        </Button>
      )}
    </div>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function ConversationCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-3 animate-pulse">
      <div className="flex items-start justify-between gap-2">
        <div className="h-4 bg-muted rounded w-3/4" />
        <div className="h-5 bg-muted rounded w-14" />
      </div>
      <div className="h-3 bg-muted rounded w-full" />
      <div className="h-3 bg-muted rounded w-2/3" />
      <div className="flex items-center justify-between">
        <div className="h-3 bg-muted rounded w-24" />
        <div className="flex gap-1">
          <div className="h-7 w-7 bg-muted rounded" />
          <div className="h-7 w-7 bg-muted rounded" />
        </div>
      </div>
    </div>
  );
}

// ─── Main Page Content ────────────────────────────────────────────────────────

function ConversationsPageContent() {
  const router = useRouter();
  const { t } = useI18n();

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [offset, setOffset] = useState(0);

  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [platformFilter, setPlatformFilter] = useState<PlatformFilter>('all');

  const sentinelRef = useRef<HTMLDivElement>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce search input (300ms)
  useEffect(() => {
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [searchQuery]);

  // Build API filters from current UI state
  const buildFilters = useCallback(
    (currentOffset: number) => {
      const filters: Parameters<typeof getConversations>[0] = {
        limit: PAGE_SIZE,
        offset: currentOffset,
      };

      if (debouncedSearch) filters.search = debouncedSearch;

      if (platformFilter !== 'all') {
        filters.platform = platformFilter;
      }

      if (activeTab === 'favorites') {
        filters.is_favorite = true;
        filters.is_archived = false;
      } else if (activeTab === 'archived') {
        filters.is_archived = true;
      } else {
        // 'all' tab: exclude archived by default
        filters.is_archived = false;
      }

      return filters;
    },
    [debouncedSearch, activeTab, platformFilter]
  );

  // Initial / filter-change load
  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    setOffset(0);
    try {
      const result = await getConversations(buildFilters(0));
      setConversations(result.items);
      setHasNextPage(result.has_next);
      setTotalCount(result.total_count);
      setOffset(result.items.length);
    } catch (_err) {
      setError(t('chat.error-load-failed'));
    } finally {
      setLoading(false);
    }
  }, [buildFilters]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Load more (infinite scroll)
  const loadMore = useCallback(async () => {
    if (loadingMore || !hasNextPage) return;
    setLoadingMore(true);
    try {
      const result = await getConversations(buildFilters(offset));
      setConversations((prev) => [...prev, ...result.items]);
      setHasNextPage(result.has_next);
      setTotalCount(result.total_count);
      setOffset((prev) => prev + result.items.length);
    } catch (_err) {
      // non-critical: infinite scroll failure is silent
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, hasNextPage, buildFilters, offset]);

  // Infinite scroll observer
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !loadingMore) {
          loadMore();
        }
      },
      { rootMargin: '200px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, loadingMore, loadMore]);

  // Handle card update (favorite/archive toggled from card)
  const handleConversationUpdate = useCallback((updated: ConversationSummary) => {
    setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  }, []);

  // Create new conversation and navigate to it
  const handleNewConversation = async () => {
    if (creating) return;
    setCreating(true);
    try {
      router.push('/app/chat');
    } catch (_err) {
      setCreating(false);
    }
  };

  // Tab change resets search and platform filter
  const handleTabChange = (tab: FilterTab) => {
    setActiveTab(tab);
    setSearchQuery('');
    setDebouncedSearch('');
  };

  const handlePlatformChange = (platform: PlatformFilter) => {
    setPlatformFilter(platform);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      {/* Page header */}
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div
            className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center"
            aria-hidden="true"
          >
            <MessageSquare className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold leading-tight">{t('chat.conversations-title')}</h1>
            {!loading && (
              <p className="text-xs text-muted-foreground">
                {t('chat.conversations-count', { count: totalCount })}
              </p>
            )}
          </div>
        </div>

        <Button
          onClick={handleNewConversation}
          disabled={creating}
          aria-label={t('chat.new-conversation-btn-aria')}
          className="cursor-pointer"
        >
          {creating ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" aria-hidden="true" />
          ) : (
            <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          )}
          {t('chat.new-conversation')}
        </Button>
      </header>

      {/* Search bar */}
      <div className="relative mb-4">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
          aria-hidden="true"
        />
        <label htmlFor="conversation-search" className="sr-only">
          {t('chat.search-conversations')}
        </label>
        <Input
          id="conversation-search"
          type="search"
          placeholder={t('chat.search-placeholder')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label={t('chat.search-aria')}
          className="pl-9"
        />
      </div>

      {/* Filter tabs */}
      <div
        role="tablist"
        aria-label={t('chat.filter-tabs-aria')}
        className="flex gap-1 mb-3 border-b"
      >
        {FILTER_TABS.map((tab) => {
          const label =
            tab.id === 'all'
              ? t('chat.filter-all')
              : tab.id === 'favorites'
                ? t('chat.filter-favorites')
                : t('chat.filter-archived');
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={cn(
                'px-4 py-2 text-sm font-medium transition-colors cursor-pointer',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                'border-b-2 -mb-px',
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/40'
              )}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Platform filter */}
      <div
        role="group"
        aria-label={t('chat.platform-filter-aria')}
        className="flex items-center gap-2 mb-6"
      >
        <span className="text-xs text-muted-foreground mr-1">{t('chat.platform-label')}</span>
        {PLATFORM_FILTERS.map((pf) => {
          const label =
            pf.id === 'all' ? t('chat.filter-all') : pf.id === 'web' ? 'Web' : 'Discord';
          return (
            <button
              key={pf.id}
              onClick={() => handlePlatformChange(pf.id)}
              aria-pressed={platformFilter === pf.id}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
                platformFilter === pf.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
              )}
            >
              {pf.id === 'web' && <Globe className="h-3 w-3" aria-hidden="true" />}
              {pf.id === 'discord' && <Hash className="h-3 w-3" aria-hidden="true" />}
              {label}
            </button>
          );
        })}
      </div>

      {/* Error banner */}
      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 mb-4 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-xs underline cursor-pointer hover:no-underline"
            aria-label={t('chat.close-error-btn-aria')}
          >
            {t('buttons.close')}
          </button>
        </div>
      )}

      {/* Content area */}
      {loading ? (
        <div
          role="status"
          aria-label={t('chat.loading-conversations-aria')}
          className="grid gap-3 sm:grid-cols-2"
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <ConversationCardSkeleton key={i} />
          ))}
          <span className="sr-only">{t('chat.loading-conversations-aria')}...</span>
        </div>
      ) : conversations.length === 0 ? (
        <EmptyState
          tab={activeTab}
          searchQuery={debouncedSearch}
          onNewConversation={handleNewConversation}
        />
      ) : (
        <>
          <div
            role="list"
            aria-label={t('chat.conversation-list-aria')}
            className="grid gap-3 sm:grid-cols-2"
          >
            {conversations.map((conv) => (
              <div key={conv.id} role="listitem">
                <ConversationCard conversation={conv} onUpdate={handleConversationUpdate} />
              </div>
            ))}
          </div>

          {/* Infinite scroll sentinel */}
          <div ref={sentinelRef} className="h-px" aria-hidden="true" />

          {/* Loading more indicator */}
          {loadingMore && (
            <div role="status" aria-live="polite" className="flex justify-center py-6">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden="true" />
              <span className="sr-only">{t('chat.loading-more-aria')}</span>
            </div>
          )}

          {!hasNextPage && conversations.length > 0 && (
            <p role="status" className="text-center text-xs text-muted-foreground py-6">
              {t('chat.end-of-list', { shown: conversations.length, total: totalCount })}
            </p>
          )}
        </>
      )}
    </div>
  );
}

// ─── Page Export ──────────────────────────────────────────────────────────────

export default function ConversationsHistoryPage() {
  return (
    <ProtectedRoute>
      <ConversationsPageContent />
    </ProtectedRoute>
  );
}
