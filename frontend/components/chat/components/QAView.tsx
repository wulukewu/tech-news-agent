'use client';

import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { Loader2, AlertCircle, Send, Bot } from 'lucide-react';
import { type QAMessage } from '../types';
import { QAAssistantMessage, QAUserMessage, EmptyState } from './MessageComponents';

export function QAView({
  qaMessages,
  qaLoading,
  qaError,
  qaInput,
  onQaInputChange,
  onSendQAMessage,
  onClearError,
  messagesEndRef,
  inputRef,
}: {
  qaMessages: QAMessage[];
  qaLoading: boolean;
  qaError: string | null;
  qaInput: string;
  onQaInputChange: (v: string) => void;
  onSendQAMessage: (q: string) => void;
  onClearError: () => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  inputRef: React.RefObject<HTMLInputElement>;
}) {
  const { t } = useI18n();
  return (
    <>
      <main
        className="flex-1 overflow-y-auto px-4 py-4 space-y-6"
        aria-label={t('chat.history-area-aria')}
        aria-live="polite"
        aria-atomic="false"
      >
        {qaMessages.length === 0 ? (
          <EmptyState
            onExampleClick={(q) => {
              onQaInputChange(q);
              onSendQAMessage(q);
            }}
          />
        ) : (
          <>
            {qaMessages.map((msg) =>
              msg.type === 'user' ? (
                <QAUserMessage key={msg.id} content={msg.content} />
              ) : (
                <QAAssistantMessage
                  key={msg.id}
                  message={msg}
                  onFollowUp={(q) => {
                    onQaInputChange(q);
                    onSendQAMessage(q);
                  }}
                />
              )
            )}
            {qaLoading && (
              <div
                className="flex items-start gap-3"
                role="status"
                aria-label={t('chat.generating-answer')}
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
                    {t('chat.searching-generating')}
                  </span>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} aria-hidden="true" />
      </main>
      {qaError && (
        <div
          role="alert"
          className="flex-shrink-0 mx-4 mb-2 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>{qaError}</span>
          <button
            onClick={onClearError}
            className="ml-auto text-xs underline cursor-pointer hover:no-underline"
            aria-label={t('chat.close-error-aria')}
          >
            {t('chat.close-error')}
          </button>
        </div>
      )}
      <footer className="flex-shrink-0 border-t bg-background/95 backdrop-blur px-4 py-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSendQAMessage(qaInput);
          }}
          className="flex items-center gap-2"
          aria-label={t('chat.qa-form-aria')}
        >
          <label htmlFor="qa-input" className="sr-only">
            {t('chat.qa-input-label')}
          </label>
          <Input
            id="qa-input"
            ref={inputRef}
            value={qaInput}
            onChange={(e) => onQaInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSendQAMessage(qaInput);
              }
            }}
            placeholder={t('chat.qa-placeholder')}
            disabled={qaLoading}
            autoComplete="off"
            className="flex-1"
            aria-label={t('chat.qa-input-aria')}
          />
          <Button
            type="submit"
            disabled={qaLoading || !qaInput.trim()}
            aria-label={t('chat.send-question-aria')}
            className="flex-shrink-0 cursor-pointer"
          >
            {qaLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="sr-only">{qaLoading ? t('chat.sending') : t('chat.send')}</span>
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-1.5 text-center">{t('chat.footer-hint')}</p>
      </footer>
    </>
  );
}

// ─── Main Shell ───────────────────────────────────────────────────────────────

// eslint-disable-next-line complexity
