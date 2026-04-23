'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { ConversationCard } from '@/components/chat/ConversationCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import {
  getConversations,
  createConversation,
  type ConversationSummary,
} from '@/lib/api/conversations';
import { MessageSquare, Plus, Search, Loader2, AlertCircle, Inbox } from 'lucide-react';

// ─── Filter Tabs ──────────────────────────────────────────────────────────────

type FilterTab = 'all' | 'favorites' | 'archived';

const FILTER_TABS: { id: FilterTab; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'favorites', label: 'Favorites' },
  { id: 'archived', label: 'Archived' },
];

const PAGE_SIZE = 20;

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
  const message = searchQuery
    ? `No conversations match "${searchQuery}"`
    : tab === 'favorites'
      ? 'No favorite conversations yet'
      : tab === 'archived'
        ? 'No archived conversations'
        : 'No conversations yet';

  const description = searchQuery
    ? 'Try a different search term.'
    : tab === 'all'
      ? 'Start a new conversation to get going.'
      : null;

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
          New Conversation
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

  const sentinelRef = useRef<HTMLDivElement>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce search input
  useEffect(() => {
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [searchQuery]);

  // Build filters from current state
  const buildFilters = useCallback(
    (currentOffset: number) => {
      const filters: Parameters<typeof getConversations>[0] = {
        limit: PAGE_SIZE,
        offset: currentOffset,
      };
      if (debouncedSearch) filters.search = debouncedSearch;
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
    [debouncedSearch, activeTab]
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
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError('Failed to load conversations. Please try again.');
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
    } catch (err) {
      console.error('Failed to load more conversations:', err);
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

  // Handle card update (favorite/archive toggled)
  const handleConversationUpdate = useCallback((updated: ConversationSummary) => {
    setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  }, []);

  // Create new conversation
  const handleNewConversation = async () => {
    if (creating) return;
    setCreating(true);
    try {
      const newConv = await createConversation({ platform: 'web' });
      router.push(`/chat/conversations/${newConv.id}`);
    } catch (err) {
      console.error('Failed to create conversation:', err);
      setError('Failed to create conversation. Please try again.');
      setCreating(false);
    }
  };

  // Tab change resets search
  const handleTabChange = (tab: FilterTab) => {
    setActiveTab(tab);
    setSearchQuery('');
    setDebouncedSearch('');
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center">
            <MessageSquare className="h-5 w-5 text-primary" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-bold leading-tight">Conversations</h1>
            {!loading && (
              <p className="text-xs text-muted-foreground">
                {totalCount} {totalCount === 1 ? 'conversation' : 'conversations'}
              </p>
            )}
          </div>
        </div>

        <Button
          onClick={handleNewConversation}
          disabled={creating}
          aria-label="Start a new conversation"
          className="cursor-pointer"
        >
          {creating ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" aria-hidden="true" />
          ) : (
            <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          )}
          New Conversation
        </Button>
      </div>

      {/* Search bar */}
      <div className="relative mb-4">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
          aria-hidden="true"
        />
        <Input
          type="search"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label="Search conversations"
          className="pl-9"
        />
      </div>

      {/* Filter tabs */}
      <div role="tablist" aria-label="Conversation filters" className="flex gap-1 mb-6 border-b">
        {FILTER_TABS.map((tab) => (
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
            {tab.label}
          </button>
        ))}
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
            aria-label="Dismiss error"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div role="status" aria-label="Loading conversations" className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <ConversationCardSkeleton key={i} />
          ))}
          <span className="sr-only">Loading conversations...</span>
        </div>
      ) : conversations.length === 0 ? (
        <EmptyState
          tab={activeTab}
          searchQuery={debouncedSearch}
          onNewConversation={handleNewConversation}
        />
      ) : (
        <>
          <div role="list" aria-label="Conversation list" className="grid gap-3 sm:grid-cols-2">
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
              <span className="sr-only">Loading more conversations...</span>
            </div>
          )}

          {/* End of list */}
          {!hasNextPage && conversations.length > 0 && (
            <p role="status" className="text-center text-xs text-muted-foreground py-6">
              Showing all {conversations.length} of {totalCount}{' '}
              {totalCount === 1 ? 'conversation' : 'conversations'}
            </p>
          )}
        </>
      )}
    </div>
  );
}

// ─── Page Export ──────────────────────────────────────────────────────────────

export default function ConversationsPage() {
  return (
    <ProtectedRoute>
      <ConversationsPageContent />
    </ProtectedRoute>
  );
}
