'use client';

import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { type ConversationMessage } from '@/lib/api/conversations';
import {
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
  Send,
} from 'lucide-react';
import { type ArticleSummary, type QAMessage, EXAMPLE_QUERIES } from '../types';
import { PlatformBadge } from './PlatformBadge';

export function ArticleCard({ article }: { article: ArticleSummary }) {
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

export function PreferenceAckCard({
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

export function OtherAckCard({
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

export function QAAssistantMessage({
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

export function QAUserMessage({ content }: { content: string }) {
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

export function HistoryMessageBubble({ message }: { message: ConversationMessage }) {
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

export function EmptyState({ onExampleClick }: { onExampleClick: (q: string) => void }) {
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
