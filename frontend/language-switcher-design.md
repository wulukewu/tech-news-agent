# Language Switcher Design

## Overview

The language switcher provides a low-profile, elegant way for users to switch between Traditional Chinese (繁體中文) and English. It's designed to be unobtrusive while remaining accessible and easy to use.

## Design Philosophy

**"Hide it until needed, but make it easy to find"**

The language switcher follows these principles:

- **Low visual weight**: Uses icons and compact text to minimize space
- **Contextual placement**: Different variants for different contexts
- **Always accessible**: Available on every page, but not dominating the UI
- **Consistent behavior**: Same interaction patterns across all placements

## Variants

### 1. Icon Variant (Desktop Navigation)

**Location**: Top-right corner of navigation bar

**Appearance**:

- Globe icon (🌐) button
- Subtle hover effect
- Dropdown menu on click

**Behavior**:

- Click to open dropdown
- Shows both language options with native labels
- Checkmark indicates active language
- Closes on selection, outside click, or Escape key

**Use Cases**:

- Desktop navigation bar (landing page)
- Desktop navigation bar (app pages)

```tsx
<LanguageSwitcher variant="icon" />
```

### 2. Compact Variant (Footer & Mobile)

**Location**:

- Footer bottom bar (all devices)
- Mobile drawer menu (mobile only)

**Appearance**:

- Text-based: "繁 / EN"
- Active language highlighted
- Separator between options

**Behavior**:

- Direct click to switch
- No dropdown needed
- Immediate feedback

**Use Cases**:

- Footer (visible on all pages)
- Mobile navigation drawer

```tsx
<LanguageSwitcher variant="compact" />
```

## Placement Strategy

### Landing Page

**Desktop**:

- Icon variant in top-right navigation bar
- Compact variant in footer

**Mobile**:

- Compact variant in hamburger menu drawer
- Compact variant in footer

### App Pages (Authenticated)

**Desktop**:

- Icon variant in top-right navigation bar (next to theme toggle and user menu)

**Mobile**:

- Compact variant in drawer menu (with theme toggle)

## Visual Hierarchy

The language switcher is intentionally placed lower in the visual hierarchy:

1. **Primary actions**: Login, Enter App, Main navigation
2. **Secondary actions**: Theme toggle, User menu
3. **Tertiary actions**: **Language switcher** ← Here
4. **Footer links**: Legal, social media

This ensures it doesn't compete with primary user flows while remaining accessible.

## Accessibility Features

### Keyboard Navigation

- Tab to focus
- Enter/Space to activate
- Escape to close dropdown (icon variant)

### Screen Readers

- Descriptive ARIA labels
- Language change announcements
- Proper role attributes

### Touch Targets

- Minimum 44x44px touch targets
- Adequate spacing between options

### Visual Feedback

- Clear focus indicators
- Active state highlighting
- Smooth transitions

## Implementation Details

### Component Structure

```tsx
<LanguageSwitcher
  variant="icon" | "compact"
  className="optional-custom-classes"
/>
```

### State Management

- Uses `useI18n()` hook from I18nContext
- Calls `setLocale(newLocale)` on selection
- Automatically updates all UI text

### Styling

- Uses Tailwind CSS utilities
- Respects theme (light/dark mode)
- Consistent with design system

## User Experience Flow

### First Visit

1. System detects browser language
2. Loads appropriate translations
3. Language switcher shows current language as active

### Switching Language

1. User clicks language switcher
2. Dropdown opens (icon variant) or direct switch (compact variant)
3. User selects desired language
4. UI updates within 200ms
5. Preference saved to localStorage
6. Screen reader announces change

### Return Visit

1. System loads saved preference
2. UI displays in preferred language
3. Language switcher reflects saved choice

## Design Rationale

### Why Two Variants?

**Icon Variant (Desktop)**:

- Saves horizontal space in navigation bar
- Professional, modern appearance
- Familiar pattern (globe = language)

**Compact Variant (Mobile/Footer)**:

- More direct, no extra click needed
- Clear language labels
- Better for touch interfaces

### Why These Placements?

**Top-right navigation**:

- Standard location for language switchers
- Near other settings (theme, user menu)
- Visible but not intrusive

**Footer**:

- Always accessible, even on long pages
- Common pattern for language selection
- Doesn't interfere with main content

**Mobile drawer**:

- Grouped with other settings
- Easy to access from menu
- Doesn't clutter main navigation

## Future Enhancements

Potential improvements for future iterations:

1. **Auto-detection notification**: "We detected your language preference. Switch to [language]?"
2. **Language-specific content**: Show different content based on language (e.g., localized blog posts)
3. **More languages**: Expand beyond zh-TW and en-US
4. **Regional variants**: Support zh-CN (Simplified Chinese), en-GB, etc.
5. **Keyboard shortcut**: Quick language switch with Ctrl+Shift+L

## Testing Checklist

- [ ] Icon variant renders correctly on desktop
- [ ] Compact variant renders correctly on mobile
- [ ] Dropdown opens/closes properly
- [ ] Language switches successfully
- [ ] Preference persists across sessions
- [ ] All UI text updates after switch
- [ ] Keyboard navigation works
- [ ] Screen reader announces changes
- [ ] Touch targets meet 44x44px minimum
- [ ] Works in both light and dark themes

---

**Last Updated**: 2026-04-19
**Status**: Implemented ✅
