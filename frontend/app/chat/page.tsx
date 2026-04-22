'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api/client';
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
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ArticleSummary {
  article_id: string;
  title: string;
  summary: string;
  url: string;
  relevance_score: number;
  reading_time: number;
  key_insights: string[];
  published_at: string | null;
  category: string;
}

interface QAResponse {
  query: string;
  articles: ArticleSummary[];
  insights: string[];
  recommendations: string[];
  conversation_id: string;
  response_time: number;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  response?: QAResponse;
  timestamp: Date;
  error?: string;
}

// ─── Example queries ──────────────────────────────────────────────────────────

const EXAMPLE_QUERIES = [
  '最近有哪些關於 AI 的文章？',
  'React 和 Vue 的比較有哪些討論？',
  '有什麼關於系統設計的深度文章？',
  '最新的 TypeScript 功能介紹',
];

// ─── Sub-components ───────────────────────────────────────────────────────────

function ArticleCard({ article }: { article: ArticleSummary }) {
  return (
    <div className="rounded-lg border bg-background p-4 space-y-2 hover:shadow-md transition-shadow duration-200">
      {/* Title + category + reading time */}
      <div className="flex items-start justify-between gap-2">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-semibold text-primary hover:underline leading-snug flex-1 cursor-pointer"
          aria-label={`閱讀文章：${article.title}`}
        >
          {article.title}
        </a>
        <ExternalLink
          className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0 mt-0.5"
          aria-hidden="true"
        />
      </div>

      {/* Badges row */}
      <div className="flex flex-wrap items-center gap-1.5">
        {article.category && (
          <Badge variant="secondary" className="text-xs">
            {article.category}
          </Badge>
        )}
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" aria-hidden="true" />
          {article.reading_time} 分鐘
        </span>
        {article.relevance_score > 0 && (
          <span className="text-xs text-muted-foreground">
            相關度 {Math.round(article.relevance_score * 100)}%
          </span>
        )}
      </div>

      {/* Summary */}
      <p className="text-xs text-muted-foreground leading-relaxed">{article.summary}</p>

      {/* Key insights */}
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

function AssistantMessage({
  message,
  onFollowUp,
}: {
  message: ChatMessage;
  onFollowUp: (query: string) => void;
}) {
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

  return (
    <div className="flex items-start gap-3">
      {/* Avatar */}
      <div
        className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center"
        aria-hidden="true"
      >
        <Bot className="h-4 w-4 text-primary" />
      </div>

      {/* Content bubble */}
      <div className="flex-1 space-y-4 min-w-0">
        {/* Articles */}
        {response.articles && response.articles.length > 0 && (
          <section aria-label="相關文章">
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
              相關文章 ({response.articles.length})
            </h3>
            <div className="space-y-2">
              {response.articles.map((article) => (
                <ArticleCard key={article.article_id} article={article} />
              ))}
            </div>
          </section>
        )}

        {/* Insights */}
        {response.insights && response.insights.length > 0 && (
          <section aria-label="洞察">
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              <Lightbulb className="h-3.5 w-3.5" aria-hidden="true" />
              洞察
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

        {/* Recommendations / follow-up chips */}
        {response.recommendations && response.recommendations.length > 0 && (
          <section aria-label="延伸閱讀建議">
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
              延伸閱讀
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
                  aria-label={`追問：${rec}`}
                >
                  {rec}
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Response time */}
        {response.response_time > 0 && (
          <p className="text-xs text-muted-foreground/60">
            回應時間 {response.response_time.toFixed(2)}s
          </p>
        )}
      </div>
    </div>
  );
}

function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="flex items-start justify-end gap-3">
      <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-2.5">
        <p className="text-sm leading-relaxed">{message.content}</p>
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

function EmptyState({ onExampleClick }: { onExampleClick: (q: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-16 px-4 text-center">
      <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <Bot className="h-8 w-8 text-primary" aria-hidden="true" />
      </div>
      <h2 className="text-xl font-semibold mb-2">智能問答助理</h2>
      <p className="text-muted-foreground text-sm max-w-sm mb-8">
        用自然語言提問，我會從您的文章庫中找到最相關的內容，並提供結構化的回答。
      </p>

      <div className="w-full max-w-md space-y-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          試試這些問題
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
            aria-label={`使用範例問題：${q}`}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

function ChatPageContent() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);

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
        const errorMsg = err instanceof Error ? err.message : '發生錯誤，請稍後再試。';

        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          type: 'assistant',
          content: '',
          timestamp: new Date(),
          error: `無法取得回答：${errorMsg}`,
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
            <h1 className="text-lg font-semibold leading-tight">智能問答</h1>
            <p className="text-xs text-muted-foreground">基於您的文章庫進行語義搜尋與智能回答</p>
          </div>
          {conversationId && (
            <Badge variant="outline" className="ml-auto text-xs">
              對話進行中
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
            aria-label="關閉錯誤訊息"
          >
            關閉
          </button>
        </div>
      )}

      {/* Messages area */}
      <main
        className="flex-1 overflow-y-auto px-4 py-4 space-y-6"
        aria-label="對話歷史"
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
              <div className="flex items-start gap-3" role="status" aria-label="正在生成回答">
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" aria-hidden="true" />
                </div>
                <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
                  <Loader2
                    className="h-4 w-4 animate-spin text-muted-foreground"
                    aria-hidden="true"
                  />
                  <span className="text-sm text-muted-foreground">正在搜尋並生成回答...</span>
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
        <form onSubmit={handleSubmit} className="flex items-center gap-2" aria-label="訊息輸入">
          <label htmlFor="chat-input" className="sr-only">
            輸入您的問題
          </label>
          <Input
            id="chat-input"
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="輸入您的問題，按 Enter 送出..."
            disabled={isLoading}
            autoComplete="off"
            aria-label="輸入您的問題"
            className="flex-1 min-h-10 md:min-h-10 resize-none"
          />
          <Button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            aria-label="送出問題"
            className="flex-shrink-0 cursor-pointer"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="sr-only">{isLoading ? '送出中' : '送出'}</span>
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-1.5 text-center">
          支援中文與英文查詢 · 按 Enter 送出
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
