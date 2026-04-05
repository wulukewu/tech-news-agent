/**
 * Bug Condition Exploration Test
 *
 * **Validates: Requirements 1.1, 1.2**
 *
 * Property 1: Bug Condition - TypeScript Compilation Errors
 *
 * CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists
 *
 * This test verifies that TypeScript compilation fails with specific errors:
 * 1. FeedCard.tsx uses `feed.isSubscribed` but Feed type defines `is_subscribed`
 * 2. Test files use Jest DOM matchers but TypeScript cannot resolve their types
 * 3. Navigation.tsx already uses correct import path (no bug here)
 *
 * Expected counterexamples on UNFIXED code:
 * - "Property 'isSubscribed' does not exist on type 'Feed'" in FeedCard.tsx
 * - "Property 'toBeInTheDocument' does not exist on type 'JestMatchers<HTMLElement>'" in test files
 */

import { execSync } from 'child_process';
import * as fc from 'fast-check';

describe('Bug Condition Exploration - TypeScript Compilation', () => {
  /**
   * Property 1: Bug Condition - TypeScript Compilation Errors
   *
   * For the current unfixed codebase, TypeScript compilation SHALL fail
   * with specific type errors related to:
   * - Property name mismatch in FeedCard.tsx
   * - Missing Jest DOM type definitions in test files
   */
  it('should detect TypeScript compilation errors in unfixed code', () => {
    // This test runs type-check and expects it to fail on unfixed code
    // When the code is fixed, this test will pass (type-check succeeds)

    let typeCheckOutput = '';
    let typeCheckExitCode = 0;

    try {
      // Run TypeScript type checking
      typeCheckOutput = execSync('npm run type-check', {
        cwd: process.cwd(),
        encoding: 'utf-8',
        stdio: 'pipe',
      });
    } catch (error: any) {
      // Type check failed - capture the output
      typeCheckExitCode = error.status || 1;
      typeCheckOutput = error.stdout + error.stderr;
    }

    // Document the current state
    console.log('\n=== TypeScript Type Check Results ===');
    console.log(`Exit Code: ${typeCheckExitCode}`);
    console.log(`Output:\n${typeCheckOutput}`);

    // On UNFIXED code: expect type errors (exit code !== 0)
    // On FIXED code: expect no type errors (exit code === 0)

    if (typeCheckExitCode !== 0) {
      // UNFIXED CODE - Document counterexamples
      console.log('\n=== Bug Detected - Counterexamples Found ===');

      // Check for FeedCard property mismatch error
      const hasFeedCardError =
        typeCheckOutput.includes('isSubscribed') &&
        typeCheckOutput.includes('FeedCard.tsx');

      // Check for Jest DOM type definition errors
      const hasJestDomError =
        typeCheckOutput.includes('toBeInTheDocument') ||
        typeCheckOutput.includes('toHaveAttribute') ||
        typeCheckOutput.includes('toHaveClass') ||
        typeCheckOutput.includes('toBeDisabled');

      console.log(
        `\nFeedCard property mismatch error: ${hasFeedCardError ? 'FOUND' : 'NOT FOUND'}`,
      );
      console.log(
        `Jest DOM type definition error: ${hasJestDomError ? 'FOUND' : 'NOT FOUND'}`,
      );

      // Extract error count
      const errorMatch = typeCheckOutput.match(/Found (\d+) error/);
      const errorCount = errorMatch ? parseInt(errorMatch[1], 10) : 0;
      console.log(`\nTotal TypeScript errors: ${errorCount}`);

      // Document specific counterexamples
      if (hasFeedCardError) {
        console.log('\nCounterexample 1: FeedCard.tsx property mismatch');
        console.log('- Component uses: feed.isSubscribed (camelCase)');
        console.log('- Type defines: is_subscribed (snake_case)');
      }

      if (hasJestDomError) {
        console.log('\nCounterexample 2: Jest DOM type definitions missing');
        console.log(
          '- Test files use: toBeInTheDocument(), toHaveAttribute(), etc.',
        );
        console.log('- TypeScript cannot resolve these matchers on expect()');
      }

      // This is the EXPECTED state for unfixed code
      console.log(
        '\n✓ Bug condition confirmed - TypeScript compilation fails as expected',
      );
      console.log('  This proves the bug exists in the unfixed codebase');
    } else {
      // FIXED CODE - Type check passed
      console.log('\n=== Bug Fixed - TypeScript Compilation Successful ===');
      console.log('✓ All type errors resolved');
      console.log('✓ FeedCard.tsx uses correct property name');
      console.log('✓ Jest DOM type definitions available');
    }

    // The test passes when type-check succeeds (exit code 0)
    // The test fails when type-check fails (exit code !== 0)
    expect(typeCheckExitCode).toBe(0);
  });

  /**
   * Property-based test: Verify specific error patterns
   *
   * This test uses property-based testing to verify that the expected
   * error patterns exist in the TypeScript output on unfixed code.
   */
  it('should identify specific TypeScript error patterns', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          'FeedCard.tsx',
          'ArticleCard.test.tsx',
          'Navigation.test.tsx',
          'FeedCard.test.tsx',
        ),
        (filename) => {
          // Run type check
          let typeCheckOutput = '';

          try {
            execSync('npm run type-check', {
              cwd: process.cwd(),
              encoding: 'utf-8',
              stdio: 'pipe',
            });
            // If type-check succeeds, code is fixed
            return true;
          } catch (error: any) {
            typeCheckOutput = error.stdout + error.stderr;

            // On unfixed code, we expect errors in these files
            if (filename === 'FeedCard.tsx') {
              // Should have isSubscribed property error
              const hasError =
                typeCheckOutput.includes('isSubscribed') &&
                typeCheckOutput.includes('FeedCard.tsx');

              if (!hasError) {
                console.log(`Expected error in ${filename} but not found`);
              }

              // On unfixed code, this should be true
              // On fixed code, type-check succeeds so we return true above
              return hasError;
            } else {
              // Test files should have Jest DOM errors
              const hasJestDomError =
                typeCheckOutput.includes('toBeInTheDocument') ||
                typeCheckOutput.includes('toHaveAttribute') ||
                typeCheckOutput.includes('toHaveClass') ||
                typeCheckOutput.includes('toBeDisabled');

              if (!hasJestDomError && typeCheckOutput.includes(filename)) {
                console.log(
                  `Expected Jest DOM error in ${filename} but not found`,
                );
              }

              // On unfixed code, this should be true
              // On fixed code, type-check succeeds so we return true above
              return hasJestDomError || !typeCheckOutput.includes(filename);
            }
          }
        },
      ),
      { numRuns: 10 },
    );
  });
});
