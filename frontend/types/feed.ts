/**
 * Feed type definitions
 *
 * Validates Requirements 8.3, 8.4:
 * - 8.3: EACH feed card SHALL display: feed name, category, URL, and subscription status
 * - 8.4: WHEN a user toggles a subscription, THE System SHALL call POST /api/subscriptions/toggle
 */

/**
 * Feed interface representing an RSS feed source
 */
export interface Feed {
  /** Unique identifier for the feed */
  id: string;
  /** Display name of the feed */
  name: string;
  /** RSS feed URL */
  url: string;
  /** Category classification (e.g., "AI", "Web Development") */
  category: string;
  /** Whether the current user is subscribed to this feed */
  is_subscribed: boolean;
  /** Whether this feed is recommended for new users */
  is_recommended?: boolean;
  /** Priority for recommendation sorting (higher = more recommended) */
  recommendation_priority?: number;
  /** Description of the feed */
  description?: string;
  /** Last update time */
  last_updated?: string | null;
  /** Feed health status */
  health_status?: 'healthy' | 'warning' | 'error' | 'unknown';
  /** Error message if feed has issues */
  error_message?: string;
  /** Total number of articles from this feed */
  total_articles?: number;
  /** Number of articles published this week */
  articles_this_week?: number;
  /** Average tinkering index of articles from this feed */
  average_tinkering_index?: number;
  /** Custom tags for feed organization */
  tags?: string[];
  /** Notification preferences for this feed */
  notification_enabled?: boolean;
}

/**
 * Request payload for toggling subscription status
 */
export interface SubscriptionToggleRequest {
  /** Feed ID to toggle subscription for */
  feed_id: string;
}

/**
 * Response from subscription toggle API
 */
export interface SubscriptionToggleResponse {
  /** Feed ID that was toggled */
  feed_id: string;
  /** New subscription status after toggle */
  is_subscribed: boolean;
}
