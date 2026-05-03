# SORT_OPTIONS Migration Guide

## Overview

The `SORT_OPTIONS` constant has been migrated from hardcoded Chinese labels to translation keys to support the bilingual UI system.

## Changes

### Before (Hardcoded Labels)

```typescript
export const SORT_OPTIONS = [
  { value: 'date', label: '發布日期', order: 'desc' },
  { value: 'tinkering_index', label: '技術深度', order: 'desc' },
  { value: 'category', label: '分類', order: 'asc' },
  { value: 'title', label: '標題', order: 'asc' },
] as const;
```

### After (Translation Keys)

```typescript
export const SORT_OPTIONS = [
  { value: 'date', labelKey: 'sort.date', order: 'desc' },
  { value: 'tinkering_index', labelKey: 'sort.tinkering-index', order: 'desc' },
  { value: 'category', labelKey: 'sort.category', order: 'asc' },
  { value: 'title', labelKey: 'sort.title', order: 'asc' },
] as const;
```

## How to Use

### In Components

```typescript
import { useI18n } from '@/contexts/I18nContext';
import { SORT_OPTIONS } from '@/lib/constants';

function MyComponent() {
  const { t } = useI18n();

  // Map SORT_OPTIONS to translated labels
  const translatedOptions = SORT_OPTIONS.map((option) => ({
    ...option,
    label: t(option.labelKey),
  }));

  return (
    <select>
      {translatedOptions.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
```

### Direct Translation

```typescript
import { useI18n } from '@/contexts/I18nContext';
import { SORT_OPTIONS } from '@/lib/constants';

function MyComponent() {
  const { t } = useI18n();

  return (
    <div>
      {SORT_OPTIONS.map((option) => (
        <div key={option.value}>
          {t(option.labelKey)} - {option.order}
        </div>
      ))}
    </div>
  );
}
```

## Translation Keys

The following translation keys are available in both `zh-TW.json` and `en-US.json`:

| Key                    | zh-TW    | en-US           |
| ---------------------- | -------- | --------------- |
| `sort.date`            | 發布日期 | Date            |
| `sort.tinkering-index` | 技術深度 | Technical Depth |
| `sort.category`        | 分類     | Category        |
| `sort.title`           | 標題     | Title           |

## Migration Checklist

- [x] Update `SORT_OPTIONS` constant to use `labelKey` instead of `label`
- [x] Verify translation keys exist in both language files
- [x] Update components that use `SORT_OPTIONS` to call `t(option.labelKey)`
- [x] Add tests to verify the migration
- [x] Ensure TypeScript compilation passes
- [x] Test in both languages (zh-TW and en-US)

## Notes

- The `SortingControls` component already uses its own local `SORT_OPTIONS` definition and is already using translations via `t('forms.sort-options.${option.value}')`.
- The global `SORT_OPTIONS` constant in `frontend/lib/constants/index.ts` is not currently imported anywhere, so this migration is primarily for future use and consistency.
- The migration follows the same pattern as `TINKERING_INDEX_LEVELS`, which uses `labelKey` and `descriptionKey`.

## Related Files

- `frontend/lib/constants/index.ts` - SORT_OPTIONS constant definition
- `frontend/locales/zh-TW.json` - Chinese translations
- `frontend/locales/en-US.json` - English translations
- `frontend/__tests__/unit/constants/sort-options-migration.test.ts` - Migration tests
- `frontend/features/articles/components/SortingControls.tsx` - Example usage (local definition)
