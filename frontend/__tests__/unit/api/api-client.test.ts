/**
 * Unit tests for API Client
 * Tests the exported apiClient axios instance
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/lib/config', () => ({
  getRuntimeConfig: vi.fn().mockResolvedValue({ apiBaseUrl: 'http://localhost:8000' }),
}));

vi.mock('@/lib/utils/logger', () => ({
  logger: { error: vi.fn(), warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}));

import { apiClient } from '@/lib/api/client';

describe('apiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should be defined', () => {
    expect(apiClient).toBeDefined();
  });

  it('should have interceptors configured', () => {
    expect(apiClient.interceptors).toBeDefined();
    expect(apiClient.interceptors.request).toBeDefined();
    expect(apiClient.interceptors.response).toBeDefined();
  });

  it('should have a timeout configured', () => {
    expect(apiClient.defaults.timeout).toBe(30000);
  });

  it('should have JSON content-type header', () => {
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
  });
});
