# Hardcoded Text Audit Report

**Date:** 2025-01-XX
**Task:** 13.4 - Verify no hardcoded UI text remains
**Spec:** bilingual-ui-system

## Executive Summary

ESLint scan detected **91 violations** of hardcoded Chinese text in JSX across **23 files**, plus **14 additional violations** in non-JSX code (utility functions and constants) for a total of **105 violations** in the frontend codebase.

### Violation Breakdown

- **Production Code (JSX):** 19 files with 82 violations
- **Production Code (Non-JSX):** 3 files with 14 violations
- **Example/Demo Files:** 1 file with 1 violation
- **Test Files:** 0 violations (test files excluded from scan)
- **Total Production Violations:** 96 violations across 22 files

## Production Code Violations (MUST FIX)

These files contain hardcoded Chinese text that affects the user-facing application:

### Critical Files (User-Facing UI)

1. **app/not-found.tsx** - 10 violations

   - 404 error page with hardcoded Chinese text
   - Lines: 63, 64, 75, 83, 92, 99, 107, 115, 123, 136

2. **components/OnboardingModal.tsx** - 15 violations

   - Onboarding flow with hardcoded Chinese instructions
   - Lines: 217, 218, 225, 229, 233, 237, 240, 250, 251, 288, 298, 315, 316, 317, 318

3. **components/SchedulerStatusIndicator.tsx** - 8 violations

   - Status messages and labels in Chinese
   - Lines: 109, 117, 128, 134, 135, 145 (aria-label), 146

4. **components/TooltipTour.tsx** - 3 violations

   - Tooltip guidance text in Chinese
   - Lines: 193, 202 (aria-label), 212

5. **components/EmptyState.tsx** - 3 violations

   - Empty state messages in Chinese
   - Lines: 132, 138 (2 violations)

6. **components/ProtectedRoute.tsx** - 1 violation
   - Authentication message in Chinese
   - Line: 52

### Layout Components

7. **components/layout/Header.tsx** - 9 violations

   - Navigation labels and aria-labels in Chinese
   - Lines: 84, 97, 111 (aria-labels), 132, 135, 138, 141, 151

8. **components/layout/AppLayout.tsx** - 1 violation

   - Aria-label in Chinese
   - Line: 63

9. **components/layout/Breadcrumb.tsx** - 1 violation

   - Aria-label in Chinese
   - Line: 30

10. **components/layout/DashboardLayout.tsx** - 1 violation
    - Aria-label in Chinese
    - Line: 35

### UI Components

11. **components/ui/pagination.tsx** - 14 violations

    - Pagination labels and aria-labels in Chinese
    - Lines: 96, 106, 109, 120, 170, 184, 187, 214, 215 (2), 217, 218 (2)

12. **components/ui/drag-drop-list.tsx** - 4 violations

    - Drag-drop interface labels in Chinese
    - Lines: 217, 268 (aria-labels), 282, 292

13. **components/ui/error-message.tsx** - 5 violations

    - Error message titles in Chinese
    - Lines: 104, 113, 118, 125, 182 (all title attributes)

14. **components/ui/contextual-tooltip.tsx** - 4 violations

    - Tooltip aria-labels in Chinese
    - Lines: 161, 163, 165, 166 (all aria-labels)

15. **components/ui/optimized-image.tsx** - 2 violations
    - Image loading/error text in Chinese
    - Lines: 145, 163

### Legacy/Old Files

16. **app/page-old.tsx** - 4 violations
    - Old page with hardcoded Chinese text
    - Lines: 98, 120, 121, 136
    - **Note:** This appears to be a legacy file that may be safe to ignore if not in use

## Example/Demo Files (LOWER PRIORITY)

These files are for demonstration purposes and may have intentional hardcoded text:

17. **components/examples/LanguageSwitcherExample.tsx** - 1 violation
    - Example component demonstrating language switching
    - Line: 36
    - **Justification:** Demo file showing how the language switcher works

## Test Files (ACCEPTABLE)

Test files may have intentional hardcoded text for testing purposes:

18. **components/ui/**tests**/drag-drop-list.test.tsx** - 0 violations (warnings only)
19. **components/ui/**tests**/multi-select-filter.test.tsx** - 0 violations (warnings only)

## Accessibility Violations (aria-label)

The following files have hardcoded Chinese text in `aria-label` attributes, which affects screen reader accessibility:

- components/SchedulerStatusIndicator.tsx (line 145)
- components/TooltipTour.tsx (line 202)
- components/layout/AppLayout.tsx (line 63)
- components/layout/Breadcrumb.tsx (line 30)
- components/layout/DashboardLayout.tsx (line 35)
- components/layout/Header.tsx (lines 84, 97, 111)
- components/ui/pagination.tsx (lines 96, 106, 120, 170, 184)
- components/ui/drag-drop-list.tsx (lines 217, 268)
- components/ui/contextual-tooltip.tsx (lines 161, 163, 165, 166)

## Additional Violations (Non-JSX)

ESLint rules only detect hardcoded text in JSX. Additional violations were found in TypeScript/JavaScript code:

### Utility Functions

20. **lib/utils/index.ts** - 4 violations
    - `formatRelativeTime()` function with hardcoded Chinese time labels
    - Lines: 26 ("剛剛"), 31 ("分鐘前"), 36 ("小時前"), 41 ("天前")
    - **Impact:** Relative time display (e.g., "2 小時前") is hardcoded in Chinese

### Constants

21. **lib/constants/index.ts** - 1 violation

    - `LANGUAGE_OPTIONS` constant with hardcoded Chinese label
    - Line: 197 ("繁體中文")
    - **Impact:** Language selector displays hardcoded label

22. **lib/hooks/useUrlState.ts** - 9 violations
    - Keyboard shortcut descriptions in Chinese
    - Lines: 304-312 (descriptions for j, k, r, /, f, s, Ctrl+A, c, 1-5 keys)
    - **Impact:** Keyboard shortcut help text is hardcoded in Chinese

### Total Violations Summary

- **JSX Violations (detected by ESLint):** 91 violations
- **Non-JSX Violations (manual search):** 14 violations
- **Grand Total:** 105 violations across 22 production files

## Recommendations

### Immediate Actions Required

1. **Fix Production Code (Priority 1)**

   - Migrate all 96 violations in production code to use translation keys
   - Focus on user-facing components first (OnboardingModal, SchedulerStatusIndicator, not-found page)
   - Update aria-labels to use `t('translation.key')` for accessibility
   - Fix utility functions (`formatRelativeTime`) to use translation keys
   - Update constants (`LANGUAGE_OPTIONS`, keyboard shortcuts) to use translation keys

2. **Add ESLint Rules for Non-JSX Code (Priority 2)**

   - Current ESLint rules only detect JSX violations
   - Consider adding rules to detect hardcoded Chinese in string literals
   - Add pre-commit hooks to prevent new hardcoded text

3. **Verify Legacy Files (Priority 3)**

   - Confirm if `app/page-old.tsx` is still in use
   - If not in use, consider removing or documenting as deprecated

4. **Example Files (Priority 3)**
   - Review `LanguageSwitcherExample.tsx` to determine if hardcoded text is intentional
   - If intentional, add ESLint disable comment with justification

### Migration Pattern

For each violation, follow this pattern:

**Before:**

```tsx
<button>儲存</button>
<div aria-label="關閉選單">...</div>
```

**After:**

```tsx
const { t } = useI18n();
<button>{t('buttons.save')}</button>
<div aria-label={t('aria.close-menu')}>...</div>
```

### Translation Keys Needed

Based on the violations, the following translation key categories need to be added to `locales/zh-TW.json` and `locales/en-US.json`:

- `errors.not-found.*` - 404 page messages
- `onboarding.*` - Onboarding modal steps and instructions
- `scheduler.*` - Scheduler status messages
- `tooltips.*` - Tooltip guidance text
- `empty-state.*` - Empty state messages
- `auth.*` - Authentication messages
- `aria.*` - Accessibility labels
- `pagination.*` - Pagination controls
- `drag-drop.*` - Drag and drop interface labels
- `image.*` - Image loading/error states
- `time.*` - Relative time labels (just now, minutes ago, hours ago, days ago)
- `keyboard.*` - Keyboard shortcut descriptions

## Compliance Status

### Requirement 10.5 Compliance

**Status:** ❌ **NOT COMPLIANT**

The codebase currently has **96 hardcoded Chinese text violations** in production code (82 in JSX + 14 in non-JSX), which violates:

- **Requirement 10.5:** "WHEN migration is complete, THE codebase SHALL contain no hardcoded Chinese or English UI text outside translation files"

### Next Steps

1. Create translation keys for all identified violations
2. Update components to use `useI18n()` hook and `t()` function
3. Re-run ESLint to verify all violations are resolved
4. Update this audit report with final status

## ESLint Configuration

The project has proper ESLint rules configured in `frontend/.eslintrc.json`:

```json
{
  "rules": {
    "no-restricted-syntax": [
      "error",
      {
        "selector": "JSXText[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in JSX..."
      },
      {
        "selector": "JSXAttribute[name.name='placeholder'] Literal[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in placeholder attribute..."
      },
      {
        "selector": "JSXAttribute[name.name='title'] Literal[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in title attribute..."
      },
      {
        "selector": "JSXAttribute[name.name='aria-label'] Literal[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in aria-label attribute..."
      },
      {
        "selector": "JSXAttribute[name.name='alt'] Literal[value=/[\\u4e00-\\u9fa5]/]",
        "message": "Hardcoded Chinese text detected in alt attribute..."
      }
    ]
  }
}
```

These rules successfully detect hardcoded Chinese text in:

- JSX text content
- `placeholder` attributes
- `title` attributes
- `aria-label` attributes
- `alt` attributes

## Warnings (Non-Blocking)

The ESLint scan also reported numerous warnings that are not related to hardcoded text:

- Code complexity warnings (max-lines-per-function, complexity)
- Console statement warnings
- TypeScript `any` type warnings
- Unused variable warnings
- Nested ternary warnings

These warnings should be addressed separately and are not part of the bilingual UI system migration.

---

**Report Generated:** 2025-01-XX
**Tool:** ESLint with custom i18n rules
**Command:** `npm run lint` (from frontend directory)
