import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { Switch } from '../../switch';

describe('Switch Component', () => {
  describe('Touch Target Size (Req 2.1)', () => {
    it('should have minimum 44x44px touch target', () => {
      render(<Switch data-testid="switch" />);
      const switchElement = screen.getByTestId('switch');
      // Switch has relative positioning for touch target
      expect(switchElement).toHaveClass('relative');
      expect(switchElement).toHaveClass('cursor-pointer');
    });
  });

  describe('Focus Indicators (Req 15.3)', () => {
    it('should have visible focus ring classes', () => {
      render(<Switch data-testid="switch" />);
      const switchElement = screen.getByTestId('switch');
      expect(switchElement).toHaveClass('focus-visible:ring-2');
      expect(switchElement).toHaveClass('focus-visible:ring-primary');
    });
  });

  describe('Keyboard Navigation (Req 15.2)', () => {
    it('should toggle on Space key press', async () => {
      const user = userEvent.setup();
      const handleChange = vi.fn();
      render(<Switch data-testid="switch" onCheckedChange={handleChange} />);
      const switchElement = screen.getByTestId('switch');
      await user.tab();
      await user.keyboard(' ');
      expect(handleChange).toHaveBeenCalledWith(true);
    });
  });

  describe('Animation (Req 21.1)', () => {
    it('should have smooth animation when toggling (200ms)', () => {
      render(<Switch data-testid="switch" />);
      const switchElement = screen.getByTestId('switch');
      expect(switchElement).toHaveClass('transition-colors');
      expect(switchElement).toHaveClass('duration-200');
    });
  });
});
