/**
 * Reading List type definitions
 *
 * Validates Requirements 13.2, 13.3:
 * - 13.2: THE page SHALL display articles in the reading list with their current status (Unread, Read, Archived)
 * - 13.3: EACH article SHALL include a "Mark as Read" button and rating selector (1-5 stars)
 */

/**
 * Status of a reading list item
 */
export type ReadingListStatus = 'Unread' | 'Read' | 'Archived';

/**
 * Reading list item with flat structure matching backend API response
 */
export interface ReadingListItem {
  /** Article ID (UUID) */
  articleId: string;
  /** Article title */
  title: string;
  /** Article URL */
  url: string;
  /** Category name */
  category: string;
  /** Current status of the reading list item */
  status: ReadingListStatus;
  /** User rating for the article (1-5 stars), or null if not rated */
  rating: number | null;
  /** ISO 8601 timestamp of when the item was added to the reading list */
  addedAt: string;
  /** ISO 8601 timestamp of when the item was last updated */
  updatedAt: string;
}

/**
 * Response from reading list API with pagination metadata
 */
export interface ReadingListResponse {
  /** Array of reading list items for the current page */
  items: ReadingListItem[];
  /** Current page number (1-indexed) */
  page: number;
  /** Number of items per page */
  pageSize: number;
  /** Total number of items in the reading list */
  totalCount: number;
  /** Whether there are more items to load */
  hasNextPage: boolean;
}

/**
 * Request payload for adding an article to reading list
 */
export interface AddToReadingListRequest {
  /** Article ID to add */
  articleId: string;
}

/**
 * Request payload for updating reading list item status
 */
export interface UpdateStatusRequest {
  /** New status for the reading list item */
  status: ReadingListStatus;
}

/**
 * Request payload for updating reading list item rating
 */
export interface UpdateRatingRequest {
  /** New rating for the article (1-5 stars), or null to clear */
  rating: number | null;
}
