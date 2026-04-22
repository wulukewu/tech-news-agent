# Internationalization (i18n) Developer Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Translation File Structure](#translation-file-structure)
4. [Using Translations](#using-translations)
5. [Adding New Translations](#adding-new-translations)
6. [Common Patterns](#common-patterns)
7. [Constants and Options](#constants-and-options)
8. [Validation Scripts](#validation-scripts)
9. [ESLint Rules](#eslint-rules)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Overview

### What is the i18n System?

The bilingual UI system provides seamless language switching between Traditional Chinese (zh-TW) and English (en-US). It handles:

- **Automatic language detection** from browser settings
- **Manual language switching** with persistent preferences
- **Translation management** with nested key structure
- **Type safety** with auto-generated TypeScript types
- **Developer tooling** for validation and maintenance

### Why Use It?

- **Consistent user experience** - All UI text in one language
- **Type-safe translations** - Autocomplete and compile-time checks
- **Easy maintenance** - Centralized translation files
- **Quality assurance** - Automated validation scripts
- **Performance optimized** - Lazy loading and code splitting

### Architecture

```
┌─────────────────────────────────────────┐
│         Application Root                │
│         (app/layout.tsx)                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      I18nProvider (Context)             │
│  - Language State (zh-TW | en-US)       │
│  - Translation Function (t)             │
│  - Language Switcher (setLocale)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Your Components                 │
│  const { t, locale } = useI18n()        │
│  <h1>{t('nav.articles')}</h1>           │
└─────────────────────────────────────────┘
```

---

## Quick Start

### 1. Import the Hook

```typescript
import { useI18n } from '@/contexts/I18nContext';
```

### 2. Use in Your Component

```typescript
function MyComponent() {
  const { t, locale, setLocale } = useI18n();

  return (
    <div>
      <h1>{t('nav.articles')}</h1>
      <p>{t('messages.article-count', { count: 5 })}</p>
      <button onClick={() => setLocale('zh-TW')}>中文</button>
      <button onClick={() => setLocale('en-US')}>English</button>
    </div>
  );
}
```

### 3. Available Properties

| Property    | Type                                          | Description               |
| ----------- | --------------------------------------------- | ------------------------- |
| `t`         | `(key: string, variables?: object) => string` | Translation function      |
| `locale`    | `'zh-TW' \| 'en-US'`                          | Current language          |
| `setLocale` | `(locale: Locale) => void`                    | Change language           |
| `isLoading` | `boolean`                                     | Translation loading state |

---

## Translation File Structure

### File Locations

```
frontend/locales/
├── zh-TW.json    # Traditional Chinese translations
└── en-US.json    # English translations
```

### Nested Structure

Translations are organized in a nested JSON structure for better organization:

```json
{
  "nav": {
    "articles": "文章",
    "reading-list": "閱讀清單",
    "subscriptions": "訂閱"
  },
  "buttons": {
    "save": "儲存",
    "cancel": "取消",
    "delete": "刪除"
  },
  "messages": {
    "loading": "載入中...",
    "article-count": "成功抓取 {count} 篇新文章"
  },
  "errors": {
    "network-error": "網路連線異常，請檢查您的網路設定",
    "server-error": "伺服器發生錯誤，請稍後再試"
  }
}
```

### Key Naming Conventions

- Use **kebab-case** for keys: `reading-list`, `article-count`
- Use **dot notation** for nesting: `nav.articles`, `errors.network-error`
- Group related translations: `buttons.*`, `messages.*`, `errors.*`
- Be descriptive: `article-count` not `msg1`

---

## Using Translations

### Basic Translation

```typescript
const { t } = useI18n();

// Simple translation
<h1>{t('nav.articles')}</h1>
// Output (zh-TW): "文章"
// Output (en-US): "Articles"
```

### Translation with Variables (Interpolation)

```typescript
const { t } = useI18n();

// Translation with variable interpolation
<p>{t('messages.article-count', { count: 5 })}</p>
// Output (zh-TW): "成功抓取 5 篇新文章"
// Output (en-US): "Successfully fetched 5 new articles"

// Multiple variables
<p>{t('messages.welcome', { name: 'John', role: 'Admin' })}</p>
// Translation: "Welcome {name}, you are logged in as {role}"
// Output: "Welcome John, you are logged in as Admin"
```

### Nested Key Access

```typescript
const { t } = useI18n();

// Access deeply nested keys
<span>{t('forms.labels.feed-url')}</span>
// Accesses: translations.forms.labels['feed-url']
```

### Conditional Translation

```typescript
const { t, locale } = useI18n();

// Use locale for conditional logic
const dateFormat = locale === 'zh-TW' ? 'YYYY年MM月DD日' : 'MMM DD, YYYY';

// Conditional translation keys
const messageKey = isSuccess ? 'success.saved' : 'errors.save-failed';
<p>{t(messageKey)}</p>
```

### Translation in Attributes

```typescript
const { t } = useI18n();

// In JSX attributes
<input
  placeholder={t('forms.placeholders.search-feed')}
  aria-label={t('forms.labels.feed-url')}
  title={t('buttons.save')}
/>

// In button text
<button>{t('buttons.save')}</button>
```

---

## Adding New Translations

### Step-by-Step Guide

#### 1. Add to Both Language Files

**zh-TW.json:**

```json
{
  "profile": {
    "edit-bio": "編輯個人簡介",
    "bio-placeholder": "請輸入您的個人簡介..."
  }
}
```

**en-US.json:**

```json
{
  "profile": {
    "edit-bio": "Edit Bio",
    "bio-placeholder": "Enter your bio..."
  }
}
```

#### 2. Regenerate TypeScript Types

```bash
npm run generate:i18n-types
```

This updates `frontend/types/i18n.generated.ts` with the new keys.

#### 3. Use in Your Component

```typescript
const { t } = useI18n();

<div>
  <h2>{t('profile.edit-bio')}</h2>
  <textarea placeholder={t('profile.bio-placeholder')} />
</div>
```

#### 4. Validate Translations

```bash
npm run find:missing-translations
```

This ensures both language files have the same keys.

### Quick Reference

```bash
# 1. Edit translation files
vim frontend/locales/zh-TW.json
vim frontend/locales/en-US.json

# 2. Regenerate types
npm run generate:i18n-types

# 3. Validate
npm run find:missing-translations

# 4. Check for unused keys (optional)
npm run find:unused-translations
```

---

## Common Patterns

### 1. Interpolation (Variable Substitution)

**Translation File:**

```json
{
  "messages": {
    "article-count": "成功抓取 {count} 篇新文章",
    "welcome": "歡迎 {name}！",
    "progress": "已完成 {current} / {total}"
  }
}
```

**Usage:**

```typescript
const { t } = useI18n();

// Single variable
<p>{t('messages.article-count', { count: 5 })}</p>

// Multiple variables
<p>{t('messages.progress', { current: 3, total: 10 })}</p>

// Dynamic values
<p>{t('messages.welcome', { name: user.name })}</p>
```

### 2. Nested Keys

**Translation File:**

```json
{
  "forms": {
    "labels": {
      "feed-url": "RSS Feed URL",
      "feed-name": "Feed Name"
    },
    "placeholders": {
      "feed-url": "https://example.com/feed.xml",
      "feed-name": "Auto-detected from feed"
    }
  }
}
```

**Usage:**

```typescript
const { t } = useI18n();

<input
  placeholder={t('forms.placeholders.feed-url')}
  aria-label={t('forms.labels.feed-url')}
/>
```

### 3. Dynamic Key Selection

```typescript
const { t } = useI18n();

// Based on status
const statusKey = `status.${article.status}`; // 'status.published'
<span>{t(statusKey)}</span>

// Based on level
const levelKey = `tinkering-index.level-${level}`; // 'tinkering-index.level-3'
<span>{t(levelKey)}</span>

// With fallback
const key = error ? 'errors.network-error' : 'messages.loading';
<p>{t(key)}</p>
```

### 4. Array Mapping

```typescript
const { t } = useI18n();

// Translate array of options
const sortOptions = ['date', 'tinkering-index', 'category'].map((option) => ({
  value: option,
  label: t(`sort.${option}`),
}));

// Translate constant array
const levels = TINKERING_INDEX_LEVELS.map((level) => ({
  ...level,
  label: t(`tinkering-index.level-${level.value}`),
  description: t(`tinkering-index.level-${level.value}-desc`),
}));
```

### 5. Conditional Rendering

```typescript
const { t, locale } = useI18n();

// Show different content based on language
{locale === 'zh-TW' ? (
  <p>繁體中文特定內容</p>
) : (
  <p>English-specific content</p>
)}

// Use locale for formatting
const formattedDate = locale === 'zh-TW'
  ? format(date, 'YYYY年MM月DD日')
  : format(date, 'MMM DD, YYYY');
```

---

## Constants and Options

### Migrating Constants to i18n

**Before (Hardcoded):**

```typescript
export const TINKERING_INDEX_LEVELS = [
  { value: 1, label: '入門', description: '適合初學者' },
  { value: 2, label: '基礎', description: '需要基本知識' },
  // ...
];
```

**After (i18n-ready):**

```typescript
// Define constant with translation keys
export const TINKERING_INDEX_LEVELS = [
  { value: 1, labelKey: 'tinkering-index.level-1', descKey: 'tinkering-index.level-1-desc' },
  { value: 2, labelKey: 'tinkering-index.level-2', descKey: 'tinkering-index.level-2-desc' },
  // ...
];

// Use in component
function TinkeringFilter() {
  const { t } = useI18n();

  const levels = TINKERING_INDEX_LEVELS.map(level => ({
    value: level.value,
    label: t(level.labelKey),
    description: t(level.descKey)
  }));

  return (
    <select>
      {levels.map(level => (
        <option key={level.value} value={level.value} title={level.description}>
          {level.label}
        </option>
      ))}
    </select>
  );
}
```

### Dropdown Options

**Translation File:**

```json
{
  "sort-options": {
    "date": "發布日期",
    "date-desc": "按文章發布時間排序",
    "tinkering-index": "技術深度",
    "tinkering-index-desc": "按技術深度評分排序"
  },
  "order-options": {
    "asc": "升序",
    "asc-desc": "從低到高 / 從舊到新",
    "desc": "降序",
    "desc-desc": "從高到低 / 從新到舊"
  }
}
```

**Usage:**

```typescript
const { t } = useI18n();

const sortOptions = [
  { value: 'date', label: t('sort-options.date'), description: t('sort-options.date-desc') },
  { value: 'tinkering-index', label: t('sort-options.tinkering-index'), description: t('sort-options.tinkering-index-desc') }
];

<select>
  {sortOptions.map(option => (
    <option key={option.value} value={option.value} title={option.description}>
      {option.label}
    </option>
  ))}
</select>
```

### Theme Options

```typescript
const { t } = useI18n();

const themeOptions = [
  { value: 'light', label: t('theme.light') },
  { value: 'dark', label: t('theme.dark') },
  { value: 'system', label: t('theme.system') },
];
```

---

## Validation Scripts

### 1. Find Missing Translations

**Purpose:** Identifies translation keys that exist in one language file but not the other, or have empty values.

**Command:**

```bash
npm run find:missing-translations
```

**Output:**

```
Translation Completeness Report

Total keys in zh-TW.json: 156
Total keys in en-US.json: 156

✗ Found 3 translation issue(s)

Missing in en-US.json (2):
  ✗ profile.edit-bio
    zh-TW value: "編輯個人簡介"
  ✗ profile.bio-placeholder
    zh-TW value: "請輸入您的個人簡介..."

Empty values in zh-TW.json (1):
  ⚠ settings.notification-sound
    en-US value: "Notification Sound"

Summary:
  Missing keys: 2
  Empty values: 1
```

**When to Run:**

- After adding new translations
- Before committing changes
- During code review
- As part of CI/CD pipeline

### 2. Find Unused Translations

**Purpose:** Identifies translation keys that are defined but never used in the codebase.

**Command:**

```bash
npm run find:unused-translations
```

**Output:**

```
Scanning codebase for translation usage...

Found 247 source files to scan

Unused Translations Report

Total translation keys: 156
Source files scanned: 247

⚠ Found 5 unused translation key(s)

buttons:
  ⚠ buttons.archive
    zh-TW: "封存"
    en-US: "Archive"

messages:
  ⚠ messages.old-notification
    zh-TW: "舊通知訊息"
    en-US: "Old notification message"

Summary:
  Unused keys: 5
  Usage rate: 96.8%

Note: These keys may be unused or the script may have missed dynamic key usage.
Please review carefully before removing any keys.
```

**When to Run:**

- During cleanup/refactoring
- Before major releases
- When optimizing bundle size
- Periodically (monthly/quarterly)

**Important:** Review carefully before removing keys - they might be used dynamically or planned for future features.

### 3. Generate TypeScript Types

**Purpose:** Auto-generates TypeScript types from translation files for type safety and autocomplete.

**Command:**

```bash
npm run generate:i18n-types
```

**Output:**

```
🔧 Generating i18n TypeScript types...

📖 Reading zh-TW.json...
   Found 156 keys
📖 Reading en-US.json...
   Found 156 keys

🔍 Verifying key consistency...
✅ All keys are consistent across translation files

📝 Generating type definition...
💾 Writing to frontend/types/i18n.generated.ts...

✨ Successfully generated 156 translation key types!
📄 Output: frontend/types/i18n.generated.ts
```

**Generated File:**

```typescript
// frontend/types/i18n.generated.ts
/**
 * Auto-generated translation keys
 * DO NOT EDIT MANUALLY
 */
export type TranslationKey =
  | 'nav.articles'
  | 'nav.reading-list'
  | 'buttons.save'
  | 'buttons.cancel';
// ... all keys
```

**When to Run:**

- After adding new translation keys
- After modifying translation structure
- Before committing changes
- Automatically via pre-commit hook

### Script Locations

All scripts are located in `frontend/scripts/`:

```
frontend/scripts/
├── find-missing-translations.js
├── find-unused-translations.js
└── generate-i18n-types.js
```

---

## ESLint Rules

### Preventing Hardcoded Text

The project includes ESLint rules to prevent hardcoded Chinese text in JSX:

**Configuration (`.eslintrc.json`):**

```json
{
  "rules": {
    "no-restricted-syntax": [
      "error",
      {
        "selector": "JSXText[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in JSX. Use translation keys with useI18n hook instead: const { t } = useI18n(); <element>{t('translation.key')}</element>"
      },
      {
        "selector": "JSXAttribute[name.name='placeholder'] Literal[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in placeholder attribute. Use translation keys: placeholder={t('translation.key')}"
      },
      {
        "selector": "JSXAttribute[name.name='title'] Literal[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in title attribute. Use translation keys: title={t('translation.key')}"
      },
      {
        "selector": "JSXAttribute[name.name='aria-label'] Literal[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in aria-label attribute. Use translation keys: aria-label={t('translation.key')}"
      }
    ]
  }
}
```

### What Gets Flagged

**❌ Will Trigger Error:**

```typescript
// Hardcoded Chinese in JSX text
<h1>文章列表</h1>

// Hardcoded Chinese in attributes
<input placeholder="搜尋文章..." />
<button title="儲存" />
<div aria-label="關閉對話框" />
```

**✅ Correct Usage:**

```typescript
const { t } = useI18n();

// Use translation keys
<h1>{t('nav.articles')}</h1>

// Use translation keys in attributes
<input placeholder={t('forms.placeholders.search-feed')} />
<button title={t('buttons.save')} />
<div aria-label={t('dialogs.close')} />
```

### Running ESLint

```bash
# Check for linting errors
npm run lint

# Auto-fix fixable issues
npm run lint:fix
```

### Disabling Rules (Use Sparingly)

If you absolutely need to disable the rule for a specific line:

```typescript
// eslint-disable-next-line no-restricted-syntax
<div>特殊情況下的中文文字</div>
```

**Note:** Always add a comment explaining why the rule is disabled.

---

## Best Practices

### 1. Always Use Translation Keys

**❌ Bad:**

```typescript
<button>儲存</button>
<button>Save</button>
```

**✅ Good:**

```typescript
const { t } = useI18n();
<button>{t('buttons.save')}</button>
```

### 2. Group Related Translations

**❌ Bad:**

```json
{
  "save-button": "儲存",
  "cancel-button": "取消",
  "delete-button": "刪除"
}
```

**✅ Good:**

```json
{
  "buttons": {
    "save": "儲存",
    "cancel": "取消",
    "delete": "刪除"
  }
}
```

### 3. Use Descriptive Key Names

**❌ Bad:**

```json
{
  "msg1": "載入中...",
  "err2": "網路錯誤",
  "btn3": "確認"
}
```

**✅ Good:**

```json
{
  "messages": {
    "loading": "載入中..."
  },
  "errors": {
    "network-error": "網路錯誤"
  },
  "buttons": {
    "confirm": "確認"
  }
}
```

### 4. Keep Translations Synchronized

Always add keys to **both** language files simultaneously:

```bash
# Edit both files together
vim frontend/locales/zh-TW.json frontend/locales/en-US.json

# Or use a split view
code frontend/locales/zh-TW.json frontend/locales/en-US.json
```

### 5. Use Variables for Dynamic Content

**❌ Bad:**

```typescript
// Creating translation keys dynamically
<p>{t(`messages.fetched-${count}-articles`)}</p>
// Requires: "fetched-1-articles", "fetched-2-articles", etc.
```

**✅ Good:**

```typescript
// Use interpolation
<p>{t('messages.article-count', { count })}</p>
// Translation: "成功抓取 {count} 篇新文章"
```

### 6. Validate Before Committing

```bash
# Run validation scripts
npm run find:missing-translations
npm run generate:i18n-types
npm run lint
```

### 7. Document Complex Translations

Add comments in translation files for context:

```json
{
  "messages": {
    // Used in article fetch notification
    // {count} is the number of articles fetched
    "article-count": "成功抓取 {count} 篇新文章"
  }
}
```

### 8. Handle Missing Keys Gracefully

The system returns the key itself if translation is missing:

```typescript
t('non.existent.key'); // Returns: 'non.existent.key'
```

In development, a warning is logged to console.

### 9. Use TypeScript Types

Import and use the generated types:

```typescript
import type { TranslationKey } from '@/types/i18n.generated';

function translateKey(key: TranslationKey) {
  const { t } = useI18n();
  return t(key);
}
```

### 10. Test Both Languages

Always test your UI in both languages:

```typescript
// In your component or test
const { setLocale } = useI18n();

// Test Chinese
setLocale('zh-TW');
// Verify UI

// Test English
setLocale('en-US');
// Verify UI
```

---

## Troubleshooting

### Issue: Translation Not Showing

**Symptoms:**

- Translation key appears as-is in UI
- Example: `nav.articles` instead of "文章"

**Solutions:**

1. **Check if key exists in translation file:**

   ```bash
   npm run find:missing-translations
   ```

2. **Verify key spelling:**

   ```typescript
   // Wrong
   t('nav.article'); // Missing 's'

   // Correct
   t('nav.articles');
   ```

3. **Check translation file syntax:**

   ```bash
   # Validate JSON
   cat frontend/locales/zh-TW.json | jq .
   ```

4. **Regenerate types:**
   ```bash
   npm run generate:i18n-types
   ```

### Issue: ESLint Error for Hardcoded Text

**Symptoms:**

```
Hardcoded Chinese text detected in JSX. Use translation keys with useI18n hook instead
```

**Solution:**

1. **Add translation key:**

   ```json
   // zh-TW.json
   {
     "your-section": {
       "your-key": "您的中文文字"
     }
   }
   ```

2. **Use translation in component:**

   ```typescript
   const { t } = useI18n();
   <div>{t('your-section.your-key')}</div>
   ```

3. **Regenerate types:**
   ```bash
   npm run generate:i18n-types
   ```

### Issue: Language Not Switching

**Symptoms:**

- Clicking language switcher doesn't change UI
- Language persists after reload

**Solutions:**

1. **Check if component uses `useI18n`:**

   ```typescript
   // Make sure you're using the hook
   const { t } = useI18n();
   ```

2. **Verify I18nProvider is in layout:**

   ```typescript
   // app/layout.tsx
   <I18nProvider>
     {children}
   </I18nProvider>
   ```

3. **Clear localStorage:**

   ```javascript
   // In browser console
   localStorage.removeItem('language');
   location.reload();
   ```

4. **Check browser console for errors:**
   - Open DevTools → Console
   - Look for translation loading errors

### Issue: Missing Translation Warning in Console

**Symptoms:**

```
Warning: Translation key not found: profile.new-key
```

**Solution:**

1. **Add the key to both language files:**

   ```json
   // zh-TW.json
   { "profile": { "new-key": "新鍵值" } }

   // en-US.json
   { "profile": { "new-key": "New Key" } }
   ```

2. **Run validation:**

   ```bash
   npm run find:missing-translations
   ```

3. **Regenerate types:**
   ```bash
   npm run generate:i18n-types
   ```

### Issue: TypeScript Error for Translation Key

**Symptoms:**

```typescript
Type '"invalid.key"' is not assignable to type 'TranslationKey'
```

**Solution:**

1. **Check if key exists in translation files**

2. **Regenerate types:**

   ```bash
   npm run generate:i18n-types
   ```

3. **Restart TypeScript server:**
   - VS Code: `Cmd+Shift+P` → "TypeScript: Restart TS Server"

### Issue: Interpolation Not Working

**Symptoms:**

- Variables not replaced: "成功抓取 {count} 篇新文章"

**Solution:**

1. **Check variable name matches:**

   ```typescript
   // Translation: "成功抓取 {count} 篇新文章"

   // Wrong
   t('messages.article-count', { number: 5 });

   // Correct
   t('messages.article-count', { count: 5 });
   ```

2. **Verify translation syntax:**

   ```json
   // Correct
   { "message": "Hello {name}" }

   // Wrong
   { "message": "Hello ${name}" }
   { "message": "Hello {{name}}" }
   ```

### Issue: Performance - Slow Language Switching

**Symptoms:**

- Language switch takes > 200ms
- UI freezes during switch

**Solutions:**

1. **Check translation file size:**

   ```bash
   ls -lh frontend/locales/*.json
   ```

2. **Optimize large translation files:**
   - Split into smaller sections
   - Remove unused keys

3. **Check for unnecessary re-renders:**

   ```typescript
   // Use React.memo for expensive components
   export const MyComponent = React.memo(MyComponentImpl);
   ```

4. **Verify code splitting:**
   ```typescript
   // Translations should be dynamically imported
   const response = await import(`@/locales/${targetLocale}.json`);
   ```

### Getting Help

If you're still stuck:

1. **Check the design document:** `.kiro/specs/bilingual-ui-system/design.md`
2. **Check the requirements:** `.kiro/specs/bilingual-ui-system/requirements.md`
3. **Review existing usage:** Search codebase for `useI18n` examples
4. **Ask the team:** Post in #frontend or #i18n Slack channel

---

## Related Documentation

- [Requirements Document](.kiro/specs/bilingual-ui-system/requirements.md)
- [Design Document](.kiro/specs/bilingual-ui-system/design.md)
- [I18nContext Implementation](../frontend/contexts/I18nContext.tsx)
- [LanguageSwitcher Component](../frontend/components/LanguageSwitcher.tsx)
- [Translation Files](../frontend/locales/)

---

**Last Updated:** 2025-01-XX
**Version:** 1.0
**Maintainer:** Frontend Team
