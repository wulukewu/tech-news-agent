# ESLint I18n Rules

This document describes the ESLint rules configured to prevent hardcoded UI text in the codebase, ensuring all user-facing text uses the translation system.

## Overview

The bilingual UI system requires all user-facing text to be translated using translation keys. To enforce this, we've configured ESLint rules that detect hardcoded Chinese text in JSX and common attributes.

## Rules

### 1. Hardcoded Chinese Text in JSX Content

**Rule:** Detects Chinese characters (Unicode range `\u4e00-\u9fa5`) in JSX text content.

**❌ Bad Example:**

```tsx
export function BadComponent() {
  return <div>這是硬編碼的中文</div>;
}
```

**✅ Good Example:**

```tsx
import { useI18n } from '@/contexts/I18nContext';

export function GoodComponent() {
  const { t } = useI18n();
  return <div>{t('common.welcome-message')}</div>;
}
```

### 2. Hardcoded Chinese Text in `placeholder` Attribute

**Rule:** Detects Chinese characters in the `placeholder` attribute of form inputs.

**❌ Bad Example:**

```tsx
<input placeholder="請輸入您的名字" />
```

**✅ Good Example:**

```tsx
const { t } = useI18n();
<input placeholder={t('forms.placeholders.enter-name')} />;
```

### 3. Hardcoded Chinese Text in `title` Attribute

**Rule:** Detects Chinese characters in the `title` attribute (used for tooltips).

**❌ Bad Example:**

```tsx
<button title="點擊這裡">Click</button>
```

**✅ Good Example:**

```tsx
const { t } = useI18n();
<button title={t('buttons.click-here')}>Click</button>;
```

### 4. Hardcoded Chinese Text in `aria-label` Attribute

**Rule:** Detects Chinese characters in the `aria-label` attribute (used for accessibility).

**❌ Bad Example:**

```tsx
<button aria-label="關閉對話框">X</button>
```

**✅ Good Example:**

```tsx
const { t } = useI18n();
<button aria-label={t('buttons.close-dialog')}>X</button>;
```

### 5. Hardcoded Chinese Text in `alt` Attribute

**Rule:** Detects Chinese characters in the `alt` attribute of images.

**❌ Bad Example:**

```tsx
<img src="/image.jpg" alt="美麗的風景" />
```

**✅ Good Example:**

```tsx
const { t } = useI18n();
<img src="/image.jpg" alt={t('images.beautiful-landscape')} />;
```

## Running ESLint

To check your code for hardcoded text violations:

```bash
# Check all files
npm run lint

# Check specific file
npx eslint path/to/file.tsx

# Auto-fix issues (where possible)
npm run lint:fix
```

## Exceptions

### Technical Terms and Code

Technical terms, code snippets, and non-UI text are allowed:

```tsx
// ✅ These are OK - not user-facing UI text
<code>const API_URL = 'https://api.example.com';</code>
<pre>npm install react</pre>
<span>HTTP 404 Not Found</span>
```

### Constants Files

The rules apply to JSX files (`.tsx`, `.jsx`). Constants defined in `.ts` files are not checked by these rules, but should still use translation keys:

```typescript
// frontend/lib/constants/index.ts
export const LANGUAGE_OPTIONS = [
  { value: 'zh-TW', labelKey: 'language.chinese' },
  { value: 'en-US', labelKey: 'language.english' },
] as const;
```

## Disabling Rules (Use Sparingly)

In rare cases where hardcoded text is necessary (e.g., technical documentation, code examples), you can disable the rule:

```tsx
{
  /* eslint-disable-next-line no-restricted-syntax */
}
<div>這是技術文件中的範例</div>;
```

**⚠️ Warning:** Only disable the rule when absolutely necessary. Most UI text should use translations.

## Adding New Translation Keys

When you need to add new UI text:

1. **Add translation keys to both language files:**

   ```json
   // frontend/locales/zh-TW.json
   {
     "buttons": {
       "new-action": "新動作"
     }
   }
   ```

   ```json
   // frontend/locales/en-US.json
   {
     "buttons": {
       "new-action": "New Action"
     }
   }
   ```

2. **Use the translation key in your component:**

   ```tsx
   const { t } = useI18n();
   <button>{t('buttons.new-action')}</button>;
   ```

3. **Validate translations:**

   ```bash
   npm run validate:translations
   ```

## Configuration

The ESLint rules are configured in `frontend/.eslintrc.json`:

```json
{
  "rules": {
    "no-restricted-syntax": [
      "error",
      {
        "selector": "JSXText[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in JSX..."
      }
      // ... more rules
    ]
  }
}
```

## Benefits

These ESLint rules provide:

1. **Automatic Detection:** Catch hardcoded text during development
2. **Consistent Enforcement:** Prevent hardcoded text from being committed
3. **Clear Error Messages:** Helpful guidance on how to fix violations
4. **CI/CD Integration:** Fail builds with hardcoded text violations
5. **Developer Education:** Teach best practices through error messages

## Limitations

### English Text Detection

Currently, the rules only detect Chinese characters. Detecting hardcoded English text is more challenging because:

1. **False Positives:** Technical terms, variable names, and code snippets contain English
2. **Ambiguity:** Difficult to distinguish UI text from technical content
3. **Maintenance Burden:** Would require extensive whitelisting

**Recommendation:** Use code reviews to catch hardcoded English text until better automated detection is available.

### Dynamic Content

These rules only detect static text in JSX. They cannot detect:

- Text generated at runtime
- Text from API responses
- Text in JavaScript template literals (unless in JSX)

**Recommendation:** Follow coding standards and use code reviews for these cases.

## Related Documentation

- [I18n Guide](./i18n-guide.md) - Complete guide to using the translation system
- [Translation File Structure](./i18n-guide.md#translation-file-structure) - How to organize translations
- [Adding New Translations](./i18n-guide.md#adding-new-translations) - Step-by-step guide

## Troubleshooting

### Rule Not Triggering

If the rule isn't detecting hardcoded text:

1. **Check file extension:** Rules only apply to `.tsx` and `.jsx` files
2. **Check ESLint is running:** Run `npx eslint path/to/file.tsx`
3. **Check configuration:** Verify `.eslintrc.json` has the rules
4. **Check overrides:** Some files may have rule overrides

### False Positives

If the rule triggers incorrectly:

1. **Verify it's actually UI text:** Technical content should not be in JSX text
2. **Move to constants:** Extract technical content to separate files
3. **Use comments:** Add explanatory comments for legitimate exceptions
4. **Disable sparingly:** Use `eslint-disable-next-line` only when necessary

## Future Enhancements

Potential improvements to the ESLint rules:

1. **English Text Detection:** Implement heuristics to detect hardcoded English UI text
2. **Custom Plugin:** Create a dedicated ESLint plugin for i18n enforcement
3. **Auto-fix:** Automatically suggest translation keys for common patterns
4. **Translation Key Validation:** Verify translation keys exist in translation files
5. **Unused Key Detection:** Identify translation keys that are never used

---

**Last Updated:** 2025-01-XX
**Requirement:** 12.6 - ESLint rules to prevent hardcoded UI text
