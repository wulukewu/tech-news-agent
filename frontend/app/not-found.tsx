'use client';

/**
 * 404 Not Found Page
 *
 * Custom 404 error page with a friendly message and navigation options.
 * Matches the overall design system of the application.
 *
 * Features:
 * - Clean, professional design
 * - Helpful navigation options
 * - Responsive layout
 * - Accessible keyboard navigation
 * - Does not redirect to login (even for /dashboard/* paths)
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Home, Search, ArrowLeft, FileQuestion } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useNotFound } from '@/contexts/NotFoundContext';

export default function NotFound() {
  const { setIsNotFound } = useNotFound();

  // Mark this as a 404 page to prevent auth redirect
  useEffect(() => {
    setIsNotFound(true);
    return () => setIsNotFound(false);
  }, [setIsNotFound]);
  const messages = ['找不到這個頁面', '頁面不存在', '這個頁面可能已被移除', '網址可能有誤'];

  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-background via-background to-muted">
      {/* Background decoration - matching landing page style */}
      <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]" />

      {/* Main content */}
      <div className="container relative z-10 mx-auto flex min-h-screen flex-col items-center justify-center px-4 py-16">
        <div className="mx-auto max-w-2xl text-center space-y-8">
          {/* Icon */}
          <div className="flex justify-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="relative">
              <div className="absolute inset-0 blur-3xl bg-primary/20 rounded-full" />
              <div className="relative inline-flex p-6 rounded-full bg-primary/10 text-primary">
                <FileQuestion className="h-24 w-24" />
              </div>
            </div>
          </div>

          {/* 404 Number */}
          <h1 className="text-8xl md:text-9xl font-bold tracking-tight animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            404
          </h1>

          {/* Message */}
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            <p className="text-2xl md:text-3xl font-semibold transition-all duration-500">
              {messages[messageIndex]}
            </p>
            <p className="text-base md:text-lg text-muted-foreground max-w-md mx-auto">
              您訪問的頁面不存在或已被移除。請檢查網址是否正確，或返回首頁繼續瀏覽。
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
            <Link href="/">
              <Button size="lg" className="text-base px-8 py-6 h-auto group w-full sm:w-auto">
                <Home className="mr-2 h-5 w-5" />
                回到首頁
              </Button>
            </Link>
            <Link href="/app/articles">
              <Button
                size="lg"
                variant="outline"
                className="text-base px-8 py-6 h-auto group w-full sm:w-auto"
              >
                <Search className="mr-2 h-5 w-5" />
                探索新聞
              </Button>
            </Link>
          </div>

          {/* Helpful suggestions card */}
          <Card className="mt-12 text-left animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500">
            <CardHeader>
              <CardTitle className="text-lg">可能的原因</CardTitle>
              <CardDescription>以下是一些常見的情況</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>網址輸入錯誤或包含拼寫錯誤</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>頁面已被移動或刪除</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>連結已過期或失效</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>您沒有訪問此頁面的權限</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Back button */}
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground cursor-pointer animate-in fade-in duration-700 delay-700"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>返回上一頁</span>
          </button>
        </div>
      </div>
    </div>
  );
}
