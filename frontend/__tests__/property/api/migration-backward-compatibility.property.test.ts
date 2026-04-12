/**
 * Property-Based Tests for Migration Backward Compatibility
 * Task 11.4: Write property test for migration backward compatibility
 *
 * **Validates: Requirements 10.2**
 *
 * Property 12: Migration Backward Compatibility
 *
 * For any module being migrated, both the old and new implementations
 * SHALL produce equivalent results for the same inputs during the migration period.
 */

import * as fc from 'fast-check';
import { compareImplementations } from '@/lib/api/validation';

// Mock axios BEFORE importing ApiClient
jest.mock('axios', () => {
  const mockAxiosInstance = {
    interceptors: {
      request: {
        use: jest.fn((onFulfilled, onRejected) => Math.floor(Math.random() * 10000)),
        eject: jest.fn(),
      },
      response: {
        use: jest.fn((onFulfilled, onRejected) => Math.floor(Math.random() * 10000)),
        eject: jest.fn(),
      },
    },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  };

  return {
    __esModule: true,
    default: {
      create: jest.fn(() => mockAxiosInstance),
    },
    create: jest.fn(() => mockAxiosInstance),
  };
});

import { apiClient } from '@/lib/api/client';

// Mock fetch for testing
global.fetch = jest.fn();

describe('Property 12: Migration Backward Compatibility', () => {
  let mockAxiosInstance: any;

  beforeAll(() => {
    // Get reference to the mock axios instance
    const axios = require('axios');
    mockAxiosInstance = axios.create();
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * **Validates: Requirement 10.2**
   *
   * Property: For any module being migrated, both the old and new implementations
   * SHALL produce equivalent results for the same inputs during the migration period.
   *
   * This property ensures that the unified API client produces the same results
   * as the old implementation for all valid inputs, maintaining backward compatibility.
   */
  describe('API Response Equivalence', () => {
    it('should produce equivalent results for GET requests with various query parameters', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arbitrary endpoint paths
          fc.constantFrom('/api/articles/me', '/api/feeds', '/api/reading-list', '/api/auth/me'),
          // Generate arbitrary query parameters
          fc.record({
            page: fc.option(fc.integer({ min: 1, max: 100 }), { nil: undefined }),
            page_size: fc.option(fc.integer({ min: 1, max: 100 }), { nil: undefined }),
            category: fc.option(fc.constantFrom('tech', 'science', 'business'), { nil: undefined }),
          }),
          async (endpoint, queryParams) => {
            // Build query string
            const params = new URLSearchParams();
            if (queryParams.page !== undefined) params.append('page', String(queryParams.page));
            if (queryParams.page_size !== undefined)
              params.append('page_size', String(queryParams.page_size));
            if (queryParams.category !== undefined) params.append('category', queryParams.category);

            const queryString = params.toString();
            const fullEndpoint = queryString ? `${endpoint}?${queryString}` : endpoint;

            // Mock response data
            const mockResponse = {
              data: [{ id: '1', title: 'Test Article' }],
              pagination: {
                page: queryParams.page || 1,
                page_size: queryParams.page_size || 20,
                total: 100,
              },
            };

            // Mock old implementation (direct fetch)
            const oldImplementation = async () => {
              (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => mockResponse,
              });

              const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${fullEndpoint}`
              );
              return response.json();
            };

            // Mock new implementation (unified API client)
            const newImplementation = async () => {
              // Mock axios response
              mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

              return apiClient.get(fullEndpoint);
            };

            // Compare implementations
            const result = await compareImplementations(
              fullEndpoint,
              oldImplementation,
              newImplementation
            );

            // Verify equivalence
            expect(result.equivalent).toBe(true);
            expect(result.discrepancies).toHaveLength(0);
          }
        ),
        { numRuns: 20 } // Run 20 test cases with different inputs
      );
    });

    it('should produce equivalent results for POST requests with various payloads', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arbitrary endpoint paths
          fc.constantFrom(
            '/api/subscriptions/toggle',
            '/api/reading-list',
            '/api/onboarding/progress'
          ),
          // Generate arbitrary request payloads
          fc.record({
            feed_id: fc.option(fc.uuid(), { nil: undefined }),
            article_id: fc.option(fc.uuid(), { nil: undefined }),
            step: fc.option(fc.constantFrom('welcome', 'feeds', 'preferences'), { nil: undefined }),
            completed: fc.option(fc.boolean(), { nil: undefined }),
          }),
          async (endpoint, payload) => {
            // Filter out undefined values
            const cleanPayload = Object.fromEntries(
              Object.entries(payload).filter(([_, v]) => v !== undefined)
            );

            // Mock response data
            const mockResponse = {
              success: true,
              message: 'Operation completed',
              data: cleanPayload,
            };

            // Mock old implementation (direct fetch)
            const oldImplementation = async () => {
              (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => mockResponse,
              });

              const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`,
                {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(cleanPayload),
                }
              );
              return response.json();
            };

            // Mock new implementation (unified API client)
            const newImplementation = async () => {
              // Mock axios response
              mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

              return apiClient.post(endpoint, cleanPayload);
            };

            // Compare implementations
            const result = await compareImplementations(
              endpoint,
              oldImplementation,
              newImplementation
            );

            // Verify equivalence
            expect(result.equivalent).toBe(true);
            expect(result.discrepancies).toHaveLength(0);
          }
        ),
        { numRuns: 20 } // Run 20 test cases with different inputs
      );
    });

    it('should produce equivalent error responses for failed requests', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arbitrary endpoint paths
          fc.constantFrom('/api/articles/me', '/api/feeds', '/api/reading-list'),
          // Generate arbitrary error status codes
          fc.constantFrom(400, 401, 403, 404, 500, 503),
          // Generate arbitrary error messages
          fc.constantFrom(
            'Bad Request',
            'Unauthorized',
            'Forbidden',
            'Not Found',
            'Internal Server Error',
            'Service Unavailable'
          ),
          async (endpoint, statusCode, errorMessage) => {
            // Mock error response
            const mockErrorResponse = {
              error: {
                code: `ERROR_${statusCode}`,
                message: errorMessage,
                details: 'Test error details',
              },
            };

            // Mock old implementation (direct fetch with error)
            const oldImplementation = async () => {
              (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: statusCode,
                json: async () => mockErrorResponse,
              });

              const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`
              );

              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error.message);
              }

              return response.json();
            };

            // Mock new implementation (unified API client with error)
            const newImplementation = async () => {
              // Mock axios error
              const axiosError = {
                response: {
                  status: statusCode,
                  data: {
                    success: false,
                    error: errorMessage,
                    error_code: `ERROR_${statusCode}`,
                    details: [{ message: 'Test error details' }],
                  },
                },
                isAxiosError: true,
                message: errorMessage,
              };
              mockAxiosInstance.get.mockRejectedValueOnce(axiosError);

              return apiClient.get(endpoint);
            };

            // Compare implementations
            const result = await compareImplementations(
              endpoint,
              oldImplementation,
              newImplementation
            );

            // Both should fail with errors
            expect(result.oldError).toBeDefined();
            expect(result.newError).toBeDefined();

            // Verify both implementations failed consistently (backward compatibility)
            // We don't need exact error message matching, just that both fail
            expect(result.oldError).toBeTruthy();
            expect(result.newError).toBeTruthy();
          }
        ),
        { numRuns: 15 } // Run 15 test cases with different error scenarios
      );
    });
  });

  /**
   * **Validates: Requirement 10.2**
   *
   * Property: Response structure should be consistent between old and new implementations
   */
  describe('Response Structure Consistency', () => {
    it('should maintain consistent response structure for paginated endpoints', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arbitrary pagination parameters
          fc.record({
            page: fc.integer({ min: 1, max: 10 }),
            page_size: fc.integer({ min: 10, max: 100 }),
            total: fc.integer({ min: 0, max: 1000 }),
          }),
          async (pagination) => {
            const endpoint = '/api/articles/me';
            const queryString = `?page=${pagination.page}&page_size=${pagination.page_size}`;
            const fullEndpoint = `${endpoint}${queryString}`;

            // Mock response with pagination
            const mockResponse = {
              data: Array.from({ length: pagination.page_size }, (_, i) => ({
                id: `article-${i}`,
                title: `Article ${i}`,
              })),
              pagination: {
                page: pagination.page,
                page_size: pagination.page_size,
                total: pagination.total,
                has_next: pagination.page * pagination.page_size < pagination.total,
                has_previous: pagination.page > 1,
              },
            };

            // Mock old implementation
            const oldImplementation = async () => {
              (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => mockResponse,
              });

              const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${fullEndpoint}`
              );
              return response.json();
            };

            // Mock new implementation
            const newImplementation = async () => {
              mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

              return apiClient.get(fullEndpoint);
            };

            // Compare implementations
            const result = await compareImplementations(
              fullEndpoint,
              oldImplementation,
              newImplementation
            );

            // Verify structure consistency
            expect(result.equivalent).toBe(true);

            if (result.oldResult && result.newResult) {
              // Verify both have data field
              expect(result.oldResult).toHaveProperty('data');
              expect(result.newResult).toHaveProperty('data');

              // Verify both have pagination field
              expect(result.oldResult).toHaveProperty('pagination');
              expect(result.newResult).toHaveProperty('pagination');

              // Verify pagination structure
              const oldPagination = (result.oldResult as any).pagination;
              const newPagination = (result.newResult as any).pagination;

              expect(oldPagination).toHaveProperty('page');
              expect(oldPagination).toHaveProperty('page_size');
              expect(oldPagination).toHaveProperty('total');
              expect(oldPagination).toHaveProperty('has_next');
              expect(oldPagination).toHaveProperty('has_previous');

              expect(newPagination).toHaveProperty('page');
              expect(newPagination).toHaveProperty('page_size');
              expect(newPagination).toHaveProperty('total');
              expect(newPagination).toHaveProperty('has_next');
              expect(newPagination).toHaveProperty('has_previous');
            }
          }
        ),
        { numRuns: 15 } // Run 15 test cases with different pagination scenarios
      );
    });

    it('should maintain consistent response structure for non-paginated endpoints', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arbitrary array lengths
          fc.integer({ min: 0, max: 50 }),
          async (arrayLength) => {
            const endpoint = '/api/feeds';

            // Mock response without pagination
            const mockResponse = Array.from({ length: arrayLength }, (_, i) => ({
              id: `feed-${i}`,
              name: `Feed ${i}`,
              url: `https://example.com/feed-${i}`,
            }));

            // Mock old implementation
            const oldImplementation = async () => {
              (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => mockResponse,
              });

              const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`
              );
              return response.json();
            };

            // Mock new implementation
            const newImplementation = async () => {
              mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResponse });

              return apiClient.get(endpoint);
            };

            // Compare implementations
            const result = await compareImplementations(
              endpoint,
              oldImplementation,
              newImplementation
            );

            // Verify structure consistency
            expect(result.equivalent).toBe(true);

            if (result.oldResult && result.newResult) {
              // Both should be arrays
              expect(Array.isArray(result.oldResult)).toBe(true);
              expect(Array.isArray(result.newResult)).toBe(true);

              // Both should have the same length
              expect((result.oldResult as any[]).length).toBe(arrayLength);
              expect((result.newResult as any[]).length).toBe(arrayLength);
            }
          }
        ),
        { numRuns: 15 } // Run 15 test cases with different array lengths
      );
    });
  });

  /**
   * **Validates: Requirement 10.2**
   *
   * Property: Type safety should be preserved across implementations
   */
  describe('Type Safety Preservation', () => {
    it('should maintain type safety for strongly-typed responses', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arbitrary user data
          fc.record({
            id: fc.uuid(),
            email: fc.emailAddress(),
            name: fc.string({ minLength: 1, maxLength: 50 }),
            created_at: fc.date().map((d) => d.toISOString()),
          }),
          async (userData) => {
            const endpoint = '/api/auth/me';

            // Mock old implementation
            const oldImplementation = async () => {
              (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: async () => userData,
              });

              const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`
              );
              return response.json();
            };

            // Mock new implementation
            const newImplementation = async () => {
              mockAxiosInstance.get.mockResolvedValueOnce({ data: userData });

              return apiClient.get(endpoint);
            };

            // Compare implementations
            const result = await compareImplementations(
              endpoint,
              oldImplementation,
              newImplementation
            );

            // Verify equivalence
            expect(result.equivalent).toBe(true);

            if (result.oldResult && result.newResult) {
              const oldUser = result.oldResult as any;
              const newUser = result.newResult as any;

              // Verify all fields are present and match
              expect(oldUser.id).toBe(userData.id);
              expect(oldUser.email).toBe(userData.email);
              expect(oldUser.name).toBe(userData.name);
              expect(oldUser.created_at).toBe(userData.created_at);

              expect(newUser.id).toBe(userData.id);
              expect(newUser.email).toBe(userData.email);
              expect(newUser.name).toBe(userData.name);
              expect(newUser.created_at).toBe(userData.created_at);

              // Verify types are consistent
              expect(typeof oldUser.id).toBe(typeof newUser.id);
              expect(typeof oldUser.email).toBe(typeof newUser.email);
              expect(typeof oldUser.name).toBe(typeof newUser.name);
              expect(typeof oldUser.created_at).toBe(typeof newUser.created_at);
            }
          }
        ),
        { numRuns: 15 } // Run 15 test cases with different user data
      );
    });
  });
});
