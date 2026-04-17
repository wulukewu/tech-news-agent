# SearchBar Component

A search input component with debounced filtering, clear functionality, and loading states.

## Requirements Coverage

- **18.1**: Full-width search input on mobile (< 768px)
- **18.2**: 300ms debounce for search queries
- **18.3**: Clear search button when active
- **16.6**: Minimum 48px height on mobile

## Features

- **Debounced Search**: Configurable debounce delay (default 300ms) to prevent excessive filtering
- **Clear Button**: X icon appears when text is entered, allows quick clearing
- **Search Icon**: Visual indicator on the left side of the input
- **Loading Indicator**: Shows spinner during search operations
- **Keyboard Support**: Escape key clears the search
- **Accessibility**: Proper ARIA labels and roles for screen readers
- **Responsive**: Full-width on mobile, auto-width on desktop

## Usage

### Basic Usage

```tsx
import { SearchBar } from '@/components/SearchBar';

function MyComponent() {
  const handleSearch = (query: string) => {
    console.log('Search query:', query);
    // Perform search/filtering logic
  };

  return <SearchBar onSearch={handleSearch} />;
}
```

### With Loading State

```tsx
import { SearchBar } from '@/components/SearchBar';
import { useState } from 'react';

function MyComponent() {
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (query: string) => {
    setIsSearching(true);
    try {
      // Perform async search
      await searchArticles(query);
    } finally {
      setIsSearching(false);
    }
  };

  return <SearchBar onSearch={handleSearch} isLoading={isSearching} />;
}
```

### Custom Configuration

```tsx
<SearchBar
  onSearch={handleSearch}
  placeholder="Find articles..."
  debounceMs={500}
  className="mb-4"
  isLoading={isSearching}
/>
```

## Props

| Prop          | Type                      | Default                | Description                                    |
| ------------- | ------------------------- | ---------------------- | ---------------------------------------------- |
| `onSearch`    | `(query: string) => void` | Required               | Callback when search query changes (debounced) |
| `placeholder` | `string`                  | `"Search articles..."` | Placeholder text for the input                 |
| `debounceMs`  | `number`                  | `300`                  | Debounce delay in milliseconds                 |
| `className`   | `string`                  | `undefined`            | Additional CSS classes                         |
| `isLoading`   | `boolean`                 | `false`                | Show loading indicator                         |

## Client-Side Filtering Example

The SearchBar is designed to work with client-side filtering. Here's a complete example:

```tsx
import { SearchBar } from '@/components/SearchBar';
import { useState, useMemo } from 'react';

function ArticleList({ articles }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Filter articles based on search query
  const filteredArticles = useMemo(() => {
    if (!searchQuery.trim()) {
      return articles;
    }

    const query = searchQuery.toLowerCase().trim();

    return articles.filter((article) => {
      // Search in title
      if (article.title.toLowerCase().includes(query)) {
        return true;
      }

      // Search in summary
      if (article.summary?.toLowerCase().includes(query)) {
        return true;
      }

      // Search in category
      if (article.category.toLowerCase().includes(query)) {
        return true;
      }

      return false;
    });
  }, [articles, searchQuery]);

  const handleSearch = (query: string) => {
    setIsSearching(true);
    setSearchQuery(query);
    // Simulate search delay
    setTimeout(() => setIsSearching(false), 100);
  };

  return (
    <div>
      <SearchBar onSearch={handleSearch} isLoading={isSearching} />

      {/* Display result count */}
      {searchQuery && (
        <p className="text-sm text-muted-foreground mt-2">
          {filteredArticles.length} result{filteredArticles.length !== 1 ? 's' : ''} found
        </p>
      )}

      {/* Display filtered articles */}
      <div className="mt-4">
        {filteredArticles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>
    </div>
  );
}
```

## Accessibility

The SearchBar component follows WCAG 2.1 Level AA guidelines:

- **Keyboard Navigation**: Full keyboard support with Escape to clear
- **ARIA Labels**: Proper labels for screen readers
- **Focus Management**: Visible focus indicators
- **Loading Announcements**: Screen readers announce loading state
- **Semantic HTML**: Uses `role="search"` for the container

## Styling

The component uses Tailwind CSS and is fully responsive:

- **Mobile (< 768px)**: Full-width input with minimum 48px height
- **Desktop (≥ 768px)**: Auto-width with minimum 320px width
- **Icons**: 16px (h-4 w-4) for search and clear icons
- **Spacing**: Proper padding to accommodate icons

## Testing

The component includes comprehensive tests covering:

- Rendering with different props
- Search functionality and debouncing
- Clear button behavior
- Keyboard interactions (Escape key)
- Loading states
- Accessibility features
- Responsive behavior

Run tests with:

```bash
npm test -- SearchBar.test.tsx
```

## Implementation Notes

### Debouncing

The component uses the `debounce` utility from `@/lib/utils` to prevent excessive calls to the `onSearch` callback. The debounce function is created once using `useCallback` and memoized to avoid recreating it on every render.

### State Management

The component maintains internal state for the input value and triggers the debounced search callback when the value changes. This allows the parent component to remain unaware of the debouncing logic.

### Clear Functionality

The clear button:

- Only appears when there's text in the input
- Calls `onSearch('')` to notify the parent
- Clears the internal input state
- Can also be triggered by pressing Escape

## Related Components

- **Input**: Base input component used internally
- **Button**: Used for the clear button
- **ArticleGrid**: Typically displays filtered results

## Future Enhancements

Potential improvements for future iterations:

- Search history/suggestions
- Highlight matching text in results
- Advanced filters (date range, category)
- Voice search support
- Search analytics
