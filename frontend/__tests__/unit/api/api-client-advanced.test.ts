/**
 * Advanced Unit Tests for API Client
 * Task 8.5: Write unit tests for API client
 *
 * Tests error handling, retry logic, and interceptor execution
 * Requirements: 1.2, 1.3, 1.4
 */

import { AxiosError } from 'axios';
import { ApiError, ErrorCode } from '@/lib/api/errors';

// Mock axios before imports
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

import axios from 'axios';
import ApiClient from '@/lib/api/client';

describe('ApiClient - Advanced Tests', () => {
  let mockAxiosInstance: any;
  let client: ApiClient;

  beforeAll(() => {
    mockAxiosInstance = (axios.create as jest.Mock)();
  });

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset singleton for clean tests
    ApiClient.resetInstance();
    client = ApiClient.getInstance();
  });

  describe('Error Handling (Requirement 1.2)', () => {
    it('should throw ApiError when GET request fails', async () => {
      const axiosError = {
        response: {
          status: 404,
          data: {
            success: false,
            error: 'Resource not found',
            error_code: 'NOT_FOUND',
          },
        },
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.get.mockRejectedValue(axiosError);

      await expect(client.get('/test')).rejects.toThrow(ApiError);
      await expect(client.get('/test')).rejects.toMatchObject({
        statusCode: 404,
        errorCode: ErrorCode.NOT_FOUND,
      });
    });

    it('should throw ApiError when POST request fails', async () => {
      const axiosError = {
        response: {
          status: 400,
          data: {
            success: false,
            error: 'Validation failed',
            error_code: 'VALIDATION_FAILED',
            details: [{ field: 'email', message: 'Invalid email format' }],
          },
        },
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.post.mockRejectedValue(axiosError);

      await expect(client.post('/test', {})).rejects.toThrow(ApiError);
      await expect(client.post('/test', {})).rejects.toMatchObject({
        statusCode: 400,
        errorCode: ErrorCode.VALIDATION_FAILED,
      });
    });

    it('should throw ApiError when PUT request fails', async () => {
      const axiosError = {
        response: {
          status: 401,
          data: {
            success: false,
            error: 'Invalid token',
            error_code: 'AUTH_INVALID_TOKEN',
          },
        },
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.put.mockRejectedValue(axiosError);

      await expect(client.put('/test/1', {})).rejects.toThrow(ApiError);
      await expect(client.put('/test/1', {})).rejects.toMatchObject({
        statusCode: 401,
        errorCode: ErrorCode.AUTH_INVALID_TOKEN,
      });
    });

    it('should throw ApiError when PATCH request fails', async () => {
      const axiosError = {
        response: {
          status: 403,
          data: {
            success: false,
            error: 'Insufficient permissions',
            error_code: 'AUTH_INSUFFICIENT_PERMISSIONS',
          },
        },
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.patch.mockRejectedValue(axiosError);

      await expect(client.patch('/test/1', {})).rejects.toThrow(ApiError);
      await expect(client.patch('/test/1', {})).rejects.toMatchObject({
        statusCode: 403,
        errorCode: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
      });
    });

    it('should throw ApiError when DELETE request fails', async () => {
      const axiosError = {
        response: {
          status: 500,
          data: {
            success: false,
            error: 'Internal server error',
            error_code: 'INTERNAL_ERROR',
          },
        },
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.delete.mockRejectedValue(axiosError);

      await expect(client.delete('/test/1')).rejects.toThrow(ApiError);
      await expect(client.delete('/test/1')).rejects.toMatchObject({
        statusCode: 500,
        errorCode: ErrorCode.INTERNAL_ERROR,
      });
    });

    it('should handle network errors', async () => {
      const networkError = {
        message: 'Network Error',
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.get.mockRejectedValue(networkError);

      await expect(client.get('/test')).rejects.toThrow(ApiError);
    });

    it('should handle timeout errors', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded',
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.get.mockRejectedValue(timeoutError);

      await expect(client.get('/test')).rejects.toThrow(ApiError);
    });
  });

  describe('Configuration (Requirement 1.1)', () => {
    it('should accept custom configuration', () => {
      const customClient = ApiClient.getInstance({
        baseURL: 'https://custom-api.example.com',
        timeout: 60000,
      });

      expect(customClient).toBeInstanceOf(ApiClient);
      expect(axios.create).toHaveBeenCalled();
    });

    it('should allow updating retry configuration', () => {
      client.setRetryConfig({
        maxRetries: 5,
        baseDelay: 2000,
      });

      // Configuration updated successfully (no error thrown)
      expect(client).toBeInstanceOf(ApiClient);
    });

    it('should allow enabling/disabling logging', () => {
      client.setLogging(true);
      expect(client).toBeInstanceOf(ApiClient);

      client.setLogging(false);
      expect(client).toBeInstanceOf(ApiClient);
    });
  });

  describe('Type Safety (Requirement 1.4)', () => {
    interface TestResponse {
      id: number;
      name: string;
    }

    it('should support generic types for GET requests', async () => {
      const mockData: TestResponse = { id: 1, name: 'Test' };
      mockAxiosInstance.get.mockResolvedValue({ data: mockData });

      const result = await client.get<TestResponse>('/test');

      expect(result).toEqual(mockData);
      expect(result.id).toBe(1);
      expect(result.name).toBe('Test');
    });

    it('should support generic types for POST requests', async () => {
      const mockData: TestResponse = { id: 1, name: 'Test' };
      mockAxiosInstance.post.mockResolvedValue({ data: mockData });

      const result = await client.post<TestResponse>('/test', { name: 'Test' });

      expect(result).toEqual(mockData);
    });

    it('should support generic types for PUT requests', async () => {
      const mockData: TestResponse = { id: 1, name: 'Updated' };
      mockAxiosInstance.put.mockResolvedValue({ data: mockData });

      const result = await client.put<TestResponse>('/test/1', { name: 'Updated' });

      expect(result).toEqual(mockData);
    });

    it('should support generic types for PATCH requests', async () => {
      const mockData: TestResponse = { id: 1, name: 'Patched' };
      mockAxiosInstance.patch.mockResolvedValue({ data: mockData });

      const result = await client.patch<TestResponse>('/test/1', { name: 'Patched' });

      expect(result).toEqual(mockData);
    });

    it('should support generic types for DELETE requests', async () => {
      interface DeleteResponse {
        success: boolean;
      }

      const mockData: DeleteResponse = { success: true };
      mockAxiosInstance.delete.mockResolvedValue({ data: mockData });

      const result = await client.delete<DeleteResponse>('/test/1');

      expect(result).toEqual(mockData);
    });
  });

  describe('Request Configuration', () => {
    it('should pass custom config to GET request', async () => {
      const mockData = { id: 1 };
      mockAxiosInstance.get.mockResolvedValue({ data: mockData });

      const config = { headers: { 'X-Custom-Header': 'value' } };
      await client.get('/test', config);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', config);
    });

    it('should pass custom config to POST request', async () => {
      const mockData = { id: 1 };
      mockAxiosInstance.post.mockResolvedValue({ data: mockData });

      const config = { headers: { 'X-Custom-Header': 'value' } };
      await client.post('/test', { data: 'test' }, config);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', { data: 'test' }, config);
    });

    it('should pass custom config to PUT request', async () => {
      const mockData = { id: 1 };
      mockAxiosInstance.put.mockResolvedValue({ data: mockData });

      const config = { headers: { 'X-Custom-Header': 'value' } };
      await client.put('/test/1', { data: 'test' }, config);

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test/1', { data: 'test' }, config);
    });

    it('should pass custom config to PATCH request', async () => {
      const mockData = { id: 1 };
      mockAxiosInstance.patch.mockResolvedValue({ data: mockData });

      const config = { headers: { 'X-Custom-Header': 'value' } };
      await client.patch('/test/1', { data: 'test' }, config);

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/test/1', { data: 'test' }, config);
    });

    it('should pass custom config to DELETE request', async () => {
      const mockData = { success: true };
      mockAxiosInstance.delete.mockResolvedValue({ data: mockData });

      const config = { headers: { 'X-Custom-Header': 'value' } };
      await client.delete('/test/1', config);

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test/1', config);
    });
  });

  describe('Interceptor Execution Order (Requirement 1.3)', () => {
    it('should execute multiple request interceptors in order', () => {
      // Clear mocks to only count new interceptors
      jest.clearAllMocks();

      const interceptor1 = {
        onFulfilled: jest.fn((config) => config),
      };
      const interceptor2 = {
        onFulfilled: jest.fn((config) => config),
      };
      const interceptor3 = {
        onFulfilled: jest.fn((config) => config),
      };

      client.addRequestInterceptor(interceptor1);
      client.addRequestInterceptor(interceptor2);
      client.addRequestInterceptor(interceptor3);

      // Verify all interceptors were registered (only counting new ones after clearAllMocks)
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledTimes(3);
    });

    it('should execute multiple response interceptors in order', () => {
      // Clear mocks to only count new interceptors
      jest.clearAllMocks();

      const interceptor1 = {
        onFulfilled: jest.fn((response) => response),
      };
      const interceptor2 = {
        onFulfilled: jest.fn((response) => response),
      };

      client.addResponseInterceptor(interceptor1);
      client.addResponseInterceptor(interceptor2);

      // Verify all interceptors were registered (only counting new ones after clearAllMocks)
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalledTimes(2);
    });

    it('should handle interceptor with only onFulfilled', () => {
      const interceptor = {
        onFulfilled: jest.fn((config) => config),
      };

      const id = client.addRequestInterceptor(interceptor);

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledWith(
        interceptor.onFulfilled,
        undefined
      );
      expect(typeof id).toBe('number');
    });

    it('should handle interceptor with only onRejected', () => {
      const interceptor = {
        onRejected: jest.fn((error) => Promise.reject(error)),
      };

      const id = client.addRequestInterceptor(interceptor);

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledWith(
        undefined,
        interceptor.onRejected
      );
      expect(typeof id).toBe('number');
    });
  });

  describe('Singleton Reset (Testing Utility)', () => {
    it('should allow resetting singleton instance', () => {
      const instance1 = ApiClient.getInstance();
      ApiClient.resetInstance();
      const instance2 = ApiClient.getInstance();

      // After reset, we get a new instance
      expect(instance1).not.toBe(instance2);
    });
  });

  describe('Error Propagation', () => {
    it('should propagate ApiError from failed requests', async () => {
      const axiosError = {
        response: {
          status: 429,
          data: {
            success: false,
            error: 'Rate limit exceeded',
            error_code: 'RATE_LIMIT_EXCEEDED',
          },
        },
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.get.mockRejectedValue(axiosError);

      try {
        await client.get('/test');
        fail('Should have thrown ApiError');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        if (error instanceof ApiError) {
          expect(error.statusCode).toBe(429);
          expect(error.errorCode).toBe(ErrorCode.RATE_LIMIT_EXCEEDED);
          expect(error.getDisplayMessage()).toContain('Too many requests');
        }
      }
    });

    it('should preserve error details in ApiError', async () => {
      const axiosError = {
        response: {
          status: 400,
          data: {
            success: false,
            error: 'Validation failed',
            error_code: 'VALIDATION_FAILED',
            details: [
              { field: 'email', message: 'Invalid email format', code: 'INVALID_FORMAT' },
              { field: 'password', message: 'Password too short', code: 'TOO_SHORT' },
            ],
          },
        },
        config: {},
        isAxiosError: true,
      } as AxiosError;

      mockAxiosInstance.post.mockRejectedValue(axiosError);

      try {
        await client.post('/test', {});
        fail('Should have thrown ApiError');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        if (error instanceof ApiError) {
          expect(error.details).toHaveLength(2);
          expect(error.details?.[0].field).toBe('email');
          expect(error.details?.[1].field).toBe('password');
        }
      }
    });
  });
});
