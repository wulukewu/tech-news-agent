'use client';

import { useState } from 'react';
import { Star, Archive, Trash2, X, Loader2, CheckSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  updateConversation,
  deleteConversation,
  type ConversationSummary,
} from '@/lib/api/conversations';

// ─── Props ────────────────────────────────────────────────────────────────────

interface BulkActionsProps {
  /** IDs of selected conversations */
  selectedIds: string[];
  /** All conversations (used to determine current state for toggles) */
  conversations: ConversationSummary[];
  /** Called when the selection should be cleared */
  onClearSelection: () => void;
  /** Called after a bulk operation completes with the updated conversations */
  onBulkUpdate: (updated: ConversationSummary[]) => void;
  /** Called after bulk delete with the deleted IDs */
  onBulkDelete: (deletedIds: string[]) => void;
  /** Optional CSS class for the wrapper */
  className?: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Bulk action toolbar shown when one or more conversations are selected.
 *
 * Provides: favorite all, archive all, delete all, and clear selection.
 *
 * Validates Requirements 3.4, 3.5
 */
export function BulkActions({
  selectedIds,
  conversations,
  onClearSelection,
  onBulkUpdate,
  onBulkDelete,
  className,
}: BulkActionsProps) {
  const [loading, setLoading] = useState<'favorite' | 'archive' | 'delete' | null>(null);

  if (selectedIds.length === 0) return null;

  const selectedConversations = conversations.filter((c) => selectedIds.includes(c.id));

  // Determine toggle direction: if all selected are already favorited, unfavorite; otherwise favorite
  const allFavorited = selectedConversations.every((c) => c.is_favorite);
  const allArchived = selectedConversations.every((c) => c.is_archived);

  const handleBulkFavorite = async () => {
    if (loading) return;
    setLoading('favorite');
    const newValue = !allFavorited;
    try {
      const results = await Promise.allSettled(
        selectedIds.map((id) => updateConversation(id, { is_favorite: newValue }))
      );
      const updated = results
        .filter((r): r is PromiseFulfilledResult<ConversationSummary> => r.status === 'fulfilled')
        .map((r) => r.value);
      onBulkUpdate(updated);
    } catch (err) {
      console.error('Bulk favorite failed:', err);
    } finally {
      setLoading(null);
    }
  };

  const handleBulkArchive = async () => {
    if (loading) return;
    setLoading('archive');
    const newValue = !allArchived;
    try {
      const results = await Promise.allSettled(
        selectedIds.map((id) => updateConversation(id, { is_archived: newValue }))
      );
      const updated = results
        .filter((r): r is PromiseFulfilledResult<ConversationSummary> => r.status === 'fulfilled')
        .map((r) => r.value);
      onBulkUpdate(updated);
    } catch (err) {
      console.error('Bulk archive failed:', err);
    } finally {
      setLoading(null);
    }
  };

  const handleBulkDelete = async () => {
    if (loading) return;
    const confirmed = window.confirm(
      `確定要刪除選取的 ${selectedIds.length} 個對話嗎？此操作無法復原。`
    );
    if (!confirmed) return;

    setLoading('delete');
    try {
      const results = await Promise.allSettled(selectedIds.map((id) => deleteConversation(id)));
      const deletedIds = selectedIds.filter((_, i) => results[i].status === 'fulfilled');
      onBulkDelete(deletedIds);
    } catch (err) {
      console.error('Bulk delete failed:', err);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div
      role="toolbar"
      aria-label="批量操作"
      className={cn(
        'flex items-center gap-2 px-4 py-2.5 rounded-lg border bg-primary/5 border-primary/20',
        className
      )}
    >
      {/* Selection count */}
      <div className="flex items-center gap-1.5 text-sm font-medium mr-2">
        <CheckSquare className="h-4 w-4 text-primary" aria-hidden="true" />
        <span>已選取 {selectedIds.length} 個</span>
      </div>

      {/* Favorite toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleBulkFavorite}
        disabled={loading !== null}
        aria-label={allFavorited ? '取消收藏選取的對話' : '收藏選取的對話'}
        className={cn(
          'cursor-pointer gap-1.5',
          allFavorited ? 'text-yellow-500' : 'text-muted-foreground hover:text-yellow-500'
        )}
      >
        {loading === 'favorite' ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : (
          <Star
            className="h-3.5 w-3.5"
            fill={allFavorited ? 'currentColor' : 'none'}
            aria-hidden="true"
          />
        )}
        <span className="text-xs">{allFavorited ? '取消收藏' : '收藏'}</span>
      </Button>

      {/* Archive toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleBulkArchive}
        disabled={loading !== null}
        aria-label={allArchived ? '取消歸檔選取的對話' : '歸檔選取的對話'}
        className="cursor-pointer gap-1.5 text-muted-foreground hover:text-foreground"
      >
        {loading === 'archive' ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : (
          <Archive className="h-3.5 w-3.5" aria-hidden="true" />
        )}
        <span className="text-xs">{allArchived ? '取消歸檔' : '歸檔'}</span>
      </Button>

      {/* Delete */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleBulkDelete}
        disabled={loading !== null}
        aria-label="刪除選取的對話"
        className="cursor-pointer gap-1.5 text-muted-foreground hover:text-destructive"
      >
        {loading === 'delete' ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : (
          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
        )}
        <span className="text-xs">刪除</span>
      </Button>

      {/* Clear selection */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onClearSelection}
        disabled={loading !== null}
        aria-label="取消選取"
        className="cursor-pointer ml-auto text-muted-foreground hover:text-foreground h-7 w-7 p-0"
      >
        <X className="h-3.5 w-3.5" aria-hidden="true" />
      </Button>
    </div>
  );
}
