# FormInput Component

Enhanced input component with label, helper text, and error state support, built on top of the base Input component.

## Requirements Coverage

This component implements the following requirements from the Frontend UI/UX Redesign spec:

- **Req 11.1**: Label with 8px spacing above input
- **Req 11.2**: Placeholder with muted color
- **Req 11.3**: Error state with destructive color
- **Req 11.5**: Full-width on mobile, auto-width on desktop
- **Req 11.6**: 48px minimum height on mobile
- **Req 11.7**: Visible focus ring (2px, primary color)
- **Req 11.8**: Disabled state (50% opacity, not-allowed cursor)

## Features

- ✅ Accessible label with proper association
- ✅ Helper text for additional context
- ✅ Error state with validation messages
- ✅ Responsive sizing (mobile-first)
- ✅ Touch-friendly on mobile (48px min height)
- ✅ Visible focus indicators
- ✅ Disabled state styling
- ✅ Full keyboard navigation support
- ✅ ARIA attributes for screen readers

## Usage

### Basic Input

```tsx
import { FormInput } from '@/components/ui/form-input';

<FormInput id="email" label="Email Address" placeholder="you@example.com" />;
```

### Input with Helper Text

```tsx
<FormInput
  id="username"
  label="Username"
  placeholder="Choose a username"
  helperText="Username must be 3-20 characters long"
/>
```

### Input with Error State

```tsx
<FormInput
  id="email"
  label="Email Address"
  type="email"
  error="Please enter a valid email address"
/>
```

### Disabled Input

```tsx
<FormInput
  id="status"
  label="Account Status"
  value="Active"
  disabled
  helperText="This field cannot be edited"
/>
```

### Password Input

```tsx
<FormInput
  id="password"
  label="Password"
  type="password"
  placeholder="Enter your password"
  helperText="Must be at least 8 characters"
/>
```

### Controlled Input

```tsx
const [email, setEmail] = useState('');

<FormInput
  id="email"
  label="Email"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>;
```

### With Validation

```tsx
const [email, setEmail] = useState('');
const [error, setError] = useState('');

const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setEmail(e.target.value);
  if (e.target.value && !e.target.value.includes('@')) {
    setError('Please enter a valid email address');
  } else {
    setError('');
  }
};

<FormInput
  id="email"
  label="Email Address"
  type="email"
  value={email}
  onChange={handleEmailChange}
  error={error}
/>;
```

## Props

### FormInputProps

Extends all standard HTML input attributes plus:

| Prop                 | Type      | Required | Description                                                          |
| -------------------- | --------- | -------- | -------------------------------------------------------------------- |
| `id`                 | `string`  | Yes      | Unique identifier for the input (required for accessibility)         |
| `label`              | `string`  | No       | Label text displayed above the input                                 |
| `helperText`         | `string`  | No       | Helper text displayed below the input                                |
| `error`              | `string`  | No       | Error message displayed below the input with destructive color       |
| `hasError`           | `boolean` | No       | Whether the input is in an error state (alternative to `error` prop) |
| `containerClassName` | `string`  | No       | Additional classes for the wrapper div                               |
| `className`          | `string`  | No       | Additional classes for the input element                             |
| `disabled`           | `boolean` | No       | Whether the input is disabled                                        |

All other props from `React.ComponentProps<'input'>` are supported.

## Styling

### Responsive Behavior

- **Mobile (< 768px)**:
  - Full-width container and input
  - Minimum height: 48px (touch-friendly)
- **Desktop (≥ 768px)**:
  - Auto-width container and input
  - Minimum height: 40px

### States

#### Default

- Border: `border-input`
- Background: `bg-background`
- Text: `text-foreground`
- Placeholder: `text-muted-foreground`

#### Focus

- Ring: 2px solid primary color
- Ring offset: 2px
- Outline: none (using ring instead)

#### Error

- Border: `border-destructive`
- Focus ring: `ring-destructive`
- Error message: `text-destructive`
- Label: `text-destructive`

#### Disabled

- Opacity: 50%
- Cursor: `not-allowed`
- All child elements inherit disabled styling

### Spacing

- Label to input: 8px (`mb-2`)
- Input to helper/error text: 8px (`mt-2`)

## Accessibility

### ARIA Attributes

- `aria-invalid`: Set to `true` when in error state
- `aria-describedby`: Links to helper text or error message
- `role="alert"`: Applied to error messages

### Keyboard Navigation

- Tab: Focus the input
- Shift+Tab: Focus previous element
- All standard input keyboard interactions supported

### Screen Reader Support

- Label properly associated with input via `htmlFor` and `id`
- Helper text and error messages announced via `aria-describedby`
- Error state announced via `aria-invalid` and `role="alert"`

## Best Practices

### Always Provide an ID

```tsx
// ✅ Good
<FormInput id="email" label="Email" />

// ❌ Bad - TypeScript will error
<FormInput label="Email" />
```

### Use Labels for Accessibility

```tsx
// ✅ Good - Label provides accessible name
<FormInput id="email" label="Email Address" />

// ⚠️ Acceptable - But less accessible
<FormInput id="email" placeholder="Email" aria-label="Email Address" />
```

### Provide Helpful Error Messages

```tsx
// ✅ Good - Specific and actionable
<FormInput
  id="email"
  error="Please enter a valid email address (e.g., you@example.com)"
/>

// ❌ Bad - Vague and unhelpful
<FormInput id="email" error="Invalid input" />
```

### Use Helper Text for Context

```tsx
// ✅ Good - Provides clear guidance
<FormInput
  id="password"
  label="Password"
  type="password"
  helperText="Must be at least 8 characters with 1 number and 1 special character"
/>
```

## Examples

See `form-input.example.tsx` for comprehensive examples including:

- Basic inputs
- Validation patterns
- Form integration
- Custom styling
- Responsive behavior

## Testing

The component has comprehensive test coverage including:

- Basic rendering
- Label spacing
- Placeholder styling
- Error states
- Helper text
- Responsive width
- Minimum height
- Focus ring
- Disabled state
- Keyboard navigation
- Accessibility
- Custom styling
- Input types
- Edge cases

Run tests with:

```bash
npm test -- form-input.test.tsx
```

## Related Components

- `Input` - Base input component
- `Label` - Label component used internally
- `Button` - For form submission
- `Form` - For form layout and validation (if available)

## Migration from Base Input

If you're currently using the base `Input` component and want to add labels and error handling:

### Before

```tsx
<div>
  <label htmlFor="email">Email</label>
  <Input id="email" type="email" />
  {error && <p className="text-destructive">{error}</p>}
</div>
```

### After

```tsx
<FormInput id="email" label="Email" type="email" error={error} />
```

## Browser Support

Works in all modern browsers that support:

- CSS Grid and Flexbox
- CSS Custom Properties
- ES6+ JavaScript

## Performance

- Lightweight component with minimal overhead
- No external dependencies beyond base components
- Efficient re-renders with React.forwardRef
- Optimized for mobile performance
