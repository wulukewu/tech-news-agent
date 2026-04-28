/**
 * API Validation Tests - Task 11.3
 * Requirements: 10.2, 10.3, 11.1
 *
 * This test suite validates the unified API client implementation by:
 * - Testing validation utilities
 * - Testing response format validation
 * - Testing error rate monitoring
 * - Testing discrepancy logging
 */

import {
  validateApiCall,
  runParallelValidation,
  compareImplementations,
  type ValidationResult,
  type ExpectedResponse,
} from '@/lib/api/validation';
import { performanceMonitor } from '@/lib/api/performance';
import { apiClient, ApiError } from '@/lib/api/client';

// Mock the API client
vi.mock('@/lib/api/client', () => {
  const actualModule = jest.requireActual('@/lib/api/client');
  return {
    ...actualModule,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    },
  };
});

describe('API Validation Tests - Task 11.3', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    performanceMonitor.clearMetrics();
    performanceMonitor.setEnabled(true);
  });

  describe('validateApiCall', () => {
    it('should validate successful API call with correct response structure', async () => {
      const mockResponse = {
        data: [{ id: '1', title: 'Test' }],
        pagination: { page: 1, page_size: 20, total: 1 },
      };

      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const expectedResponse: ExpectedResponse = {
        hasDataField: true,
        hasPaginationField: true,
      };

      const result = await validateApiCall('/api/articles/me', 'GET', expectedResponse);

      expect(result.success).toBe(true);
      expect(result.discrepancies).toHaveLength(0);
      expect(result.responseTime).toBeGreaterThan(0);
    });

    it('should detect missing data field in response', async () => {
      const mockResponse = {
        items: [{ id: '1' }], // Wrong field name
        pagination: { page: 1, page_size: 20, total: 1 },
      };

      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const expectedResponse: ExpectedResponse = {
        hasDataField: true,
        hasPaginationField: true,
      };

      const result = await validateApiCall('/api/articles/me', 'GET', expectedResponse);

      expect(result.success).toBe(true); // Request succeeded
      expect(result.discrepancies).toContain('Missing "data" field in response');
    });

    it('should detect missing pagination field in response', async () => {
      const mockResponse = {
        data: [{ id: '1' }],
        // Missing pagination field
      };

      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const expectedResponse: ExpectedResponse = {
        hasDataField: true,
        hasPaginationField: true,
      };

      const result = await validateApiCall('/api/articles/me', 'GET', expectedResponse);

      expect(result.success).toBe(true);
      expect(result.discrepancies).toContain('Missing "pagination" field in response');
    });

    it('should run custom validation and detect issues', async () => {
      const mockResponse = {
        data: 'not an array', // Should be array
        pagination: { page: 1, page_size: 20, total: 1 },
      };

      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const expectedResponse: ExpectedResponse = {
        hasDataField: true,
        customValidation: (response: any) => {
          if (!Array.isArray(response.data)) {
            return '"data" field should be an array';
          }
          return null;
        },
      };

      const result = await validateApiCall('/api/articles/me', 'GET', expectedResponse);

      expect(result.success).toBe(true);
      expect(result.discrepancies).toContain('"data" field should be an array');
    });

    it('should handle API errors correctly', async () => {
      const mockError = new ApiError(
        404,
        'RESOURCE_NOT_FOUND' as any,
        'Resource not found',
        'The requested resource was not found.'
      );

      (apiClient.get as jest.Mock).mockRejectedValue(mockError);

      const result = await validateApiCall('/api/nonexistent', 'GET');

      expect(result.success).toBe(false);
      expect(result.statusCode).toBe(404);
      expect(result.error).toBe('The requested resource was not found.');
    });

    it('should validate error structure', async () => {
      const mockError = new ApiError(
        500,
        'INTERNAL_ERROR' as any,
        'Internal error',
        'An internal error occurred. Please try again later.'
      );

      (apiClient.get as jest.Mock).mockRejectedValue(mockError);

      const expectedResponse: ExpectedResponse = {
        hasErrorField: true,
        hasErrorCodeField: true,
      };

      const result = await validateApiCall('/api/test', 'GET', expectedResponse);

      expect(result.success).toBe(false);
      expect(result.discrepancies).toHaveLength(0); // Error structure is correct
    });
  });

  describe('runParallelValidation', () => {
    it('should run multiple validation tests in parallel', async () => {
      const mockResponse1 = { data: [], pagination: { page: 1, page_size: 20, total: 0 } };
      const mockResponse2 = { categories: ['Tech', 'Science'] };

      (apiClient.get as jest.Mock)
        .mockResolvedValueOnce(mockResponse1)
        .mockResolvedValueOnce(mockResponse2);

      const tests = [
        {
          endpoint: '/api/articles/me',
          method: 'GET' as const,
          expectedResponse: { hasDataField: true, hasPaginationField: true },
        },
        {
          endpoint: '/api/articles/categories',
          method: 'GET' as const,
        },
      ];

      const report = await runParallelValidation(tests);

      expect(report.totalTests).toBe(2);
      expect(report.passedTests).toBe(2);
      expect(report.failedTests).toBe(0);
      expect(report.averageResponseTime).toBeGreaterThan(0);
    });

    it('should calculate error rate correctly', async () => {
      const mockSuccess = { data: [] };
      const mockError = new ApiError(500, 'INTERNAL_ERROR' as any, 'Error', 'Error message');

      (apiClient.get as jest.Mock)
        .mockResolvedValueOnce(mockSuccess)
        .mockRejectedValueOnce(mockError)
        .mockResolvedValueOnce(mockSuccess);

      const tests = [
        { endpoint: '/api/test1', method: 'GET' as const },
        { endpoint: '/api/test2', method: 'GET' as const },
        { endpoint: '/api/test3', method: 'GET' as const },
      ];

      const report = await runParallelValidation(tests);

      expect(report.totalTests).toBe(3);
      expect(report.passedTests).toBe(2);
      expect(report.failedTests).toBe(1);
      expect(report.errorRate).toBeCloseTo(0.333, 2);
    });

    it('should collect all discrepancies', async () => {
      const mockResponse1 = { items: [] }; // Missing 'data' field
      const mockResponse2 = { data: [] }; // Missing 'pagination' field

      (apiClient.get as jest.Mock)
        .mockResolvedValueOnce(mockResponse1)
        .mockResolvedValueOnce(mockResponse2);

      const tests = [
        {
          endpoint: '/api/test1',
          method: 'GET' as const,
          expectedResponse: { hasDataField: true },
        },
        {
          endpoint: '/api/test2',
          method: 'GET' as const,
          expectedResponse: { hasPaginationField: true },
        },
      ];

      const report = await runParallelValidation(tests);

      expect(report.discrepancies.length).toBe(2);
      expect(report.discrepancies[0].description).toContain('Missing "data" field');
      expect(report.discrepancies[1].description).toContain('Missing "pagination" field');
    });
  });

  describe('compareImplementations', () => {
    it('should detect equivalent implementations', async () => {
      const mockData = { data: [{ id: '1' }] };
      const oldImpl = vi.fn().mockResolvedValue(mockData);
      const newImpl = vi.fn().mockResolvedValue(mockData);

      const result = await compareImplementations('/api/test', oldImpl, newImpl);

      expect(result.equivalent).toBe(true);
      expect(result.discrepancies).toHaveLength(0);
    });

    it('should detect different responses', async () => {
      const oldData = { data: [{ id: '1' }] };
      const newData = { data: [{ id: '2' }] };
      const oldImpl = vi.fn().mockResolvedValue(oldData);
      const newImpl = vi.fn().mockResolvedValue(newData);

      const result = await compareImplementations('/api/test', oldImpl, newImpl);

      expect(result.equivalent).toBe(false);
      expect(result.discrepancies).toContain('Response data differs between implementations');
    });

    it('should detect inconsistent behavior (one succeeds, one fails)', async () => {
      const oldImpl = vi.fn().mockResolvedValue({ data: [] });
      const newImpl = vi.fn().mockRejectedValue(new Error('Failed'));

      const result = await compareImplementations('/api/test', oldImpl, newImpl);

      expect(result.equivalent).toBe(false);
      expect(result.discrepancies).toContain('One implementation succeeded while the other failed');
    });

    it('should handle both implementations failing with same error', async () => {
      const error = new Error('Same error');
      const oldImpl = vi.fn().mockRejectedValue(error);
      const newImpl = vi.fn().mockRejectedValue(error);

      const result = await compareImplementations('/api/test', oldImpl, newImpl);

      expect(result.equivalent).toBe(true);
      expect(result.discrepancies).toHaveLength(0);
    });
  });

  describe('Performance Monitoring Integration', () => {
    it('should track performance metrics during validation', async () => {
      const mockResponse = { data: [] };
      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      // The validation utilities track their own timing
      const result = await validateApiCall('/api/test', 'GET');

      // Validation should record response time
      expect(result.responseTime).toBeGreaterThan(0);
      expect(result.success).toBe(true);
    });

    it('should calculate average response time', async () => {
      const mockResponse = { data: [] };
      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const tests = [
        { endpoint: '/api/test1', method: 'GET' as const },
        { endpoint: '/api/test2', method: 'GET' as const },
        { endpoint: '/api/test3', method: 'GET' as const },
      ];

      const report = await runParallelValidation(tests);

      expect(report.averageResponseTime).toBeGreaterThan(0);
      expect(report.averageResponseTime).toBeLessThan(1000); // Should be fast for mocked calls
    });
  });

  describe('Type Safety Validation', () => {
    it('should maintain type safety with validation utilities', async () => {
      interface TestResponse {
        data: string[];
        count: number;
      }

      const mockResponse: TestResponse = {
        data: ['item1', 'item2'],
        count: 2,
      };

      (apiClient.get as jest.Mock).mockResolvedValue(mockResponse);

      const expectedResponse: ExpectedResponse = {
        customValidation: (response: TestResponse) => {
          if (!Array.isArray(response.data)) {
            return 'data should be array';
          }
          if (typeof response.count !== 'number') {
            return 'count should be number';
          }
          return null;
        },
      };

      const result = await validateApiCall('/api/test', 'GET', expectedResponse);

      expect(result.success).toBe(true);
      expect(result.discrepancies).toHaveLength(0);
    });
  });
});
