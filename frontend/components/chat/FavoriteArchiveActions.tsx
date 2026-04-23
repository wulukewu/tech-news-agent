'use client';

import { useState } from 'react';
import { Star, Archive, ArchiveRestore, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// ─── Props ────────────────────────────────────────────────────────────────────

interface FavoriteArchiveActionsProps {
  /** Whether the conversation is currently favorited */
  isFavorite: boolean;
  /** Whether the conversation is currently archived */
  isArchived: boolean;
  /** Called when the user toggles the favorite state */
  onToggleFavorite: () => Promise<void>;
  /** Called when the user toggles the archive state */
  onToggleArchive: () => Promise<void>;
  /** Optional CSS class for the wrapper */
  className?: string;
  /** Render as icon-only buttons (no text labels) */
  iconOnly?: boolean;
  /** Whether the actions are disabled */
  disabled?: boolean;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Favorite and archive toggle buttons for a conversation.
 *
 * Validates Requirements 3.2, 3.4
 */
export function FavoriteArchiveActions({
  isFavorite,
  isArchived,
  onToggleFavorite,
  onToggleArchive,
  className,
  iconOnly = false,
  disabled = false,
}: FavoriteArchiveActionsProps) {
  const [savingFavorite, setSavingFavorite] = useState(false);
  const [savingArchive, setSavingArchive] = useState(false);

  const handleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (savingFavorite || disabled) return;
    setSavingFavorite(true);
    try {
      await onToggleFavorite();
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    } finally {
      setSavingFavorite(false);
    }
  };

  const handleArchive = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (savingArchive || disabled) return;
    setSavingArchive(true);
    try {
      await onToggleArchive();
    } catch (err) {
      console.error('Failed to toggle archive:', err);
    } finally {
      setSavingArchive(false);
    }
  };

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {/* Favorite */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleFavorite}
        disabled={savingFavorite || disabled}
        aria-label={isFavorite ? '取消收藏' : '加入收藏'}
        aria-pressed={isFavorite}
        className={cn(
          'cursor-pointer',
          iconOnly ? 'h-7 w-7 p-0' : 'h-8 gap-1.5 px-2',
          isFavorite
            ? 'text-yellow-500 hover:text-yellow-600'
            : 'text-muted-foreground hover:text-yellow-500'
        )}
      >
        {savingFavorite ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : (
          <Star
            className="h-3.5 w-3.5"
            fill={isFavorite ? 'currentColor' : 'none'}
            aria-hidden="true"
          />
        )}
        {!iconOnly && <span className="text-xs">{isFavorite ? '已收藏' : '收藏'}</span>}
      </Button>

      {/* Archive */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleArchive}
        disabled={savingArchive || disabled}
        aria-label={isArchived ? '取消歸檔' : '歸檔對話'}
        aria-pressed={isArchived}
        className={cn(
          'cursor-pointer text-muted-foreground hover:text-foreground',
          iconOnly ? 'h-7 w-7 p-0' : 'h-8 gap-1.5 px-2'
        )}
      >
        {savingArchive ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : isArchived ? (
          <ArchiveRestore className="h-3.5 w-3.5" aria-hidden="true" />
        ) : (
          <Archive className="h-3.5 w-3.5" aria-hidden="true" />
        )}
        {!iconOnly && <span className="text-xs">{isArchived ? '取消歸檔' : '歸檔'}</span>}
      </Button>
    </div>
  );
}
