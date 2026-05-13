'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { formatDistanceToNow } from 'date-fns';
import { ArrowLeft, Send, Loader2, AlertCircle, ChevronRight, Settings } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';
import {
  getConversation,
  getConversationMessages,
  addMessage,
  exportConversation,
  type ConversationDetail,
  type ConversationMessage,
} from '@/lib/api/conversations';
import { PlatformBadge, MessageBubble, SettingsSidebar } from './ConversationComponents';

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
