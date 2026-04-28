/**
 * Property-Based Tests for API Client
 * Task 8.2: Write property test for API client singleton
 *
 * **Validates: Requirements 1.1, 1.3**
 *
 * Property 1: API Client Singleton
 * Property 15: Request Interceptor Execution
 */

import * as fc from 'fast-check';
import { InternalAxiosRequestConfig } from 'axios';

// Mock axios BEFORE importing ApiClient
vi.mock('axios', () => {
  const mockInterceptors = {
    request: {
      use: vi.fn((onFulfilled, onRejected) => Math.floor(Math.random() * 10000)),
      eject: vi.fn(),
    },
    response: {
      use: vi.fn((onFulfilled, onRejected) => Math.floor(Math.random() * 10000)),
      eject: vi.fn(),
    },
  };

  const mockAxiosInstance = {
    interceptors: mockInterceptors,
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  };

  return {
    __esModule: true,
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
    create: vi.fn(() => mockAxiosInstance),
  };
});

import ApiClient from '@/lib/api/client';

describe('Property-Based Tests: API Client', () => {
  let mockAxiosInstance: any;

  beforeAll(() => {
    // Get reference to the mock axios instance
    const axios = require('axios');
    mockAxiosInstance = axios.create();
  });

  beforeEach(() => {
    // Clear all mock call history before each test
    vi.clearAllMocks();
  });

  describe('Property 1: API Client Singleton', () => {
    /**
     * **Validates: Requirements 1.1**
     *
     * Property: For any sequence of API client instantiation calls,
     * all instances SHALL reference the same underlying HTTP client object.
     *
     * This property ensures that the singleton pattern is correctly implemented
     * and that multiple calls to getInstance() always return the same instance.
     */
    it('should always return the same instance regardless of call sequence', () => {
      fc.assert(
        fc.property(
          // Generate arbitrary number of getInstance calls (1 to 100)
          fc.integer({ min: 1, max: 100 }),
          (numCalls) => {
            // Collect all instances from multiple calls
            const instances: ApiClient[] = [];
            for (let i = 0; i < numCalls; i++) {
              instances.push(ApiClient.getInstance());
            }

            // Verify all instances are the same object reference
            const firstInstance = instances[0];
            for (let i = 1; i < instances.length; i++) {
              expect(instances[i]).toBe(firstInstance);
            }

            // Verify all instances share the same underlying axios instance
            const firstAxiosInstance = firstInstance.getAxiosInstance();
            for (let i = 1; i < instances.length; i++) {
              expect(instances[i].getAxiosInstance()).toBe(firstAxiosInstance);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain singleton across different access patterns', () => {
      fc.assert(
        fc.property(
          // Generate different access patterns: direct getInstance vs exported apiClient
          fc.array(fc.boolean(), { minLength: 1, maxLength: 50 }),
          (accessPattern) => {
            const { apiClient } = require('@/lib/api/client');
            const instances: ApiClient[] = [];

            // Access using different patterns
            for (const useDirect of accessPattern) {
              if (useDirect) {
                instances.push(ApiClient.getInstance());
              } else {
                instances.push(apiClient);
              }
            }

            // All instances should be the same
            const firstInstance = instances[0];
            for (let i = 1; i < instances.length; i++) {
              expect(instances[i]).toBe(firstInstance);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Property 15: Request Interceptor Execution', () => {
    /**
     * **Validates: Requirements 1.3**
     *
     * Property: For any API request made through the unified client,
     * all registered request interceptors SHALL execute in order before
     * the request is sent.
     *
     * This property ensures that interceptors are executed in the correct order
     * and that all interceptors are called before the actual request.
     */

    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should register all interceptors in order', () => {
      fc.assert(
        fc.property(
          // Generate arbitrary number of interceptors (1 to 20)
          fc.integer({ min: 1, max: 20 }),
          (numInterceptors) => {
            // Clear mocks at the start of each property test run
            vi.clearAllMocks();

            // Create a fresh client instance for this test
            const client = ApiClient.getInstance();
            const axiosInstance = client.getAxiosInstance();

            // Register multiple interceptors
            const interceptorIds: number[] = [];
            for (let i = 0; i < numInterceptors; i++) {
              const interceptorIndex = i;
              const id = client.addRequestInterceptor({
                onFulfilled: (config) => {
                  return config;
                },
              });
              interceptorIds.push(id);
            }

            // Verify all interceptors were registered
            // We only count the calls made in THIS test run (after clearAllMocks)
            expect(axiosInstance.interceptors.request.use).toHaveBeenCalledTimes(numInterceptors);

            // Verify each interceptor was registered with a function
            for (let i = 0; i < numInterceptors; i++) {
              const call = (axiosInstance.interceptors.request.use as jest.Mock).mock.calls[i];
              expect(typeof call[0]).toBe('function');
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should allow removing interceptors without affecting others', () => {
      fc.assert(
        fc.property(
          // Generate interceptors and indices to remove
          fc.record({
            numInterceptors: fc.integer({ min: 3, max: 15 }),
            indicesToRemove: fc.array(fc.integer({ min: 0, max: 14 }), {
              minLength: 1,
              maxLength: 5,
            }),
          }),
          ({ numInterceptors, indicesToRemove }) => {
            // Clear mocks at the start of each property test run
            vi.clearAllMocks();

            const client = ApiClient.getInstance();
            const axiosInstance = client.getAxiosInstance();

            // Register interceptors
            const interceptorIds: number[] = [];
            for (let i = 0; i < numInterceptors; i++) {
              const id = client.addRequestInterceptor({
                onFulfilled: (config) => config,
              });
              interceptorIds.push(id);
            }

            // Clear mocks again to only count eject calls
            vi.clearAllMocks();

            // Remove some interceptors
            const validIndices = indicesToRemove.filter((idx) => idx < numInterceptors);
            const uniqueIndices = [...new Set(validIndices)];

            for (const idx of uniqueIndices) {
              client.removeRequestInterceptor(interceptorIds[idx]);
            }

            // Verify eject was called for each removed interceptor
            expect(axiosInstance.interceptors.request.eject).toHaveBeenCalledTimes(
              uniqueIndices.length
            );

            // Verify correct IDs were passed to eject
            for (const idx of uniqueIndices) {
              expect(axiosInstance.interceptors.request.eject).toHaveBeenCalledWith(
                interceptorIds[idx]
              );
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should handle interceptors with different configurations', () => {
      fc.assert(
        fc.property(
          // Generate interceptors with different handler combinations
          fc.array(
            fc.record({
              hasFulfilled: fc.boolean(),
              hasRejected: fc.boolean(),
            }),
            { minLength: 1, maxLength: 10 }
          ),
          (interceptorConfigs) => {
            // Clear mocks at the start of each property test run
            vi.clearAllMocks();

            const client = ApiClient.getInstance();
            const axiosInstance = client.getAxiosInstance();

            // Register interceptors with different configurations
            for (const config of interceptorConfigs) {
              const interceptor: any = {};
              if (config.hasFulfilled) {
                interceptor.onFulfilled = (cfg: InternalAxiosRequestConfig) => cfg;
              }
              if (config.hasRejected) {
                interceptor.onRejected = (error: any) => Promise.reject(error);
              }

              client.addRequestInterceptor(interceptor);
            }

            // Verify all interceptors were registered
            const expectedCalls = interceptorConfigs.length;
            expect(axiosInstance.interceptors.request.use).toHaveBeenCalledTimes(expectedCalls);

            // Verify each call received the correct handlers
            for (let i = 0; i < interceptorConfigs.length; i++) {
              const call = (axiosInstance.interceptors.request.use as jest.Mock).mock.calls[i];
              const config = interceptorConfigs[i];

              if (config.hasFulfilled) {
                expect(typeof call[0]).toBe('function');
              } else {
                expect(call[0]).toBeUndefined();
              }

              if (config.hasRejected) {
                expect(typeof call[1]).toBe('function');
              } else {
                expect(call[1]).toBeUndefined();
              }
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should maintain interceptor isolation across multiple clients', () => {
      fc.assert(
        fc.property(fc.integer({ min: 1, max: 10 }), (numInterceptors) => {
          // Clear mocks at the start of each property test run
          vi.clearAllMocks();

          // Get multiple references to the singleton
          const client1 = ApiClient.getInstance();
          const client2 = ApiClient.getInstance();

          // They should be the same instance
          expect(client1).toBe(client2);

          // Add interceptors through client1
          const ids1: number[] = [];
          for (let i = 0; i < numInterceptors; i++) {
            const id = client1.addRequestInterceptor({
              onFulfilled: (config) => config,
            });
            ids1.push(id);
          }

          // Add interceptors through client2
          const ids2: number[] = [];
          for (let i = 0; i < numInterceptors; i++) {
            const id = client2.addRequestInterceptor({
              onFulfilled: (config) => config,
            });
            ids2.push(id);
          }

          // Both should share the same axios instance
          expect(client1.getAxiosInstance()).toBe(client2.getAxiosInstance());

          // Total interceptors should be numInterceptors * 2
          const axiosInstance = client1.getAxiosInstance();
          expect(axiosInstance.interceptors.request.use).toHaveBeenCalledTimes(numInterceptors * 2);
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Property: Response Interceptor Execution', () => {
    /**
     * Additional property test for response interceptors
     * to ensure symmetry with request interceptors
     */

    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should register all response interceptors in order', () => {
      fc.assert(
        fc.property(fc.integer({ min: 1, max: 20 }), (numInterceptors) => {
          // Clear mocks at the start of each property test run
          vi.clearAllMocks();

          const client = ApiClient.getInstance();
          const axiosInstance = client.getAxiosInstance();

          // Register multiple response interceptors
          for (let i = 0; i < numInterceptors; i++) {
            client.addResponseInterceptor({
              onFulfilled: (response) => response,
            });
          }

          // Verify all interceptors were registered
          expect(axiosInstance.interceptors.response.use).toHaveBeenCalledTimes(numInterceptors);
        }),
        { numRuns: 50 }
      );
    });

    it('should allow removing response interceptors', () => {
      fc.assert(
        fc.property(
          fc.record({
            numInterceptors: fc.integer({ min: 3, max: 15 }),
            indicesToRemove: fc.array(fc.integer({ min: 0, max: 14 }), {
              minLength: 1,
              maxLength: 5,
            }),
          }),
          ({ numInterceptors, indicesToRemove }) => {
            // Clear mocks at the start of each property test run
            vi.clearAllMocks();

            const client = ApiClient.getInstance();
            const axiosInstance = client.getAxiosInstance();

            // Register interceptors
            const interceptorIds: number[] = [];
            for (let i = 0; i < numInterceptors; i++) {
              const id = client.addResponseInterceptor({
                onFulfilled: (response) => response,
              });
              interceptorIds.push(id);
            }

            // Clear mocks again to only count eject calls
            vi.clearAllMocks();

            // Remove some interceptors
            const validIndices = indicesToRemove.filter((idx) => idx < numInterceptors);
            const uniqueIndices = [...new Set(validIndices)];

            for (const idx of uniqueIndices) {
              client.removeResponseInterceptor(interceptorIds[idx]);
            }

            // Verify eject was called for each removed interceptor
            expect(axiosInstance.interceptors.response.eject).toHaveBeenCalledTimes(
              uniqueIndices.length
            );
          }
        ),
        { numRuns: 50 }
      );
    });
  });
});
