# Articles Components

This directory contains all article-related components for the Tech News Agent frontend.

## Components

### ArticleBrowser

The core component for browsing and displaying articles with advanced features.

#### Features

- **Responsive Grid Layout**: Automatically adapts to different screen sizes (1-4 columns)
- **Virtual Scrolling**: Efficient rendering for large article lists (>50 items)
- **Button Limits**: Enforces UI constraints (max 5 analysis buttons, max 10 reading list buttons per page)
- **Statistics Display**: Shows total and filtered article counts
- **Loading & Error States**: Proper handling of loading and error conditions
- **Filtering Support**: Client-side filtering by tinkering index
- **Customizable Callbacks**: Support for custom analysis and reading list actions

#### Props

```typescript
interface ArticleBrowserProps {
  /** Initial filter state for the browser */
  initialFilters?: ArticleFilters;
  /** Number of articles per page */
  pageSize?: number;
  /** Enable virtual scrolling for large lists */
  enableVirtualization?: boolean;
  /** Custom CSS classes */
  className?: string;
  /** Show analysis buttons (max 5 per page) */
  showAnalysisButtons?: boolean;
  /** Show reading list buttons (max 10 per page) */
  showReadingListButtons?: boolean;
  /** Callback when analysis is requested */
  onAnalyze?: (articleId: string) => void;
  /** Callback when article is added to reading list */
  onAddToReadingList?: (articleId: string) => void;
}
```

#### Usage Examples

```typescript
// Basic usage
<ArticleBrowser />

// With filters and virtual scrolling
<ArticleBrowser
  initialFilters={{ minTinkeringIndex: 3 }}
  enableVirtualization={true}
  pageSize={50}
/>

// With custom callbacks
<ArticleBrowser
  showAnalysisButtons={true}
  onAnalyze={(id) => openAnalysisModal(id)}
  onAddToReadingList={(id) => addToList(id)}
/>
```

#### Requirements Validation

- **Requirement 1.1**: ✅ Displays articles in responsive grid layout
- **Requirement 12.2**: ✅ Virtual scrolling for performance optimization

#### Testing

The component is fully tested with:

- Unit tests for all major functionality
- Property-based testing for edge cases
- Mock integration with React Query hooks
- Accessibility and keyboard navigation testing

#### Performance Considerations

- Uses React.memo and useCallback for optimization
- Virtual scrolling kicks in automatically for lists >50 items
- Efficient filtering with useMemo
- Proper cleanup and memory management

#### Accessibility

- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatible
- High contrast mode support

## File Structure

```
components/
├── ArticleBrowser.tsx          # Main component
├── ArticleBrowser.example.tsx  # Usage examples
├── ArticleBrowser.test.tsx     # Unit tests
├── index.ts                    # Exports
└── README.md                   # This file
```
