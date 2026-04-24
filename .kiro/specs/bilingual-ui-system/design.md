# Design Document: Bilingual UI System

## Overview

This document provides the technical design for implementing a bilingual user interface system that supports seamless switching between Traditional Chinese (zh-TW) and English (en-US). The system addresses the current issue where UI text is inconsistently mixed between languages by providing a comprehensive internationalization (i18n) solution.

### Goals

- Enable automatic language detection based on browser/system settings
- Provide manual language switching with persistent preferences
- Ensure all UI elements are properly translated in both languages
- Maintain high performance with lazy loading and code splitting
- Deliver excellent developer experience with TypeScript support and tooling
- Ensure full accessibility compliance for language switching

### Non-Goals

- Support for additional languages beyond zh-TW and en-US (future enhancement)
- Translation of user-generated content or article text
- Right-to-left (RTL) language support
- Server-side rendering of translations (client-side only)

## Architecture

### High-Level Architecture

The bilingual UI system follows a provider-based architecture similar to the existing ThemeContext pattern:

```
┌─────────────────────────────────────────────────────────┐
│                     Application Root                     │
│                      (app/layout.tsx)                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  I18nProvider (Context)                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  - Language State (locale: 'zh-TW' | 'en-US')    │  │
│  │  - Translation Functions (t, setLocale)          │  │
│  │  - Translation Cache                             │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Language   │  │ Translation │  │   Storage   │
│  Detector   │  │   Loader    │  │   Manager   │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Browser   │  │ Translation │  │ localStorage│
│   Settings  │  │    Files    │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Component Responsibilities

#### I18nProvider (Context)

- Manages current locale state
- Provides translation function `t(key, variables?)`
- Handles locale switching
- Caches loaded translations
- Coordinates between Language Detector, Translation Loader, and Storage Manager

#### Language Detector

- Detects browser language on initial load
- Maps detected language to supported locales
- Provides fallback to en-US for unsupported languages
- Completes detection within 100ms

#### Translation Loader

- Lazy loads translation files on demand
- Implements code splitting for optimal bundle size
- Caches loaded translations in memory
- Handles missing translation keys with fallback

#### Storage Manager

- Persists language preference to localStorage
- Retrieves stored preference on app initialization
- Validates stored values
- Handles localStorage unavailability gracefully

#### Language Switcher (UI Component)

- Displays language options with native labels
- Provides visual feedback for active language
- Supports keyboard navigation
- Meets WCAG AA accessibility standards

## Components and Interfaces

### Core Types

```typescript
// frontend/types/i18n.ts

/**
 * Supported locales
 */
export type Locale = 'zh-TW' | 'en-US';

/**
 * Translation key paths (generated from translation files)
 */
export type TranslationKey = string;

/**
 * Translation variables for interpolation
 */
export type TranslationVariables = Record<string, string | number>;

/**
 * Translation function type
 */
export type TranslationFunction = (key: TranslationKey, variables?: TranslationVariables) => string;

/**
 * I18n Context type
 */
export interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: TranslationFunction;
  isLoading: boolean;
}

/**
 * Translation file structure
 */
export interface TranslationFile {
  nav: {
    articles: string;
    'reading-list': string;
    subscriptions: string;
    analytics: string;
    settings: string;
    'system-status': string;
  };
  buttons: {
    save: string;
    cancel: string;
    delete: string;
    edit: string;
    add: string;
    remove: string;
    // ... more buttons
  };
  messages: {
    'article-count': string; // "成功抓取 {count} 篇新文章"
    loading: string;
    // ... more messages
  };
  errors: Record<string, string>;
  success: Record<string, string>;
  // ... more sections
}
```

### I18nContext Implementation

```typescript
// frontend/contexts/I18nContext.tsx

'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Locale, I18nContextType, TranslationFunction } from '@/types/i18n';

const I18nContext = createContext<I18nContextType | undefined>(undefined);

const LANGUAGE_STORAGE_KEY = 'language';
const SUPPORTED_LOCALES: Locale[] = ['zh-TW', 'en-US'];

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en-US');
  const [translations, setTranslations] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(true);

  // Language detection
  const detectLanguage = useCallback((): Locale => {
    if (typeof window === 'undefined') return 'en-US';

    const browserLang = navigator.language || navigator.languages?.[0];

    // Check for Chinese variants
    if (browserLang.startsWith('zh')) {
      return 'zh-TW';
    }

    // Check for English variants
    if (browserLang.startsWith('en')) {
      return 'en-US';
    }

    // Default fallback
    return 'en-US';
  }, []);

  // Load translations
  const loadTranslations = useCallback(async (targetLocale: Locale) => {
    try {
      const response = await import(`@/locales/${targetLocale}.json`);
      setTranslations(response.default);
    } catch (error) {
      console.error(`Failed to load translations for ${targetLocale}:`, error);
      // Fallback to empty object
      setTranslations({});
    }
  }, []);

  // Translation function
  const t: TranslationFunction = useCallback(
    (key, variables) => {
      const keys = key.split('.');
      let value: any = translations;

      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = value[k];
        } else {
          // Fallback: return key if translation not found
          if (process.env.NODE_ENV === 'development') {
            console.warn(`Translation key not found: ${key}`);
          }
          return key;
        }
      }

      // Handle interpolation
      if (typeof value === 'string' && variables) {
        return value.replace(/\{(\w+)\}/g, (match, varName) => {
          return variables[varName]?.toString() || match;
        });
      }

      return typeof value === 'string' ? value : key;
    },
    [translations]
  );

  // Set locale with persistence
  const setLocale = useCallback(
    async (newLocale: Locale) => {
      setIsLoading(true);
      setLocaleState(newLocale);

      // Update HTML lang attribute
      if (typeof document !== 'undefined') {
        document.documentElement.lang = newLocale;
      }

      // Persist to localStorage
      try {
        localStorage.setItem(LANGUAGE_STORAGE_KEY, newLocale);
      } catch (error) {
        console.warn('Failed to persist language preference:', error);
      }

      // Load translations
      await loadTranslations(newLocale);
      setIsLoading(false);
    },
    [loadTranslations]
  );

  // Initialize on mount
  useEffect(() => {
    const initializeLanguage = async () => {
      let initialLocale: Locale = 'en-US';

      // Check localStorage first
      try {
        const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY) as Locale | null;
        if (stored && SUPPORTED_LOCALES.includes(stored)) {
          initialLocale = stored;
        } else {
          // Fall back to browser detection
          initialLocale = detectLanguage();
        }
      } catch (error) {
        // localStorage unavailable, use detection
        initialLocale = detectLanguage();
      }

      await setLocale(initialLocale);
    };

    initializeLanguage();
  }, [detectLanguage, setLocale]);

  const value: I18nContextType = {
    locale,
    setLocale,
    t,
    isLoading,
  };

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextType {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}
```

### Language Switcher Component

```typescript
// frontend/components/LanguageSwitcher.tsx

'use client';

import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import type { Locale } from '@/types/i18n';

const LANGUAGE_OPTIONS: Array<{ value: Locale; label: string; nativeLabel: string }> = [
  { value: 'zh-TW', label: 'Traditional Chinese', nativeLabel: '繁體中文' },
  { value: 'en-US', label: 'English', nativeLabel: 'English' },
];

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  const handleLanguageChange = (newLocale: Locale) => {
    setLocale(newLocale);
  };

  return (
    <div
      role="group"
      aria-label="Language selector"
      className="flex items-center gap-2 rounded-lg bg-gray-100 dark:bg-gray-800 p-1"
    >
      {LANGUAGE_OPTIONS.map((option) => (
        <button
          key={option.value}
          onClick={() => handleLanguageChange(option.value)}
          aria-label={`Switch to ${option.label}`}
          aria-pressed={locale === option.value}
          className={`
            px-3 py-1.5 rounded-md text-sm font-medium
            transition-colors duration-200
            min-w-[44px] min-h-[44px]
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            ${
              locale === option.value
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }
          `}
        >
          {option.nativeLabel}
        </button>
      ))}
    </div>
  );
}
```

## Data Models

### Translation File Structure

Translation files are organized in a nested JSON structure under `frontend/locales/`:

```
frontend/locales/
├── zh-TW.json
└── en-US.json
```

#### Translation File Schema

```json
{
  "nav": {
    "articles": "文章",
    "reading-list": "閱讀清單",
    "subscriptions": "訂閱",
    "analytics": "分析",
    "settings": "設定",
    "system-status": "系統狀態"
  },
  "buttons": {
    "save": "儲存",
    "cancel": "取消",
    "delete": "刪除",
    "edit": "編輯",
    "add": "新增",
    "remove": "移除",
    "confirm": "確認",
    "close": "關閉"
  },
  "messages": {
    "loading": "載入中...",
    "article-count": "成功抓取 {count} 篇新文章",
    "no-articles": "沒有發現新文章",
    "fetching-articles": "正在抓取文章...",
    "scheduler-running": "排程器執行中，請稍候"
  },
  "errors": {
    "network-error": "網路連線異常，請檢查您的網路設定",
    "analysis-timeout": "AI 分析處理時間過長，請稍後再試",
    "insufficient-permissions": "您沒有執行此操作的權限",
    "rate-limit-exceeded": "請求過於頻繁，請稍後再試",
    "invalid-input": "輸入資料格式不正確",
    "server-error": "伺服器發生錯誤，請稍後再試",
    "not-found": "找不到請求的資源",
    "unauthorized": "請先登入後再進行此操作"
  },
  "success": {
    "article-saved": "文章已加入閱讀清單",
    "article-removed": "文章已從閱讀清單移除",
    "settings-saved": "設定已儲存",
    "analysis-copied": "分析內容已複製到剪貼簿",
    "subscription-added": "訂閱已新增",
    "subscription-removed": "訂閱已移除"
  },
  "tinkering-index": {
    "level-1": "入門",
    "level-1-desc": "適合初學者",
    "level-2": "基礎",
    "level-2-desc": "需要基本知識",
    "level-3": "中級",
    "level-3-desc": "需要一定經驗",
    "level-4": "進階",
    "level-4-desc": "需要深度理解",
    "level-5": "專家",
    "level-5-desc": "需要專業知識"
  },
  "sort": {
    "date": "發布日期",
    "tinkering-index": "技術深度",
    "category": "分類",
    "title": "標題"
  },
  "theme": {
    "light": "淺色模式",
    "dark": "深色模式",
    "system": "跟隨系統"
  },
  "notification-frequency": {
    "immediate": "即時通知",
    "daily": "每日摘要",
    "weekly": "每週摘要",
    "disabled": "關閉通知"
  }
}
```

### Constants Migration Strategy

Existing constants with hardcoded Chinese text will be migrated to use translation keys:

**Before:**

```typescript
export const TINKERING_INDEX_LEVELS = [
  { value: 1, label: '入門', description: '適合初學者' },
  // ...
];
```

**After:**

```typescript
// Constants now reference translation keys
export const TINKERING_INDEX_LEVELS = [
  { value: 1, labelKey: 'tinkering-index.level-1', descriptionKey: 'tinkering-index.level-1-desc' },
  // ...
];

// Usage in components
const { t } = useI18n();
const levels = TINKERING_INDEX_LEVELS.map((level) => ({
  value: level.value,
  label: t(level.labelKey),
  description: t(level.descriptionKey),
}));
```

## Error Handling

### Missing Translation Keys

When a translation key is not found:

1. **Development Mode**: Log warning to console with missing key
2. **Production Mode**: Return the key itself as fallback text
3. **Graceful Degradation**: Application continues to function

```typescript
// Example fallback behavior
t('non.existent.key'); // Returns: 'non.existent.key'
```

### Translation File Loading Errors

When translation files fail to load:

1. **Retry Logic**: Attempt to reload once after 1 second delay
2. **Fallback**: Use empty translation object
3. **User Notification**: Show toast notification about language loading failure
4. **Graceful Degradation**: Display translation keys as text

### localStorage Unavailability

When localStorage is blocked or unavailable:

1. **Detection**: Wrap localStorage calls in try-catch
2. **Fallback**: Use browser language detection
3. **Session Persistence**: Store preference in memory for current session
4. **No Error Display**: Handle silently without user notification

### Browser Language Detection Failure

When browser language cannot be detected:

1. **Default Fallback**: Use 'en-US' as default
2. **No Error**: Handle silently
3. **User Control**: User can manually switch language

## Testing Strategy

### Property-Based Testing Applicability

**PBT is NOT applicable to this feature** because the bilingual UI system primarily involves:

1. **UI rendering and layout** - Language switcher component, visual feedback states
2. **Configuration and state management** - Language detection, localStorage persistence
3. **Side-effect operations** - Loading translation files, updating DOM attributes
4. **Browser API interactions** - navigator.language, localStorage, document.documentElement

These categories are better tested with:

- **Snapshot tests** for UI component rendering
- **Example-based unit tests** for specific behaviors
- **Integration tests** for end-to-end flows
- **Accessibility tests** for WCAG compliance

While there are some pure functions (translation key lookup, interpolation), they represent a small portion of the system and don't benefit significantly from property-based testing compared to example-based tests with edge cases.

### Testing Approach

The testing strategy uses a combination of unit tests, integration tests, and accessibility tests to ensure comprehensive coverage:

#### Unit Tests

**Language Detection Tests:**

- Test detection of Chinese variants (zh, zh-TW, zh-CN, zh-HK) → zh-TW
- Test detection of English variants (en, en-US, en-GB) → en-US
- Test fallback to en-US for unsupported languages (fr, de, ja)
- Test detection completion within 100ms
- Test handling of undefined navigator.language

**Translation Function Tests:**

- Test basic key lookup: `t('nav.articles')` returns correct translation
- Test nested key lookup: `t('errors.network-error')` traverses object correctly
- Test interpolation: `t('messages.article-count', { count: 5 })` replaces variables
- Test missing key fallback: `t('non.existent.key')` returns key itself
- Test special characters in translations (quotes, apostrophes, unicode)
- Test empty string translations
- Test numeric and boolean variable interpolation

**Storage Manager Tests:**

- Test saving valid locale to localStorage
- Test retrieving stored locale on initialization
- Test validation rejects invalid locale values
- Test graceful handling when localStorage is unavailable (private browsing)
- Test handling of corrupted stored data (invalid JSON)
- Test localStorage quota exceeded scenario

**Language Switcher Component Tests:**

- Test renders both language options (繁體中文, English)
- Test active language has correct visual styling
- Test clicking language option calls setLocale
- Test keyboard navigation with Tab key
- Test activation with Enter and Space keys
- Test ARIA attributes (role, aria-label, aria-pressed)
- Test minimum touch target size (44x44px)

#### Integration Tests

**End-to-End Language Switching Flow:**

- Test complete flow: initial detection → display → user switch → persist → reload
- Test language switch updates all UI elements within 200ms
- Test persistence across page reloads
- Test localStorage preference overrides browser detection
- Test switching between languages multiple times
- Test language switch with slow network (translation loading)

**Component Integration:**

- Test useI18n hook provides correct values in nested components
- Test translation updates propagate to all mounted components
- Test no unnecessary re-renders during language switch (React.memo effectiveness)
- Test multiple components using translations simultaneously
- Test translation updates in dynamically mounted components

**Error Handling Integration:**

- Test behavior when translation file fails to load
- Test behavior when translation file is malformed JSON
- Test behavior when localStorage is blocked
- Test behavior when browser language detection fails

#### Accessibility Tests

**Language Switcher Accessibility:**

- Test keyboard navigation: Tab moves focus between options
- Test keyboard activation: Enter and Space trigger language change
- Test focus indicators meet WCAG AA standards (2px minimum, 3:1 contrast)
- Test ARIA labels are present and descriptive
- Test ARIA pressed state updates correctly
- Test screen reader announcements on language change
- Test minimum touch target size (44x44px) on mobile viewports
- Test HTML lang attribute updates on document root

**Screen Reader Testing:**

- Test language switcher is announced correctly
- Test language change is announced to screen readers
- Test translated content is announced in correct language
- Test focus management during language switch

#### Translation Completeness Tests

**Validation Script:**

```typescript
// frontend/scripts/validate-translations.ts
// Validates that all keys exist in both language files
// Identifies missing translations
// Checks for unused translation keys
// Validates interpolation variable consistency
```

**Automated Checks:**

- All keys in zh-TW.json exist in en-US.json
- All keys in en-US.json exist in zh-TW.json
- All interpolation variables match between languages
- No duplicate keys within same file
- All translation values are non-empty strings

**Pre-commit Hook:**

- Run validation script before commits
- Prevent commits with missing translations
- Generate report of translation coverage
- Check for hardcoded Chinese/English text in components

#### Performance Tests

**Loading Performance:**

- Test initial language detection completes within 100ms
- Test language switch completes within 200ms
- Test translation file loading time
- Test memory usage with cached translations

**Bundle Size Tests:**

- Test translation files are code-split correctly
- Test only active language is in initial bundle
- Test alternative language loads on-demand

### Test Coverage Goals

- **Unit Test Coverage:** 90%+ for i18n utilities and context
- **Integration Test Coverage:** 100% of user-facing language switching flows
- **Accessibility Test Coverage:** 100% of WCAG AA requirements
- **Translation Completeness:** 100% key parity between languages

## Migration Strategy

### Phase 1: Infrastructure Setup (Week 1)

1. Create translation file structure
2. Implement I18nContext and provider
3. Implement Language Detector
4. Implement Storage Manager
5. Create LanguageSwitcher component
6. Add to app layout

### Phase 2: Translation File Population (Week 1-2)

1. Extract all hardcoded Chinese text from codebase
2. Create translation keys following naming conventions
3. Populate zh-TW.json with extracted text
4. Create English translations for en-US.json
5. Review and validate translations

### Phase 3: Component Migration (Week 2-3)

**Priority Order:**

1. Navigation components (highest visibility)
2. Common UI components (buttons, forms)
3. Notification messages
4. Error and success messages
5. Constants (TINKERING_INDEX_LEVELS, SORT_OPTIONS, etc.)
6. Feature-specific components

**Migration Pattern:**

```typescript
// Before
<button>儲存</button>

// After
const { t } = useI18n();
<button>{t('buttons.save')}</button>
```

### Phase 4: Testing and Validation (Week 3-4)

1. Run translation completeness validation
2. Execute unit tests for all i18n components
3. Perform integration testing
4. Conduct accessibility testing
5. User acceptance testing with both languages

### Phase 5: Documentation and Tooling (Week 4)

1. Create developer documentation
2. Set up ESLint rules to prevent hardcoded text
3. Create translation addition guide
4. Set up pre-commit hooks for validation

## Developer Experience

### TypeScript Support

Generate TypeScript types from translation files:

```typescript
// frontend/types/i18n.generated.ts
// Auto-generated from translation files

export type TranslationKey =
  | 'nav.articles'
  | 'nav.reading-list'
  | 'buttons.save'
  | 'buttons.cancel';
// ... all keys
```

**Generation Script:**

```bash
npm run generate:i18n-types
```

### ESLint Rules

Prevent hardcoded UI text in components:

```javascript
// .eslintrc.json
{
  "rules": {
    "no-restricted-syntax": [
      "error",
      {
        "selector": "JSXText[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected. Use translation keys instead."
      }
    ]
  }
}
```

### Validation Scripts

**Check Translation Completeness:**

```bash
npm run validate:translations
```

**Find Missing Translations:**

```bash
npm run find:missing-translations
```

**Find Unused Translation Keys:**

```bash
npm run find:unused-translations
```

### Usage Examples

**Basic Translation:**

```typescript
const { t } = useI18n();
<h1>{t('nav.articles')}</h1>
```

**Translation with Variables:**

```typescript
const { t } = useI18n();
<p>{t('messages.article-count', { count: 5 })}</p>
// Output (zh-TW): "成功抓取 5 篇新文章"
// Output (en-US): "Successfully fetched 5 new articles"
```

**Translation in Constants:**

```typescript
const { t } = useI18n();
const sortOptions = SORT_OPTIONS.map((option) => ({
  ...option,
  label: t(`sort.${option.value}`),
}));
```

**Conditional Translation:**

```typescript
const { t, locale } = useI18n();
const dateFormat = locale === 'zh-TW' ? 'YYYY年MM月DD日' : 'MMM DD, YYYY';
```

## Performance Optimization

### Code Splitting

Translation files are loaded dynamically using dynamic imports:

```typescript
const response = await import(`@/locales/${targetLocale}.json`);
```

This ensures:

- Only active language is loaded initially
- Alternative language loads on-demand
- Reduces initial bundle size by ~50%

### Caching Strategy

**Memory Cache:**

- Loaded translations cached in React state
- No redundant fetching during session
- Cache cleared on language switch

**Browser Cache:**

- Translation files cached by browser
- Cache-Control headers set appropriately
- Versioning through file hashing

### Lazy Loading

**Initial Load:**

- Load only detected/stored language
- Defer alternative language until needed

**Language Switch:**

- Load new language asynchronously
- Show loading state during fetch
- Complete within 200ms target

### Re-render Optimization

**React.memo:**

```typescript
export const LanguageSwitcher = React.memo(LanguageSwitcherComponent);
```

**useMemo for Translations:**

```typescript
const translatedOptions = useMemo(
  () => options.map((opt) => ({ ...opt, label: t(opt.labelKey) })),
  [options, t]
);
```

**Context Optimization:**

- Separate loading state from translation state
- Prevent unnecessary re-renders
- Use context selectors if needed

## Accessibility

### WCAG AA Compliance

**Language Switcher:**

- Minimum touch target: 44x44px
- Focus indicator: 2px solid border
- Color contrast: 4.5:1 minimum
- Keyboard navigation: Full support

**ARIA Attributes:**

```tsx
<div role="group" aria-label="Language selector">
  <button aria-label="Switch to English" aria-pressed={locale === 'en-US'}>
    English
  </button>
</div>
```

### Screen Reader Support

**Language Change Announcement:**

```typescript
const announceLanguageChange = (newLocale: Locale) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', 'polite');
  announcement.textContent = `Language changed to ${newLocale === 'zh-TW' ? 'Traditional Chinese' : 'English'}`;
  document.body.appendChild(announcement);
  setTimeout(() => document.body.removeChild(announcement), 1000);
};
```

### HTML Lang Attribute

Update document language on switch:

```typescript
document.documentElement.lang = newLocale;
```

This ensures:

- Screen readers use correct pronunciation
- Browser translation tools work correctly
- Search engines index correctly

### Keyboard Navigation

**Language Switcher:**

- Tab: Move focus between language options
- Enter/Space: Activate selected language
- Escape: Close dropdown (if dropdown variant)

**Focus Management:**

- Visible focus indicators
- Logical tab order
- Focus trap in modals

## Security Considerations

### XSS Prevention

**Translation Content:**

- All translations are static JSON
- No user-generated content in translations
- React automatically escapes content

**Variable Interpolation:**

```typescript
// Safe: Variables are escaped by React
<p>{t('messages.article-count', { count: userInput })}</p>
```

### localStorage Security

**Data Validation:**

```typescript
const validateLocale = (value: string): value is Locale => {
  return ['zh-TW', 'en-US'].includes(value);
};
```

**No Sensitive Data:**

- Only language preference stored
- No authentication tokens
- No personal information

## Future Enhancements

### Additional Languages

**Extensibility:**

- Architecture supports adding new locales
- Add new translation file: `ja-JP.json`
- Update Locale type: `type Locale = 'zh-TW' | 'en-US' | 'ja-JP'`
- Add to SUPPORTED_LOCALES array

### Pluralization

**Implementation:**

```typescript
// Translation file
{
  "messages": {
    "article-count": {
      "zero": "No articles",
      "one": "1 article",
      "other": "{count} articles"
    }
  }
}

// Usage
t('messages.article-count', { count: 5 }, { plural: true })
```

### Date/Time Formatting

**Integration with date-fns:**

```typescript
import { format } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';

const formatDate = (date: Date, locale: Locale) => {
  const localeMap = { 'zh-TW': zhTW, 'en-US': enUS };
  return format(date, 'PPP', { locale: localeMap[locale] });
};
```

### Number Formatting

**Locale-aware formatting:**

```typescript
const formatNumber = (num: number, locale: Locale) => {
  return new Intl.NumberFormat(locale).format(num);
};
```

### Translation Management Platform

**Future Integration:**

- Integrate with Crowdin or Lokalise
- Enable non-developer translation updates
- Automated translation sync
- Translation memory and suggestions

---

**Document Version:** 1.0
**Created:** 2025-01-XX
**Status:** Ready for Review
