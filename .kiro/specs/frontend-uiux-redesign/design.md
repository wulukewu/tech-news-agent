# Design Document: Frontend UI/UX Redesign

## Overview

This document provides the technical design for the comprehensive UI/UX redesign of the Tech News Agent web dashboard. It translates the 26 requirements into actionable design specifications, component architecture, and implementation guidelines.

**Design Approach:** Requirements-First Workflow
**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui
**Target Breakpoints:** 375px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide)

---

## Part 1: High-Level Design

### 1.1 Design System Architecture

#### Color System

**Semantic Color Tokens:**

```
Primary: #1E293B (dark slate) - Main actions, focus states
Secondary: #334155 (slate) - Secondary actions, backgrounds
Accent: #22C55E (green) - CTAs, success states
Destructive: #EF4444 (red) - Errors, warnings
Muted: #94A3B8 (slate-400) - Disabled, secondary text
Background: #0F172A (dark navy) - Page background
Foreground: #F8FAFC (off-white) - Text on dark backgrounds
```

**Dark Mode Support:**

- All colors use CSS variables for seamless theme switching
- Maintain WCAG AA contrast ratios (4.5:1 for text, 3:1 for UI)
- Smooth 200ms transitions when switching themes

**Category Color Mapping:**

- Tech News: `#3B82F6` (blue)
- AI/ML: `#A855F7` (purple)
- Web Dev: `#10B981` (green)
- DevOps: `#F97316` (orange)
- Security: `#EF4444` (red)

#### Typography System

**Font Stack:**

- Headings: Space Grotesk (600, 700 weights)
- Body: DM Sans (400, 500, 700 weights)

**Scale:**

```
xs: 12px (captions, badges)
sm: 14px (labels, helper text)
base: 16px (body text)
lg: 18px (subheadings)
xl: 20px (section titles)
2xl: 24px (page titles)
3xl: 30px (hero titles)
4xl: 36px (large headings)
5xl: 48px (display)
```

#### Spacing System

**Consistent 4px-based scale:**

```
xs: 4px
sm: 8px
md: 12px
lg: 16px
xl: 24px
2xl: 32px
3xl: 48px
4xl: 64px
```

#### Border Radius

```
sm: 2px (subtle)
md: 4px (inputs, small components)
lg: 6px (cards, buttons)
xl: 8px (modals, large components)
2xl: 12px (rounded cards)
3xl: 16px (very rounded)
```

#### Shadow System

```
sm: 0 1px 2px rgba(0,0,0,0.05)
md: 0 4px 6px rgba(0,0,0,0.1)
lg: 0 10px 15px rgba(0,0,0,0.1)
xl: 0 20px 25px rgba(0,0,0,0.1)
```

#### Animation System

**Timing:**

- Micro-interactions: 150ms
- Standard transitions: 200-300ms
- Complex animations: 500ms

**Easing Functions:**

- Enter: `ease-out` (cubic-bezier(0.4, 0, 0.2, 1))
- Exit: `ease-in` (cubic-bezier(0.4, 0, 1, 1))
- Hover: `ease-in-out` (cubic-bezier(0.4, 0, 0.2, 1))

### 1.2 Responsive Layout Architecture

#### Breakpoint Strategy

| Breakpoint | Width  | Device  | Grid  | Sidebar |
| ---------- | ------ | ------- | ----- | ------- |
| Mobile     | 375px  | Phone   | 1 col | Hidden  |
| Tablet     | 768px  | Tablet  | 2 col | Drawer  |
| Desktop    | 1024px | Desktop | 3 col | Sidebar |
| Wide       | 1440px | Large   | 3 col | Sidebar |

#### Container Widths

```
Mobile (< 768px): Full width - 16px padding
Tablet (768px-1024px): 100% - 24px padding
Desktop (1024px+): max-w-7xl (1280px) - 32px padding
```

#### Grid System

**Mobile (< 768px):**

- Single column layout
- Full-width cards
- Stacked navigation

**Tablet (768px-1024px):**

- 2-column grid for articles
- Drawer navigation
- Optimized spacing

**Desktop (1024px+):**

- 3-column grid for articles
- Sidebar navigation
- Maximum container width 1400px

### 1.3 Component Architecture

#### Core Components

**Navigation Component:**

- Desktop: Fixed sidebar (64px collapsed, 256px expanded)
- Tablet/Mobile: Hamburger menu with slide-out drawer
- Active route indication with left border highlight
- User profile section with avatar and theme toggle

**Article Card Component:**

- Mobile: Vertical layout (image, title, metadata, actions)
- Desktop: Horizontal layout (image left, content right)
- Responsive image sizing with next/image
- Tinkering index stars with color coding
- Category badge with semantic colors
- Action buttons: Read Later, Mark as Read, Share

**Dialog Component:**

- Mobile: Full-screen with slide-up animation
- Desktop: Centered overlay (max-width: 600px)
- Backdrop overlay with 50% opacity
- Close button in top-right corner
- Safe area padding for notched devices

**Form Controls:**

- Minimum 48px height on mobile
- Full-width on mobile, auto-width on desktop
- Visible focus indicators (2px ring)
- Error states with destructive color
- Helper text and character count support

**Loading States:**

- Skeleton screens matching content layout
- Shimmer animation with gradient
- Accessible loading announcements
- Respects prefers-reduced-motion

**Empty States:**

- Centered layout with icon/illustration
- Descriptive message
- Primary action button
- Muted colors

### 1.4 Page Layout Specifications

#### Dashboard Page

**Layout Structure:**

```
┌─────────────────────────────────────┐
│ Navigation (fixed/drawer)           │
├─────────────────────────────────────┤
│ Search Bar | Category Filters       │
├─────────────────────────────────────┤
│                                     │
│  Article Card Grid (1/2/3 cols)    │
│                                     │
│  [Load More / Infinite Scroll]      │
└─────────────────────────────────────┘
```

**Mobile Adjustments:**

- Search bar full-width
- Category filters as horizontal scroll
- Single column article grid
- Bottom navigation for quick access

#### Reading List Page

**Layout Structure:**

```
┌─────────────────────────────────────┐
│ Status Filter Tabs                  │
│ (All | Unread | Reading | Done)     │
├─────────────────────────────────────┤
│                                     │
│  Article List with Status/Rating    │
│                                     │
│  [Infinite Scroll]                  │
└─────────────────────────────────────┘
```

**Mobile Adjustments:**

- Tabs scroll horizontally
- Metadata stacked vertically
- Rating control full-width

#### Subscriptions Page

**Layout Structure:**

```
┌─────────────────────────────────────┐
│ Search | Bulk Actions               │
├─────────────────────────────────────┤
│ Category 1 (Collapsible)            │
│  ├─ Feed 1 [Health] [Stats]         │
│  ├─ Feed 2 [Health] [Stats]         │
│ Category 2 (Collapsible)            │
│  ├─ Feed 3 [Health] [Stats]         │
└─────────────────────────────────────┘
```

**Mobile Adjustments:**

- Full-width feed items
- Health indicator prominent
- Collapsible categories

#### Notifications Settings Page

**Layout Structure:**

```
┌─────────────────────────────────────┐
│ Global Notification Toggle          │
├─────────────────────────────────────┤
│ Per-Feed Settings                   │
│  ├─ Feed 1 [Toggle] [Slider]        │
│  ├─ Feed 2 [Toggle] [Slider]        │
│ Delivery Preferences                │
│  ├─ Frequency [Select]              │
│  ├─ Quiet Hours [Time Range]        │
└─────────────────────────────────────┘
```

**Mobile Adjustments:**

- Full-width sliders
- Stacked controls
- Larger touch targets

---

## Part 2: Low-Level Design

### 2.1 Component Implementation Details

#### Navigation Component

**Desktop Sidebar:**

```tsx
// Structure
<aside className="fixed left-0 top-0 h-screen w-64 bg-card border-r">
  <div className="p-4">
    {/* Logo */}
  </div>
  <nav className="space-y-2 p-4">
    {/* Nav items with active state */}
  </nav>
  <div className="absolute bottom-4 left-4 right-4">
    {/* User profile + theme toggle */}
  </div>
</aside>

// Active state indicator
<a className="relative pl-4 before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-primary">
  Dashboard
</a>
```

**Mobile Drawer:**

```tsx
// Hamburger trigger
<button className="lg:hidden touch-target cursor-pointer">
  <Menu className="h-6 w-6" />
</button>

// Drawer with backdrop
<div className="fixed inset-0 z-40 lg:hidden">
  <div className="absolute inset-0 bg-black/50" onClick={close} />
  <nav className="absolute left-0 top-0 bottom-0 w-64 bg-card animate-slide-in-from-left">
    {/* Nav items */}
  </nav>
</div>
```

#### Article Card Component

**Mobile Layout:**

```tsx
<article className="flex flex-col gap-3 rounded-lg border p-4 hover:shadow-md transition-shadow">
  {/* Image */}
  <Image
    src={image}
    alt={title}
    width={400}
    height={225}
    className="w-full h-auto rounded-md object-cover"
  />

  {/* Title */}
  <h3 className="line-clamp-2 text-lg font-semibold">{title}</h3>

  {/* Metadata */}
  <div className="flex items-center gap-2 text-sm text-muted-foreground">
    <span>{source}</span>
    <Badge variant="secondary">{category}</Badge>
    <span>{formatDate(publishedAt)}</span>
  </div>

  {/* Tinkering Index */}
  <div className="flex items-center gap-1">
    {Array.from({ length: 5 }).map((_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${
          i < tinkeringIndex ? 'fill-yellow-400 text-yellow-400' : 'text-muted-foreground'
        }`}
      />
    ))}
  </div>

  {/* Summary */}
  <p className="line-clamp-2 text-sm text-muted-foreground">{summary}</p>

  {/* Actions */}
  <div className="flex gap-2">
    <Button size="sm" variant="outline" className="flex-1 touch-target">
      Read Later
    </Button>
    <Button size="sm" variant="outline" className="flex-1 touch-target">
      Mark as Read
    </Button>
  </div>
</article>
```

**Desktop Layout:**

```tsx
<article className="flex gap-4 rounded-lg border p-4 hover:shadow-lg hover:-translate-y-1 transition-all">
  {/* Image - Left */}
  <Image
    src={image}
    alt={title}
    width={200}
    height={150}
    className="h-32 w-48 flex-shrink-0 rounded-md object-cover"
  />

  {/* Content - Right */}
  <div className="flex flex-1 flex-col gap-2">
    <div className="flex items-start justify-between gap-2">
      <h3 className="line-clamp-3 text-lg font-semibold flex-1">{title}</h3>
      <Button size="icon" variant="ghost" className="touch-target">
        <Share2 className="h-4 w-4" />
      </Button>
    </div>

    {/* Metadata row */}
    <div className="flex items-center gap-3 text-sm text-muted-foreground">
      <span>{source}</span>
      <Badge>{category}</Badge>
      <span>{formatDate(publishedAt)}</span>
    </div>

    {/* Tinkering Index */}
    <div className="flex items-center gap-1">{/* Stars */}</div>

    {/* Summary */}
    <p className="line-clamp-2 flex-1 text-sm">{summary}</p>

    {/* Actions */}
    <div className="flex gap-2">
      <Button size="sm" variant="outline" className="touch-target">
        Read Later
      </Button>
      <Button size="sm" variant="outline" className="touch-target">
        Mark as Read
      </Button>
    </div>
  </div>
</article>
```

#### Dialog Component

```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
    {/* Mobile: full-screen with slide-up animation */}
    {/* Desktop: centered with fade-in animation */}

    <DialogHeader>
      <DialogTitle>{title}</DialogTitle>
      <DialogDescription>{description}</DialogDescription>
    </DialogHeader>

    {/* Content */}
    <div className="space-y-4">{/* Form or content */}</div>

    <DialogFooter>
      <Button variant="outline" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button onClick={handleSubmit}>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

#### Loading State (Skeleton)

```tsx
<div className="space-y-4">
  {Array.from({ length: 3 }).map((_, i) => (
    <div key={i} className="flex gap-4 rounded-lg border p-4">
      {/* Image skeleton */}
      <div className="h-32 w-48 flex-shrink-0 rounded-md bg-muted animate-pulse" />

      {/* Content skeleton */}
      <div className="flex-1 space-y-2">
        <div className="h-6 w-3/4 rounded bg-muted animate-pulse" />
        <div className="h-4 w-full rounded bg-muted animate-pulse" />
        <div className="h-4 w-1/2 rounded bg-muted animate-pulse" />
      </div>
    </div>
  ))}
</div>
```

#### Empty State

```tsx
<div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
  <Rss className="h-12 w-12 text-muted-foreground" />
  <div>
    <h3 className="text-lg font-semibold">No articles found</h3>
    <p className="text-sm text-muted-foreground">Subscribe to feeds to get started</p>
  </div>
  <Button>Browse Feeds</Button>
</div>
```

### 2.2 Responsive Utilities

**Tailwind Configuration Additions:**

```javascript
// tailwind.config.ts
extend: {
  screens: {
    xs: '375px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  spacing: {
    '44': '44px', // Touch target
    '56': '56px', // Mobile nav item
  },
  minHeight: {
    '44': '44px',
    '48': '48px',
    '56': '56px',
  },
  minWidth: {
    '44': '44px',
    '48': '48px',
    '56': '56px',
  },
}
```

### 2.3 Accessibility Implementation

**Focus Management:**

```tsx
// Visible focus indicator
<button className="focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
  Click me
</button>

// Skip to content link
<a href="#main-content" className="sr-only focus:not-sr-only">
  Skip to main content
</a>
```

**ARIA Labels:**

```tsx
// Icon-only buttons
<button aria-label="Close dialog" className="touch-target">
  <X className="h-4 w-4" />
</button>

// Loading state
<div role="status" aria-live="polite" aria-label="Loading articles">
  <LoadingSpinner />
</div>
```

**Semantic HTML:**

```tsx
<nav>
  {/* Navigation items */}
</nav>

<main id="main-content">
  {/* Page content */}
</main>

<article>
  {/* Article content */}
</article>
```

### 2.4 Performance Optimizations

**Code Splitting:**

```tsx
// Route-based code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ReadingList = lazy(() => import('./pages/ReadingList'));

<Suspense fallback={<LoadingSkeleton />}>
  <Dashboard />
</Suspense>;
```

**Image Optimization:**

```tsx
<Image
  src={imageUrl}
  alt={title}
  width={400}
  height={225}
  priority={isAboveFold}
  placeholder="blur"
  blurDataURL={blurHash}
  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
/>
```

**Virtual Scrolling:**

```tsx
import { FixedSizeList } from 'react-window';

<FixedSizeList height={600} itemCount={articles.length} itemSize={200} width="100%">
  {({ index, style }) => (
    <div style={style}>
      <ArticleCard article={articles[index]} />
    </div>
  )}
</FixedSizeList>;
```

**Debounced Search:**

```tsx
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useMemo(
  () =>
    debounce((term: string) => {
      // Perform search
    }, 300),
  []
);

const handleSearch = (term: string) => {
  setSearchTerm(term);
  debouncedSearch(term);
};
```

---

## Part 3: Design Decisions & Rationale

### 3.1 Key Design Decisions

**1. Responsive Breakpoints (375px, 768px, 1024px, 1440px)**

- **Rationale:** Covers 99% of device sizes (mobile, tablet, desktop, wide)
- **Implementation:** Tailwind's responsive prefixes (sm:, md:, lg:, xl:)

**2. Sidebar Navigation (Desktop) + Drawer (Mobile)**

- **Rationale:** Maximizes content space on mobile while maintaining quick access on desktop
- **Implementation:** Hidden sidebar on mobile, hamburger menu triggers drawer

**3. 3-Column Grid for Articles (Desktop)**

- **Rationale:** Optimal for scanning multiple articles without excessive scrolling
- **Implementation:** Responsive grid with gap-4 spacing

**4. Minimum 44x44px Touch Targets**

- **Rationale:** WCAG 2.1 Level AAA compliance, reduces mis-taps on mobile
- **Implementation:** Tailwind utility classes and custom touch-target class

**5. Skeleton Loading States**

- **Rationale:** Improves perceived performance and reduces layout shift
- **Implementation:** Shimmer animation with gradient, matches content layout

### 3.2 Accessibility Considerations

- **WCAG AA Compliance:** All text has 4.5:1 contrast ratio
- **Keyboard Navigation:** Logical tab order, visible focus indicators
- **Screen Reader Support:** ARIA labels, semantic HTML, live regions
- **Motion Preferences:** Respects prefers-reduced-motion, disables animations

### 3.3 Performance Targets

- **FCP:** < 1.5s on 3G
- **LCP:** < 2.5s on 3G
- **TTI:** < 3.5s on 3G
- **CLS:** < 0.1 (no layout shifts)

---

## Part 4: Implementation Roadmap

### Phase 1: Design System Foundation

- [ ] Update Tailwind configuration with design tokens
- [ ] Create CSS variables for colors, spacing, typography
- [ ] Implement theme switching with next-themes

### Phase 2: Core Components

- [ ] Navigation component (desktop + mobile)
- [ ] Article card (mobile + desktop layouts)
- [ ] Dialog/Modal component
- [ ] Form controls with validation

### Phase 3: Page Layouts

- [ ] Dashboard with responsive grid
- [ ] Reading list with status filters
- [ ] Subscriptions with collapsible categories
- [ ] Notifications settings

### Phase 4: States & Interactions

- [ ] Loading states (skeleton screens)
- [ ] Error states with retry
- [ ] Empty states with CTAs
- [ ] Toast notifications

### Phase 5: Optimization & Polish

- [ ] Image optimization with next/image
- [ ] Code splitting and lazy loading
- [ ] Virtual scrolling for large lists
- [ ] Accessibility audit and fixes

---

## Part 5: Testing Strategy

### Unit Tests

- Component rendering with different props
- State management and event handlers
- Responsive behavior at different breakpoints

### Integration Tests

- Navigation between pages
- Form submission and validation
- Loading and error states

### E2E Tests

- User workflows (browse, read, save articles)
- Mobile and desktop interactions
- Theme switching

### Accessibility Tests

- Keyboard navigation
- Screen reader compatibility
- Color contrast verification

### Performance Tests

- Core Web Vitals measurement
- Bundle size analysis
- Image optimization verification

---

## Conclusion

This design document provides a comprehensive blueprint for implementing the UI/UX redesign. It balances modern design principles with practical implementation considerations, ensuring the final product is both beautiful and performant across all devices.
