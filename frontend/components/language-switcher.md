# LanguageSwitcher Component

## Overview

The `LanguageSwitcher` component provides a user interface for manually switching between Traditional Chinese (zh-TW) and English (en-US) languages in the application. It integrates with the I18nContext to manage language state and persistence.

## Features

### Core Functionality

- **Dual Language Support**: Displays both 繁體中文 and English options
- **Visual Feedback**: Highlights the currently active language with a distinct background
- **Instant Switching**: Changes language within 200ms (handled by I18nContext)
- **Persistence**: Saves language preference to localStorage automatically

### Accessibility (WCAG AA Compliant)

- **Semantic HTML**: Uses `role="group"` for proper grouping
- **ARIA Attributes**:
  - `aria-label="Language selector"` on the container
  - `aria-pressed` state on buttons to indicate active language
  - Descriptive `aria-label` on each button (e.g., "Switch to English")
- **Keyboard Navigation**:
  - Tab key to move focus between options
  - Enter or Space key to activate selection
- **Focus Indicators**: 2px blue ring with offset on focus (focus:ring-2 focus:ring-blue-500)
- **Touch Target Size**: Minimum 44x44px for mobile accessibility
- **Smooth Transitions**: 200ms color transitions for visual feedback

### Design

- **Light/Dark Mode Support**: Adapts to theme with appropriate colors
- **Responsive**: Works on all screen sizes
- **Consistent Styling**: Matches application design system

## Usage

### Basic Usage

```tsx
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

function Navigation() {
  return (
    <nav>
      <LanguageSwitcher />
    </nav>
  );
}
```

### In Navigation Bar

```tsx
<nav className="flex items-center justify-between">
  <div className="flex gap-4">
    <Logo />
    <NavLinks />
  </div>
  <LanguageSwitcher />
</nav>
```

### In Settings Panel

```tsx
<div className="settings-section">
  <h3>Language Preference</h3>
  <p>Choose your preferred interface language</p>
  <LanguageSwitcher />
</div>
```

## Integration

The component integrates with the I18nContext:

```tsx
const { locale, setLocale } = useI18n();
```

- **locale**: Current active language ('zh-TW' | 'en-US')
- **setLocale**: Function to change the language

When a user clicks a language option, the component calls `setLocale(newLocale)`, which:

1. Updates the locale state
2. Loads the corresponding translation file
3. Updates the HTML `lang` attribute
4. Persists the preference to localStorage

## Styling

The component uses Tailwind CSS classes for styling:

- **Container**: `bg-gray-100 dark:bg-gray-800` with rounded corners and padding
- **Active Button**: `bg-white dark:bg-gray-700` with shadow
- **Inactive Button**: `text-gray-600 dark:text-gray-400` with hover effects
- **Transitions**: `transition-colors duration-200` for smooth state changes
- **Focus**: `focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`

## Testing

The component has comprehensive test coverage:

- **Rendering Tests**: Verifies both language options are displayed
- **Visual Feedback Tests**: Checks active/inactive states
- **Language Switching Tests**: Validates switching behavior and persistence
- **Keyboard Navigation Tests**: Ensures Tab, Enter, and Space key support
- **Accessibility Tests**: Verifies ARIA attributes, focus indicators, and touch targets
- **Dark Mode Tests**: Confirms dark mode styling
- **Integration Tests**: Tests I18nContext integration

Run tests:

```bash
npm test -- LanguageSwitcher --run
```

## Requirements Satisfied

This component satisfies the following requirements from the bilingual-ui-system spec:

- **3.1**: Display both language options (繁體中文 and English)
- **3.2**: Change language within 200ms
- **3.3**: Visual feedback for active language
- **3.5**: Accessible from navigation bar
- **3.6**: Keyboard navigation support (Tab, Enter, Space)
- **9.1**: Proper ARIA labels
- **9.2**: Screen reader announcements (via aria-pressed)
- **9.3**: Keyboard navigable
- **9.4**: Visible focus indicators (WCAG AA)
- **9.6**: Minimum touch target size (44x44px)

## Example

See `frontend/components/examples/LanguageSwitcherExample.tsx` for a comprehensive demonstration of the component in various contexts.

## Related Files

- **Component**: `frontend/components/LanguageSwitcher.tsx`
- **Context**: `frontend/contexts/I18nContext.tsx`
- **Types**: `frontend/types/i18n.ts`
- **Tests**: `frontend/__tests__/unit/components/LanguageSwitcher.test.tsx`
- **Example**: `frontend/components/examples/LanguageSwitcherExample.tsx`
