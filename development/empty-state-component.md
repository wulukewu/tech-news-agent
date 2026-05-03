# EmptyState Component

A flexible empty state component that displays helpful messages when users have no content. Supports three variants with appropriate icons and actions.

## Features

- ✅ Three built-in variants: `no-subscriptions`, `no-articles`, `no-reading-list`
- ✅ Automatic icon selection based on variant
- ✅ Support for custom icons
- ✅ Primary and secondary action buttons
- ✅ Optional scheduler status display
- ✅ Backward compatible with legacy API
- ✅ Fully typed with TypeScript
- ✅ Responsive design with Tailwind CSS

## Installation

The component uses the following dependencies:

- `lucide-react` - For icons (Rss, FileText, BookMarked)
- `@/components/ui/card` - shadcn/ui Card components

## Basic Usage

```tsx
import { EmptyState } from '@/components/EmptyState';

function MyComponent() {
  return (
    <EmptyState
      type="no-subscriptions"
      title="還沒有訂閱"
      description="開始訂閱一些 RSS 來源來查看文章"
      primaryAction={{
        label: '管理訂閱',
        onClick: () => router.push('/subscriptions'),
      }}
    />
  );
}
```

## Props

### EmptyStateProps

| Prop              | Type                                                       | Required | Default | Description                                            |
| ----------------- | ---------------------------------------------------------- | -------- | ------- | ------------------------------------------------------ |
| `type`            | `'no-subscriptions' \| 'no-articles' \| 'no-reading-list'` | No       | -       | Variant type that determines the default icon          |
| `title`           | `string`                                                   | Yes      | -       | Main heading text                                      |
| `description`     | `string`                                                   | Yes      | -       | Description text explaining the empty state            |
| `primaryAction`   | `{ label: string; onClick: () => void }`                   | No       | -       | Primary action button                                  |
| `secondaryAction` | `{ label: string; onClick: () => void }`                   | No       | -       | Secondary action button                                |
| `action`          | `ReactNode`                                                | No       | -       | Custom action element (for backward compatibility)     |
| `icon`            | `ReactNode`                                                | No       | Auto    | Custom icon element (overrides default variant icon)   |
| `schedulerStatus` | `SchedulerStatus`                                          | No       | -       | Scheduler status information (for no-articles variant) |

### SchedulerStatus

| Property                     | Type           | Description                                              |
| ---------------------------- | -------------- | -------------------------------------------------------- |
| `lastExecutionTime`          | `Date \| null` | Last time the scheduler ran                              |
| `nextScheduledTime`          | `Date \| null` | Next scheduled execution time                            |
| `isRunning`                  | `boolean`      | Whether the scheduler is currently running               |
| `lastExecutionArticleCount`  | `number`       | Number of articles fetched in last execution             |
| `estimatedTimeUntilArticles` | `string`       | Estimated time until articles appear (e.g., "5-10 分鐘") |

## Variants

### 1. No Subscriptions (`no-subscriptions`)

Used when the user has no RSS subscriptions yet.

**Default Icon:** Rss (📡)

```tsx
<EmptyState
  type="no-subscriptions"
  title="還沒有訂閱"
  description="開始訂閱一些 RSS 來源來查看文章"
  primaryAction={{
    label: '管理訂閱',
    onClick: () => router.push('/subscriptions'),
  }}
/>
```

### 2. No Articles (`no-articles`)

Used when the user has subscriptions but no articles have been fetched yet.

**Default Icon:** FileText (📄)

```tsx
<EmptyState
  type="no-articles"
  title="還沒有文章"
  description="排程器會定期自動抓取文章"
  primaryAction={{
    label: '管理訂閱',
    onClick: () => router.push('/subscriptions'),
  }}
  secondaryAction={{
    label: '手動觸發抓取',
    onClick: handleTriggerScheduler,
  }}
  schedulerStatus={{
    lastExecutionTime: new Date(),
    nextScheduledTime: null,
    isRunning: false,
    lastExecutionArticleCount: 0,
    estimatedTimeUntilArticles: '5-10 分鐘',
  }}
/>
```

### 3. No Reading List (`no-reading-list`)

Used when the user's reading list is empty.

**Default Icon:** BookMarked (📚)

```tsx
<EmptyState
  type="no-reading-list"
  title="閱讀清單為空"
  description="瀏覽文章時，點擊書籤圖示即可加入閱讀清單"
  primaryAction={{
    label: '瀏覽文章',
    onClick: () => router.push('/'),
  }}
/>
```

## Advanced Usage

### Custom Icon

Override the default variant icon with a custom one:

```tsx
<EmptyState
  type="no-subscriptions"
  title="自訂圖示"
  description="使用自訂圖示"
  icon={<CustomIcon className="w-12 h-12" />}
  primaryAction={{
    label: '開始',
    onClick: handleStart,
  }}
/>
```

### Multiple Actions

Display both primary and secondary action buttons:

```tsx
<EmptyState
  type="no-articles"
  title="還沒有文章"
  description="您可以管理訂閱或手動觸發抓取"
  primaryAction={{
    label: '管理訂閱',
    onClick: () => router.push('/subscriptions'),
  }}
  secondaryAction={{
    label: '手動觸發抓取',
    onClick: handleTriggerScheduler,
  }}
/>
```

### With Scheduler Status

Display scheduler information for the no-articles variant:

```tsx
const schedulerStatus = {
  lastExecutionTime: new Date('2024-01-15T10:30:00Z'),
  nextScheduledTime: new Date('2024-01-15T11:00:00Z'),
  isRunning: false,
  lastExecutionArticleCount: 0,
  estimatedTimeUntilArticles: '5-10 分鐘',
};

<EmptyState
  type="no-articles"
  title="還沒有文章"
  description="排程器會定期自動抓取文章"
  schedulerStatus={schedulerStatus}
  primaryAction={{
    label: '管理訂閱',
    onClick: () => router.push('/subscriptions'),
  }}
/>;
```

### Backward Compatibility

The component still supports the legacy `action` prop:

```tsx
<EmptyState
  title="舊版 API"
  description="使用舊版 action prop"
  action={<button onClick={handleAction}>自訂動作</button>}
/>
```

## Styling

The component uses Tailwind CSS classes and follows the shadcn/ui design system:

- **Card**: Dashed border for empty state appearance
- **Content**: Centered with padding
- **Icon**: Muted foreground color, 12x12 size
- **Title**: Large semibold text
- **Description**: Muted foreground, max-width for readability
- **Buttons**: Primary uses theme colors, secondary uses border style

### Responsive Design

The action buttons stack vertically on mobile and display horizontally on larger screens:

```tsx
<div className="flex flex-col sm:flex-row gap-3">{/* Buttons */}</div>
```

## Testing

The component includes comprehensive unit tests covering:

- ✅ Basic rendering (title, description)
- ✅ Variant support (all three variants)
- ✅ Action buttons (primary, secondary, legacy)
- ✅ Scheduler status display
- ✅ Custom icon override
- ✅ Styling and layout

Run tests:

```bash
npm test -- EmptyState.test.tsx
```

## Requirements Validation

This component satisfies the following requirements from the spec:

- **Requirement 3.1**: Display EmptyState when Dashboard has no articles
- **Requirement 3.2**: Include clear heading
- **Requirement 3.6**: Display illustration or icon
- **Requirement 3.3**: Explain why there are no articles
- **Requirement 3.4**: Include primary CTA button
- **Requirement 3.5**: Include secondary CTA button
- **Requirement 3.7**: Display scheduler status information

## Design Properties

The component validates the following design properties:

- **Property 5**: Empty State Conditional Display - Component displays when article count is zero
- **Property 6**: Scheduler Status Conditional Display - Shows scheduler status when user has subscriptions but no articles

## Migration Guide

If you're using the old EmptyState API, here's how to migrate:

### Before (Old API)

```tsx
<EmptyState
  title="No Content"
  description="Add some content"
  action={<button>Add Content</button>}
  icon={<Icon />}
/>
```

### After (New API)

```tsx
<EmptyState
  type="no-subscriptions" // Add variant type
  title="No Content"
  description="Add some content"
  primaryAction={{
    // Use primaryAction instead of action
    label: 'Add Content',
    onClick: handleAdd,
  }}
  icon={<Icon />} // icon prop still works
/>
```

The old API is still supported for backward compatibility, so you can migrate gradually.

## Examples

See `EmptyState.examples.tsx` for complete working examples of all variants and use cases.

## Related Components

- `SchedulerStatusIndicator` - Displays detailed scheduler status
- `TriggerSchedulerButton` - Button to manually trigger the scheduler
- `Card` - shadcn/ui Card component used as the base

## License

Part of the Tech News Agent project.
