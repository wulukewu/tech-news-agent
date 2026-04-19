#!/usr/bin/env node

/**
 * Find Unused Translations Script
 *
 * This script identifies translation keys that are defined in translation files
 * but never used in the codebase. It searches for usage patterns like t('key')
 * and helps keep translation files clean.
 *
 * Usage:
 *   npm run find:unused-translations
 *   node scripts/find-unused-translations.js
 *
 * Exit codes:
 *   0 - All translations are used (or unused keys found - informational)
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
 * Recursively search for files in a directory
 */
function findFiles(dir, extensions) {
  const files = [];

  // Skip certain directories
  const skipDirs = ['node_modules', '.next', 'dist', 'build', '.git', 'locales', 'scripts'];

  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        if (!skipDirs.includes(entry.name)) {
          files.push(...findFiles(fullPath, extensions));
        }
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (extensions.includes(ext)) {
          files.push(fullPath);
        }
      }
    }
  } catch (error) {
    console.warn(`${colors.yellow}Warning: Could not read directory ${dir}${colors.reset}`);
  }

  return files;
}

/**
 * Search for translation key usage in a file
 */
function searchKeyInFile(filePath, key) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');

    // Escape special regex characters in the key
    const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // Search for common translation patterns:
    // - t('key')
    // - t("key")
    // - t(`key`)
    // - t('key', ...)
    // - t("key", ...)
    // - t(`key`, ...)
    const patterns = [
      new RegExp(`t\\(['"\`]${escapedKey}['"\`]`, 'g'),
      new RegExp(`t\\(['"\`]${escapedKey}['"\`]\\s*,`, 'g'),
      new RegExp(`['"\`]${escapedKey}['"\`]`, 'g'), // Also check for direct string references
    ];

    return patterns.some((pattern) => pattern.test(content));
  } catch (error) {
    console.warn(`${colors.yellow}Warning: Could not read file ${filePath}${colors.reset}`);
    return false;
  }
}

/**
 * Check if a translation key is used in the codebase
 */
function isKeyUsed(key, sourceFiles) {
  return sourceFiles.some((file) => searchKeyInFile(file, key));
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
 * Main function to find unused translations
 */
function findUnusedTranslations() {
  const localesDir = path.join(__dirname, '..', 'locales');
  const zhTWPath = path.join(localesDir, 'zh-TW.json');
  const enUSPath = path.join(localesDir, 'en-US.json');
  const frontendDir = path.join(__dirname, '..');

  // Check if translation files exist
  if (!fs.existsSync(zhTWPath)) {
    console.error(`${colors.red}Error: zh-TW.json not found at ${zhTWPath}${colors.reset}`);
    process.exit(1);
  }

  if (!fs.existsSync(enUSPath)) {
    console.error(`${colors.red}Error: en-US.json not found at ${enUSPath}${colors.reset}`);
    process.exit(1);
  }

  console.log(`${colors.cyan}Scanning codebase for translation usage...${colors.reset}\n`);

  // Load translation files
  const zhTW = loadTranslationFile(zhTWPath);
  const enUS = loadTranslationFile(enUSPath);

  // Get all translation keys (use zh-TW as reference)
  const allKeys = flattenKeys(zhTW);

  // Find all source files
  const sourceFiles = findFiles(frontendDir, ['.ts', '.tsx', '.js', '.jsx']);
  console.log(`${colors.blue}Found ${sourceFiles.length} source files to scan${colors.reset}\n`);

  // Check each key for usage
  const unusedKeys = [];
  let checkedCount = 0;

  for (const key of allKeys) {
    checkedCount++;
    if (checkedCount % 10 === 0) {
      process.stdout.write(
        `\r${colors.cyan}Checking keys: ${checkedCount}/${allKeys.length}${colors.reset}`
      );
    }

    if (!isKeyUsed(key, sourceFiles)) {
      unusedKeys.push(key);
    }
  }

  process.stdout.write('\r' + ' '.repeat(50) + '\r'); // Clear progress line

  // Report results
  console.log(`${colors.bold}${colors.cyan}Unused Translations Report${colors.reset}\n`);
  console.log(`${colors.blue}Total translation keys:${colors.reset} ${allKeys.length}`);
  console.log(`${colors.blue}Source files scanned:${colors.reset} ${sourceFiles.length}`);

  if (unusedKeys.length === 0) {
    console.log(`\n${colors.green}${colors.bold}✓ All translation keys are used!${colors.reset}\n`);
    process.exit(0);
  }

  console.log(
    `\n${colors.yellow}${colors.bold}⚠ Found ${unusedKeys.length} unused translation key(s)${colors.reset}\n`
  );

  // Group unused keys by top-level section
  const keysBySection = {};

  for (const key of unusedKeys) {
    const section = key.split('.')[0];
    if (!keysBySection[section]) {
      keysBySection[section] = [];
    }
    keysBySection[section].push(key);
  }

  // Display unused keys grouped by section
  for (const section in keysBySection) {
    console.log(`${colors.bold}${section}:${colors.reset}`);
    keysBySection[section].forEach((key) => {
      const zhValue = getNestedValue(zhTW, key);
      const enValue = getNestedValue(enUS, key);
      console.log(`  ${colors.yellow}⚠${colors.reset} ${key}`);
      console.log(`    ${colors.cyan}zh-TW:${colors.reset} "${zhValue}"`);
      console.log(`    ${colors.cyan}en-US:${colors.reset} "${enValue}"`);
    });
    console.log('');
  }

  // Summary
  console.log(`${colors.bold}Summary:${colors.reset}`);
  console.log(`  Unused keys: ${unusedKeys.length}`);
  console.log(`  Usage rate: ${((1 - unusedKeys.length / allKeys.length) * 100).toFixed(1)}%`);
  console.log('');

  console.log(
    `${colors.cyan}Note: These keys may be unused or the script may have missed dynamic key usage.${colors.reset}`
  );
  console.log(`${colors.cyan}Please review carefully before removing any keys.${colors.reset}\n`);

  process.exit(0); // Exit with 0 since unused keys are informational, not an error
}

// Run the script
findUnusedTranslations();
