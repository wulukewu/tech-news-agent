'use client';

import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, AlertCircle, Send } from 'lucide-react';
import { type ConversationMessage } from '@/lib/api/conversations';
import { type ArticleSummary, type QAMessage } from '../types';
import { QAAssistantMessage, HistoryMessageBubble } from './MessageComponents';

export function HistoryView({
  histLoading,
  histError,
  histMessages,
  histSending,
  histInput,
  onHistInputChange,
  onSendHistMessage,
  onStartNewChat,
  onFollowUp,
  messagesEndRef,
  inputRef,
}: {
  histLoading: boolean;
  histError: string | null;
  histMessages: ConversationMessage[];
  histSending: boolean;
  histInput: string;
  onHistInputChange: (v: string) => void;
  onSendHistMessage: (override?: string) => void;
  onStartNewChat: () => void;
  onFollowUp: (q: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  inputRef: React.RefObject<HTMLInputElement>;
}) {
  const { t } = useI18n();

  if (histLoading) {
    return (
      <div className="flex items-center justify-center flex-1" role="status">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" />
        <span className="sr-only">{t('chat.loading-conversation')}</span>
      </div>
    );
  }
  if (histError) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 gap-4 px-4">
        <AlertCircle className="h-10 w-10 text-destructive" aria-hidden="true" />
        <p className="text-sm text-destructive text-center">{histError}</p>
        <Button variant="outline" onClick={onStartNewChat} className="cursor-pointer">
          {t('chat.back-to-new')}
        </Button>
      </div>
    );
  }
  return (
    <>
      <div
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
        aria-label={t('chat.messages-area-aria')}
        aria-live="polite"
      >
        {histMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-16 text-center">
            <p className="text-sm text-muted-foreground">{t('chat.no-messages')}</p>
            <p className="text-xs text-muted-foreground mt-1">{t('chat.start-conversation')}</p>
          </div>
        ) : (
          histMessages.map((msg) => {
            if (
              msg.role === 'assistant' &&
              msg.metadata &&
              (msg.metadata.articles || msg.metadata.insights)
            ) {
              const intent = (msg.metadata.intent as string) || 'question';
              const qaMsg: QAMessage = {
                id: msg.id,
                type: 'assistant',
                content: msg.content,
                timestamp: new Date(msg.created_at),
                response: {
                  query: '',
                  articles: (msg.metadata.articles as ArticleSummary[]) ?? [],
                  insights: (msg.metadata.insights as string[]) ?? [],
                  recommendations: (msg.metadata.recommendations as string[]) ?? [],
                  conversation_id: msg.conversation_id,
                  response_time: (msg.metadata.response_time as number) ?? 0,
                  intent: intent as 'question' | 'preference' | 'other',
                },
              };
              return <QAAssistantMessage key={msg.id} message={qaMsg} onFollowUp={onFollowUp} />;
            }
            return <HistoryMessageBubble key={msg.id} message={msg} />;
          })
        )}
        {histSending && (
          <div className="flex items-start gap-3" role="status">
            <div className="flex-shrink-0 h-7 w-7 rounded-full bg-muted flex items-center justify-center">
              <Loader2
                className="h-3.5 w-3.5 animate-spin text-muted-foreground"
                aria-hidden="true"
              />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} aria-hidden="true" />
      </div>
      <footer className="flex-shrink-0 border-t bg-background/95 backdrop-blur px-4 py-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSendHistMessage();
          }}
          className="flex items-center gap-2"
          aria-label={t('chat.send-message-form-aria')}
        >
          <label htmlFor="hist-input" className="sr-only">
            {t('chat.message-input-label')}
          </label>
          <Input
            id="hist-input"
            ref={inputRef}
            value={histInput}
            onChange={(e) => onHistInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSendHistMessage();
              }
            }}
            placeholder={t('chat.continue-conversation-placeholder')}
            disabled={histSending}
            autoComplete="off"
            className="flex-1"
            aria-label={t('chat.message-input-aria')}
          />
          <Button
            type="submit"
            disabled={histSending || !histInput.trim()}
            aria-label={t('chat.send-aria')}
            className="flex-shrink-0 cursor-pointer"
          >
            {histSending ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="sr-only">{histSending ? t('chat.sending') : t('chat.send')}</span>
          </Button>
        </form>
      </footer>
    </>
  );
}

// ─── QA View ──────────────────────────────────────────────────────────────────
