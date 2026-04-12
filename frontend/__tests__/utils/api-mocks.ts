/**
 * API mock utilities for testing
 *
 * Provides utilities for mocking API calls using MSW (Mock Service Worker)
 * and creating mock API responses.
 */

import { rest } from 'msw';
import { setupServer } from 'msw/node';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Create MSW handlers for common API endpoints
 */
export const createApiHandlers = () => {
  return [
    // Auth endpoints
    rest.post(`${API_BASE_URL}/api/auth/login`, (req, res, ctx) => {
      return res(
        ctx.status(200),
        ctx.json({
          data: {
            access_token: 'mock-token',
            user: {
              id: 'user-1',
              username: 'testuser',
              email: 'test@example.com',
            },
          },
        })
      );
    }),

    rest.post(`${API_BASE_URL}/api/auth/logout`, (req, res, ctx) => {
      return res(ctx.status(200), ctx.json({ data: { success: true } }));
    }),

    // Articles endpoints
    rest.get(`${API_BASE_URL}/api/articles`, (req, res, ctx) => {
      return res(
        ctx.status(200),
        ctx.json({
          data: {
            items: [],
            page: 1,
            page_size: 20,
            total: 0,
            total_pages: 0,
          },
        })
      );
    }),

    rest.get(`${API_BASE_URL}/api/articles/:id`, (req, res, ctx) => {
      const { id } = req.params;
      return res(
        ctx.status(200),
        ctx.json({
          data: {
            id,
            title: 'Test Article',
            url: 'https://example.com/article',
            summary: 'Test summary',
          },
        })
      );
    }),

    // Feeds endpoints
    rest.get(`${API_BASE_URL}/api/feeds`, (req, res, ctx) => {
      return res(
        ctx.status(200),
        ctx.json({
          data: {
            items: [],
            page: 1,
            page_size: 20,
            total: 0,
            total_pages: 0,
          },
        })
      );
    }),

    // Reading list endpoints
    rest.get(`${API_BASE_URL}/api/reading-list`, (req, res, ctx) => {
      return res(
        ctx.status(200),
        ctx.json({
          data: {
            items: [],
            page: 1,
            page_size: 20,
            total: 0,
            total_pages: 0,
          },
        })
      );
    }),
  ];
};

/**
 * Setup MSW server for tests
 */
export const setupMockServer = () => {
  const server = setupServer(...createApiHandlers());

  beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  return server;
};

/**
 * Create a mock API response with standardized structure
 */
export function mockApiResponse<T>(data: T, metadata?: Record<string, any>) {
  return {
    data,
    metadata: metadata || {},
  };
}

/**
 * Create a mock API error response
 */
export function mockApiErrorResponse(
  code: string = 'ERROR',
  message: string = 'An error occurred',
  details?: any
) {
  return {
    error: {
      code,
      message,
      details: details || {},
    },
  };
}

/**
 * Create a mock paginated API response
 */
export function mockPaginatedApiResponse<T>(
  items: T[],
  page: number = 1,
  pageSize: number = 20,
  total?: number
) {
  const totalItems = total !== undefined ? total : items.length;
  return mockApiResponse(
    {
      items,
      page,
      page_size: pageSize,
      total: totalItems,
      total_pages: Math.ceil(totalItems / pageSize),
      has_next: page * pageSize < totalItems,
      has_previous: page > 1,
    },
    {
      pagination: {
        page,
        page_size: pageSize,
        total: totalItems,
      },
    }
  );
}
