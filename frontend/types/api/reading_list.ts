// Generated from reading_list.py
// Generated at: 2026-04-11T22:10:26.234505

/**
 * 加入文章到閱讀清單請求
 */
export interface AddToReadingListRequest {
  /** 文章 UUID */
  article_id: string;
}

/**
 * 更新評分請求
 */
export interface UpdateRatingRequest {
  /** 評分（1-5）或 null 清除評分 */
  rating?: number | null;
}

/**
 * 更新閱讀狀態請求
 */
export interface UpdateStatusRequest {
  /** 閱讀狀態 */
  status: string;
}

/**
 * 閱讀清單項目回應
 */
export interface ReadingListItemResponse {
  /** 文章 UUID */
  articleId: string;
  /** 文章標題 */
  title: string;
  /** 文章 URL */
  url: string;
  /** 分類 */
  category: string;
  /** 閱讀狀態 */
  status: string;
  /** 評分（1-5） */
  rating?: number | null;
  /** 加入時間 */
  addedAt: string;
  /** 更新時間 */
  updatedAt: string;
}

/**
 * 閱讀清單回應（含分頁）
 */
export interface ReadingListResponse {
  /** 閱讀清單項目 */
  items: ReadingListItemResponse[];
  /** 當前頁碼 */
  page: number;
  /** 每頁項目數 */
  pageSize: number;
  /** 總項目數 */
  totalCount: number;
  /** 是否有下一頁 */
  hasNextPage: boolean;
}

/**
 * 通用訊息回應
 */
export interface MessageResponse {
  /** 回應訊息 */
  message: string;
  /** 文章 UUID */
  articleId?: string | null;
  /** 評分 */
  rating?: number | null;
  /** 狀態 */
  status?: string | null;
}
