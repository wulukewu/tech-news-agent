/**
 * Article type definitions
 *
 * Validates Requirements 10.3, 10.4:
 * - 10.3: EACH article card SHALL display: title, feed name, category, published date, tinkering index, and AI summary
 * - 10.4: THE page SHALL support pagination with "Load More" button or infinite scroll
 */

/**
 * Article interface representing a single article from an RSS feed
 */
export interface Article {
  /** Unique identifier for the article */
  id: string;
  /** Article title */
  title: string;
  /** Original article URL */
  url: string;
  /** Name of the feed this article belongs to */
  feedName: string;
  /** Category classification (e.g., "AI", "Web Development") */
  category: string;
  /** ISO 8601 timestamp of when the article was published, or null if unknown */
  publishedAt: string | null;
  /** Tinkering index rating (1-5 scale) indicating article relevance/quality */
  tinkeringIndex: number;
  /** AI-generated summary of the article content, or null if not available */
  aiSummary: string | null;
}

/**
 * Response from article list API with pagination metadata
 */
export interface ArticleListResponse {
  /** Array of articles for the current page */
  articles: Article[];
  /** Current page number (1-indexed) */
  page: number;
  /** Number of articles per page */
  pageSize: number;
  /** Total number of articles available */
  totalCount: number;
  /** Whether there are more articles to load */
  hasNextPage: boolean;
}

/**
 * Filter options for article queries
 */
export interface ArticleFilters {
  /** Filter by category (optional) */
  category?: string;
  /** Minimum tinkering index (1-5, optional) */
  minTinkeringIndex?: number;
  /** Maximum tinkering index (1-5, optional) */
  maxTinkeringIndex?: number;
}
