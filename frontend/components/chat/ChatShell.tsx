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
  Clock,
  ExternalLink,
  Lightbulb,
  BookOpen,
  MessageSquare,
  Loader2,
  AlertCircle,
  ChevronRight,
  Plus,
  Search,
  Star,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Tag,
  X,
  Check,
  Pencil,
  Archive,
  ArchiveRestore,
  Download,
  Globe,
  Hash,
} from 'lucide-react';
import { type ArticleSummary, type QAResponse, type QAMessage, EXAMPLE_QUERIES } from './types';
import { SettingsSidebar } from './components/SettingsSidebar';
import { HistorySidebar } from './components/HistorySidebar';

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

// ─── Message Components ───────────────────────────────────────────────────────

function ArticleCard({ article }: { article: ArticleSummary }) {
  const { t } = useI18n();
  return (
    <div className="rounded-lg border bg-background p-4 space-y-2 hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between gap-2">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-semibold text-primary hover:underline leading-snug flex-1 cursor-pointer"
          aria-label={t('chat.article-read-aria', { title: article.title })}
        >
          {article.title}
        </a>
        <ExternalLink
          className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0 mt-0.5"
          aria-hidden="true"
        />
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {article.category && (
          <Badge variant="secondary" className="text-xs">
            {article.category}
          </Badge>
        )}
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" aria-hidden="true" />
          {t('chat.read-minutes', { minutes: article.reading_time })}
        </span>
        {article.relevance_score > 0 && (
          <span className="text-xs text-muted-foreground">
            {t('chat.relevance', { score: Math.round(article.relevance_score * 100) })}
          </span>
        )}
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">{article.summary}</p>
      {article.key_insights && article.key_insights.length > 0 && (
        <ul className="space-y-0.5">
          {article.key_insights.slice(0, 3).map((insight, i) => (
            <li key={i} className="flex items-start gap-1.5 text-xs text-foreground/80">
              <ChevronRight
                className="h-3 w-3 text-primary flex-shrink-0 mt-0.5"
                aria-hidden="true"
              />
              <span>{insight}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ─── Preference Ack Card ──────────────────────────────────────────────────────

function PreferenceAckCard({
  insights,
  recommendations,
}: {
  insights: string[];
  recommendations: string[];
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
        <Bot className="h-4 w-4 text-green-600 dark:text-green-400" aria-hidden="true" />
      </div>
      <div className="flex-1 rounded-2xl rounded-tl-sm border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 px-4 py-3 space-y-2">
        {insights.map((line, i) => (
          <p key={i} className="text-sm text-green-800 dark:text-green-200">
            {line}
          </p>
        ))}
        {recommendations.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {recommendations.map((rec, i) => (
              <span
                key={i}
                className="text-xs text-muted-foreground bg-background/60 rounded-full px-2 py-1 border"
              >
                {rec}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Other Ack Card ───────────────────────────────────────────────────────────

function OtherAckCard({
  insights,
  recommendations,
  onFollowUp,
}: {
  insights: string[];
  recommendations: string[];
  onFollowUp: (q: string) => void;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center">
        <Bot className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      </div>
      <div className="flex-1 rounded-2xl rounded-tl-sm bg-muted px-4 py-3 space-y-2">
        {insights.map((line, i) => (
          <p key={i} className="text-sm">
            {line}
          </p>
        ))}
        {recommendations.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {recommendations.map((rec, i) => (
              <button
                key={i}
                onClick={() => onFollowUp(rec)}
                className="text-xs px-3 py-1.5 rounded-full border bg-background hover:bg-primary hover:text-primary-foreground hover:border-primary transition-colors cursor-pointer"
              >
                {rec}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── QA Message Bubbles ───────────────────────────────────────────────────────

function QAAssistantMessage({
  message,
  onFollowUp,
}: {
  message: QAMessage;
  onFollowUp: (q: string) => void;
}) {
  const { t } = useI18n();
  const { response, error } = message;
  if (error) {
    return (
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 h-8 w-8 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertCircle className="h-4 w-4 text-destructive" aria-hidden="true" />
        </div>
        <div className="flex-1 rounded-2xl rounded-tl-sm bg-destructive/10 border border-destructive/20 px-4 py-3">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      </div>
    );
  }
  if (!response) return null;

  // Intent-aware rendering
  if (response.intent === 'preference') {
    return (
      <PreferenceAckCard insights={response.insights} recommendations={response.recommendations} />
    );
  }
  if (response.intent === 'other') {
    return (
      <OtherAckCard
        insights={response.insights}
        recommendations={response.recommendations}
        onFollowUp={onFollowUp}
      />
    );
  }
  return (
    <div className="flex items-start gap-3">
      <div
        className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center"
        aria-hidden="true"
      >
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 space-y-4 min-w-0">
        {response.articles && response.articles.length > 0 && (
          <section aria-label={t('chat.related-articles', { count: response.articles.length })}>
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
              {t('chat.related-articles', { count: response.articles.length })}
            </h3>
            <div className="space-y-2">
              {response.articles.map((a) => (
                <ArticleCard key={a.article_id} article={a} />
              ))}
            </div>
          </section>
        )}
        {response.insights && response.insights.length > 0 && (
          <section aria-label={t('chat.insights')}>
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              <Lightbulb className="h-3.5 w-3.5" aria-hidden="true" />
              {t('chat.insights')}
            </h3>
            <ul className="space-y-1.5 rounded-lg border bg-muted/30 px-4 py-3">
              {response.insights.map((insight, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-primary font-bold flex-shrink-0 mt-0.5">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
        {response.recommendations && response.recommendations.length > 0 && (
          <section aria-label={t('chat.further-reading')}>
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
              {t('chat.further-reading')}
            </h3>
            <div className="flex flex-wrap gap-2">
              {response.recommendations.map((rec, i) => (
                <button
                  key={i}
                  onClick={() => onFollowUp(rec)}
                  className={cn(
                    'text-xs px-3 py-1.5 rounded-full border',
                    'bg-background hover:bg-primary hover:text-primary-foreground hover:border-primary',
                    'transition-colors duration-200 cursor-pointer',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1'
                  )}
                  aria-label={t('chat.follow-up-aria', { question: rec })}
                >
                  {rec}
                </button>
              ))}
            </div>
          </section>
        )}
        {response.response_time > 0 && (
          <p className="text-xs text-muted-foreground/60">
            {t('chat.response-time', { seconds: response.response_time.toFixed(2) })}
          </p>
        )}
      </div>
    </div>
  );
}

function QAUserMessage({ content }: { content: string }) {
  return (
    <div className="flex items-start justify-end gap-3">
      <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-2.5">
        <p className="text-sm leading-relaxed">{content}</p>
      </div>
      <div
        className="flex-shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center"
        aria-hidden="true"
      >
        <User className="h-4 w-4 text-muted-foreground" />
      </div>
    </div>
  );
}

// ─── History Message Bubble ───────────────────────────────────────────────────

function HistoryMessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === 'user';
  let timeDisplay = '';
  try {
    const d = new Date(message.created_at);
    if (!isNaN(d.getTime())) timeDisplay = format(d, 'HH:mm');
  } catch {
    /* ignore */
  }

  return (
    <div className={cn('flex items-end gap-2', isUser ? 'flex-row-reverse' : 'flex-row')}>
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

// ─── Empty State ──────────────────────────────────────────────────────────────

function EmptyState({ onExampleClick }: { onExampleClick: (q: string) => void }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center justify-center h-full py-16 px-4 text-center">
      <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <Bot className="h-8 w-8 text-primary" aria-hidden="true" />
      </div>
      <h2 className="text-xl font-semibold mb-2">{t('chat.empty-title')}</h2>
      <p className="text-muted-foreground text-sm max-w-sm mb-8">{t('chat.empty-description')}</p>
      <div className="w-full max-w-md space-y-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          {t('chat.example-queries-label')}
        </p>
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => onExampleClick(q)}
            className={cn(
              'w-full text-left text-sm px-4 py-3 rounded-lg border',
              'bg-background hover:bg-muted/50 hover:border-primary/50',
              'transition-colors duration-200 cursor-pointer',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1'
            )}
            aria-label={t('chat.example-query-aria', { query: q })}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── History View ─────────────────────────────────────────────────────────────

function HistoryView({
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

function QAView({
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
