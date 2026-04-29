'use client';

// Shared types for ChatShell components
export interface ArticleSummary {
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

export interface QAResponse {
  query: string;
  articles: ArticleSummary[];
  insights: string[];
  recommendations: string[];
  conversation_id: string;
  response_time: number;
  intent?: 'question' | 'preference' | 'other';
}

export interface QAMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  response?: QAResponse;
  timestamp: Date;
  error?: string;
}

export const EXAMPLE_QUERIES = [
  '最近有哪些關於 AI 的文章？',
  'React 和 Vue 的比較有哪些討論？',
  '有什麼關於系統設計的深度文章？',
  '最新的 TypeScript 功能介紹',
];
