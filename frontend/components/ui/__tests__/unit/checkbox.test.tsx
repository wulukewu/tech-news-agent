import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { Checkbox } from '../../checkbox';

describe('Checkbox Component', () => {
  describe('Touch Target Size (Req 2.1)', () => {
    it('should have minimum 44x44px touch target', () => {
      render(<Checkbox data-testid="checkbox" />);
      const checkbox = screen.getByTestId('checkbox');
      expect(checkbox).toHaveClass('min-h-44');
      expect(checkbox).toHaveClass('min-w-44');
    });
  });

  describe('Focus Indicators (Req 15.3)', () => {
    it('should have visible focus ring classes', () => {
      render(<Checkbox data-testid="checkbox" />);
      const checkbox = screen.getByTestId('checkbox');
      expect(checkbox).toHaveClass('focus-visible:ring-2');
      expect(checkbox).toHaveClass('focus-visible:ring-primary');
    });
  });

  describe('Keyboard Navigation (Req 15.2)', () => {
    it('should toggle on Space key press', async () => {
      const user = userEvent.setup();
      const handleChange = vi.fn();
      render(<Checkbox data-testid="checkbox" onCheckedChange={handleChange} />);
      const checkbox = screen.getByTestId('checkbox');
      await user.tab();
      await user.keyboard(' ');
      expect(handleChange).toHaveBeenCalledWith(true);
    });
  });
});
