'use client';

/**
 * 404 Not Found Page
 *
 * 美觀且專業的 404 錯誤頁面，提供友善的導航選項
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Home, Search, ArrowLeft, FileQuestion, Sparkles } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

export default function NotFound() {
  const [mounted, setMounted] = useState(false);
  const { t } = useI18n();

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleGoBack = () => {
    if (typeof window !== 'undefined' && window.history.length > 1) {
      window.history.back();
    } else if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-background via-background to-muted">
      {/* 背景裝飾 - 網格效果 */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />

      {/* 漸層光暈效果 */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />

      {/* 主要內容 */}
      <div className="container relative z-10 mx-auto flex min-h-screen flex-col items-center justify-center px-4 py-16">
        <div className="mx-auto max-w-2xl text-center space-y-8">
          {/* 圖示 */}
          <div className="flex justify-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="relative">
              <div className="absolute inset-0 blur-2xl bg-primary/20 rounded-full animate-pulse" />
              <div className="relative inline-flex p-6 rounded-full bg-primary/10 backdrop-blur-sm border border-primary/20">
                <FileQuestion className="h-20 w-20 text-primary" strokeWidth={1.5} />
              </div>
            </div>
          </div>

          {/* 404 數字 */}
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            <h1 className="text-8xl md:text-9xl font-bold tracking-tight bg-gradient-to-br from-foreground to-foreground/50 bg-clip-text text-transparent">
              404
            </h1>
          </div>

          {/* 固定訊息 */}
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            <p className="text-2xl md:text-3xl font-semibold">{t('pages-404.title')}</p>
            <p className="text-base md:text-lg text-muted-foreground max-w-md mx-auto leading-relaxed">
              {t('pages-404.description')}
            </p>
          </div>

          {/* 操作按鈕 */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
            <Link
              href="/"
              className="group inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium text-primary-foreground bg-primary rounded-lg hover:bg-primary/90 transition-all duration-300 hover:scale-[1.02] hover:shadow-md hover:shadow-primary/25"
            >
              <Home className="h-5 w-5 transition-transform group-hover:-translate-y-0.5" />
              {t('pages-404.back-to-home')}
            </Link>

            <Link
              href="/app/articles"
              className="group inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium border border-input bg-background/50 backdrop-blur-sm rounded-lg hover:bg-accent transition-all duration-300 hover:scale-[1.02] hover:shadow-md"
            >
              <Search className="h-5 w-5 transition-transform group-hover:rotate-12" />
              {t('pages-404.explore-news')}
            </Link>
          </div>

          {/* 建議卡片 */}
          <div className="mt-12 p-6 rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm text-left animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500 hover:border-border transition-colors">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">{t('pages-404.possible-reasons')}</h3>
            </div>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li className="flex items-start gap-3 group">
                <span className="text-primary mt-0.5 transition-transform group-hover:scale-125">
                  •
                </span>
                <span className="group-hover:text-foreground transition-colors">
                  {t('pages-404.reason-1')}
                </span>
              </li>
              <li className="flex items-start gap-3 group">
                <span className="text-primary mt-0.5 transition-transform group-hover:scale-125">
                  •
                </span>
                <span className="group-hover:text-foreground transition-colors">
                  {t('pages-404.reason-2')}
                </span>
              </li>
              <li className="flex items-start gap-3 group">
                <span className="text-primary mt-0.5 transition-transform group-hover:scale-125">
                  •
                </span>
                <span className="group-hover:text-foreground transition-colors">
                  {t('pages-404.reason-3')}
                </span>
              </li>
              <li className="flex items-start gap-3 group">
                <span className="text-primary mt-0.5 transition-transform group-hover:scale-125">
                  •
                </span>
                <span className="group-hover:text-foreground transition-colors">
                  {t('pages-404.reason-4')}
                </span>
              </li>
            </ul>
          </div>

          {/* 返回按鈕 */}
          <button
            onClick={handleGoBack}
            className="group inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-all duration-200 cursor-pointer animate-in fade-in duration-700 delay-700"
          >
            <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
            <span>{t('pages-404.go-back')}</span>
          </button>

          {/* 裝飾性元素 */}
          <div className="flex justify-center gap-2 pt-8 opacity-50">
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" />
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce delay-100" />
            <div className="w-2 h-2 rounded-full bg-primary animate-bounce delay-200" />
          </div>
        </div>
      </div>
    </div>
  );
}
