# Implementation Plan: Frontend UI/UX Redesign

## Recent Fixes (2026-04-18)

### ✅ Navbar Layout Optimization

**Issue:** Logout button was too large and caused navbar elements to overflow or display incorrectly.

**Changes:**

- Reduced spacing between all navbar elements for better space utilization
  - Main container gap: `gap-4 lg:gap-6` (responsive)
  - Nav items gap: `gap-1.5 lg:gap-2` (tighter on medium screens)
  - Right section gap: `gap-2` (reduced from `gap-4`)
- Optimized Logout button styling
  - Changed from `variant="outline"` to `variant="ghost"` for less visual weight
  - Reduced padding: `px-2.5` with `gap-1.5` between icon and text
  - Added `title` attribute for tooltip
- Optimized user profile section
  - Only show on large screens (`hidden lg:flex` instead of `hidden md:flex`)
  - Reduced avatar size: `h-7 w-7` (from `h-8 w-8`)
  - Added username truncation with `max-w-[100px] truncate`
  - Smaller avatar text: `text-xs`
- Optimized nav items
  - Responsive padding: `px-2.5 lg:px-3` (tighter on medium screens)
  - Reduced icon-text gap: `gap-1.5` (from `gap-2`)
  - Added `whitespace-nowrap` to prevent text wrapping
  - Added `flex-shrink-0` to logo to prevent squishing

**Files Modified:**

- `frontend/components/Navigation.tsx`

**Result:** Navbar now fits comfortably at all screen sizes without overflow, with all elements properly visible and aligned.

### ✅ Navbar UI Fix

**Issue:** Active navigation item had a solid white background that looked incorrect in dark theme.

**Changes:**

- Fixed active navigation item styling to use subtle background instead of solid primary color
- Changed from `bg-primary text-primary-foreground` to `bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-foreground`
- Added proper text color for inactive items (`text-foreground`)
- Reduced gap between nav items from `gap-4` to `gap-2` for better spacing
- Added `font-medium` to nav item labels for better readability
- Added `text-sm` for consistent sizing

**Files Modified:**

- `frontend/components/Navigation.tsx`

### ✅ Article Image Display Fix

**Issue:** Article cards showed "No Image Available" placeholder images even when articles didn't have images.

**Changes:**

- Removed placeholder images from article cards
- Images now only display when `article.imageUrl` exists (conditional rendering)
- Improved error handling to hide broken images instead of showing placeholders
- Adjusted desktop layout padding to accommodate cards without images
- Cards without images now have proper padding on both sides (`px-4` instead of `pr-4`)

**Files Modified:**

- `frontend/components/ArticleCard.tsx`

**Result:** Cleaner UI that doesn't show unnecessary placeholder images. Cards adapt gracefully whether they have images or not.

---

## Overview

This implementation plan translates the comprehensive UI/UX redesign requirements and design specifications into actionable coding tasks. The plan follows a 5-phase approach: Design System Foundation → Core Components → Page Layouts → States & Interactions → Optimization & Polish.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui
**Target Breakpoints:** 375px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide)
**Requirements Coverage:** 30 requirements with 240+ acceptance criteria

## Tasks

### Phase 1: Design System Foundation

- [x] 1. Configure Tailwind design tokens and theme system
  - Update `tailwind.config.ts` with custom breakpoints (xs: 375px, md: 768px, lg: 1024px, xl: 1440px)
  - Add custom spacing scale (44px, 56px for touch targets)
  - Define semantic color tokens (primary, secondary, accent, destructive, muted)
  - Configure typography scale (xs: 12px through 5xl: 48px)
  - Add custom border radius values (sm: 2px through 3xl: 16px)
  - Define shadow system (sm, md, lg, xl)
  - Configure animation timing functions and durations
  - Add custom utilities for touch targets (min-h-44, min-w-44)
  - _Requirements: 1.1, 1.7, 1.8, 4.1, 4.4, 4.5, 4.7_

- [x] 2. Implement theme switching with next-themes
  - Install and configure next-themes package
  - Create CSS variables for light and dark mode colors
  - Implement theme provider in root layout
  - Add theme toggle component with sun/moon icons
  - Persist theme preference in localStorage
  - Respect prefers-color-scheme system preference
  - Add smooth color transitions (200ms) when switching themes
  - Update meta theme-color tag dynamically
  - _Requirements: 4.2, 4.8, 17.1, 17.2, 17.3, 17.6, 17.7, 17.8_

- [x] 3. Set up category color mapping system
  - Define category color constants (Tech News: blue, AI/ML: purple, Web Dev: green, DevOps: orange, Security: red)
  - Create utility function for category color lookup
  - Ensure WCAG AA contrast ratios in both themes
  - Support custom category colors
  - Implement fallback to neutral color for unknown categories
  - _Requirements: 24.1, 24.2, 24.5, 24.6, 24.7_

- [x] 4. Checkpoint - Verify design system configuration
  - Ensure all tests pass, ask the user if questions arise.

### Phase 2: Core Components

- [x] 5. Create responsive navigation component
  - [x] 5.1 Build desktop sidebar navigation
    - Create fixed sidebar with 64px collapsed / 256px expanded width
    - Add logo section at top
    - Implement navigation items with active state indicator (left border highlight)
    - Add user profile section at bottom with avatar
    - Include theme toggle in profile section
    - Use semantic HTML nav element
    - _Requirements: 3.1, 3.4, 3.5, 3.6, 17.1_
  - [x] 5.2 Build mobile drawer navigation
    - Create hamburger menu button (visible below 768px)
    - Implement slide-out drawer with backdrop overlay
    - Add slide-in/out animations (300ms)
    - Prevent body scrolling when drawer is open
    - Use full-width menu items with 56px minimum height
    - Include close button and backdrop tap-to-close
    - _Requirements: 3.2, 3.3, 3.7, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8_
  - [x] 5.3 Add skip-to-content link for accessibility
    - Create visually hidden link that appears on focus
    - Link to main content area with id="main-content"
    - _Requirements: 15.4_

- [x] 6. Build article card component with responsive layouts
  - [x] 6.1 Create mobile vertical layout
    - Stack image, title, metadata, tinkering index, summary, actions vertically
    - Use full-width layout with proper spacing
    - Implement responsive image with next/image (400x225)
    - Add line-clamp-2 for title truncation
    - Display category badge with semantic colors
    - Show tinkering index with star icons (1-5)
    - Include action buttons (Read Later, Mark as Read) with 44px touch targets
    - _Requirements: 6.1, 6.2, 6.4, 6.7, 6.8, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8_
  - [x] 6.2 Create desktop horizontal layout
    - Position image on left (200x150), content on right
    - Use line-clamp-3 for title truncation
    - Add hover effects (shadow elevation, subtle transform)
    - Include share button in top-right corner
    - Optimize layout for 3-column grid
    - _Requirements: 6.1, 6.3, 6.5, 6.7, 6.8_
  - [x] 6.3 Implement tinkering index visualization
    - Create star rating component with 1-5 stars
    - Apply color coding (1-2: gray, 3: yellow, 4-5: orange)
    - Use filled stars for rating, outlined for remaining
    - Ensure 24px minimum size on mobile
    - Add tooltip showing numeric value and description
    - _Requirements: 25.1, 25.2, 25.3, 25.6, 25.7, 25.8_

- [x] 7. Create dialog/modal component
  - Implement using shadcn/ui Dialog component
  - Add mobile full-screen layout with slide-up animation
  - Add desktop centered overlay (max-width: 600px)
  - Include backdrop with 50% opacity
  - Add close button in top-right with 44px touch target
  - Implement focus trap within dialog
  - Add Escape key to close functionality
  - Limit content height to 85vh with vertical scrolling
  - Include safe area padding for notched devices
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [x] 8. Build form control components
  - [x] 8.1 Create base input component
    - Add label with 8px spacing above input
    - Include placeholder with muted color
    - Implement error state with destructive color
    - Add helper text below input
    - Use full-width on mobile, auto-width on desktop
    - Ensure 48px minimum height on mobile
    - Add visible focus ring (2px, primary color)
    - Implement disabled state (50% opacity, not-allowed cursor)
    - _Requirements: 11.1, 11.2, 11.3, 11.5, 11.6, 11.7, 11.8_
  - [x] 8.2 Create character count component
    - Display current/max character count
    - Update in real-time as user types
    - Change color when approaching limit
    - _Requirements: 11.4_
  - [x] 8.3 Build checkbox and toggle components
    - Ensure 44px minimum touch target
    - Add visible focus indicators
    - Support keyboard navigation
    - _Requirements: 2.1, 15.2, 15.3_

- [x] 9. Checkpoint - Verify core components
  - Ensure all tests pass, ask the user if questions arise.

### Phase 3: Page Layouts

- [x] 10. Implement dashboard page layout
  - [x] 10.1 Create responsive grid layout
    - Implement 1-column grid on mobile (< 768px)
    - Implement 2-column grid on tablet (768px-1024px)
    - Implement 3-column grid on desktop (1024px+)
    - Set maximum container width to 1400px
    - Add consistent gap spacing (16px)
    - _Requirements: 1.4, 1.5, 1.6_
  - [x] 10.2 Add search bar with debounced filtering
    - Create full-width search input on mobile
    - Implement 300ms debounce for search queries
    - Display search result count
    - Add clear search button when active
    - Filter articles by title, summary, or category
    - _Requirements: 18.1, 18.2, 18.3, 16.6_
  - [x] 10.3 Implement category filter system
    - Create multi-select badge filters
    - Use horizontal scroll on mobile
    - Update article list within 300ms of filter change
    - Persist filters in URL query parameters
    - _Requirements: 18.5, 18.6, 18.7_
  - [x] 10.4 Add infinite scroll functionality
    - Implement intersection observer for bottom detection
    - Trigger load when within 200px of bottom
    - Load 20 articles per page
    - Prevent multiple simultaneous requests
    - Display "No more articles" when complete
    - Maintain scroll position on navigation back
    - Handle scroll restoration on browser back/forward
    - _Requirements: 19.1, 19.2, 19.4, 19.5, 19.6, 19.7, 19.8_

- [x] 11. Build reading list page
  - [x] 11.1 Create status filter tabs
    - Implement tabs for All, Unread, Reading, Completed
    - Add horizontal scroll on mobile
    - Show clear active state indication
    - Update list within 300ms of filter change
    - _Requirements: 7.1, 7.2_
  - [x] 11.2 Implement article list with status and rating
    - Display articles with status indicators
    - Add 1-5 star rating control with touch-friendly targets
    - Stack metadata vertically on mobile
    - Provide immediate visual feedback on updates
    - Persist changes to backend
    - _Requirements: 7.3, 7.4, 7.5, 7.6_
  - [x] 11.3 Add infinite scroll for reading list
    - Implement same pattern as dashboard
    - Show loading indicator when fetching
    - _Requirements: 7.8_

- [x] 12. Create subscriptions management page
  - [x] 12.1 Build collapsible category sections
    - Group feeds by category
    - Implement expand/collapse with 300ms animation
    - Persist expanded state in localStorage
    - _Requirements: 8.1, 8.2_
  - [x] 12.2 Add feed health indicators
    - Display health status with color coding (green: healthy, yellow: stale, red: error, gray: unknown)
    - Show health indicator icon (check circle, alert triangle, x circle)
    - Display last update timestamp (relative time)
    - Show error message in tooltip on hover
    - Sort feeds by health status within categories
    - Display health statistics summary at top
    - _Requirements: 8.3, 26.1, 26.2, 26.3, 26.5, 26.6, 26.8_
  - [x] 12.3 Implement feed statistics display
    - Show total articles, articles this week, average tinkering index
    - Use star visualization for average tinkering index
    - _Requirements: 8.6, 25.5_
  - [x] 12.4 Add bulk actions
    - Create Subscribe All, Unsubscribe All, Subscribe Recommended buttons
    - Add retry all failed feeds action
    - Show optimistic UI updates with loading states
    - _Requirements: 8.4, 8.7, 26.7_
  - [x] 12.5 Implement feed search functionality
    - Add search input to filter by name, category, or tag
    - Stack feed information vertically on mobile
    - _Requirements: 8.5, 8.8, 18.4_

- [x] 13. Build notifications settings page
  - [x] 13.1 Create global notification toggle
    - Display clear on/off state
    - Disable all per-feed controls when global is off
    - _Requirements: 9.1_
  - [x] 13.2 Implement per-feed notification controls
    - Add toggle for each feed
    - Include tinkering index threshold slider (1-5)
    - Display current value with star visualization
    - Use full-width sliders on mobile
    - _Requirements: 9.2, 9.3, 9.5, 25.4_
  - [x] 13.3 Add notification settings groups
    - Group by Global, Feed-Specific, Delivery Preferences
    - Include frequency selector and quiet hours time range
    - _Requirements: 9.4_
  - [x] 13.4 Implement notification preview
    - Show preview of notification appearance
    - Update preview when settings change
    - _Requirements: 9.6_
  - [x] 13.5 Add auto-save functionality
    - Save changes automatically with success feedback
    - Show empty state when no feed-specific notifications configured
    - _Requirements: 9.7, 9.8_

- [x] 14. Checkpoint - Verify page layouts
  - Ensure all tests pass, ask the user if questions arise.

### Phase 4: States & Interactions

- [x] 15. Implement loading states with skeleton screens
  - [x] 15.1 Create skeleton components matching content layout
    - Build article card skeleton with shimmer animation
    - Build feed list skeleton
    - Build navigation skeleton
    - Use gradient animation for shimmer effect
    - _Requirements: 12.1, 12.2, 12.6_
  - [x] 15.2 Add loading indicators for async operations
    - Display skeleton on initial page load
    - Show spinner for infinite scroll
    - Add loading state to specific components during updates
    - _Requirements: 12.3, 12.4, 19.3_
  - [x] 15.3 Implement accessible loading announcements
    - Add ARIA live regions for screen readers
    - Announce loading and completion states
    - _Requirements: 12.5_
  - [x] 15.4 Add smooth content transitions
    - Fade in content when loaded (200ms)
    - Respect prefers-reduced-motion preference
    - _Requirements: 12.7, 12.8_

- [x] 16. Create error states with recovery options
  - [x] 16.1 Build error state component
    - Display error icon, descriptive message, and retry button
    - Use destructive color for icon and message
    - Include error code or reference number
    - Add contextual help text with solutions
    - _Requirements: 13.1, 13.4, 13.5, 13.7_
  - [x] 16.2 Implement retry functionality
    - Add retry button that re-attempts operation
    - Show loading state during retry
    - _Requirements: 13.2, 13.3_
  - [x] 16.3 Add inline form error messages
    - Display errors below affected fields
    - Use destructive color and error icon
    - _Requirements: 13.6_
  - [x] 16.4 Add error logging
    - Log errors to console for debugging
    - Display user-friendly messages in UI
    - _Requirements: 13.8_

- [x] 17. Build empty states with CTAs
  - [x] 17.1 Create empty state component
    - Display icon/illustration, message, and CTA button
    - Use muted colors and centered layout
    - Adapt layout for mobile (stacked elements)
    - _Requirements: 14.1, 14.5, 14.8_
  - [x] 17.2 Add context-specific empty states
    - Dashboard: "No articles" → "Subscribe to feeds"
    - Reading list: "No saved articles" → "Browse articles"
    - Subscriptions: "No subscriptions" → "Browse recommended feeds"
    - Search results: "No results found" → "Try different keywords"
    - _Requirements: 14.2, 14.3, 14.4, 18.8, 7.7, 9.8_
  - [x] 17.3 Ensure consistent styling
    - Maintain spacing and typography with other components
    - Include primary action button with clear label
    - _Requirements: 14.6, 14.7_

- [x] 18. Implement toast notification system
  - Install and configure Sonner library
  - Position toasts (bottom-right desktop, bottom-center mobile)
  - Support variants (success, error, warning, info) with distinct colors
  - Implement auto-dismiss (5s success/info, 7s error/warning)
  - Add manual dismiss with close button
  - Stack multiple toasts with 8px spacing (max 3 visible)
  - Include progress bar for auto-dismiss countdown
  - Support action buttons within toasts (Undo, View Details)
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7, 22.8_

- [x] 19. Add hover and interaction states
  - [x] 19.1 Implement article card hover effects
    - Add shadow elevation transition (200ms)
    - Add subtle transform on desktop hover
    - Ensure no layout shift
    - _Requirements: 6.5, 21.4, 2.8_
  - [x] 19.2 Add button and control hover states
    - Implement color/opacity transitions
    - Add cursor-pointer to all interactive elements
    - Provide visual feedback within 100ms
    - _Requirements: 2.2, 2.7, 5.6_
  - [x] 19.3 Implement focus indicators
    - Add 2px visible focus ring with primary color
    - Ensure 3:1 contrast ratio for focus indicators
    - Support keyboard navigation with logical tab order
    - _Requirements: 5.5, 15.2, 15.3_

- [x] 20. Implement animations and transitions
  - [x] 20.1 Add dialog animations
    - Fade-in and scale-up for desktop (200ms)
    - Slide-up for mobile (300ms)
    - Use ease-out for enter, ease-in for exit
    - _Requirements: 21.3, 4.7_
  - [x] 20.2 Add navigation drawer animations
    - Slide-in/out from left (300ms)
    - Fade backdrop in/out
    - _Requirements: 21.2_
  - [x] 20.3 Configure animation preferences
    - Use consistent durations (150ms micro, 300ms standard, 500ms complex)
    - Use CSS transforms for GPU acceleration
    - Avoid animating layout properties
    - Use will-change sparingly
    - Respect prefers-reduced-motion preference
    - _Requirements: 21.1, 21.5, 21.6, 21.7, 21.8, 15.7_

- [x] 21. Checkpoint - Verify states and interactions
  - Ensure all tests pass, ask the user if questions arise.

### Phase 5: Optimization & Polish

- [x] 22. Implement performance optimizations
  - [x] 22.1 Add code splitting and lazy loading
    - Use React.lazy for route components
    - Add Suspense boundaries with loading fallbacks
    - _Requirements: 16.4_
  - [x] 22.2 Optimize images with next/image
    - Configure responsive image sizes for breakpoints
    - Add blur placeholders
    - Implement lazy loading for below-fold images
    - Serve WebP with JPEG fallback
    - Define aspect ratios to prevent layout shifts
    - _Requirements: 20.1, 20.2, 20.3, 20.5, 20.6, 20.7, 16.7_
  - [x] 22.3 Implement virtual scrolling for large lists
    - Use react-window for lists exceeding 50 items
    - Maintain scroll position on updates
    - _Requirements: 16.5_
  - [x] 22.4 Add debouncing for search inputs
    - Implement 300ms debounce for all search inputs
    - Cancel pending requests on new input
    - _Requirements: 16.6_
  - [x] 22.5 Minimize layout shifts
    - Reserve space for dynamic content
    - Use skeleton screens matching content dimensions
    - Target CLS < 0.1
    - _Requirements: 16.8_

- [x] 23. Implement accessibility enhancements
  - [x] 23.1 Add ARIA labels and semantic HTML
    - Add ARIA labels for icon-only buttons
    - Use semantic elements (nav, main, article, section)
    - Add alternative text for images and icons
    - _Requirements: 15.1, 15.5, 15.6_
  - [x] 23.2 Implement keyboard shortcuts
    - Add Cmd/Ctrl + K for search
    - Add Cmd/Ctrl + Shift + T for theme toggle
    - Add Cmd/Ctrl + B for navigation drawer
    - Add J/K for next/previous article, Enter to open
    - Add Cmd/Ctrl + / for shortcuts help dialog
    - Prevent shortcuts when focus is in text input
    - Display hints in tooltips
    - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7_
  - [x] 23.3 Verify WCAG AA compliance
    - Test all text contrast ratios (4.5:1 minimum)
    - Test UI component contrast (3:1 minimum)
    - Verify focus indicator contrast (3:1 minimum)
    - Test with screen reader
    - _Requirements: 15.8, 4.2_

- [x] 24. Add responsive layout refinements
  - [x] 24.1 Verify all breakpoints
    - Test at 375px (mobile)
    - Test at 768px (tablet)
    - Test at 1024px (desktop)
    - Test at 1440px (wide)
    - Ensure no horizontal scrolling at any breakpoint
    - _Requirements: 1.1, 1.2_
  - [x] 24.2 Add smooth layout transitions
    - Implement 300ms transitions between breakpoints
    - Maintain component proportions across breakpoints
    - _Requirements: 1.3, 1.8_
  - [x] 24.3 Verify touch target sizes
    - Ensure all interactive elements are 44x44px minimum
    - Verify 48px minimum height for form controls on mobile
    - Check 12px minimum spacing between touch targets
    - _Requirements: 2.1, 2.3, 2.4_
  - [x] 24.4 Add safe area padding
    - Implement safe area insets for notched devices
    - Apply to dialogs, navigation, and fixed elements
    - _Requirements: 2.5_

- [x] 25. Implement advanced features
  - [x] 25.1 Add PWA support with offline functionality
    - Create manifest.json with app metadata
    - Implement service worker for caching
    - Cache previously loaded articles
    - Display offline indicator when disconnected
    - Show informative message for offline actions
    - Sync pending actions when connection restored
    - Display install prompt after 2 visits
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6, 28.7, 28.8_
  - [x] 25.2 Create print stylesheet
    - Hide navigation, sidebars, and interactive controls
    - Use single-column layout for articles
    - Use black text on white background
    - Expand collapsed sections and truncated content
    - Add page breaks between articles
    - Display full URLs for links
    - Optimize font sizes (12pt body, 16pt headings)
    - Add print button to article detail view
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6, 29.7, 29.8_
  - [x] 25.3 Prepare internationalization infrastructure
    - Set up translation keys for all user-facing text
    - Support RTL layout for RTL languages
    - Format dates/times according to locale
    - Format numbers/currencies according to locale
    - Add language selector to navigation
    - Persist language preference in localStorage
    - Load translations asynchronously
    - Fall back to English for missing translations
    - _Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7, 30.8_

- [x] 26. Final testing and verification
  - [x] 26.1 Performance testing
    - Measure FCP (target: < 1.5s on 3G)
    - Measure LCP (target: < 2.5s on 3G)
    - Measure TTI (target: < 3.5s on 3G)
    - Measure CLS (target: < 0.1)
    - _Requirements: 16.1, 16.2, 16.3, 16.8_
  - [x] 26.2 Cross-browser testing
    - Test on Chrome, Firefox, Safari, Edge
    - Verify WebP fallback works
    - Test PWA installation on supported browsers
    - _Requirements: 20.6, 28.6_
  - [x] 26.3 Responsive testing
    - Test all pages at all breakpoints
    - Verify touch interactions on mobile devices
    - Test safe area padding on notched devices
    - Verify drawer and dialog animations
    - _Requirements: 1.1-1.8, 2.1-2.8, 10.8_
  - [x] 26.4 Accessibility audit
    - Run automated accessibility tests
    - Test keyboard navigation on all pages
    - Test with screen reader (VoiceOver/NVDA)
    - Verify prefers-reduced-motion support
    - Verify color contrast in both themes
    - _Requirements: 15.1-15.8, 21.5_
  - [x] 26.5 User acceptance testing
    - Test all user workflows (browse, search, filter, save, manage)
    - Verify error handling and recovery
    - Test offline functionality
    - Verify theme switching
    - Test notification system
    - _Requirements: All requirements_

- [x] 27. Final checkpoint - Complete redesign verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks reference specific requirements for traceability
- Checkpoints ensure incremental validation at phase boundaries
- Each task builds on previous work for smooth progression
- Focus on mobile-first responsive design throughout
- Maintain WCAG AA accessibility compliance in all components
- Test at all breakpoints (375px, 768px, 1024px, 1440px) continuously
- Respect user preferences (theme, reduced motion, language)
- Optimize for Core Web Vitals (FCP, LCP, TTI, CLS)

## Implementation Strategy

1. **Phase 1** establishes the design foundation - complete this before moving to components
2. **Phase 2** builds reusable components - these are used throughout phases 3-5
3. **Phase 3** assembles components into complete page layouts
4. **Phase 4** adds polish with states, animations, and interactions
5. **Phase 5** optimizes performance and adds advanced features

Each phase includes checkpoints to verify work before proceeding. This ensures quality and prevents rework.
