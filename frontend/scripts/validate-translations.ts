#!/usr/bin/env node
/* eslint-disable no-console, complexity, max-lines-per-function */

/**
 * Translation Validation Script
 *
 * This comprehensive script validates translation completeness and consistency between
 * zh-TW and en-US translation files. It performs the following checks:
 *
 * 1. All keys in zh-TW.json exist in en-US.json and vice versa
 * 2. All interpolation variables match between languages
 * 3. No duplicate keys within same file
 * 4. All translation values are non-empty strings
 * 5. Outputs detailed report of missing translations and mismatches
 *
 * Requirements: 11.5, 12.2, 12.3
 *
 * Usage:
 *   npm run validate:translations
 *   npx tsx scripts/validate-translations.ts
 *   node -r ts-node/register scripts/validate-translations.ts
 *
 * Exit codes:
 *   0 - All validations passed
 *   1 - Validation errors found
 */

import * as fs from 'fs';
import * as path from 'path';

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
} as const;

// Types for validation results
interface ValidationIssue {
  key: string;
  issue: 'missing' | 'empty' | 'interpolation-mismatch' | 'duplicate';
  language?: 'zh-TW' | 'en-US';
  details?: string;
  expected?: string[];
  actual?: string[];
}

interface ValidationReport {
  totalKeys: {
    zhTW: number;
    enUS: number;
  };
  issues: ValidationIssue[];
  duplicates: {
    zhTW: string[];
    enUS: string[];
  };
  summary: {
    missingKeys: number;
    emptyValues: number;
    interpolationMismatches: number;
    duplicateKeys: number;
  };
}

/**
 * Recursively flatten nested translation object into dot-notation keys
 * Also tracks the path to detect duplicates
 */
function flattenKeys(
  obj: Record<string, unknown>,
  prefix = '',
  pathTracker = new Set<string>()
): string[] {
  const keys: string[] = [];

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      const value = obj[key];

      // Check for duplicate keys at this level
      if (pathTracker.has(fullKey)) {
        throw new Error(`Duplicate key detected: ${fullKey}`);
      }
      pathTracker.add(fullKey);

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        // Recursively flatten nested objects
        keys.push(...flattenKeys(value as Record<string, unknown>, fullKey, pathTracker));
      } else {
        // Leaf node - add the key
        keys.push(fullKey);
      }
    }
  }

  return keys;
}

/**
 * Get value from nested object using dot notation
 */
function getNestedValue(obj: Record<string, unknown>, key: string): unknown {
  const keys = key.split('.');
  let value: unknown = obj;

  for (const k of keys) {
    if (
      value &&
      typeof value === 'object' &&
      value !== null &&
      k in (value as Record<string, unknown>)
    ) {
      value = (value as Record<string, unknown>)[k];
    } else {
      return undefined;
    }
  }

  return value;
}

/**
 * Check if a translation value is empty
 */
function isEmpty(value: unknown): boolean {
  return value === '' || value === null || value === undefined;
}

/**
 * Extract interpolation variables from a translation string
 * Matches patterns like {variable}, {count}, {name}, etc.
 */
function extractInterpolationVariables(text: string): string[] {
  if (typeof text !== 'string') {
    return [];
  }

  const matches = text.match(/\{(\w+)\}/g);
  if (!matches) {
    return [];
  }

  // Extract variable names without braces and sort for consistent comparison
  return matches.map((match) => match.slice(1, -1)).sort();
}

/**
 * Check for duplicate keys in a flat object structure
 */
function findDuplicateKeys(obj: Record<string, unknown>, prefix = ''): string[] {
  const duplicates: string[] = [];
  const seenKeys = new Set<string>();

  function traverse(current: Record<string, unknown>, currentPrefix: string) {
    for (const key in current) {
      if (Object.prototype.hasOwnProperty.call(current, key)) {
        const fullKey = currentPrefix ? `${currentPrefix}.${key}` : key;

        if (seenKeys.has(fullKey)) {
          duplicates.push(fullKey);
        } else {
          seenKeys.add(fullKey);
        }

        const value = current[key];
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
          traverse(value as Record<string, unknown>, fullKey);
        }
      }
    }
  }

  traverse(obj, prefix);
  return duplicates;
}

/**
 * Load and parse a translation file with error handling
 */
function loadTranslationFile(filePath: string): Record<string, unknown> {
  try {
    if (!fs.existsSync(filePath)) {
      throw new Error(`Translation file not found: ${filePath}`);
    }

    const content = fs.readFileSync(filePath, 'utf-8');

    // Validate JSON syntax
    let parsed;
    try {
      parsed = JSON.parse(content);
    } catch (jsonError) {
      throw new Error(`Invalid JSON syntax in ${filePath}: ${jsonError}`);
    }

    return parsed;
  } catch (error) {
    if (process.env.NODE_ENV !== 'test') {
      console.error(`${colors.red}Error loading ${filePath}:${colors.reset}`, error);
      process.exit(1);
    }
    throw error;
  }
}

/**
 * Validate translation completeness and consistency
 */
function validateTranslations(): ValidationReport {
  const localesDir = path.join(__dirname, '..', 'locales');
  const zhTWPath = path.join(localesDir, 'zh-TW.json');
  const enUSPath = path.join(localesDir, 'en-US.json');

  console.log(`${colors.cyan}Loading translation files...${colors.reset}`);

  // Load translation files
  const zhTW = loadTranslationFile(zhTWPath);
  const enUS = loadTranslationFile(enUSPath);

  console.log(`${colors.cyan}Validating translation structure...${colors.reset}`);

  // Check for duplicate keys
  const zhTWDuplicates = findDuplicateKeys(zhTW);
  const enUSDuplicates = findDuplicateKeys(enUS);

  // Flatten keys with duplicate detection
  let zhTWKeys: string[] = [];
  let enUSKeys: string[] = [];

  try {
    zhTWKeys = flattenKeys(zhTW);
  } catch (error) {
    console.error(`${colors.red}Error in zh-TW.json:${colors.reset}`, error);
  }

  try {
    enUSKeys = flattenKeys(enUS);
  } catch (error) {
    console.error(`${colors.red}Error in en-US.json:${colors.reset}`, error);
  }

  console.log(`${colors.cyan}Analyzing translation completeness...${colors.reset}`);

  const issues: ValidationIssue[] = [];

  // Check for keys in zh-TW but not in en-US
  for (const key of zhTWKeys) {
    if (!enUSKeys.includes(key)) {
      issues.push({
        key,
        issue: 'missing',
        language: 'en-US',
        details: `Key exists in zh-TW but missing in en-US`,
      });
    } else {
      // Check if en-US value is empty
      const enUSValue = getNestedValue(enUS, key);
      if (isEmpty(enUSValue)) {
        issues.push({
          key,
          issue: 'empty',
          language: 'en-US',
          details: `Key exists but value is empty`,
        });
      } else {
        // Check interpolation variable consistency
        const zhTWValue = getNestedValue(zhTW, key);
        const zhTWVars = extractInterpolationVariables(zhTWValue as string);
        const enUSVars = extractInterpolationVariables(enUSValue as string);

        if (zhTWVars.length !== enUSVars.length || !zhTWVars.every((v) => enUSVars.includes(v))) {
          issues.push({
            key,
            issue: 'interpolation-mismatch',
            details: `Interpolation variables don't match between languages`,
            expected: zhTWVars,
            actual: enUSVars,
          });
        }
      }
    }
  }

  // Check for keys in en-US but not in zh-TW
  for (const key of enUSKeys) {
    if (!zhTWKeys.includes(key)) {
      issues.push({
        key,
        issue: 'missing',
        language: 'zh-TW',
        details: `Key exists in en-US but missing in zh-TW`,
      });
    } else {
      // Check if zh-TW value is empty (only if not already checked above)
      const zhTWValue = getNestedValue(zhTW, key);
      if (isEmpty(zhTWValue)) {
        issues.push({
          key,
          issue: 'empty',
          language: 'zh-TW',
          details: `Key exists but value is empty`,
        });
      }
    }
  }

  // Add duplicate key issues
  for (const duplicateKey of zhTWDuplicates) {
    issues.push({
      key: duplicateKey,
      issue: 'duplicate',
      language: 'zh-TW',
      details: `Duplicate key found in zh-TW.json`,
    });
  }

  for (const duplicateKey of enUSDuplicates) {
    issues.push({
      key: duplicateKey,
      issue: 'duplicate',
      language: 'en-US',
      details: `Duplicate key found in en-US.json`,
    });
  }

  // Calculate summary statistics
  const summary = {
    missingKeys: issues.filter((i) => i.issue === 'missing').length,
    emptyValues: issues.filter((i) => i.issue === 'empty').length,
    interpolationMismatches: issues.filter((i) => i.issue === 'interpolation-mismatch').length,
    duplicateKeys: issues.filter((i) => i.issue === 'duplicate').length,
  };

  return {
    totalKeys: {
      zhTW: zhTWKeys.length,
      enUS: enUSKeys.length,
    },
    issues,
    duplicates: {
      zhTW: zhTWDuplicates,
      enUS: enUSDuplicates,
    },
    summary,
  };
}

/**
 * Print a detailed validation report
 */
function printReport(report: ValidationReport): void {
  console.log(
    `\n${colors.bold}${colors.cyan}═══════════════════════════════════════════════════════════════${colors.reset}`
  );
  console.log(
    `${colors.bold}${colors.cyan}                    TRANSLATION VALIDATION REPORT${colors.reset}`
  );
  console.log(
    `${colors.bold}${colors.cyan}═══════════════════════════════════════════════════════════════${colors.reset}\n`
  );

  // Overview statistics
  console.log(`${colors.bold}📊 Overview:${colors.reset}`);
  console.log(`${colors.blue}   Total keys in zh-TW.json:${colors.reset} ${report.totalKeys.zhTW}`);
  console.log(`${colors.blue}   Total keys in en-US.json:${colors.reset} ${report.totalKeys.enUS}`);
  console.log(`${colors.blue}   Total issues found:${colors.reset} ${report.issues.length}\n`);

  if (report.issues.length === 0) {
    console.log(`${colors.green}${colors.bold}✅ VALIDATION PASSED${colors.reset}`);
    console.log(
      `${colors.green}   All translation validations passed successfully!${colors.reset}`
    );
    console.log(`${colors.green}   • All keys exist in both language files${colors.reset}`);
    console.log(`${colors.green}   • All values are non-empty strings${colors.reset}`);
    console.log(`${colors.green}   • All interpolation variables match${colors.reset}`);
    console.log(`${colors.green}   • No duplicate keys found${colors.reset}\n`);
    return;
  }

  console.log(`${colors.red}${colors.bold}❌ VALIDATION FAILED${colors.reset}`);
  console.log(
    `${colors.red}   Found ${report.issues.length} issue(s) that need attention${colors.reset}\n`
  );

  // Summary by issue type
  console.log(`${colors.bold}📋 Issue Summary:${colors.reset}`);
  if (report.summary.missingKeys > 0) {
    console.log(`${colors.red}   • Missing keys: ${report.summary.missingKeys}${colors.reset}`);
  }
  if (report.summary.emptyValues > 0) {
    console.log(`${colors.yellow}   • Empty values: ${report.summary.emptyValues}${colors.reset}`);
  }
  if (report.summary.interpolationMismatches > 0) {
    console.log(
      `${colors.magenta}   • Interpolation mismatches: ${report.summary.interpolationMismatches}${colors.reset}`
    );
  }
  if (report.summary.duplicateKeys > 0) {
    console.log(`${colors.red}   • Duplicate keys: ${report.summary.duplicateKeys}${colors.reset}`);
  }
  console.log('');

  // Group issues by type for detailed reporting
  const missingInEnUS = report.issues.filter(
    (i) => i.issue === 'missing' && i.language === 'en-US'
  );
  const missingInZhTW = report.issues.filter(
    (i) => i.issue === 'missing' && i.language === 'zh-TW'
  );
  const emptyInEnUS = report.issues.filter((i) => i.issue === 'empty' && i.language === 'en-US');
  const emptyInZhTW = report.issues.filter((i) => i.issue === 'empty' && i.language === 'zh-TW');
  const interpolationMismatches = report.issues.filter((i) => i.issue === 'interpolation-mismatch');
  const duplicatesInZhTW = report.issues.filter(
    (i) => i.issue === 'duplicate' && i.language === 'zh-TW'
  );
  const duplicatesInEnUS = report.issues.filter(
    (i) => i.issue === 'duplicate' && i.language === 'en-US'
  );

  // Report missing keys in en-US
  if (missingInEnUS.length > 0) {
    console.log(
      `${colors.red}${colors.bold}🚫 Missing in en-US.json (${missingInEnUS.length}):${colors.reset}`
    );
    missingInEnUS.forEach((issue, index) => {
      console.log(
        `${colors.dim}   ${index + 1}.${colors.reset} ${colors.red}${issue.key}${colors.reset}`
      );
      console.log(`${colors.dim}      ${issue.details}${colors.reset}`);
    });
    console.log('');
  }

  // Report missing keys in zh-TW
  if (missingInZhTW.length > 0) {
    console.log(
      `${colors.red}${colors.bold}🚫 Missing in zh-TW.json (${missingInZhTW.length}):${colors.reset}`
    );
    missingInZhTW.forEach((issue, index) => {
      console.log(
        `${colors.dim}   ${index + 1}.${colors.reset} ${colors.red}${issue.key}${colors.reset}`
      );
      console.log(`${colors.dim}      ${issue.details}${colors.reset}`);
    });
    console.log('');
  }

  // Report empty values in en-US
  if (emptyInEnUS.length > 0) {
    console.log(
      `${colors.yellow}${colors.bold}⚠️  Empty values in en-US.json (${emptyInEnUS.length}):${colors.reset}`
    );
    emptyInEnUS.forEach((issue, index) => {
      console.log(
        `${colors.dim}   ${index + 1}.${colors.reset} ${colors.yellow}${issue.key}${colors.reset}`
      );
      console.log(`${colors.dim}      ${issue.details}${colors.reset}`);
    });
    console.log('');
  }

  // Report empty values in zh-TW
  if (emptyInZhTW.length > 0) {
    console.log(
      `${colors.yellow}${colors.bold}⚠️  Empty values in zh-TW.json (${emptyInZhTW.length}):${colors.reset}`
    );
    emptyInZhTW.forEach((issue, index) => {
      console.log(
        `${colors.dim}   ${index + 1}.${colors.reset} ${colors.yellow}${issue.key}${colors.reset}`
      );
      console.log(`${colors.dim}      ${issue.details}${colors.reset}`);
    });
    console.log('');
  }

  // Report interpolation mismatches
  if (interpolationMismatches.length > 0) {
    console.log(
      `${colors.magenta}${colors.bold}🔀 Interpolation variable mismatches (${interpolationMismatches.length}):${colors.reset}`
    );
    interpolationMismatches.forEach((issue, index) => {
      console.log(
        `${colors.dim}   ${index + 1}.${colors.reset} ${colors.magenta}${issue.key}${colors.reset}`
      );
      console.log(`${colors.dim}      ${issue.details}${colors.reset}`);
      if (issue.expected && issue.actual) {
        console.log(`${colors.dim}      Expected: [${issue.expected.join(', ')}]${colors.reset}`);
        console.log(`${colors.dim}      Actual:   [${issue.actual.join(', ')}]${colors.reset}`);
      }
    });
    console.log('');
  }

  // Report duplicate keys in zh-TW
  if (duplicatesInZhTW.length > 0) {
    console.log(
      `${colors.red}${colors.bold}🔄 Duplicate keys in zh-TW.json (${duplicatesInZhTW.length}):${colors.reset}`
    );
    duplicatesInZhTW.forEach((issue, index) => {
      console.log(
        `${colors.dim}   ${index + 1}.${colors.reset} ${colors.red}${issue.key}${colors.reset}`
      );
      console.log(`${colors.dim}      ${issue.details}${colors.reset}`);
    });
    console.log('');
  }

  // Report duplicate keys in en-US
  if (duplicatesInEnUS.length > 0) {
    console.log(
      `${colors.red}${colors.bold}🔄 Duplicate keys in en-US.json (${duplicatesInEnUS.length}):${colors.reset}`
    );
    duplicatesInEnUS.forEach((issue, index) => {
      console.log(
        `${colors.dim}   ${index + 1}.${colors.reset} ${colors.red}${issue.key}${colors.reset}`
      );
      console.log(`${colors.dim}      ${issue.details}${colors.reset}`);
    });
    console.log('');
  }

  // Recommendations
  console.log(`${colors.bold}💡 Recommendations:${colors.reset}`);
  if (report.summary.missingKeys > 0) {
    console.log(
      `${colors.cyan}   • Add missing keys to maintain translation completeness${colors.reset}`
    );
  }
  if (report.summary.emptyValues > 0) {
    console.log(`${colors.cyan}   • Provide translations for empty values${colors.reset}`);
  }
  if (report.summary.interpolationMismatches > 0) {
    console.log(
      `${colors.cyan}   • Ensure interpolation variables match between languages${colors.reset}`
    );
  }
  if (report.summary.duplicateKeys > 0) {
    console.log(`${colors.cyan}   • Remove or rename duplicate keys${colors.reset}`);
  }
  console.log('');
}

/**
 * Main execution function
 */
function main(): void {
  console.log(`${colors.bold}${colors.cyan}Translation Validation Script${colors.reset}`);
  console.log(
    `${colors.dim}Validating translation completeness and consistency...${colors.reset}\n`
  );

  try {
    const report = validateTranslations();
    printReport(report);

    // Exit with appropriate code
    if (report.issues.length === 0) {
      process.exit(0);
    } else {
      process.exit(1);
    }
  } catch (error) {
    console.error(
      `${colors.red}${colors.bold}Fatal error during validation:${colors.reset}`,
      error
    );
    process.exit(1);
  }
}

// Run the script if called directly
if (require.main === module) {
  main();
}

export { validateTranslations };
export type { ValidationReport, ValidationIssue };
