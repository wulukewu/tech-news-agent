import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { FormInput } from '../../form-input';

describe('FormInput with Character Count', () => {
  describe('Character Count Display', () => {
    it('should not show character count by default', () => {
      render(<FormInput id="test-input" maxLength={100} />);
      expect(screen.queryByText(/\/ 100/)).not.toBeInTheDocument();
    });

    it('should show character count when showCharacterCount is true', () => {
      render(<FormInput id="test-input" maxLength={100} showCharacterCount />);
      expect(screen.getByText('0 / 100')).toBeInTheDocument();
    });

    it('should not show character count without maxLength even if showCharacterCount is true', () => {
      render(<FormInput id="test-input" showCharacterCount />);
      expect(screen.queryByText(/\//)).not.toBeInTheDocument();
    });

    it('should show character count with initial value', () => {
      render(<FormInput id="test-input" maxLength={100} showCharacterCount defaultValue="Hello" />);
      expect(screen.getByText('5 / 100')).toBeInTheDocument();
    });

    it('should show character count with controlled value', () => {
      render(
        <FormInput
          id="test-input"
          maxLength={100}
          showCharacterCount
          value="Hello World"
          onChange={() => {}}
        />
      );
      expect(screen.getByText('11 / 100')).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('should update character count as user types (uncontrolled)', () => {
      render(<FormInput id="test-input" maxLength={100} showCharacterCount />);

      const input = screen.getByRole('textbox');
      expect(screen.getByText('0 / 100')).toBeInTheDocument();

      fireEvent.change(input, { target: { value: 'Hello' } });
      expect(screen.getByText('5 / 100')).toBeInTheDocument();

      fireEvent.change(input, { target: { value: 'Hello World' } });
      expect(screen.getByText('11 / 100')).toBeInTheDocument();
    });

    it('should update character count as user types (controlled)', () => {
      const TestComponent = () => {
        const [value, setValue] = React.useState('');
        return (
          <FormInput
            id="test-input"
            maxLength={100}
            showCharacterCount
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        );
      };

      render(<TestComponent />);

      const input = screen.getByRole('textbox');
      expect(screen.getByText('0 / 100')).toBeInTheDocument();

      fireEvent.change(input, { target: { value: 'Test' } });
      expect(screen.getByText('4 / 100')).toBeInTheDocument();
    });

    it('should update character count when deleting text', () => {
      render(
        <FormInput id="test-input" maxLength={100} showCharacterCount defaultValue="Hello World" />
      );

      const input = screen.getByRole('textbox');
      expect(screen.getByText('11 / 100')).toBeInTheDocument();

      fireEvent.change(input, { target: { value: 'Hello' } });
      expect(screen.getByText('5 / 100')).toBeInTheDocument();
    });
  });

  describe('Color Coding Integration', () => {
    it('should show muted color for low character count', () => {
      const { container } = render(
        <FormInput id="test-input" maxLength={100} showCharacterCount defaultValue="Hello" />
      );

      const characterCount = container.querySelector('.text-muted-foreground');
      expect(characterCount).toBeInTheDocument();
      expect(characterCount).toHaveTextContent('5 / 100');
    });

    it('should show warning color when approaching limit', () => {
      const longText = 'a'.repeat(85);
      const { container } = render(
        <FormInput id="test-input" maxLength={100} showCharacterCount defaultValue={longText} />
      );

      const characterCount = container.querySelector('.text-yellow-600');
      expect(characterCount).toBeInTheDocument();
      expect(characterCount).toHaveTextContent('85 / 100');
    });

    it('should show destructive color at limit', () => {
      const longText = 'a'.repeat(100);
      const { container } = render(
        <FormInput id="test-input" maxLength={100} showCharacterCount defaultValue={longText} />
      );

      const characterCount = container.querySelector('.text-destructive');
      expect(characterCount).toBeInTheDocument();
      expect(characterCount).toHaveTextContent('100 / 100');
    });
  });

  describe('Layout with Helper Text and Error', () => {
    it('should display both helper text and character count', () => {
      render(
        <FormInput
          id="test-input"
          maxLength={100}
          showCharacterCount
          helperText="Enter your message"
        />
      );

      expect(screen.getByText('Enter your message')).toBeInTheDocument();
      expect(screen.getByText('0 / 100')).toBeInTheDocument();
    });

    it('should display both error message and character count', () => {
      render(
        <FormInput
          id="test-input"
          maxLength={100}
          showCharacterCount
          error="This field is required"
        />
      );

      expect(screen.getByText('This field is required')).toBeInTheDocument();
      expect(screen.getByText('0 / 100')).toBeInTheDocument();
    });

    it('should position character count on the right side', () => {
      const { container } = render(
        <FormInput id="test-input" maxLength={100} showCharacterCount helperText="Helper text" />
      );

      const wrapper = container.querySelector('.flex.items-center.justify-between');
      expect(wrapper).toBeInTheDocument();

      const characterCount = container.querySelector('.ml-auto');
      expect(characterCount).toBeInTheDocument();
      expect(characterCount).toHaveTextContent('0 / 100');
    });
  });

  describe('Disabled State', () => {
    it('should show character count with reduced opacity when disabled', () => {
      render(
        <FormInput
          id="test-input"
          maxLength={100}
          showCharacterCount
          disabled
          value="Test"
          onChange={() => {}}
        />
      );

      // Character count should be visible with reduced opacity
      expect(screen.getByText('4 / 100')).toBeInTheDocument();
      const characterCount = screen.getByText('4 / 100');
      expect(characterCount).toHaveClass('opacity-50');
    });

    it('should not update character count when disabled input is changed', () => {
      render(
        <FormInput
          id="test-input"
          maxLength={100}
          showCharacterCount
          disabled
          value="Test"
          onChange={() => {}}
        />
      );

      const input = screen.getByRole('textbox');
      expect(screen.getByText('4 / 100')).toBeInTheDocument();

      // Disabled inputs shouldn't allow changes
      fireEvent.change(input, { target: { value: 'New Value' } });
      // Should still show original count since input is disabled and controlled
      expect(screen.getByText('4 / 100')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should associate character count with input via aria-describedby', () => {
      render(
        <FormInput id="test-input" maxLength={100} showCharacterCount helperText="Helper text" />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'test-input-helper');
    });

    it('should maintain aria-describedby with error message', () => {
      render(
        <FormInput id="test-input" maxLength={100} showCharacterCount error="Error message" />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'test-input-error');
    });
  });

  describe('Integration with Label', () => {
    it('should display label, input, helper text, and character count together', () => {
      render(
        <FormInput
          id="test-input"
          label="Message"
          maxLength={100}
          showCharacterCount
          helperText="Enter your message"
          defaultValue="Hello"
        />
      );

      expect(screen.getByText('Message')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByText('Enter your message')).toBeInTheDocument();
      expect(screen.getByText('5 / 100')).toBeInTheDocument();
    });

    it('should apply error styling to label when error is present', () => {
      const { container } = render(
        <FormInput
          id="test-input"
          label="Message"
          maxLength={100}
          showCharacterCount
          error="This field is required"
        />
      );

      const label = container.querySelector('label');
      expect(label).toHaveClass('text-destructive');
    });
  });

  describe('Different Input Types', () => {
    it('should work with text input', () => {
      render(
        <FormInput
          id="test-input"
          type="text"
          maxLength={50}
          showCharacterCount
          defaultValue="Text"
        />
      );

      expect(screen.getByText('4 / 50')).toBeInTheDocument();
    });

    it('should work with email input', () => {
      render(
        <FormInput
          id="test-input"
          type="email"
          maxLength={100}
          showCharacterCount
          value="test@example.com"
          onChange={() => {}}
        />
      );

      // "test@example.com" is 16 characters
      expect(screen.getByText('16 / 100')).toBeInTheDocument();
    });

    it('should work with password input', () => {
      render(
        <FormInput
          id="test-input"
          type="password"
          maxLength={20}
          showCharacterCount
          defaultValue="password123"
        />
      );

      expect(screen.getByText('11 / 20')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty string correctly', () => {
      render(<FormInput id="test-input" maxLength={100} showCharacterCount defaultValue="" />);

      expect(screen.getByText('0 / 100')).toBeInTheDocument();
    });

    it('should handle very long text', () => {
      const longText = 'a'.repeat(500);
      render(
        <FormInput id="test-input" maxLength={1000} showCharacterCount defaultValue={longText} />
      );

      expect(screen.getByText('500 / 1000')).toBeInTheDocument();
    });

    it('should handle small maxLength values', () => {
      render(<FormInput id="test-input" maxLength={10} showCharacterCount defaultValue="Test" />);

      expect(screen.getByText('4 / 10')).toBeInTheDocument();
    });

    it('should handle maxLength of 1', () => {
      render(<FormInput id="test-input" maxLength={1} showCharacterCount defaultValue="A" />);

      expect(screen.getByText('1 / 1')).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('should maintain character count display on mobile', () => {
      render(
        <FormInput id="test-input" maxLength={100} showCharacterCount defaultValue="Mobile test" />
      );

      expect(screen.getByText('11 / 100')).toBeInTheDocument();
    });

    it('should apply full-width class on mobile', () => {
      const { container } = render(
        <FormInput id="test-input" maxLength={100} showCharacterCount />
      );

      const wrapper = container.querySelector('.w-full.md\\:w-auto');
      expect(wrapper).toBeInTheDocument();
    });
  });
});
