// Generated from article.py
// Generated at: 2026-04-11T22:10:26.238050

export interface RSSSource {
  id: string;
  name: string;
  url: string;
  category: string;
}

export interface AIAnalysis {
  /** Whether the article is recommended or discarded */
  is_hardcore: boolean;
  /** A one-sentence explanation of why it was recommended or discarded */
  reason: string;
  /** The actionable value extracted (can be empty if discarded) */
  actionable_takeaway: string | null;
  /** Tinkering index (1-5) indicating technical complexity */
  tinkering_index: number;
}

/**
 * 文章資料模型（更新以匹配 Supabase 結構）
 */
export interface ArticleSchema {
  id: string | null;
  title: string;
  url: string;
  feed_id: string;
  feed_name: string;
  category: string;
  published_at: string | null;
  created_at: string;
  tinkering_index?: number | null;
  ai_summary?: string | null;
  ai_analysis: AIAnalysis | null;
  embedding: number[] | null;
}

export interface ArticlePageResult {
  page_id: string;
  page_url: string;
  title: string;
  category: string;
  tinkering_index: number;
}

export interface ReadingListItem {
  article_id: string;
  title: string;
  url: string;
  category: string;
  status: string;
  rating: number | null;
  added_at: string;
  updated_at: string;
}

/**
 * 批次操作結果
 */
export interface BatchResult {
  /** 成功插入的記錄數 */
  inserted_count: number;
  /** 成功更新的記錄數 */
  updated_count: number;
  /** 失敗的記錄數 */
  failed_count: number;
  /** 失敗的文章資訊（包含錯誤原因） */
  failed_articles: Array<Record<string, any>>;
}

/**
 * 使用者訂閱資訊
 */
export interface Subscription {
  feed_id: string;
  name: string;
  url: string;
  category: string;
  subscribed_at: string;
}

/**
 * 文章回應（用於 API）
 */
export interface ArticleResponse {
  /** 文章 UUID */
  id: string;
  /** 文章標題 */
  title: string;
  /** 文章 URL */
  url: string;
  /** 發布時間 */
  published_at?: string | null;
  /** 技術複雜度（1-5） */
  tinkering_index: number;
  /** AI 摘要 */
  ai_summary?: string | null;
  /** 來源名稱 */
  feed_name: string;
  /** 分類 */
  category: string;
}

/**
 * 文章列表回應（含分頁）
 */
export interface ArticleListResponse {
  /** 文章列表 */
  articles: ArticleResponse[];
  /** 當前頁碼 */
  page: number;
  /** 每頁文章數 */
  page_size: number;
  /** 總文章數 */
  total_count: number;
  /** 是否有下一頁 */
  has_next_page: boolean;
}
