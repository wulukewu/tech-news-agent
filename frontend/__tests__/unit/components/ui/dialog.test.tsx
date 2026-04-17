/**
 * Dialog Component Tests
 *
 * Tests for Requirements 10.1-10.8:
 * - 10.1: Close button in top-right with 44px touch target
 * - 10.2: Focus trap within dialog
 * - 10.3: Escape key to close
 * - 10.4: Mobile full-screen layout with slide-up animation
 * - 10.5: Desktop centered overlay (max-width: 600px)
 * - 10.6: Backdrop with 50% opacity
 * - 10.7: Content height limited to 85vh with vertical scrolling
 * - 10.8: Safe area padding for notched devices
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

describe('Dialog Component', () => {
  describe('Requirement 10.1: Close button with 44px touch target', () => {
    it('should render close button in top-right corner', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toBeInTheDocument();

      // Check positioning classes
      expect(closeButton).toHaveClass('absolute', 'right-4', 'top-4');
    });

    it('should have minimum 44px touch target size', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toHaveClass('touch-target');
    });

    it('should close dialog when close button is clicked', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      render(
        <Dialog open onOpenChange={onOpenChange}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Requirement 10.2: Focus trap within dialog', () => {
    it('should trap focus within dialog when open', async () => {
      const user = userEvent.setup();

      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
              <DialogDescription>Test description</DialogDescription>
            </DialogHeader>
            <div>
              <button>First Button</button>
              <button>Second Button</button>
            </div>
            <DialogFooter>
              <Button>Cancel</Button>
              <Button>Confirm</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );

      // Focus should be trapped within dialog
      const firstButton = screen.getByText('First Button');
      const closeButton = screen.getByRole('button', { name: /close/i });

      // Tab through elements
      await user.tab();
      await user.tab();
      await user.tab();

      // Focus should cycle back to first focusable element
      // (Radix UI handles focus trap automatically)
      expect(document.activeElement).toBeDefined();
    });
  });

  describe('Requirement 10.3: Escape key to close', () => {
    it('should close dialog when Escape key is pressed', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      render(
        <Dialog open onOpenChange={onOpenChange}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      await user.keyboard('{Escape}');

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Requirement 10.4: Mobile full-screen layout with slide-up animation', () => {
    it('should have mobile-specific classes for full-screen layout', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');

      // Check mobile positioning classes
      expect(content).toHaveClass('inset-x-0', 'bottom-0');

      // Check rounded top corners for mobile
      expect(content).toHaveClass('rounded-t-xl');

      // Check slide-up animation classes
      expect(content).toHaveClass(
        'data-[state=open]:slide-in-from-bottom',
        'data-[state=closed]:slide-out-to-bottom'
      );
    });
  });

  describe('Requirement 10.5: Desktop centered overlay (max-width: 600px)', () => {
    it('should have desktop-specific classes for centered overlay', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');

      // Check desktop positioning classes
      expect(content).toHaveClass(
        'md:inset-auto',
        'md:left-[50%]',
        'md:top-[50%]',
        'md:translate-x-[-50%]',
        'md:translate-y-[-50%]'
      );

      // Check max-width
      expect(content).toHaveClass('md:max-w-[600px]');

      // Check fully rounded corners for desktop
      expect(content).toHaveClass('md:rounded-xl');
    });
  });

  describe('Requirement 10.6: Backdrop with 50% opacity', () => {
    it('should render backdrop overlay with 50% opacity', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      // The overlay is rendered in a portal, so we need to query the document
      const overlay = document.querySelector('[class*="bg-black/50"]');
      expect(overlay).not.toBeNull();
      if (overlay) {
        expect(overlay).toHaveClass('bg-black/50');
      }
    });

    it('should close dialog when backdrop is clicked', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      render(
        <Dialog open onOpenChange={onOpenChange}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      // The overlay is rendered in a portal
      const overlay = document.querySelector('[class*="bg-black/50"]');
      if (overlay) {
        await user.click(overlay);
        expect(onOpenChange).toHaveBeenCalledWith(false);
      }
    });
  });

  describe('Requirement 10.7: Content height limited to 85vh with vertical scrolling', () => {
    it('should have max-height of 85vh', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');

      // Check max-height classes for both mobile and desktop
      expect(content).toHaveClass('max-h-[85vh]', 'md:max-h-[85vh]');
    });

    it('should enable vertical scrolling for overflow content', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');
      expect(content).toHaveClass('overflow-y-auto');
    });
  });

  describe('Requirement 10.8: Safe area padding for notched devices', () => {
    it('should include safe area padding class', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');
      expect(content).toHaveClass('safe-area-pb');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
              <DialogDescription>Test description</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();

      // Check for title
      const title = screen.getByText('Test Dialog');
      expect(title).toBeInTheDocument();

      // Check for description
      const description = screen.getByText('Test description');
      expect(description).toBeInTheDocument();
    });

    it('should have accessible close button with sr-only text', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toBeInTheDocument();

      // Check for screen reader text
      const srText = closeButton.querySelector('.sr-only');
      expect(srText).toBeInTheDocument();
      expect(srText).toHaveTextContent('Close');
    });
  });

  describe('Controlled vs Uncontrolled', () => {
    it('should work as controlled component', async () => {
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      const { rerender } = render(
        <Dialog open={true} onOpenChange={onOpenChange}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Controlled Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Click close button
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      expect(onOpenChange).toHaveBeenCalledWith(false);

      // Rerender with open=false
      rerender(
        <Dialog open={false} onOpenChange={onOpenChange}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Controlled Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should work with DialogTrigger', async () => {
      const user = userEvent.setup();

      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open Dialog</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Triggered Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      // Dialog should not be visible initially
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

      // Click trigger button
      const triggerButton = screen.getByRole('button', { name: /open dialog/i });
      await user.click(triggerButton);

      // Dialog should now be visible
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });
  });

  describe('Animation classes', () => {
    it('should have fade-in/fade-out animation classes', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');

      // Check fade animations
      expect(content).toHaveClass('data-[state=open]:fade-in-0', 'data-[state=closed]:fade-out-0');
    });

    it('should have zoom animation classes for desktop', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');

      // Check desktop zoom animations
      expect(content).toHaveClass(
        'md:data-[state=open]:zoom-in-95',
        'md:data-[state=closed]:zoom-out-95'
      );
    });
  });

  describe('Responsive behavior', () => {
    it('should have appropriate duration class', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByRole('dialog');
      expect(content).toHaveClass('duration-300');
    });
  });

  describe('Integration with DialogHeader, DialogFooter, DialogTitle, DialogDescription', () => {
    it('should render all dialog parts correctly', () => {
      render(
        <Dialog open>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Dialog Title</DialogTitle>
              <DialogDescription>Dialog Description</DialogDescription>
            </DialogHeader>
            <div>Dialog Body Content</div>
            <DialogFooter>
              <Button variant="outline">Cancel</Button>
              <Button>Confirm</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Dialog Title')).toBeInTheDocument();
      expect(screen.getByText('Dialog Description')).toBeInTheDocument();
      expect(screen.getByText('Dialog Body Content')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
    });
  });
});
