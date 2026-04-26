'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { formatDistanceToNow, format } from 'date-fns';
import {
  ArrowLeft,
  Bot,
  User,
  Send,
  Loader2,
  AlertCircle,
  Star,
  Archive,
  ArchiveRestore,
  Download,
  Globe,
  Hash,
  Tag,
  X,
  Check,
  Pencil,
  Settings,
  ChevronRight,
} from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';
import {
  getConversation,
  getConversationMessages,
  addMessage,
  updateConversation,
  exportConversation,
  type ConversationDetail,
  type ConversationMessage,
} from '@/lib/api/conversations';

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

// ─── Message Bubble ───────────────────────────────────────────────────────────

function MessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === 'user';
  let timeDisplay = '';
  try {
    const date = new Date(message.created_at);
    if (!isNaN(date.getTime())) {
      timeDisplay = format(date, 'HH:mm');
    }
  } catch {
    timeDisplay = '';
  }

  return (
    <div className={cn('flex items-end gap-2', isUser ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 h-7 w-7 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary/10' : 'bg-muted'
        )}
        aria-hidden="true"
      >
        {isUser ? (
          <User className="h-3.5 w-3.5 text-primary" />
        ) : (
          <Bot className="h-3.5 w-3.5 text-muted-foreground" />
        )}
      </div>

      {/* Bubble */}
      <div className={cn('flex flex-col gap-1 max-w-[75%]', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
            isUser
              ? 'rounded-tr-sm bg-primary text-primary-foreground'
              : 'rounded-tl-sm bg-muted text-foreground'
          )}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {timeDisplay && <span className="text-xs text-muted-foreground">{timeDisplay}</span>}
          <PlatformBadge platform={message.platform} />
        </div>
      </div>
    </div>
  );
}

// ─── Settings Sidebar ─────────────────────────────────────────────────────────

interface SettingsSidebarProps {
  conversation: ConversationDetail;
  onUpdate: (updated: Partial<ConversationDetail>) => void;
  onExport: () => void;
  exporting: boolean;
}

function SettingsSidebar({ conversation, onUpdate, onExport, exporting }: SettingsSidebarProps) {
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
    } catch (err) {
      console.error('Failed to update title:', err);
      setTitleValue(conversation.title);
      setEditingTitle(false);
    } finally {
      setSavingTitle(false);
    }
  };

  const handleTitleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSaveTitle();
    if (e.key === 'Escape') {
      setEditingTitle(false);
      setTitleValue(conversation.title);
    }
  };

  const handleAddTag = async () => {
    const tag = newTag.trim();
    if (!tag || conversation.tags.includes(tag)) {
      setNewTag('');
      return;
    }
    const newTags = [...conversation.tags, tag];
    try {
      const updated = await updateConversation(conversation.id, { tags: newTags });
      onUpdate({ tags: updated.tags });
      setNewTag('');
    } catch (err) {
      console.error('Failed to add tag:', err);
    }
  };

  const handleRemoveTag = async (tag: string) => {
    const newTags = conversation.tags.filter((t) => t !== tag);
    try {
      const updated = await updateConversation(conversation.id, { tags: newTags });
      onUpdate({ tags: updated.tags });
    } catch (err) {
      console.error('Failed to remove tag:', err);
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
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
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
    } catch (err) {
      console.error('Failed to toggle archive:', err);
    } finally {
      setSavingArchive(false);
    }
  };

  return (
    <aside
      className="flex flex-col gap-5 p-4 border-l bg-muted/20 min-w-[220px] max-w-[280px]"
      aria-label={t('chat.detail-settings-aria')}
    >
      <div>
        <h2 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          <Settings className="h-3.5 w-3.5" aria-hidden="true" />
          {t('chat.detail-settings-title')}
        </h2>

        {/* Title editing */}
        <div className="mb-4">
          <label className="text-xs text-muted-foreground mb-1 block">
            {t('chat.detail-title-label')}
          </label>
          {editingTitle ? (
            <div className="flex items-center gap-1">
              <Input
                ref={titleInputRef}
                value={titleValue}
                onChange={(e) => setTitleValue(e.target.value)}
                onKeyDown={handleTitleKeyDown}
                onBlur={handleSaveTitle}
                className="h-7 text-sm"
                aria-label={t('chat.detail-title-edit-aria')}
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
              aria-label={t('chat.detail-title-click-aria')}
            >
              <span className="flex-1 line-clamp-2">{conversation.title}</span>
              <Pencil
                className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                aria-hidden="true"
              />
            </button>
          )}
        </div>

        {/* Tags */}
        <div className="mb-4">
          <label className="text-xs text-muted-foreground mb-2 block flex items-center gap-1">
            <Tag className="h-3 w-3" aria-hidden="true" />
            {t('chat.detail-tags-label')}
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
                  aria-label={t('chat.detail-remove-tag-aria', { tag })}
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
              placeholder={t('chat.detail-add-tag-placeholder')}
              className="h-7 text-xs"
              aria-label={t('chat.detail-add-tag-aria')}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAddTag}
              disabled={!newTag.trim()}
              className="h-7 w-7 p-0 cursor-pointer"
              aria-label={t('chat.detail-confirm-tag-aria')}
            >
              <Check className="h-3.5 w-3.5" aria-hidden="true" />
            </Button>
          </div>
        </div>

        {/* Actions */}
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
              conversation.is_favorite
                ? t('chat.detail-unfavorite-aria')
                : t('chat.detail-favorite-aria')
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
            {conversation.is_favorite
              ? t('chat.detail-favorited-label')
              : t('chat.detail-add-favorite-label')}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleArchive}
            disabled={savingArchive}
            className="justify-start gap-2 cursor-pointer"
            aria-pressed={conversation.is_archived}
            aria-label={
              conversation.is_archived
                ? t('chat.detail-unarchive-aria')
                : t('chat.detail-archive-aria')
            }
          >
            {savingArchive ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : conversation.is_archived ? (
              <ArchiveRestore className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <Archive className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {conversation.is_archived
              ? t('chat.detail-archived-label')
              : t('chat.detail-archive-label')}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            disabled={exporting}
            className="justify-start gap-2 cursor-pointer"
            aria-label={t('chat.detail-export-aria')}
          >
            {exporting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {t('chat.detail-export-label')}
          </Button>
        </div>
      </div>
    </aside>
  );
}

// ─── Main Page Content ────────────────────────────────────────────────────────

function ConversationDetailContent({ id }: { id: string }) {
  const router = useRouter();
  const { t } = useI18n();

  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load conversation and messages
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [conv, msgs] = await Promise.all([
          getConversation(id),
          getConversationMessages(id, { limit: 100 }),
        ]);
        if (!cancelled) {
          setConversation(conv);
          setMessages(msgs);
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Failed to load conversation:', err);
          setError(t('chat.detail-load-error'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input after load
  useEffect(() => {
    if (!loading) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [loading]);

  const handleSend = useCallback(async () => {
    const content = inputValue.trim();
    if (!content || sending) return;

    const optimisticMsg: ConversationMessage = {
      id: `optimistic-${Date.now()}`,
      conversation_id: id,
      role: 'user',
      content,
      platform: 'web',
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticMsg]);
    setInputValue('');
    setSending(true);

    try {
      const saved = await addMessage(id, { role: 'user', content, platform: 'web' });
      setMessages((prev) => prev.map((m) => (m.id === optimisticMsg.id ? saved : m)));
      // Update message count on conversation
      setConversation((prev) => (prev ? { ...prev, message_count: prev.message_count + 1 } : prev));
    } catch (err) {
      console.error('Failed to send message:', err);
      // Remove optimistic message on failure
      setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
      setInputValue(content);
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [id, inputValue, sending]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleConversationUpdate = useCallback((updates: Partial<ConversationDetail>) => {
    setConversation((prev) => (prev ? { ...prev, ...updates } : prev));
  }, []);

  const handleExport = async () => {
    if (exporting) return;
    setExporting(true);
    try {
      const blob = await exportConversation(id, 'markdown');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${id.slice(0, 8)}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export conversation:', err);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]" role="status">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" />
        <span className="sr-only">{t('chat.detail-loading-aria')}</span>
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] gap-4 px-4">
        <AlertCircle className="h-10 w-10 text-destructive" aria-hidden="true" />
        <p className="text-sm text-destructive text-center">
          {error ?? t('chat.detail-not-found')}
        </p>
        <Button
          variant="outline"
          onClick={() => router.push('/app/chat/conversations')}
          className="cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4 mr-2" aria-hidden="true" />
          {t('chat.detail-back-to-list')}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <header className="flex-shrink-0 flex items-center gap-3 px-4 py-3 border-b bg-background/95 backdrop-blur">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/app/chat/conversations')}
          className="cursor-pointer flex-shrink-0"
          aria-label={t('chat.detail-back-to-list')}
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        </Button>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-base font-semibold truncate">{conversation.title}</h1>
            <PlatformBadge platform={conversation.platform} />
          </div>
          <p className="text-xs text-muted-foreground">
            {t('chat.detail-message-count', { count: conversation.message_count })}
          </p>
        </div>

        {/* Toggle sidebar on mobile */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowSidebar((v) => !v)}
          className="cursor-pointer lg:hidden"
          aria-label={
            showSidebar
              ? t('chat.detail-toggle-settings-hide')
              : t('chat.detail-toggle-settings-show')
          }
          aria-expanded={showSidebar}
        >
          <Settings className="h-4 w-4" aria-hidden="true" />
        </Button>
      </header>

      {/* Body: messages + sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Messages area */}
        <main className="flex flex-col flex-1 overflow-hidden">
          {/* Message list */}
          <div
            className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
            aria-label={t('chat.detail-messages-aria')}
            aria-live="polite"
          >
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full py-16 text-center">
                <p className="text-sm text-muted-foreground">{t('chat.detail-no-messages')}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {t('chat.detail-start-conversation')}
                </p>
              </div>
            ) : (
              messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
            )}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>

          {/* Input area */}
          <footer className="flex-shrink-0 border-t bg-background/95 backdrop-blur px-4 py-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
              aria-label={t('chat.detail-send-form-aria')}
            >
              <label htmlFor="message-input" className="sr-only">
                {t('chat.detail-input-label')}
              </label>
              <Input
                id="message-input"
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('chat.detail-input-placeholder')}
                disabled={sending}
                autoComplete="off"
                className="flex-1"
                aria-label={t('chat.detail-input-aria')}
              />
              <Button
                type="submit"
                disabled={sending || !inputValue.trim()}
                aria-label={t('chat.detail-send-aria')}
                className="flex-shrink-0 cursor-pointer"
              >
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Send className="h-4 w-4" aria-hidden="true" />
                )}
                <span className="sr-only">
                  {sending ? t('chat.detail-sending-sr') : t('chat.detail-send-sr')}
                </span>
              </Button>
            </form>
          </footer>
        </main>

        {/* Settings sidebar */}
        {showSidebar && (
          <SettingsSidebar
            conversation={conversation}
            onUpdate={handleConversationUpdate}
            onExport={handleExport}
            exporting={exporting}
          />
        )}
      </div>
    </div>
  );
}

// ─── Page Export ──────────────────────────────────────────────────────────────

export default function ConversationDetailPage() {
  const params = useParams();
  const id =
    typeof params?.id === 'string' ? params.id : Array.isArray(params?.id) ? params.id[0] : '';

  return (
    <ProtectedRoute>
      <ConversationDetailContent id={id} />
    </ProtectedRoute>
  );
}
