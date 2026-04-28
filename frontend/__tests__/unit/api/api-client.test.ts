/**
 * Unit tests for API Client
 * Tests singleton pattern, interceptor support, and HTTP methods
 *
 * Requirements: 1.1, 1.3
 */

// Mock axios before any imports
vi.mock('axios', () => {
  const mockAxiosInstance = {
    interceptors: {
      request: {
        use: vi.fn().mockReturnValue(0),
        eject: vi.fn(),
      },
      response: {
        use: vi.fn().mockReturnValue(0),
        eject: vi.fn(),
      },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };

  return {
    __esModule: true,
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
    create: vi.fn(() => mockAxiosInstance),
  };
});

import axios from 'axios';
import ApiClient, { apiClient } from '@/lib/api/client';

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('ApiClient', () => {
  let mockAxiosInstance: any;

  beforeAll(() => {
    // Get the mock instance that was created
    mockAxiosInstance = (axios.create as jest.Mock)();
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Singleton Pattern (Requirement 1.1)', () => {
    it('should return the same instance on multiple calls to getInstance', () => {
      const instance1 = ApiClient.getInstance();
      const instance2 = ApiClient.getInstance();
      const instance3 = ApiClient.getInstance();

      expect(instance1).toBe(instance2);
      expect(instance2).toBe(instance3);
    });

    it('should have axios instance configured', () => {
      const client = ApiClient.getInstance();
      const axiosInstance = client.getAxiosInstance();

      // Verify the instance has interceptors configured
      expect(axiosInstance.interceptors).toBeDefined();
      expect(axiosInstance.interceptors.request).toBeDefined();
      expect(axiosInstance.interceptors.response).toBeDefined();
    });
  });

  describe('Interceptor Support (Requirement 1.3)', () => {
    it('should allow adding custom request interceptors', () => {
      const client = ApiClient.getInstance();
      const requestInterceptor = {
        onFulfilled: vi.fn((config) => config),
        onRejected: vi.fn((error) => Promise.reject(error)),
      };

      const interceptorId = client.addRequestInterceptor(requestInterceptor);

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledWith(
        requestInterceptor.onFulfilled,
        requestInterceptor.onRejected
      );
      expect(typeof interceptorId).toBe('number');
    });

    it('should allow adding custom response interceptors', () => {
      const client = ApiClient.getInstance();
      const responseInterceptor = {
        onFulfilled: vi.fn((response) => response),
        onRejected: vi.fn((error) => Promise.reject(error)),
      };

      const interceptorId = client.addResponseInterceptor(responseInterceptor);

      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalledWith(
        responseInterceptor.onFulfilled,
        responseInterceptor.onRejected
      );
      expect(typeof interceptorId).toBe('number');
    });

    it('should allow removing request interceptors', () => {
      const client = ApiClient.getInstance();
      const requestInterceptor = {
        onFulfilled: vi.fn((config) => config),
      };

      const interceptorId = client.addRequestInterceptor(requestInterceptor);
      client.removeRequestInterceptor(interceptorId);

      expect(mockAxiosInstance.interceptors.request.eject).toHaveBeenCalledWith(interceptorId);
    });

    it('should allow removing response interceptors', () => {
      const client = ApiClient.getInstance();
      const responseInterceptor = {
        onFulfilled: vi.fn((response) => response),
      };

      const interceptorId = client.addResponseInterceptor(responseInterceptor);
      client.removeResponseInterceptor(interceptorId);

      expect(mockAxiosInstance.interceptors.response.eject).toHaveBeenCalledWith(interceptorId);
    });
  });

  describe('HTTP Methods (Requirement 1.5)', () => {
    it('should perform GET request and return data', async () => {
      const client = ApiClient.getInstance();
      const mockData = { id: 1, name: 'Test' };
      mockAxiosInstance.get.mockResolvedValue({ data: mockData });

      const result = await client.get('/test');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', undefined);
      expect(result).toEqual(mockData);
    });

    it('should perform POST request and return data', async () => {
      const client = ApiClient.getInstance();
      const mockData = { id: 1, name: 'Test' };
      const postData = { name: 'Test' };
      mockAxiosInstance.post.mockResolvedValue({ data: mockData });

      const result = await client.post('/test', postData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', postData, undefined);
      expect(result).toEqual(mockData);
    });

    it('should perform PUT request and return data', async () => {
      const client = ApiClient.getInstance();
      const mockData = { id: 1, name: 'Updated' };
      const putData = { name: 'Updated' };
      mockAxiosInstance.put.mockResolvedValue({ data: mockData });

      const result = await client.put('/test/1', putData);

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test/1', putData, undefined);
      expect(result).toEqual(mockData);
    });

    it('should perform PATCH request and return data', async () => {
      const client = ApiClient.getInstance();
      const mockData = { id: 1, name: 'Patched' };
      const patchData = { name: 'Patched' };
      mockAxiosInstance.patch.mockResolvedValue({ data: mockData });

      const result = await client.patch('/test/1', patchData);

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/test/1', patchData, undefined);
      expect(result).toEqual(mockData);
    });

    it('should perform DELETE request and return data', async () => {
      const client = ApiClient.getInstance();
      const mockData = { success: true };
      mockAxiosInstance.delete.mockResolvedValue({ data: mockData });

      const result = await client.delete('/test/1');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test/1', undefined);
      expect(result).toEqual(mockData);
    });
  });

  describe('Axios Instance Access', () => {
    it('should provide access to underlying axios instance', () => {
      const client = ApiClient.getInstance();
      const axiosInstance = client.getAxiosInstance();

      expect(axiosInstance).toBe(mockAxiosInstance);
    });
  });

  describe('Exported apiClient', () => {
    it('should export a singleton instance', () => {
      expect(apiClient).toBeInstanceOf(ApiClient);
    });
  });
});
