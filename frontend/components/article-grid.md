# ArticleGrid Component

## Overview

The `ArticleGrid` component provides a responsive grid layout for displaying articles on the dashboard page. It automatically adapts to different screen sizes using Tailwind CSS responsive utilities.

## Responsive Behavior

### Breakpoints

| Viewport | Width          | Columns   | Gap  |
| -------- | -------------- | --------- | ---- |
| Mobile   | < 768px        | 1 column  | 16px |
| Tablet   | 768px - 1024px | 2 columns | 16px |
| Desktop  | 1024px+        | 3 columns | 16px |

### Container

- Maximum width: 1400px (`max-w-7xl`)
- Responsive padding:
  - Mobile: 16px (`px-4`)
  - Tablet: 24px (`md:px-6`)
  - Desktop: 32px (`lg:px-8`)

## Usage

```tsx
import { ArticleGrid } from '@/components/ArticleGrid';
import type { Article } from '@/types/article';

const articles: Article[] = [
  // ... your articles
];

function DashboardPage() {
  return (
    <div className="container mx-auto max-w-7xl py-8 px-4 md:px-6 lg:px-8">
      <ArticleGrid articles={articles} />
    </div>
  );
}
```

## Props

```typescript
interface ArticleGridProps {
  /** Array of articles to display */
  articles: Article[];

  /** Show analysis button on cards (default: false) */
  showAnalysisButton?: boolean;

  /** Show reading list button on cards (default: true) */
  showReadingListButton?: boolean;

  /** Callback when analysis is requested */
  onAnalyze?: (articleId: string) => void;

  /** Callback when article is added to reading list */
  onAddToReadingList?: (articleId: string) => void;
}
```

## Implementation Details

### Grid Layout Classes

The component uses Tailwind's responsive grid utilities:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{/* Articles */}</div>
```

- `grid`: Enables CSS Grid layout
- `grid-cols-1`: 1 column on mobile (< 768px)
- `md:grid-cols-2`: 2 columns on tablet (≥ 768px)
- `lg:grid-cols-3`: 3 columns on desktop (≥ 1024px)
- `gap-4`: 16px gap between grid items

### Article Card Layout

Each article is rendered using the `ArticleCard` component with `layout="mobile"` prop, which provides:

- Vertical stacking on mobile
- Full-width images
- Touch-friendly buttons (44px minimum)
- Optimized spacing

## Accessibility

- Semantic HTML structure using `role="list"` and `role="listitem"`
- Descriptive `aria-label` for screen readers
- Keyboard navigation support through ArticleCard
- Focus indicators on interactive elements

## Requirements Coverage

This component satisfies the following requirements from the UI/UX Redesign spec:

- **1.4**: Single column layout on mobile viewport (< 768px)
- **1.5**: Two-column grid on tablet viewport (768px-1024px)
- **1.6**: Three-column grid on desktop viewport (1024px+) with max 1400px width
- **1.7**: Consistent 16px gap spacing between grid items

## Testing

Unit tests are located in `frontend/__tests__/unit/components/ArticleGrid.test.tsx` and cover:

- Grid rendering with multiple articles
- Responsive grid layout classes
- Gap spacing verification
- Props handling
- Accessibility attributes
- Empty state handling

Run tests with:

```bash
npm test -- ArticleGrid.test.tsx
```

## Related Components

- `ArticleCard`: Individual article display component
- `LoadingSkeleton`: Loading state for the grid
- `DashboardPage`: Main page using the grid layout
