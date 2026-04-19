'use client';

/**
 * Demo page for testing the AnalysisModal component
 *
 * This page provides a simple interface to test the AI analysis
 * modal functionality with mock data.
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AnalysisTrigger } from '@/features/ai-analysis/components';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useI18n } from '@/contexts/I18nContext';

// Create a query client for the demo
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 5 * 60 * 1000,
    },
  },
});

const mockArticles = [
  {
    id: 'demo-article-1',
    title: 'React 18 新功能深度解析：Concurrent Features 完整指南',
    source: 'React 官方部落格',
    publishedAt: '2024-01-15T10:30:00Z',
    category: '前端開發',
    summary:
      '深入探討 React 18 的並發功能，包括 Suspense、useTransition 和 useDeferredValue 的實際應用場景。',
  },
  {
    id: 'demo-article-2',
    title: 'TypeScript 5.0 重大更新：Decorators 和 const Type Parameters',
    source: 'TypeScript 團隊',
    publishedAt: '2024-01-10T14:20:00Z',
    category: '程式語言',
    summary: '探索 TypeScript 5.0 的新功能，重點介紹裝飾器語法和常數型別參數的使用方式。',
  },
  {
    id: 'demo-article-3',
    title: 'Next.js 14 App Router 效能優化最佳實踐',
    source: 'Vercel 工程團隊',
    publishedAt: '2024-01-05T09:15:00Z',
    category: '全端開發',
    summary:
      '詳細介紹 Next.js 14 App Router 的效能優化技巧，包括 Server Components 和 Streaming 的應用。',
  },
];

export default function AnalysisDemoPage() {
  const { t } = useI18n();

  return (
    <QueryClientProvider client={queryClient}>
      <div className="container mx-auto py-8 px-4">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-bold">{t('demo.ai-analysis')}</h1>
            <p className="text-muted-foreground">{t('demo.description')}</p>
          </div>

          <div className="grid gap-6">
            {mockArticles.map((article) => (
              <Card key={article.id} className="w-full">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <CardTitle className="text-lg leading-tight">{article.title}</CardTitle>
                      <CardDescription className="flex items-center gap-4 text-sm">
                        <span>{article.source}</span>
                        <span>•</span>
                        <span>{article.category}</span>
                        <span>•</span>
                        <span>{new Date(article.publishedAt).toLocaleDateString('zh-TW')}</span>
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground leading-relaxed">{article.summary}</p>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">
                        {t('demo.technical-depth')}:
                      </span>
                      <div className="flex">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <span
                            key={i}
                            className={`text-sm ${i < 4 ? 'text-yellow-400' : 'text-gray-300'}`}
                          >
                            ★
                          </span>
                        ))}
                      </div>
                    </div>

                    <AnalysisTrigger
                      articleId={article.id}
                      articleTitle={article.title}
                      articleSource={article.source}
                      articlePublishedAt={article.publishedAt}
                      variant="default"
                      size="sm"
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mt-12 p-6 bg-muted/50 rounded-lg">
            <h2 className="text-lg font-semibold mb-3">{t('demo.sample-articles')}</h2>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>
                • <strong>{t('demo.beginner')}</strong>: {t('demo.intermediate')}
              </p>
              <p>
                • <strong>{t('demo.advanced')}</strong>: {t('demo.expert')}
              </p>
              <p>
                • <strong>{t('demo.master')}</strong>: {t('demo.guru')}
              </p>
              <p>
                • <strong>{t('demo.beginner')}</strong>: {t('demo.intermediate')}
              </p>
              <p>
                • <strong>{t('demo.advanced')}</strong>: {t('demo.expert')}
              </p>
              <p>
                • <strong>{t('demo.master')}</strong>: {t('demo.guru')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </QueryClientProvider>
  );
}
