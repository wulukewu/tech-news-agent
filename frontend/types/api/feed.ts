// Generated from feed.py
// Generated at: 2026-04-11T22:10:26.235634

/**
 * Feed response model with subscription status
 *
 * Used by GET /api/feeds endpoint to return feed information
 * along with the user's subscription status.
 */
export interface FeedResponse {
  /** Feed UUID */
  id: string;
  /** Feed name */
  name: string;
  /** RSS/Atom feed URL */
  url: string;
  /** Feed category */
  category: string;
  /** Whether the user is subscribed to this feed */
  is_subscribed: boolean;
}

/**
 * Request model for toggling subscription status
 *
 * Used by POST /api/subscriptions/toggle endpoint.
 */
export interface SubscriptionToggleRequest {
  /** Feed UUID to toggle subscription for */
  feed_id: string;
}

/**
 * Response model for subscription toggle operation
 *
 * Returns the feed ID and the new subscription status.
 */
export interface SubscriptionToggleResponse {
  /** Feed UUID */
  feed_id: string;
  /** New subscription status */
  is_subscribed: boolean;
}

/**
 * Request model for batch subscription operation
 *
 * Used by POST /api/subscriptions/batch endpoint.
 */
export interface BatchSubscribeRequest {
  /** List of feed UUIDs to subscribe to */
  feed_ids: string[];
}

/**
 * Response model for batch subscription operation
 *
 * Returns counts of successful and failed subscriptions, along with error details.
 */
export interface BatchSubscribeResponse {
  /** Number of successful subscriptions */
  subscribed_count: number;
  /** Number of failed subscriptions */
  failed_count: number;
  /** List of error messages for failed subscriptions */
  errors: string[];
}
