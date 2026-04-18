'use client';

/**
 * 404 Not Found Page - Simplified for build fix
 */

import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-6 p-8">
        <h1 className="text-6xl font-bold">404</h1>
        <p className="text-xl text-muted-foreground">找不到這個頁面</p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/"
            className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            回到首頁
          </Link>
          <Link
            href="/app/articles"
            className="px-6 py-3 border border-input rounded-md hover:bg-accent"
          >
            探索新聞
          </Link>
        </div>
      </div>
    </div>
  );
}
