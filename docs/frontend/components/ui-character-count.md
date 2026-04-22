# CharacterCount Component

A reusable component that displays current/max character count with color coding based on usage percentage.

## Requirements Coverage

**Requirement 11.4**: Display character count for text inputs with maximum length constraints

- Display format: "X / Y characters" or "X / Y"
- Color coding:
  - Default: muted color (text-muted-foreground) - below 80%
  - Warning: yellow/warning color - 80-99% of limit
  - Error: destructive color (text-destructive) - at or over limit
- Real-time updates as user types
- Accessible with ARIA attributes

## Usage

### Standalone Usage

```tsx
import { CharacterCount } from '@/components/ui/character-count';
import { useState } from 'react';

function MyComponent() {
  const [message, setMessage] = useState('');
  const maxLength = 100;

  return (
    <div>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        maxLength={maxLength}
      />
      <CharacterCount current={message.length} max={maxLength} />
    </div>
  );
}
```

### Integrated with FormInput

```tsx
import { FormInput } from '@/components/ui/form-input';

function MyForm() {
  return (
    <FormInput
      id="message"
      label="Message"
      maxLength={280}
      showCharacterCount
      placeholder="Enter your message..."
    />
  );
}
```

## Props

### CharacterCount Props

| Prop               | Type      | Default  | Description                                  |
| ------------------ | --------- | -------- | -------------------------------------------- |
| `current`          | `number`  | required | Current character count                      |
| `max`              | `number`  | required | Maximum character limit                      |
| `className`        | `string`  | -        | Additional CSS classes                       |
| `warningThreshold` | `number`  | `0.8`    | Percentage threshold for warning color (0-1) |
| `showLabel`        | `boolean` | `true`   | Whether to show "characters" label           |

### FormInput Props (Character Count Related)

| Prop                 | Type      | Default | Description                                            |
| -------------------- | --------- | ------- | ------------------------------------------------------ |
| `showCharacterCount` | `boolean` | `false` | Whether to show character count                        |
| `maxLength`          | `number`  | -       | Maximum character limit (required for character count) |

## Color States

### Default State (< 80%)

- Color: `text-muted-foreground`
- Usage: 0-79% of limit
- Example: 50 / 100 characters

### Warning State (80-99%)

- Color: `text-yellow-600 dark:text-yellow-500`
- Usage: 80-99% of limit
- Example: 85 / 100 characters

### Error State (≥ 100%)

- Color: `text-destructive`
- Usage: At or over limit
- Example: 100 / 100 characters or 105 / 100 characters

## Examples

### Basic Example

```tsx
<CharacterCount current={50} max={100} />
// Output: "50 / 100 characters" (muted color)
```

### Without Label

```tsx
<CharacterCount current={50} max={100} showLabel={false} />
// Output: "50 / 100" (muted color)
```

### Custom Warning Threshold (90%)

```tsx
<CharacterCount current={85} max={100} warningThreshold={0.9} />
// Output: "85 / 100 characters" (muted color, since 85% < 90%)

<CharacterCount current={90} max={100} warningThreshold={0.9} />
// Output: "90 / 100 characters" (warning color, since 90% >= 90%)
```

### With FormInput

```tsx
<FormInput
  id="bio"
  label="Bio"
  maxLength={500}
  showCharacterCount
  helperText="Tell us about yourself"
  placeholder="Enter your bio..."
/>
```

### With Error State

```tsx
<FormInput
  id="username"
  label="Username"
  maxLength={20}
  showCharacterCount
  error="Username is already taken"
/>
```

### Disabled State

```tsx
<FormInput
  id="readonly"
  label="Read-only Field"
  maxLength={50}
  showCharacterCount
  disabled
  value="This field is disabled"
/>
```

## Accessibility

The CharacterCount component includes the following accessibility features:

- **`aria-live="polite"`**: Announces character count changes to screen readers without interrupting
- **`aria-atomic="true"`**: Ensures the entire count is announced, not just the changed part
- **Color + Text**: Uses both color and text to convey information (not color alone)
- **Smooth Transitions**: 200ms color transitions for visual feedback

## Responsive Behavior

- Works seamlessly on all screen sizes
- Text size: `text-sm` (14px) for optimal readability
- Integrates with FormInput's responsive layout (full-width on mobile, auto-width on desktop)

## Design Specifications

- **Font Size**: 14px (text-sm)
- **Transition**: 200ms color transition
- **Warning Threshold**: 80% by default (customizable)
- **Error Threshold**: 100% (at or over limit)
- **Spacing**: Positioned with `ml-auto` when used with helper text

## Integration with FormInput

When `showCharacterCount` is enabled on FormInput:

1. Character count appears on the right side of the helper text/error message
2. Updates in real-time as user types
3. Works with both controlled and uncontrolled inputs
4. Respects disabled state (shows with reduced opacity)
5. Maintains accessibility with proper ARIA attributes

## Best Practices

1. **Always set maxLength**: Character count requires a maximum length to be meaningful
2. **Choose appropriate thresholds**: Default 80% works for most cases, but adjust based on your use case
3. **Provide context**: Use helper text to explain character limits when necessary
4. **Test with real content**: Ensure limits are appropriate for your use case
5. **Consider internationalization**: Different languages may have different character counting needs

## Testing

The component includes comprehensive unit tests covering:

- Display format variations
- Color coding at different thresholds
- Custom warning thresholds
- Real-time updates
- Edge cases (zero, negative, over limit)
- Accessibility features
- Integration with FormInput

Run tests with:

```bash
npm test -- character-count
```

## Related Components

- **FormInput**: Enhanced input component with label, helper text, and error state support
- **Input**: Base input component from shadcn/ui
- **Label**: Label component for form inputs

## Browser Support

Works in all modern browsers that support:

- CSS custom properties
- Flexbox
- ARIA attributes
- CSS transitions
