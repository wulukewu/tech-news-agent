'use client';

import { useState } from 'react';
import { X, Plus, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

// ─── Props ────────────────────────────────────────────────────────────────────

interface TagManagerProps {
  /** Current list of tags */
  tags: string[];
  /** Called when tags change — receives the full new tag list */
  onTagsChange: (tags: string[]) => Promise<void>;
  /** Optional CSS class for the wrapper */
  className?: string;
  /** Whether the component is in a disabled/read-only state */
  disabled?: boolean;
  /** Maximum number of tags allowed (default: 10) */
  maxTags?: number;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Tag management component.
 *
 * Displays existing tags as removable chips and provides an input to add new
 * tags.  Duplicate and empty tags are silently ignored.
 *
 * Validates Requirements 3.2, 3.4
 */
export function TagManager({
  tags,
  onTagsChange,
  className,
  disabled = false,
  maxTags = 10,
}: TagManagerProps) {
  const { t } = useI18n();
  const [newTag, setNewTag] = useState('');
  const [saving, setSaving] = useState(false);

  const handleAddTag = async () => {
    const tag = newTag.trim();
    if (!tag || tags.includes(tag) || tags.length >= maxTags) {
      setNewTag('');
      return;
    }
    setSaving(true);
    try {
      await onTagsChange([...tags, tag]);
      setNewTag('');
    } catch (err) {
      console.error('Failed to add tag:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveTag = async (tag: string) => {
    if (disabled) return;
    setSaving(true);
    try {
      await onTagsChange(tags.filter((t) => t !== tag));
    } catch (err) {
      console.error('Failed to remove tag:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const canAddMore = tags.length < maxTags && !disabled;

  return (
    <div className={cn('space-y-2', className)}>
      {/* Existing tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5" role="list" aria-label={t('chat.tag-list-aria')}>
          {tags.map((tag) => (
            <span
              key={tag}
              role="listitem"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-muted text-muted-foreground"
            >
              {tag}
              {!disabled && (
                <button
                  onClick={() => handleRemoveTag(tag)}
                  disabled={saving}
                  className="hover:text-destructive transition-colors cursor-pointer disabled:opacity-50"
                  aria-label={t('chat.remove-tag-aria-label', { tag })}
                >
                  <X className="h-2.5 w-2.5" aria-hidden="true" />
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Add new tag */}
      {canAddMore && (
        <div className="flex items-center gap-1.5">
          <Input
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('chat.tag-manager-placeholder', { current: tags.length, max: maxTags })}
            disabled={saving}
            className="h-7 text-xs"
            aria-label={t('chat.tag-manager-input-aria')}
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleAddTag}
            disabled={!newTag.trim() || saving}
            className="h-7 w-7 p-0 cursor-pointer flex-shrink-0"
            aria-label={t('chat.tag-manager-confirm-aria')}
          >
            {saving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
            )}
          </Button>
        </div>
      )}

      {/* Max tags reached notice */}
      {tags.length >= maxTags && !disabled && (
        <p className="text-xs text-muted-foreground">
          {t('chat.max-tags-reached', { max: maxTags })}
        </p>
      )}
    </div>
  );
}
