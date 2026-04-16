/**
 * ArticleBrowser Component Usage Examples
 *
 * This file demonstrates various ways to use the ArticleBrowser component
 * with different configurations and features.
 */

import React from 'react';
import { ArticleBrowser } from './ArticleBrowser';
import type { ArticleFilters } from '@/types/article';

// Example 1: Basic usage with default settings
export function BasicArticleBrowser() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">所有文章</h1>
      <ArticleBrowser />
    </div>
  );
}

// Example 2: With initial filters
export function FilteredArticleBrowser() {
  const initialFilters: ArticleFilters = {
    category: 'tech',
    minTinkeringIndex: 3,
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">技術文章 (評分 3+ 星)</h1>
      <ArticleBrowser initialFilters={initialFilters} pageSize={15} />
    </div>
  );
}

// Example 3: With virtual scrolling enabled
export function VirtualizedArticleBrowser() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">大量文章瀏覽 (虛擬滾動)</h1>
      <ArticleBrowser enableVirtualization={true} pageSize={50} />
    </div>
  );
}

// Example 4: With custom callbacks and button configuration
export function InteractiveArticleBrowser() {
  const handleAnalyze = (articleId: string) => {
    console.log('Analyzing article:', articleId);
    // Open analysis modal or navigate to analysis page
  };

  const handleAddToReadingList = (articleId: string) => {
    console.log('Adding to reading list:', articleId);
    // Add to reading list with custom logic
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">互動式文章瀏覽</h1>
      <ArticleBrowser
        showAnalysisButtons={true}
        showReadingListButtons={true}
        onAnalyze={handleAnalyze}
        onAddToReadingList={handleAddToReadingList}
        className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg"
      />
    </div>
  );
}

// Example 5: Analysis-focused browser (only show analysis buttons)
export function AnalysisFocusedBrowser() {
  const handleAnalyze = (articleId: string) => {
    // Navigate to analysis page or open modal
    window.location.href = `/articles/${articleId}/analysis`;
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">深度分析模式</h1>
      <p className="text-muted-foreground mb-4">每頁最多顯示 5 個「Deep Dive Analysis」按鈕</p>
      <ArticleBrowser
        showAnalysisButtons={true}
        showReadingListButtons={false}
        onAnalyze={handleAnalyze}
      />
    </div>
  );
}

// Example 6: Reading list focused browser
export function ReadingListFocusedBrowser() {
  const handleAddToReadingList = (articleId: string) => {
    // Custom reading list logic
    console.log('Adding to reading list:', articleId);
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">閱讀清單模式</h1>
      <p className="text-muted-foreground mb-4">每頁最多顯示 10 個「Add to Reading List」按鈕</p>
      <ArticleBrowser
        showAnalysisButtons={false}
        showReadingListButtons={true}
        onAddToReadingList={handleAddToReadingList}
      />
    </div>
  );
}

// Example 7: Compact view with smaller page size
export function CompactArticleBrowser() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">精簡檢視</h1>
      <ArticleBrowser pageSize={10} className="max-w-4xl" />
    </div>
  );
}

// Example 8: High-performance browser for large datasets
export function HighPerformanceBrowser() {
  const initialFilters: ArticleFilters = {
    minTinkeringIndex: 4, // Only high-quality articles
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">高效能瀏覽器</h1>
      <p className="text-muted-foreground mb-4">針對大量資料優化，啟用虛擬滾動和篩選</p>
      <ArticleBrowser
        initialFilters={initialFilters}
        enableVirtualization={true}
        pageSize={100}
        showAnalysisButtons={true}
        showReadingListButtons={true}
      />
    </div>
  );
}
