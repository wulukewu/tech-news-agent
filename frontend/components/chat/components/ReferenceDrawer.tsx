'use client';

import React, { useState } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import {
  BookOpen,
  Copy,
  Check,
  ExternalLink,
  MessageSquare,
  Sparkles,
  ChevronDown,
  Clock,
  Zap,
} from 'lucide-react';

export interface DrawerArticle {
  id: string;
  title: string;
  url: string;
  summary: string | null;
  category: string;
  tinkeringIndex: number;
  readingTime?: number;
  keyInsights?: string[];
  actionableTakeaway?: string | null;
  feedName?: string;
  publishedAt?: string | null;
}

interface ReferenceDrawerProps {
  articles: DrawerArticle[];
  selectedArticleId: string | null;
  onSelectArticle: (id: string) => void;
  onQuickAsk: (prompt: string) => void;
  onClose: () => void;
}

export function ReferenceDrawer({
  articles,
  selectedArticleId,
  onSelectArticle,
  onQuickAsk,
  className,
}: ReferenceDrawerProps & { className?: string }) {
  const { t } = useI18n();
  const [copiedStates, setCopiedStates] = useState<{ [key: string]: boolean }>({});
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Active article based on selected id or fallback to first
  const activeArticle = articles.find((a) => a.id === selectedArticleId) || articles[0] || null;

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedStates((prev) => ({ ...prev, [key]: true }));
    setTimeout(() => {
      setCopiedStates((prev) => ({ ...prev, [key]: false }));
    }, 2000);
  };

  const getTinkeringColor = (index: number) => {
    if (index >= 4) return 'bg-red-500/10 text-red-500 border-red-500/20';
    if (index >= 3)
      return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-500 border-yellow-500/20';
    return 'bg-green-500/10 text-green-500 border-green-500/20';
  };

  const getRelevanceColor = (score?: number) => {
    if (!score) return 'bg-primary/10 text-primary';
    if (score >= 80) return 'bg-emerald-500/10 text-emerald-500';
    if (score >= 50) return 'bg-blue-500/10 text-blue-500';
    return 'bg-muted text-muted-foreground';
  };

  // Pre-configured templates for quick asking
  const quickQuestions = activeArticle
    ? [
        {
          label: t('chat.quick-prompt-conclusion', { defaultValue: '摘要文章三個核心結論' }),
          prompt: `請幫我分析《${activeArticle.title}》這篇文章，並整理出三個最核心的結論與技術重點。`,
        },
        {
          label: t('chat.quick-prompt-practice', { defaultValue: '詢問具體實作範例' }),
          prompt: `關於《${activeArticle.title}》中提到的技術，在實際生產環境中有哪些具體的實作範例或最佳實踐（Best Practices）？`,
        },
        {
          label: t('chat.quick-prompt-background', { defaultValue: '適合哪種技術背景？' }),
          prompt: `這篇文章中所討論的架構與技術，通常適合什麼樣技術背景的開發者閱讀？需要哪些前置知識？`,
        },
        {
          label: t('chat.quick-prompt-roadmap', { defaultValue: '生成相關學習路徑' }),
          prompt: `請針對《${activeArticle.title}》涉及的主題（${activeArticle.category}），為我規劃一個循序漸進的實用學習路徑與推薦資源。`,
        },
      ]
    : [];

  return (
    <aside
      className={cn(
        'flex flex-col border-l bg-background/80 backdrop-blur-md w-full md:w-[360px] lg:w-[400px] flex-shrink-0 overflow-hidden relative transition-all duration-300 shadow-xl',
        className
      )}
      aria-label={t('chat.contextual-drawer-label', { defaultValue: '參考文章詳情' })}
    >
      {/* Title Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-background/50 backdrop-blur">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
          {t('chat.contextual-drawer-title', { defaultValue: '參考文章' })}
        </h2>
        {articles.length > 0 && (
          <Badge variant="outline" className="text-xs bg-primary/5">
            {articles.length}
          </Badge>
        )}
      </div>

      {articles.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 p-6 text-center text-muted-foreground">
          <BookOpen className="h-10 w-10 text-muted/30 mb-3 stroke-[1.5]" />
          <p className="text-sm">
            {t('chat.no-reference-article', {
              defaultValue: '此對話內容中尚無參考文章。',
            })}
          </p>
        </div>
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Article Switcher Dropdown (if multiple articles exist) */}
          {articles.length > 1 && (
            <div className="p-3 border-b bg-muted/10 relative z-50">
              <button
                onClick={() => setDropdownOpen((o) => !o)}
                className="w-full flex items-center justify-between px-3 py-2 bg-background border rounded-lg text-sm hover:border-primary transition-all duration-200 shadow-sm text-left font-medium text-foreground cursor-pointer"
              >
                <span className="truncate flex-1 pr-2">{activeArticle?.title}</span>
                <ChevronDown
                  className={cn(
                    'h-4 w-4 text-muted-foreground transition-transform duration-200 flex-shrink-0',
                    dropdownOpen && 'rotate-180'
                  )}
                />
              </button>
              {dropdownOpen && (
                <div className="absolute top-[calc(100%-4px)] left-3 right-3 mt-1 bg-popover border rounded-lg shadow-xl overflow-hidden max-h-60 overflow-y-auto animate-in fade-in slide-in-from-top-1 duration-150 z-[100]">
                  {articles.map((art) => (
                    <button
                      key={art.id}
                      onClick={() => {
                        onSelectArticle(art.id);
                        setDropdownOpen(false);
                      }}
                      className={cn(
                        'w-full text-left px-3 py-2 text-xs border-b last:border-b-0 hover:bg-muted transition-colors truncate block cursor-pointer',
                        art.id === activeArticle?.id
                          ? 'bg-primary/5 font-semibold text-primary'
                          : 'text-foreground'
                      )}
                    >
                      {art.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeArticle && (
            <ScrollArea className="flex-1">
              <div className="p-4 flex flex-col gap-5">
                {/* Meta details */}
                <div className="flex flex-wrap items-center gap-1.5 text-xs">
                  {/* Category badge */}
                  <Badge
                    variant="secondary"
                    className="bg-primary/5 text-primary border border-primary/10"
                  >
                    {activeArticle.category}
                  </Badge>

                  {/* Feed name */}
                  {activeArticle.feedName && (
                    <span className="text-muted-foreground border-r pr-2 py-0.5 max-w-[120px] truncate">
                      {activeArticle.feedName}
                    </span>
                  )}

                  {/* Reading Time */}
                  {activeArticle.readingTime && (
                    <span className="text-muted-foreground flex items-center gap-1 border-r pr-2 py-0.5">
                      <Clock className="h-3 w-3" />
                      {t('chat.read-minutes', {
                        minutes: activeArticle.readingTime,
                        defaultValue: `${activeArticle.readingTime} 分鐘閱讀`,
                      })}
                    </span>
                  )}

                  {/* Tinkering Index */}
                  <span
                    className={cn(
                      'px-2 py-0.5 rounded-full text-[10px] font-medium border flex items-center gap-0.5',
                      getTinkeringColor(activeArticle.tinkeringIndex)
                    )}
                  >
                    <Zap className="h-2.5 w-2.5 fill-current" />
                    {t('chat.tinkering-index', {
                      value: activeArticle.tinkeringIndex,
                      defaultValue: `技術深度：${activeArticle.tinkeringIndex}`,
                    })}
                  </span>
                </div>

                {/* Article Title */}
                <div>
                  <a
                    href={activeArticle.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group text-base font-semibold leading-snug text-foreground hover:text-primary transition-colors flex items-start gap-1"
                    aria-label={t('chat.article-read-aria', {
                      title: activeArticle.title,
                      defaultValue: `閱讀文章：${activeArticle.title}`,
                    })}
                  >
                    <span className="group-hover:underline">{activeArticle.title}</span>
                    <ExternalLink className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary opacity-70 group-hover:opacity-100 flex-shrink-0 mt-1 transition-all" />
                  </a>
                </div>

                {/* AI Summary Section */}
                {activeArticle.summary && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center justify-between">
                      <span>{t('chat.article-summary', { defaultValue: 'AI 摘要' })}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(activeArticle.summary!, 'summary')}
                        className="h-6 px-1.5 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
                        aria-label={t('chat.copy-to-clipboard', { defaultValue: '複製到剪貼簿' })}
                      >
                        {copiedStates['summary'] ? (
                          <Check className="h-3 w-3 text-emerald-500 mr-1" />
                        ) : (
                          <Copy className="h-3 w-3 mr-1" />
                        )}
                        {copiedStates['summary']
                          ? t('chat.copied', { defaultValue: '已複製！' })
                          : t('chat.copy-to-clipboard', { defaultValue: '複製' })}
                      </Button>
                    </h3>
                    <div className="text-sm text-foreground bg-muted/30 border border-muted/50 rounded-xl p-3.5 leading-relaxed whitespace-pre-line shadow-inner">
                      {activeArticle.summary}
                    </div>
                  </div>
                )}

                {/* 1-sec technical takeaway */}
                {activeArticle.actionableTakeaway && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center justify-between">
                      <span>{t('chat.article-takeaway', { defaultValue: '核心技術精華' })}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(activeArticle.actionableTakeaway!, 'takeaway')}
                        className="h-6 px-1.5 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
                      >
                        {copiedStates['takeaway'] ? (
                          <Check className="h-3 w-3 text-emerald-500 mr-1" />
                        ) : (
                          <Copy className="h-3 w-3 mr-1" />
                        )}
                        {copiedStates['takeaway']
                          ? t('chat.copied', { defaultValue: '已複製！' })
                          : t('chat.copy-to-clipboard', { defaultValue: '複製' })}
                      </Button>
                    </h3>
                    <div className="text-sm font-medium text-primary bg-primary/5 border border-primary/10 rounded-xl p-3.5 leading-relaxed shadow-sm">
                      {activeArticle.actionableTakeaway}
                    </div>
                  </div>
                )}

                {/* Key Insights bullet points (if QA search result has them) */}
                {activeArticle.keyInsights && activeArticle.keyInsights.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {t('chat.article-key-insights', { defaultValue: '核心要點' })}
                    </h3>
                    <div className="flex flex-col gap-2.5">
                      {activeArticle.keyInsights.map((insight, idx) => (
                        <div
                          key={idx}
                          className="group/item flex flex-col gap-2 p-3 bg-muted/20 hover:bg-muted/40 border rounded-xl transition-all duration-200"
                        >
                          <p className="text-xs text-foreground leading-relaxed">{insight}</p>
                          <div className="flex items-center justify-end gap-1.5 opacity-60 group-hover/item:opacity-100 transition-opacity">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCopy(insight, `insight-${idx}`)}
                              className="h-6 px-2 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
                            >
                              {copiedStates[`insight-${idx}`] ? (
                                <Check className="h-3 w-3 text-emerald-500 mr-1" />
                              ) : (
                                <Copy className="h-3 w-3 mr-1" />
                              )}
                              {copiedStates[`insight-${idx}`] ? '已複製' : '複製'}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                onQuickAsk(`關於此要點「${insight}」，請幫我深入分析...`)
                              }
                              className="h-6 px-2 text-[10px] text-primary hover:bg-primary/5 hover:text-primary cursor-pointer flex items-center gap-1"
                            >
                              <MessageSquare className="h-3 w-3" />
                              {t('chat.quick-ask', { defaultValue: '快速提問' })}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quick Prompts Recommendations (Always helpful for interactions) */}
                <div className="space-y-2 pt-2 border-t border-muted/50">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    <span>{t('chat.quick-prompts', { defaultValue: '推薦快速提問' })}</span>
                  </h3>
                  <div className="flex flex-col gap-2">
                    {quickQuestions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => onQuickAsk(q.prompt)}
                        className="text-left text-xs p-2.5 rounded-xl border border-muted/60 bg-background hover:bg-primary/5 hover:text-primary hover:border-primary/20 transition-all duration-200 shadow-sm cursor-pointer block font-medium"
                      >
                        {q.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </ScrollArea>
          )}
        </div>
      )}
    </aside>
  );
}
