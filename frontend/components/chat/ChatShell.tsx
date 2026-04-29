'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api/client';
import {
  getConversations,
  getConversation,
  getConversationMessages,
  addMessage,
  updateConversation,
  exportConversation,
  type ConversationSummary,
  type ConversationDetail,
  type ConversationMessage,
} from '@/lib/api/conversations';
import { formatDistanceToNow, format } from 'date-fns';
import {
  Send,
  Bot,
  User,
  Loader2,
  AlertCircle,
  Plus,
  Search,
  Star,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Globe,
  Hash,
} from 'lucide-react';
import { type ArticleSummary, type QAResponse, type QAMessage, EXAMPLE_QUERIES } from './types';
import { SettingsSidebar } from './components/SettingsSidebar';
import { HistorySidebar } from './components/HistorySidebar';
import {
  ArticleCard,
  QAAssistantMessage,
  QAUserMessage,
  HistoryMessageBubble,
  EmptyState,
} from './components/MessageComponents';
import { HistoryView } from './components/HistoryView';
import { QAView } from './components/QAView';
import { PlatformBadge } from './components/PlatformBadge';

// ─── Message Components ───────────────────────────────────────────────────────

export function ChatShell({ initialId }: { initialId: string | null }) {
  const { t } = useI18n();

  // mode: 'new' = blank QA, 'history' = loaded existing conversation
  const [mode, setMode] = useState<'new' | 'history'>(initialId ? 'history' : 'new');
  const [activeId, setActiveId] = useState<string | null>(initialId);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showSettings, setShowSettings] = useState(true);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);

  // New-conversation QA state
  const [qaMessages, setQaMessages] = useState<QAMessage[]>([]);
  const [qaInput, setQaInput] = useState('');
  const [qaLoading, setQaLoading] = useState(false);
  const [qaError, setQaError] = useState<string | null>(null);

  // History-conversation state
  const [histConversation, setHistConversation] = useState<ConversationDetail | null>(null);
  const [histMessages, setHistMessages] = useState<ConversationMessage[]>([]);
  const [histLoading, setHistLoading] = useState(false);
  const [histError, setHistError] = useState<string | null>(null);
  const [histInput, setHistInput] = useState('');
  const [histSending, setHistSending] = useState(false);
  const [histExporting, setHistExporting] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [qaMessages, histMessages]);

  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 100);
  }, [mode, activeId]);

  // Load a conversation from history (called by sidebar click or on mount when initialId is set)
  const loadConversation = useCallback(
    async (id: string, updateUrl = true) => {
      setMode('history');
      setActiveId(id);
      setHistLoading(true);
      setHistError(null);
      setHistMessages([]);
      setHistConversation(null);
      if (updateUrl) {
        // Use pushState directly to avoid triggering a Next.js navigation/re-render
        window.history.pushState(null, '', `/app/chat/${id}`);
      }
      try {
        const [conv, msgs] = await Promise.all([
          getConversation(id),
          getConversationMessages(id, { limit: 100 }),
        ]);
        setHistConversation(conv);
        setHistMessages(msgs);
      } catch {
        setHistError(t('chat.load-failed'));
      } finally {
        setHistLoading(false);
      }
    },
    [t]
  );

  // Load initialId on mount (when navigating directly to /app/chat/[id])
  useEffect(() => {
    if (initialId) {
      loadConversation(initialId, false); // URL is already correct, don't push again
    }
  }, [initialId, loadConversation]);

  const startNewChat = useCallback(() => {
    setMode('new');
    setActiveId(null);
    setQaMessages([]);
    setQaInput('');
    setQaError(null);
    setHistConversation(null);
    setHistMessages([]);
    window.history.pushState(null, '', '/app/chat');
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // Send message in NEW conversation (QA flow)
  const sendQAMessage = useCallback(
    async (query: string) => {
      const trimmed = query.trim();
      if (!trimmed || qaLoading) return;

      setQaMessages((prev) => [
        ...prev,
        { id: `user-${Date.now()}`, type: 'user', content: trimmed, timestamp: new Date() },
      ]);
      setQaInput('');
      setQaLoading(true);
      setQaError(null);

      try {
        let data: QAResponse;

        if (activeId) {
          const res = await apiClient.post<{ success: boolean; data: QAResponse }>(
            `/api/qa/conversations/${activeId}/continue`,
            { query: trimmed }
          );
          data = res.data.data;
        } else {
          const res = await apiClient.post<{
            success: boolean;
            data: { conversation_id: string; query_result?: QAResponse };
          }>('/api/qa/conversations', { initial_query: trimmed });
          const newId = res.data.data.conversation_id;

          if (res.data.data.query_result) {
            data = res.data.data.query_result;
            data.conversation_id = newId;
          } else {
            const fallback = await apiClient.post<{ success: boolean; data: QAResponse }>(
              '/api/qa/query',
              { query: trimmed, conversation_id: newId }
            );
            data = fallback.data.data;
          }

          // Update URL to /app/chat/[id] now that we have a real conversation
          setActiveId(newId);
          window.history.pushState(null, '', `/app/chat/${newId}`);
          setSidebarRefreshKey((k) => k + 1);
        }

        setQaMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            type: 'assistant',
            content: '',
            response: data,
            timestamp: new Date(),
          },
        ]);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : t('errors.server-error');
        setQaMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            type: 'assistant',
            content: '',
            timestamp: new Date(),
            error: `${t('chat.load-failed')} ${msg}`,
          },
        ]);
      } finally {
        setQaLoading(false);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    },
    [activeId, qaLoading, t]
  );

  // Send message in HISTORY conversation
  const sendHistMessage = useCallback(
    async (overrideContent?: string) => {
      const content = (overrideContent ?? histInput).trim();
      if (!content || histSending || !activeId) return;

      const optimistic: ConversationMessage = {
        id: `optimistic-${Date.now()}`,
        conversation_id: activeId,
        role: 'user',
        content,
        platform: 'web',
        created_at: new Date().toISOString(),
      };

      setHistMessages((prev) => [...prev, optimistic]);
      if (!overrideContent) setHistInput('');
      setHistSending(true);

      try {
        // Call QA continue endpoint to get AI response
        const res = await apiClient.post<{ success: boolean; data: QAResponse }>(
          `/api/qa/conversations/${activeId}/continue`,
          { query: content }
        );
        const qaData = res.data.data;

        const userMsg: ConversationMessage = {
          id: `user-${Date.now()}`,
          conversation_id: activeId,
          role: 'user',
          content,
          platform: 'web',
          created_at: new Date().toISOString(),
        };
        const assistantMsg: ConversationMessage = {
          id: `assistant-${Date.now()}`,
          conversation_id: activeId,
          role: 'assistant',
          content: qaData.insights?.join('\n') || '',
          platform: 'web',
          created_at: new Date().toISOString(),
          metadata: {
            articles: qaData.articles,
            insights: qaData.insights,
            recommendations: qaData.recommendations,
            response_time: qaData.response_time,
            intent: qaData.intent ?? 'question',
          },
        };

        setHistMessages((prev) => [
          ...prev.filter((m) => m.id !== optimistic.id),
          userMsg,
          assistantMsg,
        ]);
        setHistConversation((prev) =>
          prev ? { ...prev, message_count: prev.message_count + 2 } : prev
        );
      } catch {
        // QA failed — fall back to just saving the user message
        try {
          const saved = await addMessage(activeId, { role: 'user', content, platform: 'web' });
          setHistMessages((prev) => prev.map((m) => (m.id === optimistic.id ? saved : m)));
          setHistConversation((prev) =>
            prev ? { ...prev, message_count: prev.message_count + 1 } : prev
          );
        } catch {
          setHistMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
          if (!overrideContent) setHistInput(content);
        }
      } finally {
        setHistSending(false);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    },
    [activeId, histInput, histSending]
  );

  const handleExport = async () => {
    if (histExporting || !activeId) return;
    setHistExporting(true);
    try {
      const blob = await exportConversation(activeId, 'markdown');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${activeId.slice(0, 8)}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      /* ignore */
    } finally {
      setHistExporting(false);
    }
  };

  // ── Centre panel content ──────────────────────────────────────────────────

  return (
    <div className="-m-4 lg:-m-6 flex overflow-hidden" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Left: history sidebar */}
      {sidebarOpen && (
        <HistorySidebar
          activeId={activeId}
          onNewChat={startNewChat}
          onSelect={(id) => loadConversation(id, true)}
          refreshKey={sidebarRefreshKey}
        />
      )}

      {/* Centre + right */}
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        {/* Header */}
        <header className="flex-shrink-0 px-3 py-3 border-b bg-background/95 backdrop-blur">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen((v) => !v)}
              className="cursor-pointer flex-shrink-0 h-8 w-8 p-0"
              aria-label={
                sidebarOpen
                  ? t('chat.toggle-sidebar-close-aria')
                  : t('chat.toggle-sidebar-open-aria')
              }
              aria-expanded={sidebarOpen}
            >
              {sidebarOpen ? (
                <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
              ) : (
                <PanelLeftOpen className="h-4 w-4" aria-hidden="true" />
              )}
            </Button>
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Bot className="h-4 w-4 text-primary" aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              {mode === 'history' && histConversation && (
                <>
                  <h1 className="text-base font-semibold leading-tight truncate">
                    {histConversation.title}
                  </h1>
                  <p className="text-xs text-muted-foreground">
                    {t('chat.message-count', { count: histConversation.message_count })}
                  </p>
                </>
              )}
              {mode === 'history' && !histConversation && histLoading && (
                <>
                  <div
                    className="h-4 w-40 bg-muted animate-pulse rounded mb-1"
                    aria-hidden="true"
                  />
                  <div className="h-3 w-20 bg-muted animate-pulse rounded" aria-hidden="true" />
                </>
              )}
              {mode === 'new' && (
                <>
                  <h1 className="text-base font-semibold leading-tight">
                    {t('chat.smart-qa-title')}
                  </h1>
                  <p className="text-xs text-muted-foreground hidden sm:block">
                    {t('chat.smart-qa-subtitle')}
                  </p>
                </>
              )}
            </div>
            {mode === 'history' && histConversation && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSettings((v) => !v)}
                className="cursor-pointer flex-shrink-0 h-8 w-8 p-0"
                aria-label={
                  showSettings ? t('chat.hide-settings-aria') : t('chat.show-settings-aria')
                }
                aria-expanded={showSettings}
              >
                <Settings className="h-4 w-4" aria-hidden="true" />
              </Button>
            )}
          </div>
        </header>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          <div className="flex flex-col flex-1 overflow-hidden">
            {mode === 'history' && (
              <HistoryView
                histLoading={histLoading}
                histError={histError}
                histMessages={histMessages}
                histSending={histSending}
                histInput={histInput}
                onHistInputChange={setHistInput}
                onSendHistMessage={sendHistMessage}
                onStartNewChat={startNewChat}
                onFollowUp={(q) => sendHistMessage(q)}
                messagesEndRef={messagesEndRef}
                inputRef={inputRef}
              />
            )}
            {mode === 'new' && (
              <QAView
                qaMessages={qaMessages}
                qaLoading={qaLoading}
                qaError={qaError}
                qaInput={qaInput}
                onQaInputChange={setQaInput}
                onSendQAMessage={sendQAMessage}
                onClearError={() => setQaError(null)}
                messagesEndRef={messagesEndRef}
                inputRef={inputRef}
              />
            )}
          </div>
          {mode === 'history' && histConversation && showSettings && (
            <SettingsSidebar
              conversation={histConversation}
              onUpdate={(updates) =>
                setHistConversation((prev) => (prev ? { ...prev, ...updates } : prev))
              }
              onExport={handleExport}
              exporting={histExporting}
            />
          )}
        </div>
      </div>
    </div>
  );
}
