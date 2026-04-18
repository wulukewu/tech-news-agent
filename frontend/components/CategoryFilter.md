# CategoryFilter Component

A reusable category filter component with multi-select badges, horizontal scrolling on mobile, and full accessibility support.

## Features

- ✅ Multi-select badge filters with visual feedback
- ✅ Horizontal scroll on mobile (< 768px) with hidden scrollbar
- ✅ Touch-friendly targets (44px minimum height)
- ✅ Keyboard navigation support (Enter/Space to toggle)
- ✅ Full ARIA attributes for screen readers
- ✅ Loading skeleton state
- ✅ Select All / Clear All buttons
- ✅ Smooth transitions (200ms)
- ✅ Snap scrolling on mobile for better UX

## Usage

```tsx
import { CategoryFilter } from '@/components/CategoryFilter';

function MyPage() {
  const [categories, setCategories] = useState(['Tech News', 'AI/ML', 'Web Dev']);
  const [selectedCategories, setSelectedCategories] = useState(['Tech News']);

  const handleToggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  const handleSelectAll = () => {
    setSelectedCategories(categories);
  };

  const handleClearAll = () => {
    setSelectedCategories([]);
  };

  return (
    <CategoryFilter
      categories={categories}
      selectedCategories={selectedCategories}
      onToggleCategory={handleToggleCategory}
      onSelectAll={handleSelectAll}
      onClearAll={handleClearAll}
      loading={false}
    />
  );
}
```

## Props

| Prop                 | Type                         | Required | Description                                       |
| -------------------- | ---------------------------- | -------- | ------------------------------------------------- |
| `categories`         | `string[]`                   | Yes      | Array of available category names                 |
| `selectedCategories` | `string[]`                   | Yes      | Array of currently selected category names        |
| `onToggleCategory`   | `(category: string) => void` | Yes      | Callback when a category badge is clicked         |
| `onSelectAll`        | `() => void`                 | Yes      | Callback when Select All button is clicked        |
| `onClearAll`         | `() => void`                 | Yes      | Callback when Clear All button is clicked         |
| `loading`            | `boolean`                    | No       | Shows loading skeleton when true (default: false) |

## Accessibility

### ARIA Attributes

- Each badge has `role="checkbox"` and `aria-checked` state
- Container has `role="group"` with `aria-label="Category filters"`
- Each badge has descriptive `aria-label` (e.g., "Filter by Tech News")
- All badges are keyboard focusable with `tabIndex={0}`

### Keyboard Navigation

- **Tab**: Navigate between badges and buttons
- **Enter**: Toggle selected badge
- **Space**: Toggle selected badge
- **Shift + Tab**: Navigate backwards

### Screen Reader Support

- Selected state is announced as "checked" or "unchecked"
- Button states (enabled/disabled) are properly announced
- Loading state provides appropriate feedback

## Responsive Design

### Mobile (< 768px)

- Horizontal scrolling container with hidden scrollbar
- Snap scrolling for better touch experience
- Full-width touch targets (44px minimum height)
- Padding adjustments for better scroll experience

### Desktop (≥ 768px)

- Badges wrap naturally if they fit
- Hover effects with shadow elevation
- Cursor pointer on interactive elements

## Styling

The component uses Tailwind CSS classes and follows the design system:

- **Selected badges**: `variant="default"` (primary color background)
- **Unselected badges**: `variant="outline"` (border only)
- **Transitions**: 200ms for all state changes
- **Focus indicators**: 2px outline with primary color
- **Shadows**: Subtle shadow on selected badges

## Performance

- Updates within 300ms of filter change (requirement 18.6)
- Efficient re-renders with proper React key usage
- No layout shifts during interactions
- Smooth scrolling with CSS `scroll-smooth`

## Integration with URL Persistence

The CategoryFilter component is designed to work with URL query parameters. See the dashboard page implementation for an example:

```tsx
// In your page component
const searchParams = useSearchParams();
const router = useRouter();

// Initialize from URL
useEffect(() => {
  const categoriesParam = searchParams.get('categories');
  if (categoriesParam) {
    const urlCategories = categoriesParam.split(',').filter(Boolean);
    setSelectedCategories(urlCategories);
  }
}, [searchParams]);

// Update URL when filters change
const updateURL = (newCategories: string[]) => {
  const params = new URLSearchParams();
  if (newCategories.length > 0) {
    params.set('categories', newCategories.join(','));
  }
  const queryString = params.toString();
  const newURL = queryString ? `/dashboard?${queryString}` : '/dashboard';
  router.replace(newURL, { scroll: false });
};

const handleToggleCategory = (category: string) => {
  setSelectedCategories((prev) => {
    const newCategories = prev.includes(category)
      ? prev.filter((c) => c !== category)
      : [...prev, category];
    updateURL(newCategories);
    return newCategories;
  });
};
```

## Testing

The component has comprehensive test coverage:

- **Unit tests**: `__tests__/unit/components/CategoryFilter.test.tsx`
  - Rendering with different states
  - Selection state management
  - User interactions (click, keyboard)
  - Accessibility attributes
  - Responsive design classes
  - Performance (< 300ms updates)

- **Integration tests**: `__tests__/integration/dashboard-category-filter.test.tsx`
  - URL query parameter persistence
  - Filter performance
  - Invalid URL parameter handling
  - Combined search and filter functionality

Run tests:

```bash
npm test -- CategoryFilter.test.tsx
npm test -- dashboard-category-filter.test.tsx
```

## Requirements Coverage

This component satisfies the following requirements:

- **18.5**: Multi-select category badges ✅
- **18.6**: Update article list within 300ms ✅
- **18.7**: Persist filters in URL query parameters ✅
- **2.1**: Minimum 44px touch targets ✅
- **15.1-15.8**: Full accessibility compliance ✅
- **21.1-21.4**: Smooth animations and transitions ✅

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Notes

- The component does not render when `categories` array is empty
- Loading state shows skeleton with shimmer animation
- Select All button is disabled when all categories are selected
- Clear All button is disabled when no categories are selected
- Horizontal scroll uses `scrollbar-hide` utility class (defined in Tailwind config)
