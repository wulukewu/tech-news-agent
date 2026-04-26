import { logger } from '@/lib/utils/logger';
/**
 * API Validation Utilities - Task 11.3
 * Requirements: 10.2, 10.3, 11.1
 *
 * This module provides utilities for validating API implementations:
 * - Parallel validation tests
 * - Response format comparison
 * - Error rate monitoring
 * - Discrepancy logging
 */

import { apiClient, ApiError } from './client';
import { performanceMonitor } from './performance';
import { apiLogger } from '../utils/logger';

/**
 * Validation result for a single API call
 */
export interface ValidationResult {
  endpoint: string;
  method: string;
  success: boolean;
  responseTime: number;
  statusCode?: number;
  error?: string;
  discrepancies: string[];
}

/**
 * Aggregated validation report
 */
export interface ValidationReport {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  averageResponseTime: number;
  errorRate: number;
  discrepancies: Array<{
    endpoint: string;
    type: string;
    description: string;
  }>;
  results: ValidationResult[];
}

/**
 * Expected response structure for validation
 */
export interface ExpectedResponse {
  hasDataField?: boolean;
  hasPaginationField?: boolean;
  hasErrorField?: boolean;
  hasErrorCodeField?: boolean;
  customValidation?: (response: any) => string | null; // Returns error message or null
}

/**
 * Validate a single API call
 *
 * @param endpoint - API endpoint to test
 * @param method - HTTP method (GET, POST, etc.)
 * @param expectedResponse - Expected response structure
 * @param requestData - Optional request data for POST/PUT/PATCH
 * @returns Validation result
 */
export async function validateApiCall(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'GET',
  expectedResponse: ExpectedResponse = {},
  requestData?: any
): Promise<ValidationResult> {
  const result: ValidationResult = {
    endpoint,
    method,
    success: false,
    responseTime: 0,
    discrepancies: [],
  };

  const startTime = performance.now();

  try {
    let response: any;

    // Make API call based on method
    switch (method) {
      case 'GET':
        response = await apiClient.get(endpoint);
        break;
      case 'POST':
        response = await apiClient.post(endpoint, requestData);
        break;
      case 'PUT':
        response = await apiClient.put(endpoint, requestData);
        break;
      case 'PATCH':
        response = await apiClient.patch(endpoint, requestData);
        break;
      case 'DELETE':
        response = await apiClient.delete(endpoint);
        break;
    }

    result.responseTime = performance.now() - startTime;
    result.statusCode = 200; // Successful response
    result.success = true;

    // Validate response structure
    if (expectedResponse.hasDataField && !response.hasOwnProperty('data')) {
      result.discrepancies.push('Missing "data" field in response');
    }

    if (expectedResponse.hasPaginationField && !response.hasOwnProperty('pagination')) {
      result.discrepancies.push('Missing "pagination" field in response');
    }

    // Custom validation
    if (expectedResponse.customValidation) {
      const customError = expectedResponse.customValidation(response);
      if (customError) {
        result.discrepancies.push(customError);
      }
    }

    // Log discrepancies
    if (result.discrepancies.length > 0) {
      logger.warn(`[API Validation] Discrepancies found for ${method} ${endpoint}:`, {
        discrepancies: result.discrepancies,
        response,
      });
    }
  } catch (error) {
    result.responseTime = performance.now() - startTime;
    result.success = false;

    const apiError = error as any;
    if (apiError.response) {
      result.statusCode = apiError.response.status;
      result.error = apiError.message || 'Unknown error';

      // Validate error structure
      if (expectedResponse.hasErrorField && !apiError.message) {
        result.discrepancies.push('Missing error message');
      }

      if (expectedResponse.hasErrorCodeField && !apiError.code) {
        result.discrepancies.push('Missing error code');
      }
    } else {
      result.error = error instanceof Error ? error.message : 'Unknown error';
      result.discrepancies.push('Error is not an API error response');
    }

    // Log error discrepancies
    if (result.discrepancies.length > 0) {
      logger.warn(`[API Validation] Error discrepancies for ${method} ${endpoint}:`, {
        discrepancies: result.discrepancies,
        error,
      });
    }
  }

  return result;
}

/**
 * Run parallel validation tests for multiple endpoints
 *
 * @param tests - Array of test configurations
 * @returns Validation report
 */
export async function runParallelValidation(
  tests: Array<{
    endpoint: string;
    method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
    expectedResponse?: ExpectedResponse;
    requestData?: any;
  }>
): Promise<ValidationReport> {
  logger.debug(`[API Validation] Running ${tests.length} parallel validation tests...`);

  // Clear performance metrics before testing
  performanceMonitor.clearMetrics();
  performanceMonitor.setEnabled(true);

  // Run all tests in parallel
  const results = await Promise.all(
    tests.map((test) =>
      validateApiCall(test.endpoint, test.method, test.expectedResponse, test.requestData)
    )
  );

  // Calculate statistics
  const passedTests = results.filter((r) => r.success && r.discrepancies.length === 0).length;
  const failedTests = results.length - passedTests;
  const totalResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0);
  const averageResponseTime = totalResponseTime / results.length;
  const errorRate = failedTests / results.length;

  // Collect all discrepancies
  const discrepancies: Array<{ endpoint: string; type: string; description: string }> = [];
  results.forEach((result) => {
    result.discrepancies.forEach((discrepancy) => {
      discrepancies.push({
        endpoint: `${result.method} ${result.endpoint}`,
        type: result.success ? 'response_format' : 'error_format',
        description: discrepancy,
      });
    });
  });

  const report: ValidationReport = {
    totalTests: results.length,
    passedTests,
    failedTests,
    averageResponseTime,
    errorRate,
    discrepancies,
    results,
  };

  // Log report summary
  logger.debug('[API Validation] Validation Report:', {
    totalTests: report.totalTests,
    passedTests: report.passedTests,
    failedTests: report.failedTests,
    averageResponseTime: `${report.averageResponseTime.toFixed(2)}ms`,
    errorRate: `${(report.errorRate * 100).toFixed(1)}%`,
    discrepanciesCount: report.discrepancies.length,
  });

  // Log discrepancies if any
  if (report.discrepancies.length > 0) {
    logger.warn('[API Validation] Discrepancies found:');
    report.discrepancies.forEach((d) => {
      logger.warn(`  - ${d.endpoint}: ${d.description} (${d.type})`);
    });
  }

  // Get performance stats
  const perfStats = performanceMonitor.getStats();
  logger.debug('[API Validation] Performance Statistics:', {
    totalRequests: perfStats.totalRequests,
    successRate: `${((perfStats.successfulRequests / perfStats.totalRequests) * 100).toFixed(1)}%`,
    averageResponseTime: `${perfStats.averageResponseTime.toFixed(2)}ms`,
    slowRequests: perfStats.slowRequestsCount,
  });

  return report;
}

/**
 * Compare two API implementations (old vs new)
 *
 * @param endpoint - API endpoint to test
 * @param oldImpl - Old implementation function
 * @param newImpl - New implementation function
 * @returns Comparison result
 */
export async function compareImplementations<T>(
  endpoint: string,
  oldImpl: () => Promise<T>,
  newImpl: () => Promise<T>
): Promise<{
  endpoint: string;
  equivalent: boolean;
  oldResult?: T;
  newResult?: T;
  oldError?: string;
  newError?: string;
  discrepancies: string[];
}> {
  const result: {
    endpoint: string;
    equivalent: boolean;
    oldResult?: T;
    newResult?: T;
    oldError?: string;
    newError?: string;
    discrepancies: string[];
  } = {
    endpoint,
    equivalent: false,
    discrepancies: [],
  };

  try {
    // Run both implementations in parallel
    const [oldResult, newResult] = await Promise.allSettled([oldImpl(), newImpl()]);

    // Both succeeded
    if (oldResult.status === 'fulfilled' && newResult.status === 'fulfilled') {
      result.oldResult = oldResult.value;
      result.newResult = newResult.value;

      // Compare results
      const oldJson = JSON.stringify(oldResult.value);
      const newJson = JSON.stringify(newResult.value);

      if (oldJson === newJson) {
        result.equivalent = true;
      } else {
        result.discrepancies.push('Response data differs between implementations');
        logger.warn(`[API Validation] Implementation discrepancy for ${endpoint}:`, {
          old: oldResult.value,
          new: newResult.value,
        });
      }
    }
    // Both failed
    else if (oldResult.status === 'rejected' && newResult.status === 'rejected') {
      result.oldError = oldResult.reason?.message || 'Unknown error';
      result.newError = newResult.reason?.message || 'Unknown error';

      // Compare error messages
      if (result.oldError === result.newError) {
        result.equivalent = true;
      } else {
        result.discrepancies.push('Error messages differ between implementations');
        logger.warn(`[API Validation] Error discrepancy for ${endpoint}:`, {
          oldError: result.oldError,
          newError: result.newError,
        });
      }
    }
    // One succeeded, one failed
    else {
      result.discrepancies.push('One implementation succeeded while the other failed');
      if (oldResult.status === 'fulfilled') {
        result.oldResult = oldResult.value;
        result.newError = (newResult as PromiseRejectedResult).reason?.message || 'Unknown error';
      } else {
        result.oldError = (oldResult as PromiseRejectedResult).reason?.message || 'Unknown error';
        result.newResult = (newResult as PromiseFulfilledResult<T>).value;
      }
      logger.warn(`[API Validation] Inconsistent behavior for ${endpoint}:`, {
        oldStatus: oldResult.status,
        newStatus: newResult.status,
      });
    }
  } catch (error) {
    result.discrepancies.push('Unexpected error during comparison');
    console.error(`[API Validation] Comparison error for ${endpoint}:`, error);
  }

  return result;
}

/**
 * Monitor error rates over time
 *
 * @param durationMs - Duration to monitor in milliseconds
 * @returns Error rate statistics
 */
export async function monitorErrorRates(durationMs: number = 60000): Promise<{
  duration: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  errorRate: number;
  errorsByCode: Record<string, number>;
}> {
  logger.debug(`[API Validation] Monitoring error rates for ${durationMs}ms...`);

  performanceMonitor.clearMetrics();
  performanceMonitor.setEnabled(true);

  const startTime = Date.now();
  const errorsByCode: Record<string, number> = {};

  // Monitor until duration expires
  await new Promise((resolve) => setTimeout(resolve, durationMs));

  const stats = performanceMonitor.getStats();
  const duration = Date.now() - startTime;

  // Get error breakdown from metrics
  const metrics = performanceMonitor.getMetrics();
  metrics.forEach((metric) => {
    if (!metric.success && metric.errorCode) {
      errorsByCode[metric.errorCode] = (errorsByCode[metric.errorCode] || 0) + 1;
    }
  });

  const result = {
    duration,
    totalRequests: stats.totalRequests,
    successfulRequests: stats.successfulRequests,
    failedRequests: stats.failedRequests,
    errorRate: stats.errorRate,
    errorsByCode,
  };

  logger.debug('[API Validation] Error rate monitoring complete:', {
    duration: `${duration}ms`,
    totalRequests: result.totalRequests,
    errorRate: `${(result.errorRate * 100).toFixed(1)}%`,
    errorsByCode: result.errorsByCode,
  });

  return result;
}

/**
 * Export validation report as JSON
 *
 * @param report - Validation report
 * @returns JSON string
 */
export function exportValidationReport(report: ValidationReport): string {
  return JSON.stringify(
    {
      ...report,
      timestamp: new Date().toISOString(),
      performanceStats: performanceMonitor.getStats(),
    },
    null,
    2
  );
}
