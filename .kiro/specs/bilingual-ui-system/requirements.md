# Requirements Document: Bilingual UI System

## Introduction

This document defines the requirements for implementing a bilingual user interface system that supports seamless switching between Chinese (Traditional Chinese, zh-TW) and English (en-US) languages. The system addresses the current issue where UI text is inconsistently mixed between Chinese and English, providing users with a unified language experience based on their preference or system settings.

The bilingual system will enable users to view all UI elements, messages, labels, and content in their preferred language, with automatic detection of system language preferences and manual override capabilities. Language preferences will persist across sessions to maintain a consistent user experience.

## Glossary

- **I18n_System**: The internationalization system responsible for managing translations and language switching
- **Language_Detector**: Component that detects the user's preferred language from browser/system settings
- **Translation_Provider**: React context provider that supplies translation functions to components
- **Language_Switcher**: UI component that allows users to manually change the interface language
- **Translation_Key**: Unique identifier for each translatable text string
- **Locale**: Language and region code (e.g., zh-TW, en-US)
- **Storage_Manager**: Component that persists language preferences to localStorage
- **UI_Text**: Any user-facing text including labels, messages, notifications, and descriptions

## Requirements

### Requirement 1: Language Detection and Initialization

**User Story:** As a user, I want the application to automatically detect my preferred language from my browser/system settings, so that I see the interface in my native language by default.

#### Acceptance Criteria

1. WHEN the application loads for the first time, THE Language_Detector SHALL detect the browser's language setting
2. IF the detected language is Chinese (zh, zh-TW, zh-CN, zh-HK), THEN THE I18n_System SHALL set the default language to zh-TW
3. IF the detected language is English (en, en-US, en-GB), THEN THE I18n_System SHALL set the default language to en-US
4. IF the detected language is neither Chinese nor English, THEN THE I18n_System SHALL default to en-US
5. WHEN a stored language preference exists in localStorage, THE I18n_System SHALL use the stored preference instead of browser detection
6. THE Language_Detector SHALL complete detection within 100ms to prevent UI flash

### Requirement 2: Language Persistence

**User Story:** As a user, I want my language preference to be remembered across sessions, so that I don't have to select my language every time I visit the application.

#### Acceptance Criteria

1. WHEN a user selects a language, THE Storage_Manager SHALL save the preference to localStorage
2. THE Storage_Manager SHALL use the key "language" for storing the language preference
3. WHEN the application loads, THE I18n_System SHALL retrieve the stored language preference before applying browser detection
4. IF localStorage is unavailable or blocked, THEN THE I18n_System SHALL fall back to browser detection without throwing errors
5. THE Storage_Manager SHALL validate stored language values and reject invalid locales

### Requirement 3: Manual Language Switching

**User Story:** As a user, I want to manually switch between Chinese and English at any time, so that I can choose my preferred language regardless of system settings.

#### Acceptance Criteria

1. THE Language_Switcher SHALL display both language options (繁體中文 and English)
2. WHEN a user clicks a language option, THE I18n_System SHALL change the interface language within 200ms
3. THE Language_Switcher SHALL indicate the currently active language with visual feedback
4. WHEN the language changes, THE Translation_Provider SHALL update all UI_Text immediately without requiring page reload
5. THE Language_Switcher SHALL be accessible from the navigation bar on all authenticated pages
6. THE Language_Switcher SHALL support keyboard navigation (Tab, Enter, Space)

### Requirement 4: Translation Coverage

**User Story:** As a user, I want all UI elements to be properly translated, so that I have a consistent experience in my chosen language.

#### Acceptance Criteria

1. THE I18n_System SHALL provide translations for all navigation labels (Articles, Reading List, Subscriptions, Analytics, Settings, System Status)
2. THE I18n_System SHALL provide translations for all button labels (Save, Cancel, Delete, Edit, Add, Remove, etc.)
3. THE I18n_System SHALL provide translations for all form labels and placeholders
4. THE I18n_System SHALL provide translations for all notification messages (success, error, warning, info)
5. THE I18n_System SHALL provide translations for all status messages and loading indicators
6. THE I18n_System SHALL provide translations for all error messages defined in ERROR_MESSAGES constant
7. THE I18n_System SHALL provide translations for all success messages defined in SUCCESS_MESSAGES constant
8. THE I18n_System SHALL provide translations for all dropdown options (sort options, theme options, notification frequency)
9. THE I18n_System SHALL provide translations for all tinkering index levels and descriptions
10. THE I18n_System SHALL provide translations for all keyboard shortcut descriptions

### Requirement 5: Translation File Structure

**User Story:** As a developer, I want translation files to be well-organized and maintainable, so that adding new translations is straightforward.

#### Acceptance Criteria

1. THE I18n_System SHALL organize translations in JSON files under `frontend/locales/` directory
2. THE I18n_System SHALL maintain separate files for each locale: `zh-TW.json` and `en-US.json`
3. THE I18n_System SHALL use nested object structure to group related translations (e.g., `nav`, `buttons`, `messages`, `errors`)
4. THE I18n_System SHALL use kebab-case for Translation_Keys (e.g., `reading-list`, `add-to-list`)
5. WHEN a Translation_Key is missing, THE I18n_System SHALL return the key itself as fallback text
6. THE I18n_System SHALL log warnings to console when Translation_Keys are missing in development mode

### Requirement 6: Dynamic Content Translation

**User Story:** As a user, I want dynamic content like counts and dates to be properly formatted in my chosen language, so that all information is culturally appropriate.

#### Acceptance Criteria

1. WHEN displaying article counts, THE I18n_System SHALL use language-appropriate number formatting
2. WHEN displaying dates, THE I18n_System SHALL format dates according to the selected locale (zh-TW: YYYY年MM月DD日, en-US: MMM DD, YYYY)
3. WHEN displaying relative time (e.g., "2 hours ago"), THE I18n_System SHALL use locale-appropriate text
4. THE I18n_System SHALL support interpolation for dynamic values in translations (e.g., "成功抓取 {count} 篇新文章")
5. THE I18n_System SHALL support pluralization rules for both languages

### Requirement 7: Translation Provider Integration

**User Story:** As a developer, I want a simple API for accessing translations in components, so that implementing translations is consistent and easy.

#### Acceptance Criteria

1. THE Translation_Provider SHALL expose a `t` function for translating keys
2. THE Translation_Provider SHALL expose a `locale` value indicating the current language
3. THE Translation_Provider SHALL expose a `setLocale` function for changing the language
4. THE Translation_Provider SHALL be accessible via React hooks (e.g., `useTranslation`)
5. WHEN a component calls `t(key)`, THE Translation_Provider SHALL return the translated string for the current locale
6. THE Translation_Provider SHALL support nested key access using dot notation (e.g., `t('nav.articles')`)
7. THE Translation_Provider SHALL support passing variables for interpolation (e.g., `t('messages.article-count', { count: 5 })`)

### Requirement 8: Performance Optimization

**User Story:** As a user, I want language switching to be fast and smooth, so that the interface remains responsive.

#### Acceptance Criteria

1. THE I18n_System SHALL load only the active language's translations on initial render
2. THE I18n_System SHALL lazy-load alternative language translations when user switches languages
3. WHEN switching languages, THE I18n_System SHALL complete the switch within 200ms
4. THE I18n_System SHALL cache loaded translations in memory to prevent redundant fetching
5. THE I18n_System SHALL use code splitting to avoid including all translations in the main bundle
6. THE Translation_Provider SHALL use React.memo or useMemo to prevent unnecessary re-renders

### Requirement 9: Accessibility

**User Story:** As a user with accessibility needs, I want the language switcher to be fully accessible, so that I can change languages using keyboard or screen readers.

#### Acceptance Criteria

1. THE Language_Switcher SHALL have proper ARIA labels indicating its purpose
2. THE Language_Switcher SHALL announce language changes to screen readers
3. THE Language_Switcher SHALL be keyboard navigable with Tab, Enter, and Space keys
4. THE Language_Switcher SHALL have visible focus indicators meeting WCAG AA standards (2px minimum)
5. WHEN the language changes, THE I18n_System SHALL update the HTML lang attribute on the document root
6. THE Language_Switcher SHALL have a minimum touch target size of 44x44px on mobile devices

### Requirement 10: Migration of Existing Text

**User Story:** As a developer, I want existing hardcoded Chinese text to be migrated to the translation system, so that all text is properly internationalized.

#### Acceptance Criteria

1. THE I18n_System SHALL replace all hardcoded Chinese text in constants (TINKERING_INDEX_LEVELS, SORT_OPTIONS, THEME_OPTIONS, etc.)
2. THE I18n_System SHALL replace all hardcoded Chinese text in notification messages (useSchedulerNotifications hook)
3. THE I18n_System SHALL replace all hardcoded Chinese text in keyboard shortcut descriptions
4. THE I18n_System SHALL replace all hardcoded Chinese text in error and success messages
5. WHEN migration is complete, THE codebase SHALL contain no hardcoded Chinese or English UI text outside translation files
6. THE I18n_System SHALL maintain backward compatibility during migration by supporting both old and new translation keys temporarily

### Requirement 11: Testing and Validation

**User Story:** As a developer, I want comprehensive tests for the i18n system, so that language switching works reliably.

#### Acceptance Criteria

1. THE I18n_System SHALL include unit tests for language detection logic
2. THE I18n_System SHALL include unit tests for translation key lookup and fallback behavior
3. THE I18n_System SHALL include unit tests for interpolation and pluralization
4. THE I18n_System SHALL include integration tests for language switching in components
5. THE I18n_System SHALL include tests verifying all Translation_Keys have corresponding values in both language files
6. THE I18n_System SHALL include tests for localStorage persistence and retrieval
7. THE I18n_System SHALL include accessibility tests for the Language_Switcher component

### Requirement 12: Developer Experience

**User Story:** As a developer, I want clear documentation and tooling for working with translations, so that adding new features with i18n support is straightforward.

#### Acceptance Criteria

1. THE I18n_System SHALL provide TypeScript types for all Translation_Keys to enable autocomplete
2. THE I18n_System SHALL provide a script to validate that all keys exist in both language files
3. THE I18n_System SHALL provide a script to identify missing translations
4. THE I18n_System SHALL include documentation on how to add new translations
5. THE I18n_System SHALL include examples of common translation patterns (interpolation, pluralization, nested keys)
6. THE I18n_System SHALL provide ESLint rules to prevent hardcoded UI text in components

---

**Document Version:** 1.0
**Created:** 2025-01-XX
**Status:** Ready for Review
