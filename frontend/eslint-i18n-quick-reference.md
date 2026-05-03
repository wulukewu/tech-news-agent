# ESLint I18n Rules - Quick Reference

Quick reference for preventing hardcoded UI text in the codebase.

## ❌ Don't Do This

```tsx
// Hardcoded Chinese text
<div>這是硬編碼的中文</div>
<input placeholder="請輸入您的名字" />
<button title="點擊這裡">Click</button>
<button aria-label="關閉對話框">X</button>
<img src="/image.jpg" alt="美麗的風景" />
```

## ✅ Do This Instead

```tsx
import { useI18n } from '@/contexts/I18nContext';

export function MyComponent() {
  const { t } = useI18n();

  return (
    <>
      <div>{t('common.welcome-message')}</div>
      <input placeholder={t('forms.placeholders.enter-name')} />
      <button title={t('buttons.click-here')}>Click</button>
      <button aria-label={t('buttons.close-dialog')}>X</button>
      <img src="/image.jpg" alt={t('images.beautiful-landscape')} />
    </>
  );
}
```

## Adding New Translations

### 1. Add to both language files

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

### 2. Use in component

```tsx
const { t } = useI18n();
<button>{t('buttons.new-action')}</button>;
```

### 3. Validate

```bash
npm run validate:translations
```

## Common Patterns

### With Variables

```tsx
// Translation file
{
  "messages": {
    "article-count": "成功抓取 {count} 篇新文章"
  }
}

// Component
<p>{t('messages.article-count', { count: 5 })}</p>
// Output: "成功抓取 5 篇新文章"
```

### In Constants

```typescript
// ❌ Bad
export const OPTIONS = [
  { value: 1, label: '選項一' },
  { value: 2, label: '選項二' },
];

// ✅ Good
export const OPTIONS = [
  { value: 1, labelKey: 'options.option-one' },
  { value: 2, labelKey: 'options.option-two' },
];

// Usage
const { t } = useI18n();
const translatedOptions = OPTIONS.map((opt) => ({
  ...opt,
  label: t(opt.labelKey),
}));
```

## Running ESLint

```bash
# Check all files
npm run lint

# Check specific file
npx eslint path/to/file.tsx

# Auto-fix (where possible)
npm run lint:fix
```

## Exceptions (Use Sparingly)

```tsx
{
  /* eslint-disable-next-line no-restricted-syntax */
}
<div>這是技術文件中的範例</div>;
```

## What Gets Detected

✅ **Detected:**

- Chinese characters in JSX text: `<div>中文</div>`
- Chinese in `placeholder`: `<input placeholder="中文" />`
- Chinese in `title`: `<button title="中文">...</button>`
- Chinese in `aria-label`: `<button aria-label="中文">...</button>`
- Chinese in `alt`: `<img alt="中文" />`

❌ **Not Detected (Yet):**

- Hardcoded English text (too many false positives)
- Text in JavaScript template literals (unless in JSX)
- Dynamic text from API responses

## Need Help?

- 📖 [Full Documentation](../docs/eslint-i18n-rules.md)
- 📝 [Violation Examples](../docs/eslint-i18n-violations-example.md)
- 🌐 [I18n Guide](../docs/i18n-guide.md)

---

**Remember:** All user-facing text should use translation keys!
