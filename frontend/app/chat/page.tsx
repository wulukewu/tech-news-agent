'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api/client';
import { Send, Loader2, AlertCircle } from 'lucide-react';

import { useI18n } from '@/contexts/I18nContext';
import { Badge } from '@/components/ui/badge';
import { Bot } from 'lucide-react';
import {
  AssistantMessage,
  ChatMessage,
  EmptyState,
  QAResponse,
  UserMessage,
} from './ChatComponents';

// ─── Main Page ────────────────────────────────────────────────────────────────

function ChatPageContent() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const { t } = useI18n();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = useCallback(
    async (query: string) => {
      const trimmed = query.trim();
      if (!trimmed || isLoading) return;

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        content: trimmed,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInputValue('');
      setIsLoading(true);
      setGlobalError(null);

      try {
        let data: QAResponse;

        if (conversationId) {
          // Continue existing conversation
          const res = await apiClient.post<{ success: boolean; data: QAResponse }>(
            `/api/qa/conversations/${conversationId}/continue`,
            { query: trimmed }
          );
          data = res.data.data; // Extract from SuccessResponse wrapper
        } else {
          // Start new conversation
          const res = await apiClient.post<{
            success: boolean;
            data: { conversation_id: string; query_result?: QAResponse };
          }>('/api/qa/conversations', { initial_query: trimmed });

          if (res.data.data.query_result) {
            data = res.data.data.query_result;
            // Ensure conversation_id is set from the response
            data.conversation_id = res.data.data.conversation_id;
          } else {
            // Fallback: use single query endpoint
            const fallback = await apiClient.post<{ success: boolean; data: QAResponse }>(
              '/api/qa/query',
              {
                query: trimmed,
                conversation_id: res.data.data.conversation_id,
              }
            );
            data = fallback.data.data; // Extract from SuccessResponse wrapper
          }

          setConversationId(res.data.data.conversation_id);
        }

        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          type: 'assistant',
          content: '',
          response: data,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : t('errors.server-error');

        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          type: 'assistant',
          content: '',
          timestamp: new Date(),
          error: `${t('chat.load-failed')} ${errorMsg}`,
        };

        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
        // Re-focus input after response
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    },
    [conversationId, isLoading]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const handleExampleClick = (query: string) => {
    setInputValue(query);
    sendMessage(query);
  };

  const handleFollowUp = (query: string) => {
    setInputValue(query);
    sendMessage(query);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto">
      {/* Header */}
      <header className="flex-shrink-0 px-4 py-4 border-b bg-background/95 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center">
            <Bot className="h-5 w-5 text-primary" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-lg font-semibold leading-tight">{t('chat.header-title')}</h1>
            <p className="text-xs text-muted-foreground">{t('chat.header-subtitle')}</p>
          </div>
          {conversationId && (
            <Badge variant="outline" className="ml-auto text-xs">
              {t('chat.header-in-progress')}
            </Badge>
          )}
        </div>
      </header>

      {/* Global error banner */}
      {globalError && (
        <div
          role="alert"
          className="flex-shrink-0 mx-4 mt-3 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>{globalError}</span>
          <button
            onClick={() => setGlobalError(null)}
            className="ml-auto text-xs underline cursor-pointer hover:no-underline"
            aria-label={t('chat.close-error-aria-label')}
          >
            {t('chat.close-error-label')}
          </button>
        </div>
      )}

      {/* Messages area */}
      <main
        className="flex-1 overflow-y-auto px-4 py-4 space-y-6"
        aria-label={t('chat.history-aria')}
        aria-live="polite"
        aria-atomic="false"
      >
        {messages.length === 0 ? (
          <EmptyState onExampleClick={handleExampleClick} />
        ) : (
          <>
            {messages.map((message) =>
              message.type === 'user' ? (
                <UserMessage key={message.id} message={message} />
              ) : (
                <AssistantMessage key={message.id} message={message} onFollowUp={handleFollowUp} />
              )
            )}

            {/* Loading indicator */}
            {isLoading && (
              <div
                className="flex items-start gap-3"
                role="status"
                aria-label={t('chat.generating-answer-aria')}
              >
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" aria-hidden="true" />
                </div>
                <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
                  <Loader2
                    className="h-4 w-4 animate-spin text-muted-foreground"
                    aria-hidden="true"
                  />
                  <span className="text-sm text-muted-foreground">
                    {t('chat.searching-generating-text')}
                  </span>
                </div>
              </div>
            )}
          </>
        )}
        {/* Scroll anchor */}
        <div ref={messagesEndRef} aria-hidden="true" />
      </main>

      {/* Input area */}
      <footer className="flex-shrink-0 border-t bg-background/95 backdrop-blur px-4 py-3">
        <form
          onSubmit={handleSubmit}
          className="flex items-center gap-2"
          aria-label={t('chat.qa-form-aria-label')}
        >
          <label htmlFor="chat-input" className="sr-only">
            {t('chat.qa-input-label-text')}
          </label>
          <Input
            id="chat-input"
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('chat.qa-placeholder-text')}
            disabled={isLoading}
            autoComplete="off"
            aria-label={t('chat.qa-input-aria-text')}
            className="flex-1 min-h-10 md:min-h-10 resize-none"
          />
          <Button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            aria-label={t('chat.qa-send-aria')}
            className="flex-shrink-0 cursor-pointer"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="sr-only">
              {isLoading ? t('chat.qa-sending-sr') : t('chat.qa-send-sr')}
            </span>
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-1.5 text-center">
          {t('chat.qa-footer-hint')}
        </p>
      </footer>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatPageContent />
    </ProtectedRoute>
  );
}
