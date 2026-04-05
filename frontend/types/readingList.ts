/**
 * Reading List type definitions
 *
 * Validates Requirements 13.2, 13.3:
 * - 13.2: THE page SHALL display articles in the reading list with their current status (Unread, Read, Archived)
 * - 13.3: EACH article SHALL include a "Mark as Read" button and rating selector (1-5 stars)
 */

import { Article } from './article';

/**
 * Status of a reading list item
 */
export type ReadingListStatus = 'Unread' | 'Read' | 'Archived';

/**
 * Reading list item representing an article saved to the user's reading list
 */
export interface ReadingListItem {
  /** Unique identifier for the reading list item */
  id: string;
  /** The article associated with this reading list item */
  article: Article;
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
 * Request payload for updating a reading list item
 */
export interface UpdateReadingListRequest {
  /** New status for the reading list item (optional) */
  status?: ReadingListStatus;
  /** New rating for the article (1-5 stars, optional) */
  rating?: number;
}
