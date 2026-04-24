# Requirements Document: Frontend UI/UX Redesign

## Introduction

This document defines the requirements for a comprehensive UI/UX redesign of the Tech News Agent web dashboard. The redesign addresses critical usability issues identified through user feedback, focusing on responsive design, mobile optimization, and overall user experience improvements. The system is a technical news aggregation platform built with Next.js 14, React 18, TypeScript, Tailwind CSS, and shadcn/ui components.

**Current Pain Points:**

- Poor usability on smaller screens (responsive design failures)
- Inadequate mobile experience (touch targets, spacing, navigation)
- Inconsistent visual hierarchy and information architecture
- Suboptimal interaction patterns and feedback mechanisms

**Design Goals:**

- Establish a modern, professional design system
- Implement comprehensive responsive design (375px to 1440px+)
- Optimize mobile experience with touch-friendly interfaces
- Improve information architecture and visual hierarchy
- Maintain dark mode support
- Enhance overall usability and interaction experience

## Glossary

- **Dashboard**: The main application interface displaying article lists and feed management
- **Reading_List**: User's personal collection of saved articles with status tracking
- **Subscriptions_Page**: Interface for managing RSS feed subscriptions
- **Notifications_Settings**: Configuration interface for notification preferences
- **Design_System**: Comprehensive set of design tokens, components, and patterns
- **Responsive_Breakpoint**: Screen width threshold triggering layout changes (375px, 768px, 1024px, 1440px)
- **Touch_Target**: Interactive element with minimum 44x44px size for mobile accessibility
- **Visual_Hierarchy**: Organization of UI elements by importance using size, color, spacing
- **Component_Library**: shadcn/ui based reusable UI components
- **Theme_System**: next-themes powered light/dark mode implementation
- **Mobile_Viewport**: Screen width below 768px
- **Tablet_Viewport**: Screen width between 768px and 1024px
- **Desktop_Viewport**: Screen width above 1024px
- **Safe_Area**: Device-specific inset areas (notches, rounded corners) requiring padding
- **Interaction_Feedback**: Visual response to user actions (hover, focus, active states)
- **Loading_State**: UI representation during asynchronous operations
- **Error_State**: UI representation when operations fail
- **Empty_State**: UI representation when no data is available
- **Navigation_Component**: Top-level navigation bar with routing and user controls
- **Article_Card**: Component displaying article preview with metadata
- **Dialog_Component**: Modal overlay for focused interactions
- **Form_Control**: Interactive input element (button, checkbox, slider, select)

## Requirements

### Requirement 1: Responsive Layout System

**User Story:** As a user, I want the application to adapt seamlessly to different screen sizes, so that I can access content comfortably on any device.

#### Acceptance Criteria

1. WHEN the viewport width is 375px or greater, THE Dashboard SHALL display all content without horizontal scrolling
2. WHEN the viewport width is below 768px, THE Navigation_Component SHALL transform into a mobile-optimized layout
3. WHEN the viewport width transitions between breakpoints, THE Design_System SHALL apply smooth layout transitions within 300ms
4. WHILE the viewport width is below 768px, THE Article_Card SHALL stack vertically with full width
5. WHILE the viewport width is between 768px and 1024px, THE Article_Card SHALL display in a two-column grid
6. WHILE the viewport width is above 1024px, THE Article_Card SHALL display in a three-column grid with maximum container width of 1400px
7. THE Design_System SHALL define consistent spacing scales (4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px) across all breakpoints
8. THE Design_System SHALL maintain consistent component proportions across all Responsive_Breakpoint values

### Requirement 2: Mobile Touch Optimization

**User Story:** As a mobile user, I want all interactive elements to be easily tappable, so that I can navigate the application without frustration.

#### Acceptance Criteria

1. THE Design_System SHALL enforce minimum Touch_Target size of 44x44px for all interactive elements
2. WHEN a user taps a Touch_Target on Mobile_Viewport, THE Component_Library SHALL provide visual feedback within 100ms
3. WHILE the viewport width is below 768px, THE Form_Control SHALL have minimum height of 48px
4. WHILE the viewport width is below 768px, THE Navigation_Component SHALL have minimum touch target spacing of 12px between items
5. THE Dialog_Component SHALL include Safe_Area padding on devices with notches or rounded corners
6. WHEN a Dialog_Component is displayed on Mobile_Viewport, THE Design_System SHALL limit content height to 85vh with vertical scrolling
7. THE Component_Library SHALL use `cursor-pointer` class for all clickable elements
8. WHEN a user hovers over an interactive element on Desktop_Viewport, THE Component_Library SHALL display hover state without layout shift

### Requirement 3: Navigation and Information Architecture

**User Story:** As a user, I want clear and consistent navigation, so that I can quickly access different sections of the application.

#### Acceptance Criteria

1. THE Navigation_Component SHALL display primary navigation items (Dashboard, Reading_List, Subscriptions_Page, Notifications_Settings) with consistent visual treatment
2. WHEN the viewport width is below 768px, THE Navigation_Component SHALL transform into a hamburger menu with slide-out drawer
3. WHILE the hamburger menu is open on Mobile_Viewport, THE Navigation_Component SHALL prevent body scrolling
4. THE Navigation_Component SHALL indicate the current active route with distinct visual styling
5. WHEN a user navigates between pages, THE Navigation_Component SHALL persist its state and position
6. THE Navigation_Component SHALL include user profile controls and theme toggle in consistent locations across all breakpoints
7. WHILE the viewport width is below 768px, THE Navigation_Component SHALL use full-width menu items with minimum 56px height
8. THE Design_System SHALL maintain navigation z-index hierarchy to prevent content overlap

### Requirement 4: Visual Design System

**User Story:** As a user, I want a cohesive and professional visual design, so that the application feels polished and trustworthy.

#### Acceptance Criteria

1. THE Design_System SHALL define a comprehensive color palette with semantic naming (primary, secondary, accent, muted, destructive)
2. THE Theme_System SHALL support both light and dark modes with WCAG AA contrast ratios (4.5:1 for text, 3:1 for UI components)
3. THE Design_System SHALL define typography scale with consistent font sizes (12px, 14px, 16px, 18px, 20px, 24px, 30px, 36px, 48px)
4. THE Design_System SHALL use consistent border radius values (2px, 4px, 6px, 8px, 12px, 16px)
5. THE Design_System SHALL define shadow system for elevation (sm, md, lg, xl) with appropriate blur and opacity
6. THE Component_Library SHALL use consistent icon sizing (16px, 20px, 24px, 32px) from Lucide React icon set
7. THE Design_System SHALL define animation timing functions (ease-in-out, ease-out) and durations (150ms, 200ms, 300ms, 500ms)
8. WHEN the Theme_System switches between light and dark modes, THE Design_System SHALL transition colors smoothly within 200ms

### Requirement 5: Component State Management

**User Story:** As a user, I want clear feedback on component states, so that I understand what the application is doing.

#### Acceptance Criteria

1. WHEN an asynchronous operation is in progress, THE Component_Library SHALL display a Loading_State with spinner or skeleton
2. WHEN an operation fails, THE Component_Library SHALL display an Error_State with descriptive message and retry action
3. WHEN no data is available, THE Component_Library SHALL display an Empty_State with illustration and call-to-action
4. THE Form_Control SHALL display distinct visual states for default, hover, focus, active, disabled, and error conditions
5. WHEN a Form_Control receives focus, THE Component_Library SHALL display a visible focus ring with 2px width and primary color
6. WHEN a user interacts with a Form_Control, THE Component_Library SHALL provide Interaction_Feedback within 100ms
7. THE Loading_State SHALL include accessible loading announcements for screen readers
8. THE Error_State SHALL include error icon, message, and actionable recovery options

### Requirement 6: Article Card Redesign

**User Story:** As a user, I want article cards to be readable and actionable on all devices, so that I can quickly scan and interact with content.

#### Acceptance Criteria

1. THE Article_Card SHALL display title, source, category, published date, tinkering index, and summary in consistent hierarchy
2. WHILE the viewport width is below 768px, THE Article_Card SHALL use vertical layout with full-width elements
3. WHILE the viewport width is above 768px, THE Article_Card SHALL use horizontal layout with image thumbnail (if available)
4. THE Article_Card SHALL include action buttons (Read Later, Mark as Read, Share) with minimum Touch_Target size
5. WHEN a user hovers over an Article_Card on Desktop_Viewport, THE Component_Library SHALL elevate the card with shadow transition
6. THE Article_Card SHALL display tinkering index using star icons with color coding (1-2: gray, 3: yellow, 4-5: orange)
7. THE Article_Card SHALL truncate long titles to 2 lines on Mobile_Viewport and 3 lines on Desktop_Viewport
8. THE Article_Card SHALL display category badge with consistent color mapping across the application

### Requirement 7: Reading List Interface

**User Story:** As a user, I want to manage my reading list efficiently, so that I can track and organize articles I want to read.

#### Acceptance Criteria

1. THE Reading_List SHALL display status filter tabs (All, Unread, Reading, Completed) with clear active state indication
2. WHEN a user selects a status filter, THE Reading_List SHALL update the article list within 300ms
3. THE Reading_List SHALL display articles with status indicators, rating controls, and action buttons
4. WHILE the viewport width is below 768px, THE Reading_List SHALL stack article metadata vertically
5. THE Reading_List SHALL include rating control with 1-5 star selection using touch-friendly targets
6. WHEN a user updates article status or rating, THE Reading_List SHALL provide immediate visual feedback and persist changes
7. THE Reading_List SHALL display Empty_State when no articles match the selected filter
8. THE Reading_List SHALL support infinite scroll with Loading_State indicator when fetching more articles

### Requirement 8: Subscriptions Management Interface

**User Story:** As a user, I want to manage my feed subscriptions easily, so that I can customize my content sources.

#### Acceptance Criteria

1. THE Subscriptions_Page SHALL group feeds by category with collapsible sections
2. WHEN a user toggles a category section, THE Subscriptions_Page SHALL animate the expansion/collapse within 300ms
3. THE Subscriptions_Page SHALL display feed health indicators (healthy, stale, error) with color coding
4. THE Subscriptions_Page SHALL include bulk actions (Subscribe All, Unsubscribe All, Subscribe Recommended)
5. WHILE the viewport width is below 768px, THE Subscriptions_Page SHALL stack feed information vertically with full-width controls
6. THE Subscriptions_Page SHALL display feed statistics (total articles, articles this week, average tinkering index)
7. WHEN a user toggles a subscription, THE Subscriptions_Page SHALL update the UI optimistically and show loading state on the specific feed
8. THE Subscriptions_Page SHALL include search functionality to filter feeds by name, category, or tag

### Requirement 9: Notifications Settings Interface

**User Story:** As a user, I want to configure notification preferences, so that I receive relevant updates without being overwhelmed.

#### Acceptance Criteria

1. THE Notifications_Settings SHALL display global notification toggle with clear on/off state
2. THE Notifications_Settings SHALL include per-feed notification controls with minimum tinkering index threshold slider
3. WHEN a user adjusts the tinkering index slider, THE Notifications_Settings SHALL display current value with star visualization
4. THE Notifications_Settings SHALL group notification settings by category (Global, Feed-Specific, Delivery Preferences)
5. WHILE the viewport width is below 768px, THE Notifications_Settings SHALL stack controls vertically with full-width sliders
6. THE Notifications_Settings SHALL include preview of notification appearance for different settings
7. WHEN a user changes notification settings, THE Notifications_Settings SHALL save changes automatically with success feedback
8. THE Notifications_Settings SHALL display Empty_State when no feed-specific notifications are configured

### Requirement 10: Dialog and Modal Components

**User Story:** As a user, I want modal dialogs to be accessible and usable on all devices, so that I can complete focused tasks without confusion.

#### Acceptance Criteria

1. THE Dialog_Component SHALL include close button in consistent position (top-right) with minimum Touch_Target size
2. WHEN a Dialog_Component is displayed, THE Component_Library SHALL trap keyboard focus within the dialog
3. WHEN a user presses Escape key, THE Dialog_Component SHALL close and return focus to the trigger element
4. WHILE the viewport width is below 768px, THE Dialog_Component SHALL use full-screen layout with slide-up animation
5. WHILE the viewport width is above 768px, THE Dialog_Component SHALL use centered overlay with maximum width of 600px
6. THE Dialog_Component SHALL include backdrop overlay with 50% opacity preventing interaction with background content
7. THE Dialog_Component SHALL limit content height to 85vh with vertical scrolling for overflow content
8. THE Dialog_Component SHALL include Safe_Area padding on devices with notches or rounded corners

### Requirement 11: Form Controls and Inputs

**User Story:** As a user, I want form controls to be easy to use and understand, so that I can input data accurately and efficiently.

#### Acceptance Criteria

1. THE Form_Control SHALL display labels with consistent typography and spacing (8px above input)
2. THE Form_Control SHALL include placeholder text with muted color and appropriate contrast ratio
3. WHEN a Form_Control has validation errors, THE Component_Library SHALL display error message below the input with destructive color
4. THE Form_Control SHALL display character count for text inputs with maximum length constraints
5. WHILE the viewport width is below 768px, THE Form_Control SHALL use full-width layout with minimum 48px height
6. THE Form_Control SHALL support keyboard navigation with visible focus indicators
7. THE Form_Control SHALL include helper text below inputs when additional context is needed
8. WHEN a Form_Control is disabled, THE Component_Library SHALL reduce opacity to 50% and show not-allowed cursor

### Requirement 12: Loading and Skeleton States

**User Story:** As a user, I want to see loading indicators that match the content structure, so that I understand what is being loaded.

#### Acceptance Criteria

1. THE Loading_State SHALL use skeleton screens that match the layout of loaded content
2. THE Loading_State SHALL animate with shimmer effect using gradient animation
3. WHEN initial page load occurs, THE Dashboard SHALL display skeleton Article_Card components matching the expected grid layout
4. WHEN infinite scroll loads more content, THE Dashboard SHALL display loading spinner at the bottom of the list
5. THE Loading_State SHALL include accessible loading announcements for screen readers
6. THE Loading_State SHALL maintain consistent spacing and dimensions with actual content
7. WHEN a component transitions from Loading_State to loaded content, THE Component_Library SHALL fade in content within 200ms
8. THE Loading_State SHALL respect user's prefers-reduced-motion preference by disabling animations

### Requirement 13: Error Handling and Recovery

**User Story:** As a user, I want clear error messages and recovery options, so that I can resolve issues and continue using the application.

#### Acceptance Criteria

1. THE Error_State SHALL display error icon, descriptive message, and actionable recovery button
2. WHEN a network request fails, THE Component_Library SHALL display Error_State with "Retry" button
3. WHEN a user clicks the retry button, THE Component_Library SHALL attempt the operation again and show Loading_State
4. THE Error_State SHALL include error code or reference number for support purposes
5. THE Error_State SHALL use destructive color for error icon and message
6. WHEN an error occurs during form submission, THE Form_Control SHALL display inline error messages below affected fields
7. THE Error_State SHALL include contextual help text suggesting possible solutions
8. THE Error_State SHALL log errors to console for debugging while displaying user-friendly messages

### Requirement 14: Empty States

**User Story:** As a user, I want helpful empty states, so that I understand why content is missing and what actions I can take.

#### Acceptance Criteria

1. THE Empty_State SHALL display illustration or icon, descriptive message, and call-to-action button
2. WHEN the Dashboard has no articles, THE Empty_State SHALL suggest subscribing to feeds or triggering manual fetch
3. WHEN the Reading_List is empty, THE Empty_State SHALL suggest browsing articles and adding items
4. WHEN the Subscriptions_Page has no subscriptions, THE Empty_State SHALL highlight recommended feeds
5. THE Empty_State SHALL use muted colors and centered layout
6. THE Empty_State SHALL include primary action button with clear label (e.g., "Browse Articles", "Add Subscription")
7. THE Empty_State SHALL maintain consistent spacing and typography with other components
8. THE Empty_State SHALL adapt layout for Mobile_Viewport with stacked elements

### Requirement 15: Accessibility Compliance

**User Story:** As a user with disabilities, I want the application to be accessible, so that I can use all features effectively.

#### Acceptance Criteria

1. THE Component_Library SHALL include ARIA labels for all interactive elements without visible text
2. THE Component_Library SHALL support keyboard navigation with logical tab order
3. THE Component_Library SHALL display visible focus indicators with minimum 2px width and 3:1 contrast ratio
4. THE Component_Library SHALL include skip-to-content link for keyboard users
5. THE Component_Library SHALL use semantic HTML elements (nav, main, article, section, button)
6. THE Component_Library SHALL provide alternative text for all images and icons
7. THE Component_Library SHALL respect user's prefers-reduced-motion preference by disabling non-essential animations
8. THE Component_Library SHALL maintain WCAG AA contrast ratios for all text and UI components

### Requirement 16: Performance Optimization

**User Story:** As a user, I want the application to load quickly and respond smoothly, so that I can work efficiently.

#### Acceptance Criteria

1. THE Dashboard SHALL achieve First Contentful Paint (FCP) within 1.5 seconds on 3G connection
2. THE Dashboard SHALL achieve Largest Contentful Paint (LCP) within 2.5 seconds on 3G connection
3. THE Dashboard SHALL achieve Time to Interactive (TTI) within 3.5 seconds on 3G connection
4. THE Component_Library SHALL use React.lazy for code splitting of route components
5. THE Component_Library SHALL implement virtual scrolling for lists exceeding 50 items
6. THE Component_Library SHALL debounce search inputs with 300ms delay
7. THE Component_Library SHALL optimize images with next/image component and appropriate sizing
8. THE Component_Library SHALL minimize layout shifts with reserved space for dynamic content (CLS < 0.1)

### Requirement 17: Theme System Implementation

**User Story:** As a user, I want to switch between light and dark themes, so that I can use the application comfortably in different lighting conditions.

#### Acceptance Criteria

1. THE Theme_System SHALL provide theme toggle control in Navigation_Component
2. WHEN a user toggles the theme, THE Theme_System SHALL persist the preference in localStorage
3. THE Theme_System SHALL apply theme preference on initial page load without flash of unstyled content
4. THE Theme_System SHALL define color tokens for both light and dark modes with semantic naming
5. THE Theme_System SHALL maintain WCAG AA contrast ratios in both light and dark modes
6. THE Theme_System SHALL transition colors smoothly within 200ms when switching themes
7. THE Theme_System SHALL respect user's prefers-color-scheme system preference as default
8. THE Theme_System SHALL update meta theme-color tag to match current theme

### Requirement 18: Search and Filter Functionality

**User Story:** As a user, I want to search and filter content, so that I can quickly find relevant articles and feeds.

#### Acceptance Criteria

1. THE Dashboard SHALL include search input with real-time filtering of articles by title, summary, or category
2. WHEN a user types in the search input, THE Dashboard SHALL debounce input with 300ms delay before filtering
3. THE Dashboard SHALL display search result count and clear search button when search is active
4. THE Subscriptions_Page SHALL include search functionality to filter feeds by name, category, or tag
5. THE Dashboard SHALL include category filter with multi-select badges
6. WHEN a user selects category filters, THE Dashboard SHALL update the article list within 300ms
7. THE Dashboard SHALL persist search and filter state in URL query parameters for shareable links
8. THE Dashboard SHALL display Empty_State when search or filter returns no results

### Requirement 19: Infinite Scroll Implementation

**User Story:** As a user, I want to load more content automatically as I scroll, so that I can browse articles continuously without clicking pagination buttons.

#### Acceptance Criteria

1. THE Dashboard SHALL implement infinite scroll with intersection observer detecting bottom of list
2. WHEN a user scrolls within 200px of the bottom, THE Dashboard SHALL load the next page of articles
3. THE Dashboard SHALL display loading spinner at the bottom of the list while fetching more articles
4. THE Dashboard SHALL prevent multiple simultaneous fetch requests during infinite scroll
5. WHEN all articles are loaded, THE Dashboard SHALL display "No more articles" message
6. THE Dashboard SHALL maintain scroll position when navigating back from article detail page
7. THE Dashboard SHALL load 20 articles per page for optimal performance
8. THE Dashboard SHALL handle scroll restoration on browser back/forward navigation

### Requirement 20: Responsive Images and Media

**User Story:** As a user, I want images to load efficiently and display correctly on all devices, so that I can view content without performance issues.

#### Acceptance Criteria

1. THE Article_Card SHALL use next/image component for automatic image optimization
2. THE Article_Card SHALL define responsive image sizes for different breakpoints (375px, 768px, 1024px, 1440px)
3. THE Article_Card SHALL display placeholder with blur effect while images are loading
4. THE Article_Card SHALL handle missing images with fallback illustration or icon
5. THE Article_Card SHALL lazy load images below the fold using intersection observer
6. THE Article_Card SHALL serve WebP format with JPEG fallback for browser compatibility
7. THE Article_Card SHALL limit image dimensions to prevent layout shifts (aspect ratio 16:9 or 4:3)
8. THE Article_Card SHALL include alt text for all images for accessibility and SEO

### Requirement 21: Animation and Transitions

**User Story:** As a user, I want smooth animations and transitions, so that the interface feels polished and responsive.

#### Acceptance Criteria

1. THE Component_Library SHALL use consistent animation durations (150ms for micro-interactions, 300ms for transitions, 500ms for complex animations)
2. THE Component_Library SHALL use ease-out timing function for enter animations and ease-in for exit animations
3. WHEN a Dialog_Component opens, THE Component_Library SHALL animate with fade-in and scale-up effect within 200ms
4. WHEN a user hovers over an Article_Card, THE Component_Library SHALL transition shadow and transform within 200ms
5. THE Component_Library SHALL respect user's prefers-reduced-motion preference by disabling non-essential animations
6. THE Component_Library SHALL use CSS transforms for animations to leverage GPU acceleration
7. THE Component_Library SHALL avoid animating layout properties (width, height, margin, padding) to prevent reflows
8. THE Component_Library SHALL use will-change property sparingly for performance-critical animations

### Requirement 22: Notification Toast System

**User Story:** As a user, I want non-intrusive notifications for actions and events, so that I receive feedback without disrupting my workflow.

#### Acceptance Criteria

1. THE Component_Library SHALL display toast notifications using Sonner library with consistent positioning (bottom-right on desktop, bottom-center on mobile)
2. THE Component_Library SHALL support toast variants (success, error, warning, info) with distinct colors and icons
3. WHEN a toast notification appears, THE Component_Library SHALL auto-dismiss after 5 seconds for success/info and 7 seconds for error/warning
4. THE Component_Library SHALL allow users to manually dismiss toasts with close button
5. THE Component_Library SHALL stack multiple toasts vertically with 8px spacing
6. THE Component_Library SHALL limit maximum visible toasts to 3, queuing additional toasts
7. THE Component_Library SHALL include progress bar indicating time until auto-dismiss
8. THE Component_Library SHALL support action buttons within toasts for contextual actions (e.g., "Undo", "View Details")

### Requirement 23: Mobile Navigation Drawer

**User Story:** As a mobile user, I want easy access to navigation, so that I can move between sections efficiently on small screens.

#### Acceptance Criteria

1. WHILE the viewport width is below 768px, THE Navigation_Component SHALL display hamburger menu icon in top-left corner
2. WHEN a user taps the hamburger icon, THE Navigation_Component SHALL slide in drawer from left edge within 300ms
3. WHILE the drawer is open, THE Navigation_Component SHALL display backdrop overlay preventing interaction with main content
4. WHEN a user taps the backdrop or close button, THE Navigation_Component SHALL slide out drawer within 300ms
5. THE Navigation_Component SHALL prevent body scrolling while drawer is open
6. THE Navigation_Component SHALL display navigation items with full-width touch targets (minimum 56px height)
7. THE Navigation_Component SHALL include user profile section at top of drawer with avatar and username
8. THE Navigation_Component SHALL highlight current active route in drawer navigation

### Requirement 24: Category Badge System

**User Story:** As a user, I want consistent category visualization, so that I can quickly identify article topics.

#### Acceptance Criteria

1. THE Design_System SHALL define color mapping for common categories (Tech News: blue, AI/ML: purple, Web Dev: green, DevOps: orange, Security: red)
2. THE Article_Card SHALL display category badge with consistent styling (rounded corners, padding, font size)
3. THE Dashboard SHALL use category badges in filter controls with same color mapping
4. THE Subscriptions_Page SHALL display category badges for feed grouping with same color mapping
5. THE Design_System SHALL ensure category badge colors maintain WCAG AA contrast ratios in both light and dark modes
6. THE Design_System SHALL support custom category colors defined by users
7. THE Design_System SHALL fall back to neutral color for uncategorized or unknown categories
8. THE Design_System SHALL use consistent badge sizing (small: 20px height, medium: 24px height, large: 28px height)

### Requirement 25: Tinkering Index Visualization

**User Story:** As a user, I want clear visualization of article technical depth, so that I can prioritize content based on complexity.

#### Acceptance Criteria

1. THE Article_Card SHALL display tinkering index using 1-5 star icons with color coding
2. THE Design_System SHALL use gray color for 1-2 stars (beginner), yellow for 3 stars (intermediate), orange for 4-5 stars (advanced)
3. THE Article_Card SHALL display filled stars for the rating value and outlined stars for remaining positions
4. THE Notifications_Settings SHALL use slider control for minimum tinkering index threshold with star visualization
5. THE Subscriptions_Page SHALL display average tinkering index for each feed with star visualization
6. THE Design_System SHALL ensure star icons are touch-friendly (minimum 24px size) on Mobile_Viewport
7. THE Design_System SHALL include tooltip on hover showing numeric value and description (e.g., "3 - Intermediate")
8. THE Design_System SHALL use consistent star icon sizing (16px for compact views, 20px for standard views, 24px for emphasized views)

### Requirement 26: Feed Health Indicators

**User Story:** As a user, I want to see feed health status, so that I can identify and troubleshoot problematic subscriptions.

#### Acceptance Criteria

1. THE Subscriptions_Page SHALL display health indicator for each feed with color coding (green: healthy, yellow: stale, red: error, gray: unknown)
2. THE Subscriptions_Page SHALL show last update timestamp relative to current time (e.g., "2 hours ago", "3 days ago")
3. WHEN a feed has error status, THE Subscriptions_Page SHALL display error message in tooltip on hover
4. THE Subscriptions_Page SHALL include refresh button for manual feed update with loading state
5. THE Subscriptions_Page SHALL display health indicator icon (check circle, alert triangle, x circle) with consistent sizing
6. THE Subscriptions_Page SHALL sort feeds by health status (healthy first, errors last) within each category
7. THE Subscriptions_Page SHALL include bulk action to retry all failed feeds
8. THE Subscriptions_Page SHALL display health statistics summary (X healthy, Y stale, Z errors) at top of page

### Requirement 27: Keyboard Shortcuts

**User Story:** As a power user, I want keyboard shortcuts, so that I can navigate and perform actions efficiently.

#### Acceptance Criteria

1. THE Component_Library SHALL support keyboard shortcut for opening search (Cmd/Ctrl + K)
2. THE Component_Library SHALL support keyboard shortcut for toggling theme (Cmd/Ctrl + Shift + T)
3. THE Component_Library SHALL support keyboard shortcut for opening navigation drawer on mobile (Cmd/Ctrl + B)
4. THE Dashboard SHALL support keyboard shortcuts for navigation (J/K for next/previous article, Enter to open)
5. THE Component_Library SHALL display keyboard shortcuts help dialog (Cmd/Ctrl + /)
6. THE Component_Library SHALL prevent keyboard shortcuts from triggering when focus is in text input
7. THE Component_Library SHALL display keyboard shortcut hints in tooltips for applicable actions
8. THE Component_Library SHALL allow users to customize keyboard shortcuts in settings

### Requirement 28: Offline Support and PWA

**User Story:** As a user, I want basic offline functionality, so that I can access previously loaded content without internet connection.

#### Acceptance Criteria

1. THE Dashboard SHALL cache previously loaded articles for offline viewing
2. WHEN the user is offline, THE Dashboard SHALL display offline indicator in Navigation_Component
3. WHEN the user attempts to load new content while offline, THE Dashboard SHALL display informative message with cached content
4. THE Dashboard SHALL implement service worker for caching static assets (CSS, JS, images)
5. THE Dashboard SHALL support installation as Progressive Web App (PWA) with manifest.json
6. THE Dashboard SHALL display install prompt on supported browsers after 2 visits
7. THE Dashboard SHALL sync pending actions (ratings, status updates) when connection is restored
8. THE Dashboard SHALL display sync status indicator when syncing offline changes

### Requirement 29: Print Stylesheet

**User Story:** As a user, I want to print articles cleanly, so that I can read content offline or share physical copies.

#### Acceptance Criteria

1. THE Component_Library SHALL include print stylesheet hiding navigation, sidebars, and interactive controls
2. THE Article_Card SHALL display in single-column layout when printed
3. THE Component_Library SHALL use black text on white background for print regardless of theme
4. THE Component_Library SHALL expand collapsed sections and truncated content when printing
5. THE Component_Library SHALL include page breaks between articles to prevent awkward splits
6. THE Component_Library SHALL display full URLs for links in print view
7. THE Component_Library SHALL optimize font sizes for print (12pt body text, 16pt headings)
8. THE Component_Library SHALL include print button in article detail view

### Requirement 30: Internationalization Preparation

**User Story:** As a user, I want the interface to support my language, so that I can use the application in my preferred language.

#### Acceptance Criteria

1. THE Component_Library SHALL use translation keys for all user-facing text strings
2. THE Component_Library SHALL support right-to-left (RTL) layout for RTL languages
3. THE Component_Library SHALL format dates and times according to user's locale
4. THE Component_Library SHALL format numbers and currencies according to user's locale
5. THE Component_Library SHALL include language selector in Navigation_Component
6. THE Component_Library SHALL persist language preference in localStorage
7. THE Component_Library SHALL load translations asynchronously to reduce initial bundle size
8. THE Component_Library SHALL fall back to English for missing translations
