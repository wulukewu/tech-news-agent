import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormInput } from '../../form-input';

describe('FormInput Component', () => {
  describe('Basic Rendering', () => {
    it('renders input with label', () => {
      render(<FormInput id="test-input" label="Test Label" />);

      expect(screen.getByLabelText('Test Label')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders input without label', () => {
      render(<FormInput id="test-input" placeholder="Enter text" />);

      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
      expect(screen.queryByRole('label')).not.toBeInTheDocument();
    });

    it('renders with helper text', () => {
      render(<FormInput id="test-input" label="Email" helperText="Enter your email address" />);

      expect(screen.getByText('Enter your email address')).toBeInTheDocument();
    });
  });

  describe('Label Spacing (Req 11.1)', () => {
    it('applies 8px spacing above input', () => {
      render(<FormInput id="test-input" label="Test Label" />);

      const label = screen.getByText('Test Label');
      expect(label).toHaveClass('mb-2'); // 8px spacing
    });
  });

  describe('Placeholder (Req 11.2)', () => {
    it('renders placeholder with muted color', () => {
      render(<FormInput id="test-input" placeholder="Enter text" />);

      const input = screen.getByPlaceholderText('Enter text');
      expect(input).toHaveClass('placeholder:text-muted-foreground');
    });
  });

  describe('Error State (Req 11.3)', () => {
    it('displays error message with destructive color', () => {
      render(<FormInput id="test-input" label="Email" error="Invalid email address" />);

      const errorMessage = screen.getByText('Invalid email address');
      expect(errorMessage).toBeInTheDocument();
      expect(errorMessage).toHaveClass('text-destructive');
      expect(errorMessage).toHaveAttribute('role', 'alert');
    });

    it('applies destructive border color when hasError is true', () => {
      render(<FormInput id="test-input" label="Email" hasError />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('border-destructive');
    });

    it('applies destructive color to label in error state', () => {
      render(<FormInput id="test-input" label="Email" error="Invalid email" />);

      const label = screen.getByText('Email');
      expect(label).toHaveClass('text-destructive');
    });

    it('sets aria-invalid when in error state', () => {
      render(<FormInput id="test-input" error="Error message" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('links error message with aria-describedby', () => {
      render(<FormInput id="test-input" error="Error message" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'test-input-error');
    });
  });

  describe('Helper Text (Req 11.7)', () => {
    it('displays helper text below input', () => {
      render(<FormInput id="test-input" helperText="This is a helper text" />);

      const helperText = screen.getByText('This is a helper text');
      expect(helperText).toBeInTheDocument();
      expect(helperText).toHaveClass('text-muted-foreground');
    });

    it('links helper text with aria-describedby', () => {
      render(<FormInput id="test-input" helperText="Helper text" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'test-input-helper');
    });

    it('prioritizes error message over helper text', () => {
      render(<FormInput id="test-input" helperText="Helper text" error="Error message" />);

      expect(screen.getByText('Error message')).toBeInTheDocument();
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument();
    });
  });

  describe('Responsive Width (Req 11.5)', () => {
    it('applies full-width on mobile, auto-width on desktop', () => {
      render(<FormInput id="test-input" label="Test" />);

      const container = screen.getByRole('textbox').parentElement;
      expect(container).toHaveClass('w-full', 'md:w-auto');

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('w-full', 'md:w-auto');
    });
  });

  describe('Minimum Height (Req 11.6)', () => {
    it('applies 48px minimum height on mobile', () => {
      render(<FormInput id="test-input" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('min-h-12'); // 48px
    });

    it('applies 40px minimum height on desktop', () => {
      render(<FormInput id="test-input" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('md:min-h-10'); // 40px
    });
  });

  describe('Focus Ring (Req 11.7)', () => {
    it('applies visible 2px focus ring with primary color', () => {
      render(<FormInput id="test-input" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass(
        'focus-visible:ring-2',
        'focus-visible:ring-primary',
        'focus-visible:ring-offset-2'
      );
    });

    it('applies destructive focus ring in error state', () => {
      render(<FormInput id="test-input" error="Error" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('focus-visible:ring-destructive');
    });
  });

  describe('Disabled State (Req 11.8)', () => {
    it('applies 50% opacity when disabled', () => {
      render(<FormInput id="test-input" label="Test" disabled />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('opacity-50');
      expect(input).toBeDisabled();
    });

    it('applies not-allowed cursor when disabled', () => {
      render(<FormInput id="test-input" label="Test" disabled />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('cursor-not-allowed');
    });

    it('applies disabled styles to label', () => {
      render(<FormInput id="test-input" label="Test Label" disabled />);

      const label = screen.getByText('Test Label');
      expect(label).toHaveClass('opacity-50', 'cursor-not-allowed');
    });

    it('applies disabled styles to helper text', () => {
      render(<FormInput id="test-input" helperText="Helper text" disabled />);

      const helperText = screen.getByText('Helper text');
      expect(helperText).toHaveClass('opacity-50');
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports keyboard focus', async () => {
      const user = userEvent.setup();
      render(<FormInput id="test-input" label="Test" />);

      const input = screen.getByRole('textbox');

      await user.tab();
      expect(input).toHaveFocus();
    });

    it('allows typing when focused', async () => {
      const user = userEvent.setup();
      render(<FormInput id="test-input" label="Test" />);

      const input = screen.getByRole('textbox') as HTMLInputElement;

      await user.click(input);
      await user.keyboard('Hello World');

      expect(input.value).toBe('Hello World');
    });
  });

  describe('Accessibility', () => {
    it('associates label with input using htmlFor and id', () => {
      render(<FormInput id="test-input" label="Test Label" />);

      const label = screen.getByText('Test Label');
      const input = screen.getByRole('textbox');

      expect(label).toHaveAttribute('for', 'test-input');
      expect(input).toHaveAttribute('id', 'test-input');
    });

    it('provides accessible name through label', () => {
      render(<FormInput id="test-input" label="Email Address" />);

      expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    });

    it('provides accessible description through helper text', () => {
      render(
        <FormInput id="test-input" label="Password" helperText="Must be at least 8 characters" />
      );

      const input = screen.getByRole('textbox');
      const helperText = screen.getByText('Must be at least 8 characters');

      expect(input).toHaveAttribute('aria-describedby', 'test-input-helper');
      expect(helperText).toHaveAttribute('id', 'test-input-helper');
    });
  });

  describe('Custom Styling', () => {
    it('accepts custom className for input', () => {
      render(<FormInput id="test-input" className="custom-input-class" />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('custom-input-class');
    });

    it('accepts custom containerClassName', () => {
      render(
        <FormInput id="test-input" label="Test" containerClassName="custom-container-class" />
      );

      const container = screen.getByRole('textbox').parentElement;
      expect(container).toHaveClass('custom-container-class');
    });
  });

  describe('Input Types', () => {
    it('supports different input types', () => {
      const { rerender } = render(<FormInput id="test-input" type="email" />);
      let input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('type', 'email');

      rerender(<FormInput id="test-input" type="password" />);
      input = document.getElementById('test-input') as HTMLInputElement;
      expect(input).toHaveAttribute('type', 'password');

      rerender(<FormInput id="test-input" type="number" />);
      input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('type', 'number');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty strings for optional props', () => {
      render(<FormInput id="test-input" label="" helperText="" error="" />);

      // Empty strings should not render the elements
      expect(screen.queryByRole('label')).not.toBeInTheDocument();
    });

    it('handles long error messages', () => {
      const longError =
        'This is a very long error message that should wrap properly and not break the layout';
      render(<FormInput id="test-input" error={longError} />);

      expect(screen.getByText(longError)).toBeInTheDocument();
    });

    it('handles long helper text', () => {
      const longHelper = 'This is a very long helper text that provides detailed instructions';
      render(<FormInput id="test-input" helperText={longHelper} />);

      expect(screen.getByText(longHelper)).toBeInTheDocument();
    });
  });
});
