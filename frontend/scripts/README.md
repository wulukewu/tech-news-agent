# Frontend Scripts

This directory contains utility scripts for the frontend application.

## Translation Management Scripts

### find-missing-translations.js

Identifies translation keys that exist in one language file but not the other, and reports keys with empty values.

**Usage:**

```bash
npm run find:missing-translations
```

**What it checks:**

- Keys present in `zh-TW.json` but missing in `en-US.json`
- Keys present in `en-US.json` but missing in `zh-TW.json`
- Keys with empty string values in either file
- Keys with null or undefined values

**Exit codes:**

- `0` - All translations are complete
- `1` - Missing translations or empty values found

**Example output:**

```
Translation Completeness Report

Total keys in zh-TW.json: 166
Total keys in en-US.json: 166

✗ Found 2 translation issue(s)

Missing in en-US.json (1):
  ✗ nav.new-feature
    zh-TW value: "新功能"

Empty values in en-US.json (1):
  ⚠ buttons.submit
    zh-TW value: "提交"

Summary:
  Missing keys: 1
  Empty values: 1
```

### find-unused-translations.js

Identifies translation keys that are defined in translation files but never used in the codebase.

**Usage:**

```bash
npm run find:unused-translations
```

**What it checks:**

- Scans all `.ts`, `.tsx`, `.js`, `.jsx` files in the frontend directory
- Searches for translation key usage patterns:
  - `t('key')`
  - `t("key")`
  - `t(\`key\`)`
  - Direct string references to keys
- Reports keys that are never referenced

**Exit codes:**

- `0` - Always exits with 0 (unused keys are informational, not an error)

**Example output:**

```
Scanning codebase for translation usage...

Found 394 source files to scan

Unused Translations Report

Total translation keys: 166
Source files scanned: 394

⚠ Found 3 unused translation key(s)

nav:
  ⚠ nav.old-feature
    zh-TW: "舊功能"
    en-US: "Old Feature"

buttons:
  ⚠ buttons.deprecated-action
    zh-TW: "已棄用操作"
    en-US: "Deprecated Action"

Summary:
  Unused keys: 3
  Usage rate: 98.2%

Note: These keys may be unused or the script may have missed dynamic key usage.
Please review carefully before removing any keys.
```

**Important notes:**

- The script may miss dynamically constructed keys (e.g., `t(\`nav.\${page}\`)`)
- Review the results carefully before removing any keys
- Some keys might be used in ways the script doesn't detect

## Other Scripts

### generate-i18n-types.js

Generates TypeScript type definitions from translation files for autocomplete support.

**Usage:**

```bash
npm run generate:i18n-types
```

### validate-api.ts

Validates the unified API client implementation against the backend.

**Usage:**

```bash
npm run validate-api
```

## Development Workflow

### Adding New Translations

1. Add the key-value pairs to both `locales/zh-TW.json` and `locales/en-US.json`
2. Run `npm run find:missing-translations` to verify completeness
3. Run `npm run generate:i18n-types` to update TypeScript types
4. Use the translation in your component: `const { t } = useI18n(); t('your.new.key')`

### Cleaning Up Translations

1. Run `npm run find:unused-translations` to identify unused keys
2. Review the output carefully
3. Remove unused keys from both translation files
4. Run `npm run find:missing-translations` to verify consistency
5. Run `npm run generate:i18n-types` to update TypeScript types

### Pre-commit Checklist

Before committing changes that involve translations:

- [ ] Run `npm run find:missing-translations` - should pass with no issues
- [ ] Run `npm run generate:i18n-types` - update type definitions
- [ ] Verify translations display correctly in both languages
- [ ] Check that no hardcoded UI text remains in components

## Troubleshooting

### Script reports false positives for unused keys

The script may not detect:

- Dynamically constructed keys: `t(\`section.\${variable}\`)`
- Keys used in configuration files
- Keys used in external packages

Review the output carefully and keep keys that are actually used.

### Script doesn't find a missing translation

Make sure:

- The translation files are valid JSON
- The key path uses dot notation correctly
- There are no typos in the key names

### Permission denied when running scripts

Make the scripts executable:

```bash
chmod +x scripts/find-missing-translations.js
chmod +x scripts/find-unused-translations.js
```
