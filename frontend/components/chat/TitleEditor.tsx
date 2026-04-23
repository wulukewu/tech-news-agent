'use client';

import { useState, useEffect, useRef } from 'react';
import { Pencil, Check, X, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

// ─── Props ────────────────────────────────────────────────────────────────────

interface TitleEditorProps {
  /** Current title value */
  title: string;
  /** Called with the new title when the user confirms the edit */
  onSave: (newTitle: string) => Promise<void>;
  /** Optional CSS class for the wrapper */
  className?: string;
  /** Whether the component is in a disabled/read-only state */
  disabled?: boolean;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Inline title editor.
 *
 * Renders the title as a clickable text element.  Clicking it (or pressing
 * Enter / Space) switches to an input field.  The user can confirm with Enter
 * or the ✓ button, or cancel with Escape or the ✕ button.
 *
 * Validates Requirements 3.2
 */
export function TitleEditor({ title, onSave, className, disabled = false }: TitleEditorProps) {
  const { t } = useI18n();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(title);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Keep local value in sync when the prop changes externally
  useEffect(() => {
    if (!editing) setValue(title);
  }, [title, editing]);

  // Focus and select all text when entering edit mode
  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  const handleConfirm = async () => {
    const trimmed = value.trim();
    if (!trimmed) {
      // Revert to original if empty
      setValue(title);
      setEditing(false);
      return;
    }
    if (trimmed === title) {
      setEditing(false);
      return;
    }
    setSaving(true);
    try {
      await onSave(trimmed);
      setEditing(false);
    } catch {
      // Revert on error
      setValue(title);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setValue(title);
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleConfirm();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  };

  if (editing) {
    return (
      <div className={cn('flex items-center gap-1', className)}>
        <Input
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleConfirm}
          disabled={saving}
          aria-label={t('chat.edit-title-aria')}
          className="h-8 text-sm"
        />
        {saving ? (
          <Loader2
            className="h-4 w-4 animate-spin text-muted-foreground flex-shrink-0"
            aria-hidden="true"
          />
        ) : (
          <>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleConfirm}
              className="h-8 w-8 p-0 cursor-pointer text-green-600 hover:text-green-700"
              aria-label={t('chat.confirm-edit-aria')}
            >
              <Check className="h-3.5 w-3.5" aria-hidden="true" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancel}
              className="h-8 w-8 p-0 cursor-pointer text-muted-foreground hover:text-foreground"
              aria-label={t('chat.cancel-edit-aria')}
            >
              <X className="h-3.5 w-3.5" aria-hidden="true" />
            </Button>
          </>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => !disabled && setEditing(true)}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
          e.preventDefault();
          setEditing(true);
        }
      }}
      disabled={disabled}
      aria-label={t('chat.click-to-edit-aria', { title })}
      className={cn(
        'group flex items-center gap-1.5 text-left w-full',
        !disabled && 'cursor-pointer hover:text-primary transition-colors',
        disabled && 'cursor-default',
        className
      )}
    >
      <span className="flex-1 font-semibold truncate">{title}</span>
      {!disabled && (
        <Pencil
          className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
          aria-hidden="true"
        />
      )}
    </button>
  );
}
