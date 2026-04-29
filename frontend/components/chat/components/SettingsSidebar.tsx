'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { updateConversation, type ConversationDetail } from '@/lib/api/conversations';
import {
  Settings,
  Tag,
  X,
  Check,
  Pencil,
  Archive,
  ArchiveRestore,
  Download,
  Star,
  Loader2,
} from 'lucide-react';

export function SettingsSidebar({
  conversation,
  onUpdate,
  onExport,
  exporting,
}: {
  conversation: ConversationDetail;
  onUpdate: (updates: Partial<ConversationDetail>) => void;
  onExport: () => void;
  exporting: boolean;
}) {
  const { t } = useI18n();
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState(conversation.title);
  const [savingTitle, setSavingTitle] = useState(false);
  const [newTag, setNewTag] = useState('');
  const [savingFavorite, setSavingFavorite] = useState(false);
  const [savingArchive, setSavingArchive] = useState(false);
  const titleInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setTitleValue(conversation.title);
  }, [conversation.title]);
  useEffect(() => {
    if (editingTitle) {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }
  }, [editingTitle]);

  const handleSaveTitle = async () => {
    const trimmed = titleValue.trim();
    if (!trimmed || trimmed === conversation.title) {
      setEditingTitle(false);
      setTitleValue(conversation.title);
      return;
    }
    setSavingTitle(true);
    try {
      const updated = await updateConversation(conversation.id, { title: trimmed });
      onUpdate({ title: updated.title });
      setEditingTitle(false);
    } catch {
      setTitleValue(conversation.title);
      setEditingTitle(false);
    } finally {
      setSavingTitle(false);
    }
  };

  const handleAddTag = async () => {
    const tag = newTag.trim();
    if (!tag || conversation.tags.includes(tag)) {
      setNewTag('');
      return;
    }
    try {
      const updated = await updateConversation(conversation.id, {
        tags: [...conversation.tags, tag],
      });
      onUpdate({ tags: updated.tags });
      setNewTag('');
    } catch {
      /* ignore */
    }
  };

  const handleRemoveTag = async (tag: string) => {
    try {
      const updated = await updateConversation(conversation.id, {
        tags: conversation.tags.filter((t) => t !== tag),
      });
      onUpdate({ tags: updated.tags });
    } catch {
      /* ignore */
    }
  };

  const handleToggleFavorite = async () => {
    if (savingFavorite) return;
    setSavingFavorite(true);
    try {
      const updated = await updateConversation(conversation.id, {
        is_favorite: !conversation.is_favorite,
      });
      onUpdate({ is_favorite: updated.is_favorite });
    } catch {
      /* ignore */
    } finally {
      setSavingFavorite(false);
    }
  };

  const handleToggleArchive = async () => {
    if (savingArchive) return;
    setSavingArchive(true);
    try {
      const updated = await updateConversation(conversation.id, {
        is_archived: !conversation.is_archived,
      });
      onUpdate({ is_archived: updated.is_archived });
    } catch {
      /* ignore */
    } finally {
      setSavingArchive(false);
    }
  };

  return (
    <aside
      className="flex flex-col gap-5 p-4 border-l bg-muted/20 w-64 flex-shrink-0 overflow-y-auto"
      aria-label={t('chat.settings-sidebar-label')}
    >
      <div>
        <h2 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          <Settings className="h-3.5 w-3.5" aria-hidden="true" />
          {t('chat.settings-title')}
        </h2>
        <div className="mb-4">
          <label className="text-xs text-muted-foreground mb-1 block">
            {t('chat.title-label')}
          </label>
          {editingTitle ? (
            <div className="flex items-center gap-1">
              <Input
                ref={titleInputRef}
                value={titleValue}
                onChange={(e) => setTitleValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveTitle();
                  if (e.key === 'Escape') {
                    setEditingTitle(false);
                    setTitleValue(conversation.title);
                  }
                }}
                onBlur={handleSaveTitle}
                className="h-7 text-sm"
                aria-label={t('chat.edit-title-aria')}
                disabled={savingTitle}
              />
              {savingTitle && (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground flex-shrink-0" />
              )}
            </div>
          ) : (
            <button
              onClick={() => setEditingTitle(true)}
              className="flex items-center gap-1.5 w-full text-left text-sm font-medium hover:text-primary transition-colors group cursor-pointer"
              aria-label={t('chat.click-to-edit-aria')}
            >
              <span className="flex-1 line-clamp-2">{conversation.title}</span>
              <Pencil
                className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                aria-hidden="true"
              />
            </button>
          )}
        </div>
        <div className="mb-4">
          <label className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
            <Tag className="h-3 w-3" aria-hidden="true" />
            {t('chat.tags-label')}
          </label>
          <div className="flex flex-wrap gap-1 mb-2">
            {conversation.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-muted text-muted-foreground"
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:text-destructive transition-colors cursor-pointer"
                  aria-label={t('chat.remove-tag-aria', { tag })}
                >
                  <X className="h-2.5 w-2.5" aria-hidden="true" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <Input
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddTag();
                }
              }}
              placeholder={t('chat.add-tag-placeholder')}
              className="h-7 text-xs"
              aria-label={t('chat.add-tag-aria')}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAddTag}
              disabled={!newTag.trim()}
              className="h-7 w-7 p-0 cursor-pointer"
              aria-label={t('chat.confirm-add-tag-aria')}
            >
              <Check className="h-3.5 w-3.5" aria-hidden="true" />
            </Button>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleFavorite}
            disabled={savingFavorite}
            className={cn(
              'justify-start gap-2 cursor-pointer',
              conversation.is_favorite && 'text-yellow-600 border-yellow-300'
            )}
            aria-pressed={conversation.is_favorite}
            aria-label={
              conversation.is_favorite ? t('chat.unfavorite-aria') : t('chat.favorite-aria')
            }
          >
            {savingFavorite ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Star
                className="h-3.5 w-3.5"
                fill={conversation.is_favorite ? 'currentColor' : 'none'}
                aria-hidden="true"
              />
            )}
            {conversation.is_favorite ? t('chat.favorited') : t('chat.add-to-favorites')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleArchive}
            disabled={savingArchive}
            className="justify-start gap-2 cursor-pointer"
            aria-pressed={conversation.is_archived}
            aria-label={
              conversation.is_archived ? t('chat.unarchive-aria') : t('chat.archive-aria')
            }
          >
            {savingArchive && <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />}
            {!savingArchive && conversation.is_archived && (
              <ArchiveRestore className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {!savingArchive && !conversation.is_archived && (
              <Archive className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {conversation.is_archived ? t('chat.unarchive') : t('chat.archive')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            disabled={exporting}
            className="justify-start gap-2 cursor-pointer"
            aria-label={t('chat.export-aria')}
          >
            {exporting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {t('chat.export-markdown')}
          </Button>
        </div>
      </div>
    </aside>
  );
}
