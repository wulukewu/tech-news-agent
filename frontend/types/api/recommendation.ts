// Generated from recommendation.py
// Generated at: 2026-04-11T22:10:26.236403

/**
 * Recommended feed response model
 *
 * Represents a feed with recommendation metadata.
 * Used by GET /api/feeds/recommended endpoint.
 */
export interface RecommendedFeed {
  /** Feed UUID */
  id: string;
  /** Feed name */
  name: string;
  /** Feed RSS URL */
  url: string;
  /** Feed category (AI, Web Development, Security, etc.) */
  category: string;
  /** User-facing description of the feed content */
  description?: string | null;
  /** Whether this feed is recommended for new users */
  is_recommended: boolean;
  /** Priority for ordering (higher = more important) */
  recommendation_priority: number;
  /** Whether the current user is subscribed to this feed */
  is_subscribed: boolean;
}

/**
 * Response model for recommended feeds endpoint
 *
 * Returns both a flat list and grouped by category.
 */
export interface RecommendedFeedsResponse {
  /** All recommended feeds sorted by priority */
  feeds: RecommendedFeed[];
  /** Feeds grouped by category, each group sorted by priority */
  grouped_by_category: Record<string, any>;
  /** Total number of recommended feeds */
  total_count: number;
}

/**
 * Request model for updating feed recommendation status
 *
 * Used by admin endpoints to manage recommended feeds.
 */
export interface UpdateRecommendationStatusRequest {
  /** Whether the feed should be recommended */
  is_recommended: boolean;
  /** Priority for ordering (0-1000, higher = more important) */
  recommendation_priority: number;
}

/**
 * Response model for feeds grouped by category
 *
 * Used by subscription page to display feeds in collapsible sections.
 */
export interface FeedsByCategoryResponse {
  /** Category name */
  category: string;
  /** Feeds in this category sorted by priority */
  feeds: RecommendedFeed[];
  /** Number of feeds in this category */
  feed_count: number;
}
