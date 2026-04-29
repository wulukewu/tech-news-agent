'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { getConversations, type ConversationSummary } from '@/lib/api/conversations';
import { formatDistanceToNow } from 'date-fns';
import { Plus, Search, MessageSquare, Loader2, Star } from 'lucide-react';

export function HistorySidebar({
  activeId,
  onNewChat,
  onSelect,
  refreshKey,
}: {
  activeId: string | null;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  refreshKey: number;
}) {
  const router = useRouter();
  const { t } = useI18n();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getConversations({
        limit: 40,
        offset: 0,
        is_archived: false,
        search: debouncedSearch || undefined,
      });
      setConversations(result.items);
    } catch {
      /* non-critical */
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <aside
      className="flex flex-col h-full border-r bg-muted/20 w-64 flex-shrink-0"
      aria-label={t('chat.history-sidebar-label')}
    >
      <div className="flex-shrink-0 px-3 py-3 border-b">
        <Button
          onClick={onNewChat}
          size="sm"
          className="w-full cursor-pointer justify-start gap-2"
          aria-label={t('chat.new-conversation-aria')}
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          {t('chat.new-conversation')}
        </Button>
      </div>
      <div className="flex-shrink-0 px-3 py-2 border-b">
        <div className="relative">
          <Search
            className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none"
            aria-hidden="true"
          />
          <label htmlFor="sidebar-search" className="sr-only">
            {t('chat.search-conversations')}
          </label>
          <Input
            id="sidebar-search"
            type="search"
            placeholder={t('chat.search-placeholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-xs"
          />
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto py-1" aria-label={t('chat.history-nav-label')}>
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" aria-hidden="true" />
            <span className="sr-only">{t('chat.loading')}</span>
          </div>
        )}
        {!loading && conversations.length === 0 && (
          <p className="px-3 py-8 text-center text-xs text-muted-foreground">
            {debouncedSearch
              ? t('chat.no-results', { query: debouncedSearch })
              : t('chat.no-conversations')}
          </p>
        )}
        {!loading && conversations.length > 0 && (
          <ul role="list">
            {conversations.map((conv) => {
              const isActive = conv.id === activeId;
              let timeDisplay = '';
              try {
                const d = new Date(conv.last_message_at);
                if (!isNaN(d.getTime())) timeDisplay = formatDistanceToNow(d, { addSuffix: true });
              } catch {
                /* ignore */
              }
              return (
                <li key={conv.id} role="listitem">
                  <button
                    onClick={() => onSelect(conv.id)}
                    className={cn(
                      'w-full text-left px-3 py-2.5 transition-colors cursor-pointer',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
                      isActive ? 'bg-primary/10 text-primary' : 'hover:bg-muted/60 text-foreground'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                    aria-label={t('chat.open-conversation-aria', { title: conv.title })}
                  >
                    <div className="flex items-start gap-2">
                      <MessageSquare
                        className={cn(
                          'h-3.5 w-3.5 flex-shrink-0 mt-0.5',
                          isActive ? 'text-primary' : 'text-muted-foreground'
                        )}
                        aria-hidden="true"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium leading-snug line-clamp-2 break-words">
                          {conv.title}
                        </p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          {timeDisplay && (
                            <span className="text-[10px] text-muted-foreground">{timeDisplay}</span>
                          )}
                          {conv.is_favorite && (
                            <Star
                              className="h-2.5 w-2.5 text-yellow-500 fill-yellow-500"
                              aria-label={t('chat.favorited-aria')}
                            />
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </nav>
      <div className="flex-shrink-0 px-3 py-2 border-t">
        <button
          onClick={() => router.push('/app/chat/conversations')}
          className="w-full text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer text-center py-1"
          aria-label={t('chat.view-all-aria')}
        >
          {t('chat.view-all-conversations')}
        </button>
      </div>
    </aside>
  );
}
