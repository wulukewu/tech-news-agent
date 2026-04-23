'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { formatDistanceToNow } from 'date-fns';
import { Star, Archive, ArchiveRestore, MessageSquare, Globe, Hash, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ConversationSummary } from '@/lib/api/conversations';
import { updateConversation } from '@/lib/api/conversations';

// ─── Props ────────────────────────────────────────────────────────────────────

interface ConversationCardProps {
  conversation: ConversationSummary;
  onUpdate?: (updated: ConversationSummary) => void;
}

// ─── Platform Badge ───────────────────────────────────────────────────────────

function PlatformBadge({ platform }: { platform: 'web' | 'discord' }) {
  if (platform === 'discord') {
    return (
      <Badge
        variant="secondary"
        className="flex items-center gap-1 text-xs bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 border-0"
      >
        <Hash className="h-3 w-3" aria-hidden="true" />
        Discord
      </Badge>
    );
  }

  return (
    <Badge
      variant="secondary"
      className="flex items-center gap-1 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-0"
    >
      <Globe className="h-3 w-3" aria-hidden="true" />
      Web
    </Badge>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * ConversationCard displays a single conversation summary with quick actions.
 * Validates Requirements 3.1, 3.2
 */
export function ConversationCard({ conversation, onUpdate }: ConversationCardProps) {
  const router = useRouter();
  const [loadingAction, setLoadingAction] = useState<'favorite' | 'archive' | null>(null);

  // Format last message time
  let timeDisplay = '';
  try {
    const date = new Date(conversation.last_message_at);
    if (!isNaN(date.getTime())) {
      timeDisplay = formatDistanceToNow(date, { addSuffix: true });
    }
  } catch {
    timeDisplay = '';
  }

  const handleCardClick = () => {
    router.push(`/app/chat/${conversation.id}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCardClick();
    }
  };

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loadingAction) return;
    setLoadingAction('favorite');
    try {
      const updated = await updateConversation(conversation.id, {
        is_favorite: !conversation.is_favorite,
      });
      onUpdate?.(updated);
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleToggleArchive = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loadingAction) return;
    setLoadingAction('archive');
    try {
      const updated = await updateConversation(conversation.id, {
        is_archived: !conversation.is_archived,
      });
      onUpdate?.(updated);
    } catch (err) {
      console.error('Failed to toggle archive:', err);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      aria-label={`Open conversation: ${conversation.title}`}
      className={cn(
        'group relative flex flex-col gap-3 rounded-lg border bg-card p-4',
        'cursor-pointer transition-all duration-200',
        'hover:shadow-md hover:border-primary/40',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        conversation.is_archived && 'opacity-60'
      )}
    >
      {/* Header row: title + platform badge */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="flex-1 text-sm font-semibold leading-snug text-foreground line-clamp-2 group-hover:text-primary transition-colors">
          {conversation.title}
        </h3>
        <PlatformBadge platform={conversation.platform} />
      </div>

      {/* Summary */}
      {conversation.summary && (
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
          {conversation.summary}
        </p>
      )}

      {/* Tags */}
      {conversation.tags && conversation.tags.length > 0 && (
        <div className="flex flex-wrap gap-1" aria-label="Tags">
          {conversation.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-muted text-muted-foreground"
            >
              {tag}
            </span>
          ))}
          {conversation.tags.length > 4 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-muted text-muted-foreground">
              +{conversation.tags.length - 4}
            </span>
          )}
        </div>
      )}

      {/* Footer row: message count + time + actions */}
      <div className="flex items-center justify-between gap-2 mt-auto">
        {/* Left: message count + time */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{conversation.message_count}</span>
          </span>
          {timeDisplay && <span>{timeDisplay}</span>}
        </div>

        {/* Right: quick action buttons */}
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {/* Favorite toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggleFavorite}
            disabled={loadingAction !== null}
            aria-label={conversation.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
            aria-pressed={conversation.is_favorite}
            className={cn(
              'h-7 w-7 p-0 cursor-pointer',
              conversation.is_favorite
                ? 'text-yellow-500 hover:text-yellow-600'
                : 'text-muted-foreground hover:text-yellow-500'
            )}
          >
            {loadingAction === 'favorite' ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Star
                className="h-3.5 w-3.5"
                fill={conversation.is_favorite ? 'currentColor' : 'none'}
                aria-hidden="true"
              />
            )}
          </Button>

          {/* Archive toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggleArchive}
            disabled={loadingAction !== null}
            aria-label={
              conversation.is_archived ? 'Unarchive conversation' : 'Archive conversation'
            }
            aria-pressed={conversation.is_archived}
            className="h-7 w-7 p-0 cursor-pointer text-muted-foreground hover:text-foreground"
          >
            {loadingAction === 'archive' ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : conversation.is_archived ? (
              <ArchiveRestore className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <Archive className="h-3.5 w-3.5" aria-hidden="true" />
            )}
          </Button>
        </div>
      </div>
    </article>
  );
}
