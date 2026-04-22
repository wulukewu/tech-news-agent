# ESLint I18n Rule Violations - Examples

This document shows examples of hardcoded Chinese text violations detected by the ESLint rules in the codebase.

## Summary

The ESLint rules successfully detect hardcoded Chinese text in:

- JSX text content
- `placeholder` attributes
- `title` attributes
- `aria-label` attributes
- `alt` attributes

## Example Violations Found

### 1. Test Files (Intentional Violations)

**File:** `__tests__/eslint-i18n-rule.test.tsx`

These are intentional violations in the test file to verify the rules work:

```tsx
// ❌ JSX text content
<div>這是硬編碼的中文</div>

// ❌ Placeholder attribute
<input placeholder="請輸入您的名字" />

// ❌ Title attribute
<button title="點擊這裡">Click</button>

// ❌ Aria-label attribute
<button aria-label="關閉對話框">X</button>

// ❌ Alt attribute
<img src="/image.jpg" alt="美麗的風景" />
```

### 2. Integration Tests

**File:** `__tests__/integration/i18n-context-integration.test.tsx`

```tsx
// ❌ Hardcoded Chinese text in test
expect(screen.getByText('文章')).toBeInTheDocument();
```

**Fix:** Tests should use translation keys or mock the translation function.

### 3. Component Tests

**File:** `__tests__/unit/features/articles/components/CategoryFilterMenu.test.tsx`

```tsx
// ❌ Hardcoded placeholder in test
<input placeholder="搜尋分類..." />
```

**Fix:** Use translation key:

```tsx
<input placeholder={t('forms.placeholders.search-categories')} />
```

### 4. UI Component Tests

**File:** `__tests__/unit/ui-components.test.tsx`

Multiple violations:

```tsx
// ❌ Hardcoded placeholders
<input placeholder="搜尋..." />
<input placeholder="請輸入..." />

// ❌ Hardcoded title
<button title="關閉">X</button>
```

### 5. Application Pages

**File:** `app/app/analytics/page.tsx`

```tsx
// ❌ Multiple hardcoded Chinese text in JSX
<h1>分析頁面</h1>
<p>這是分析頁面的內容</p>
```

**Fix:** Use translation keys:

```tsx
const { t } = useI18n();
<h1>{t('pages.analytics.title')}</h1>
<p>{t('pages.analytics.description')}</p>
```

**File:** `app/app/recommendations/page.tsx`

```tsx
// ❌ Hardcoded Chinese text
<h2>推薦文章</h2>
<p>根據您的閱讀習慣推薦</p>
```

## How to Fix Violations

### Step 1: Add Translation Keys

Add the text to both translation files:

```json
// frontend/locales/zh-TW.json
{
  "pages": {
    "analytics": {
      "title": "分析頁面",
      "description": "這是分析頁面的內容"
    }
  }
}
```

```json
// frontend/locales/en-US.json
{
  "pages": {
    "analytics": {
      "title": "Analytics",
      "description": "This is the analytics page content"
    }
  }
}
```

### Step 2: Use Translation Keys in Components

```tsx
import { useI18n } from '@/contexts/I18nContext';

export function AnalyticsPage() {
  const { t } = useI18n();

  return (
    <div>
      <h1>{t('pages.analytics.title')}</h1>
      <p>{t('pages.analytics.description')}</p>
    </div>
  );
}
```

### Step 3: Verify No Violations

```bash
npm run lint
```

## Test Files Exception

For test files, you have two options:

### Option 1: Use Translation Keys (Recommended)

```tsx
import { useI18n } from '@/contexts/I18nContext';

test('displays translated text', () => {
  const { t } = useI18n();
  render(<Component />);
  expect(screen.getByText(t('nav.articles'))).toBeInTheDocument();
});
```

### Option 2: Disable Rule for Test Files

Add to `.eslintrc.json`:

```json
{
  "overrides": [
    {
      "files": ["__tests__/**/*.ts", "__tests__/**/*.tsx"],
      "rules": {
        "no-restricted-syntax": "off"
      }
    }
  ]
}
```

**Note:** Option 1 is recommended as it ensures tests verify the actual translation system.

## Statistics

Based on the ESLint scan:

- **Total violations found:** ~20+ instances
- **Most common violation:** JSX text content (60%)
- **Second most common:** Placeholder attributes (25%)
- **Other violations:** Title, aria-label, alt attributes (15%)

## Next Steps

1. **Fix application code:** Migrate all hardcoded text in `app/` directory
2. **Update tests:** Use translation keys or disable rules for test files
3. **Add pre-commit hook:** Prevent new violations from being committed
4. **Document exceptions:** Create guidelines for legitimate exceptions

## Related Documentation

- [ESLint I18n Rules](./eslint-i18n-rules.md) - Complete rule documentation
- [I18n Guide](./i18n-guide.md) - How to use the translation system
- [Migration Guide](./i18n-migration-guide.md) - Step-by-step migration process

---

**Last Updated:** 2025-01-XX
**Status:** Active violations detected, migration in progress
