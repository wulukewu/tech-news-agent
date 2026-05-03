# Design Tokens Reference

This document provides a comprehensive reference for all design tokens configured in the Tailwind theme system for the Tech News Agent UI/UX redesign.

## Breakpoints (Responsive Design)

Custom breakpoints for responsive layouts:

| Token | Value  | Device Type   | Usage                   |
| ----- | ------ | ------------- | ----------------------- |
| `xs`  | 375px  | Mobile        | Minimum mobile viewport |
| `sm`  | 640px  | Small devices | Small tablets           |
| `md`  | 768px  | Tablet        | Tablet portrait         |
| `lg`  | 1024px | Desktop       | Desktop/laptop          |
| `xl`  | 1440px | Wide desktop  | Large screens           |
| `2xl` | 1536px | Extra wide    | Ultra-wide displays     |

**Requirements Coverage:** 1.1, 1.2

## Spacing Scale

Custom spacing values for consistent layouts:

| Token | Value         | Purpose                |
| ----- | ------------- | ---------------------- |
| `18`  | 4.5rem (72px) | Large spacing          |
| `44`  | 44px          | Touch target size      |
| `56`  | 56px          | Mobile nav item height |
| `88`  | 22rem (352px) | Extra large spacing    |

**Requirements Coverage:** 1.7, 2.1

## Semantic Colors

Color tokens using CSS variables for theme switching:

| Token         | CSS Variable    | Purpose                        |
| ------------- | --------------- | ------------------------------ |
| `primary`     | `--primary`     | Main actions, focus states     |
| `secondary`   | `--secondary`   | Secondary actions, backgrounds |
| `accent`      | `--accent`      | CTAs, success states           |
| `destructive` | `--destructive` | Errors, warnings               |
| `muted`       | `--muted`       | Disabled, secondary text       |
| `background`  | `--background`  | Page background                |
| `foreground`  | `--foreground`  | Text on backgrounds            |
| `border`      | `--border`      | Border colors                  |
| `input`       | `--input`       | Input borders                  |
| `ring`        | `--ring`        | Focus rings                    |
| `card`        | `--card`        | Card backgrounds               |
| `popover`     | `--popover`     | Popover backgrounds            |

Each color token includes a `foreground` variant for text on that color.

**Requirements Coverage:** 4.1, 4.2

## Typography Scale

Font sizes with optimized line heights:

| Token  | Size | Line Height | Usage               |
| ------ | ---- | ----------- | ------------------- |
| `xs`   | 12px | 1.5         | Captions, badges    |
| `sm`   | 14px | 1.5         | Labels, helper text |
| `base` | 16px | 1.5         | Body text           |
| `lg`   | 18px | 1.5         | Subheadings         |
| `xl`   | 20px | 1.4         | Section titles      |
| `2xl`  | 24px | 1.3         | Page titles         |
| `3xl`  | 30px | 1.2         | Hero titles         |
| `4xl`  | 36px | 1.2         | Large headings      |
| `5xl`  | 48px | 1.1         | Display text        |

**Requirements Coverage:** 4.3

## Border Radius

Consistent corner rounding values:

| Token | Value | Usage                    |
| ----- | ----- | ------------------------ |
| `sm`  | 2px   | Subtle rounding          |
| `md`  | 4px   | Inputs, small components |
| `lg`  | 6px   | Cards, buttons           |
| `xl`  | 8px   | Modals, large components |
| `2xl` | 12px  | Rounded cards            |
| `3xl` | 16px  | Very rounded elements    |

**Requirements Coverage:** 4.4

## Shadow System

Elevation shadows for depth:

| Token | Value                       | Usage              |
| ----- | --------------------------- | ------------------ |
| `sm`  | 0 1px 2px rgba(0,0,0,0.05)  | Subtle elevation   |
| `md`  | 0 4px 6px rgba(0,0,0,0.1)   | Standard elevation |
| `lg`  | 0 10px 15px rgba(0,0,0,0.1) | High elevation     |
| `xl`  | 0 20px 25px rgba(0,0,0,0.1) | Maximum elevation  |

**Requirements Coverage:** 4.5

## Touch Targets

Minimum dimensions for mobile accessibility:

| Token      | Value | Purpose                     |
| ---------- | ----- | --------------------------- |
| `min-h-44` | 44px  | Minimum touch target height |
| `min-w-44` | 44px  | Minimum touch target width  |
| `min-h-48` | 48px  | Form controls on mobile     |
| `min-h-56` | 56px  | Mobile nav items            |

**Requirements Coverage:** 2.1, 2.3

## Animation Durations

Consistent timing for transitions:

| Token | Value | Usage                |
| ----- | ----- | -------------------- |
| `150` | 150ms | Micro-interactions   |
| `200` | 200ms | Standard transitions |
| `300` | 300ms | Standard transitions |
| `500` | 500ms | Complex animations   |

**Requirements Coverage:** 4.7, 21.1

## Animation Timing Functions

Easing curves for natural motion:

| Token         | Value                        | Usage            |
| ------------- | ---------------------------- | ---------------- |
| `ease-out`    | cubic-bezier(0.4, 0, 0.2, 1) | Enter animations |
| `ease-in`     | cubic-bezier(0.4, 0, 1, 1)   | Exit animations  |
| `ease-in-out` | cubic-bezier(0.4, 0, 0.2, 1) | Hover effects    |

**Requirements Coverage:** 4.7, 21.1

## Keyframe Animations

Pre-defined animation keyframes:

| Animation            | Duration | Easing   | Usage                    |
| -------------------- | -------- | -------- | ------------------------ |
| `accordion-down`     | 200ms    | ease-out | Accordion expansion      |
| `accordion-up`       | 200ms    | ease-out | Accordion collapse       |
| `fade-in`            | 200ms    | ease-out | Content appearance       |
| `fade-out`           | 200ms    | ease-out | Content disappearance    |
| `slide-in-from-left` | 300ms    | ease-out | Drawer entrance          |
| `slide-out-to-left`  | 300ms    | ease-out | Drawer exit              |
| `slide-up`           | 300ms    | ease-out | Modal entrance (mobile)  |
| `scale-up`           | 200ms    | ease-out | Modal entrance (desktop) |
| `shimmer`            | 2s       | linear   | Loading skeleton         |

**Requirements Coverage:** 21.2, 21.3

## Custom Utilities

Additional utility classes:

| Class           | Properties                                  | Usage                   |
| --------------- | ------------------------------------------- | ----------------------- |
| `.touch-target` | min-height: 44px; min-width: 44px           | Touch-friendly elements |
| `.safe-area-pb` | padding-bottom: env(safe-area-inset-bottom) | Bottom safe area        |
| `.safe-area-pt` | padding-top: env(safe-area-inset-top)       | Top safe area           |
| `.safe-area-pl` | padding-left: env(safe-area-inset-left)     | Left safe area          |
| `.safe-area-pr` | padding-right: env(safe-area-inset-right)   | Right safe area         |

**Requirements Coverage:** 2.5

## Usage Examples

### Responsive Layout

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{/* Content */}</div>
```

### Touch Target Button

```tsx
<button className="touch-target min-h-44 min-w-44 rounded-lg">Click me</button>
```

### Animated Card

```tsx
<div className="rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
  {/* Card content */}
</div>
```

### Typography Hierarchy

```tsx
<h1 className="text-5xl font-bold">Display Title</h1>
<h2 className="text-2xl font-semibold">Page Title</h2>
<p className="text-base">Body text</p>
<span className="text-sm text-muted-foreground">Helper text</span>
```

### Mobile Drawer Animation

```tsx
<div className="animate-slide-in-from-left">{/* Drawer content */}</div>
```

## Notes

- All color tokens use CSS variables for seamless theme switching
- Breakpoints follow mobile-first approach
- Touch targets meet WCAG 2.1 Level AAA guidelines (44x44px minimum)
- Animation durations respect `prefers-reduced-motion` preference
- Shadow values maintain consistent opacity for predictable elevation
- Typography scale uses optimal line heights for readability

## Related Files

- `frontend/tailwind.config.ts` - Tailwind configuration
- `frontend/app/globals.css` - CSS variable definitions
- `frontend/__tests__/unit/tailwind-config.test.ts` - Configuration tests
