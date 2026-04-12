/**
 * Shared mock data and factory functions for tests
 *
 * Provides reusable mock data for articles, users, feeds, and other entities.
 * Use these factories to create consistent test data across all tests.
 */

import { Article, User, Feed, ReadingListItem } from '@/types';

/**
 * Create a mock article with default or custom values
 */
export function mockArticle(overrides?: Partial<Article>): Article {
  return {
    id: '1',
    title: 'Test Article',
    url: 'https://example.com/article',
    summary: 'This is a test article summary',
    content: 'Full article content goes here',
    author: 'Test Author',
    published_at: '2024-01-01T00:00:00Z',
    source: 'Test Source',
    categories: ['前端開發'],
    image_url: 'https://example.com/image.jpg',
    reading_time: 5,
    ...overrides,
  };
}

/**
 * Create a mock user with default or custom values
 */
export function mockUser(overrides?: Partial<User>): User {
  return {
    id: 'user-1',
    discord_id: '123456789',
    username: 'testuser',
    avatar_url: 'https://example.com/avatar.jpg',
    email: 'test@example.com',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create a mock feed with default or custom values
 */
export function mockFeed(overrides?: Partial<Feed>): Feed {
  return {
    id: 'feed-1',
    name: 'Test Feed',
    url: 'https://example.com/feed.xml',
    description: 'A test RSS feed',
    is_subscribed: false,
    subscriber_count: 10,
    article_count: 100,
    last_fetched_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create a mock reading list item with default or custom values
 */
export function mockReadingListItem(overrides?: Partial<ReadingListItem>): ReadingListItem {
  return {
    article_id: '1',
    status: 'unread',
    added_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create multiple mock articles
 */
export function mockArticles(count: number, overrides?: Partial<Article>): Article[] {
  return Array.from({ length: count }, (_, i) =>
    mockArticle({
      id: `article-${i + 1}`,
      title: `Test Article ${i + 1}`,
      ...overrides,
    })
  );
}

/**
 * Create multiple mock feeds
 */
export function mockFeeds(count: number, overrides?: Partial<Feed>): Feed[] {
  return Array.from({ length: count }, (_, i) =>
    mockFeed({
      id: `feed-${i + 1}`,
      name: `Test Feed ${i + 1}`,
      ...overrides,
    })
  );
}

/**
 * Mock API response with pagination
 */
export function mockPaginatedResponse<T>(items: T[], page: number = 1, pageSize: number = 20) {
  return {
    items,
    page,
    page_size: pageSize,
    total: items.length,
    total_pages: Math.ceil(items.length / pageSize),
  };
}

/**
 * Mock API error response
 */
export function mockErrorResponse(
  message: string = 'An error occurred',
  code: string = 'ERROR',
  details?: any
) {
  return {
    error: {
      code,
      message,
      details,
    },
  };
}

/**
 * Mock axios error
 */
export function mockAxiosError(
  status: number = 500,
  message: string = 'Internal Server Error',
  data?: any
) {
  return {
    response: {
      status,
      statusText: message,
      data: data || mockErrorResponse(message),
      headers: {},
      config: {} as any,
    },
    isAxiosError: true,
    toJSON: () => ({}),
    name: 'AxiosError',
    message,
  };
}
