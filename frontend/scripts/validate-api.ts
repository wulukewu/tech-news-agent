#!/usr/bin/env ts-node
/**
 * API Validation Script - Task 11.3
 * Requirements: 10.2, 10.3, 11.1
 *
 * This script validates the unified API client implementation by:
 * - Running parallel validation tests against real backend
 * - Comparing response formats
 * - Monitoring error rates
 * - Logging discrepancies
 *
 * Usage:
 *   npm run validate-api
 *   or
 *   ts-node frontend/scripts/validate-api.ts
 */

import { runParallelValidation, exportValidationReport } from '../lib/api/validation';
import { performanceMonitor } from '../lib/api/performance';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Main validation function
 */
async function main() {
  console.log('='.repeat(80));
  console.log('API Validation Script - Task 11.3');
  console.log('='.repeat(80));
  console.log('');

  // Define test cases for all API endpoints
  const tests = [
    // Articles API
    {
      endpoint: '/api/articles/categories',
      method: 'GET' as const,
      expectedResponse: {
        hasDataField: false, // Returns { categories: string[] }
        customValidation: (response: any) => {
          if (!response.categories || !Array.isArray(response.categories)) {
            return 'Missing or invalid "categories" field';
          }
          return null;
        },
      },
    },
    {
      endpoint: '/api/articles/me?page=1&page_size=20',
      method: 'GET' as const,
      expectedResponse: {
        hasDataField: true,
        hasPaginationField: true,
        customValidation: (response: any) => {
          if (!Array.isArray(response.data)) {
            return '"data" field should be an array';
          }
          if (!response.pagination.page || !response.pagination.page_size) {
            return 'Invalid pagination structure';
          }
          return null;
        },
      },
    },

    // Auth API
    {
      endpoint: '/api/auth/me',
      method: 'GET' as const,
      expectedResponse: {
        customValidation: (response: any) => {
          if (!response.id || !response.email) {
            return 'Missing user fields (id, email)';
          }
          return null;
        },
      },
    },

    // Feeds API
    {
      endpoint: '/api/feeds',
      method: 'GET' as const,
      expectedResponse: {
        customValidation: (response: any) => {
          if (!Array.isArray(response)) {
            return 'Response should be an array of feeds';
          }
          return null;
        },
      },
    },

    // Reading List API
    {
      endpoint: '/api/reading-list?page=1&page_size=20',
      method: 'GET' as const,
      expectedResponse: {
        hasDataField: true,
        hasPaginationField: true,
        customValidation: (response: any) => {
          if (!Array.isArray(response.data)) {
            return '"data" field should be an array';
          }
          return null;
        },
      },
    },

    // Scheduler API
    {
      endpoint: '/api/scheduler/status',
      method: 'GET' as const,
      expectedResponse: {
        customValidation: (response: any) => {
          if (!response.status) {
            return 'Missing "status" field';
          }
          return null;
        },
      },
    },
  ];

  console.log(`Running ${tests.length} validation tests...\n`);

  // Run parallel validation
  const report = await runParallelValidation(tests);

  console.log('\n' + '='.repeat(80));
  console.log('Validation Report Summary');
  console.log('='.repeat(80));
  console.log(`Total Tests: ${report.totalTests}`);
  console.log(
    `Passed: ${report.passedTests} (${((report.passedTests / report.totalTests) * 100).toFixed(
      1
    )}%)`
  );
  console.log(
    `Failed: ${report.failedTests} (${((report.failedTests / report.totalTests) * 100).toFixed(
      1
    )}%)`
  );
  console.log(`Average Response Time: ${report.averageResponseTime.toFixed(2)}ms`);
  console.log(`Error Rate: ${(report.errorRate * 100).toFixed(1)}%`);
  console.log(`Discrepancies Found: ${report.discrepancies.length}`);
  console.log('');

  // Display detailed results
  if (report.discrepancies.length > 0) {
    console.log('Discrepancies:');
    report.discrepancies.forEach((d, i) => {
      console.log(`  ${i + 1}. ${d.endpoint}`);
      console.log(`     Type: ${d.type}`);
      console.log(`     Description: ${d.description}`);
    });
    console.log('');
  }

  // Display performance statistics
  const perfStats = performanceMonitor.getStats();
  console.log('Performance Statistics:');
  console.log(`  Total Requests: ${perfStats.totalRequests}`);
  console.log(`  Successful: ${perfStats.successfulRequests}`);
  console.log(`  Failed: ${perfStats.failedRequests}`);
  console.log(`  Average Response Time: ${perfStats.averageResponseTime.toFixed(2)}ms`);
  console.log(`  Min Response Time: ${perfStats.minResponseTime.toFixed(2)}ms`);
  console.log(`  Max Response Time: ${perfStats.maxResponseTime.toFixed(2)}ms`);
  console.log(`  Slow Requests (>1s): ${perfStats.slowRequestsCount}`);
  console.log('');

  // Display per-endpoint statistics
  if (Object.keys(perfStats.byEndpoint).length > 0) {
    console.log('Per-Endpoint Statistics:');
    Object.entries(perfStats.byEndpoint)
      .sort((a, b) => b[1].averageTime - a[1].averageTime)
      .forEach(([endpoint, stats]) => {
        console.log(`  ${endpoint}:`);
        console.log(`    Calls: ${stats.count}`);
        console.log(`    Avg Time: ${stats.averageTime.toFixed(2)}ms`);
        console.log(`    Errors: ${stats.errorCount}`);
      });
    console.log('');
  }

  // Export report to file
  const reportJson = exportValidationReport(report);
  const reportPath = path.join(__dirname, '..', 'validation-report.json');
  fs.writeFileSync(reportPath, reportJson);
  console.log(`Validation report exported to: ${reportPath}`);
  console.log('');

  // Exit with appropriate code
  if (report.failedTests > 0 || report.discrepancies.length > 0) {
    console.log('❌ Validation completed with issues');
    process.exit(1);
  } else {
    console.log('✅ Validation completed successfully');
    process.exit(0);
  }
}

// Run main function
main().catch((error) => {
  console.error('Fatal error during validation:', error);
  process.exit(1);
});
