#!/usr/bin/env node

/**
 * Find Missing Translations Script
 *
 * This script identifies translation keys that exist in one language file but not the other,
 * and reports keys with empty values. It helps maintain translation completeness across
 * all supported languages.
 *
 * Usage:
 *   npm run find:missing-translations
 *   node scripts/find-missing-translations.js
 *
 * Exit codes:
 *   0 - All translations are complete
 *   1 - Missing translations found
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

/**
 * Recursively flatten nested translation object into dot-notation keys
 */
function flattenKeys(obj, prefix = '') {
  const keys = [];

  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      const value = obj[key];

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        // Recursively flatten nested objects
        keys.push(...flattenKeys(value, fullKey));
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
function getNestedValue(obj, key) {
  const keys = key.split('.');
  let value = obj;

  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return undefined;
    }
  }

  return value;
}

/**
 * Check if a translation value is empty
 */
function isEmpty(value) {
  return value === '' || value === null || value === undefined;
}

/**
 * Load and parse a translation file
 */
function loadTranslationFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`${colors.red}Error loading ${filePath}:${colors.reset}`, error);
    process.exit(1);
  }
}

/**
 * Main function to find missing translations
 */
function findMissingTranslations() {
  const localesDir = path.join(__dirname, '..', 'locales');
  const zhTWPath = path.join(localesDir, 'zh-TW.json');
  const enUSPath = path.join(localesDir, 'en-US.json');

  // Check if translation files exist
  if (!fs.existsSync(zhTWPath)) {
    console.error(`${colors.red}Error: zh-TW.json not found at ${zhTWPath}${colors.reset}`);
    process.exit(1);
  }

  if (!fs.existsSync(enUSPath)) {
    console.error(`${colors.red}Error: en-US.json not found at ${enUSPath}${colors.reset}`);
    process.exit(1);
  }

  // Load translation files
  const zhTW = loadTranslationFile(zhTWPath);
  const enUS = loadTranslationFile(enUSPath);

  // Flatten keys
  const zhTWKeys = flattenKeys(zhTW);
  const enUSKeys = flattenKeys(enUS);

  // Find issues
  const issues = [];

  // Check for keys in zh-TW but not in en-US
  for (const key of zhTWKeys) {
    if (!enUSKeys.includes(key)) {
      issues.push({ key, issue: 'missing', language: 'en-US' });
    } else {
      // Check if en-US value is empty
      const enUSValue = getNestedValue(enUS, key);
      if (isEmpty(enUSValue)) {
        issues.push({ key, issue: 'empty', language: 'en-US' });
      }
    }
  }

  // Check for keys in en-US but not in zh-TW
  for (const key of enUSKeys) {
    if (!zhTWKeys.includes(key)) {
      issues.push({ key, issue: 'missing', language: 'zh-TW' });
    } else {
      // Check if zh-TW value is empty
      const zhTWValue = getNestedValue(zhTW, key);
      if (isEmpty(zhTWValue)) {
        issues.push({ key, issue: 'empty', language: 'zh-TW' });
      }
    }
  }

  // Report results
  console.log(`\n${colors.bold}${colors.cyan}Translation Completeness Report${colors.reset}\n`);
  console.log(`${colors.blue}Total keys in zh-TW.json:${colors.reset} ${zhTWKeys.length}`);
  console.log(`${colors.blue}Total keys in en-US.json:${colors.reset} ${enUSKeys.length}`);

  if (issues.length === 0) {
    console.log(`\n${colors.green}${colors.bold}✓ All translations are complete!${colors.reset}\n`);
    process.exit(0);
  }

  // Group issues by type and language
  const missingInEnUS = issues.filter((i) => i.issue === 'missing' && i.language === 'en-US');
  const missingInZhTW = issues.filter((i) => i.issue === 'missing' && i.language === 'zh-TW');
  const emptyInEnUS = issues.filter((i) => i.issue === 'empty' && i.language === 'en-US');
  const emptyInZhTW = issues.filter((i) => i.issue === 'empty' && i.language === 'zh-TW');

  console.log(
    `\n${colors.red}${colors.bold}✗ Found ${issues.length} translation issue(s)${colors.reset}\n`
  );

  // Report missing keys in en-US
  if (missingInEnUS.length > 0) {
    console.log(
      `${colors.yellow}${colors.bold}Missing in en-US.json (${missingInEnUS.length}):${colors.reset}`
    );
    missingInEnUS.forEach((issue) => {
      const zhValue = getNestedValue(zhTW, issue.key);
      console.log(`  ${colors.red}✗${colors.reset} ${issue.key}`);
      console.log(`    ${colors.cyan}zh-TW value:${colors.reset} "${zhValue}"`);
    });
    console.log('');
  }

  // Report missing keys in zh-TW
  if (missingInZhTW.length > 0) {
    console.log(
      `${colors.yellow}${colors.bold}Missing in zh-TW.json (${missingInZhTW.length}):${colors.reset}`
    );
    missingInZhTW.forEach((issue) => {
      const enValue = getNestedValue(enUS, issue.key);
      console.log(`  ${colors.red}✗${colors.reset} ${issue.key}`);
      console.log(`    ${colors.cyan}en-US value:${colors.reset} "${enValue}"`);
    });
    console.log('');
  }

  // Report empty values in en-US
  if (emptyInEnUS.length > 0) {
    console.log(
      `${colors.yellow}${colors.bold}Empty values in en-US.json (${emptyInEnUS.length}):${colors.reset}`
    );
    emptyInEnUS.forEach((issue) => {
      const zhValue = getNestedValue(zhTW, issue.key);
      console.log(`  ${colors.yellow}⚠${colors.reset} ${issue.key}`);
      console.log(`    ${colors.cyan}zh-TW value:${colors.reset} "${zhValue}"`);
    });
    console.log('');
  }

  // Report empty values in zh-TW
  if (emptyInZhTW.length > 0) {
    console.log(
      `${colors.yellow}${colors.bold}Empty values in zh-TW.json (${emptyInZhTW.length}):${colors.reset}`
    );
    emptyInZhTW.forEach((issue) => {
      const enValue = getNestedValue(enUS, issue.key);
      console.log(`  ${colors.yellow}⚠${colors.reset} ${issue.key}`);
      console.log(`    ${colors.cyan}en-US value:${colors.reset} "${enValue}"`);
    });
    console.log('');
  }

  // Summary
  console.log(`${colors.bold}Summary:${colors.reset}`);
  console.log(`  Missing keys: ${missingInEnUS.length + missingInZhTW.length}`);
  console.log(`  Empty values: ${emptyInEnUS.length + emptyInZhTW.length}`);
  console.log('');

  process.exit(1);
}

// Run the script
findMissingTranslations();
