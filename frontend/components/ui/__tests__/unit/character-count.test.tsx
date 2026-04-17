import { render, screen } from '@testing-library/react';
import { CharacterCount } from '../../character-count';

describe('CharacterCount', () => {
  describe('Display Format', () => {
    it('should display character count with label by default', () => {
      render(<CharacterCount current={10} max={100} />);
      expect(screen.getByText('10 / 100 characters')).toBeInTheDocument();
    });

    it('should display character count without label when showLabel is false', () => {
      render(<CharacterCount current={10} max={100} showLabel={false} />);
      expect(screen.getByText('10 / 100')).toBeInTheDocument();
      expect(screen.queryByText('characters')).not.toBeInTheDocument();
    });

    it('should display zero count correctly', () => {
      render(<CharacterCount current={0} max={100} />);
      expect(screen.getByText('0 / 100 characters')).toBeInTheDocument();
    });

    it('should display count at maximum correctly', () => {
      render(<CharacterCount current={100} max={100} />);
      expect(screen.getByText('100 / 100 characters')).toBeInTheDocument();
    });

    it('should display count over maximum correctly', () => {
      render(<CharacterCount current={105} max={100} />);
      expect(screen.getByText('105 / 100 characters')).toBeInTheDocument();
    });
  });

  describe('Color Coding - Default State', () => {
    it('should use muted color when below warning threshold', () => {
      const { container } = render(<CharacterCount current={50} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');
      expect(element).not.toHaveClass('text-yellow-600');
      expect(element).not.toHaveClass('text-destructive');
    });

    it('should use muted color at 79% (just below default 80% threshold)', () => {
      const { container } = render(<CharacterCount current={79} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');
    });

    it('should use muted color for very low usage', () => {
      const { container } = render(<CharacterCount current={5} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');
    });
  });

  describe('Color Coding - Warning State', () => {
    it('should use warning color at 80% threshold (default)', () => {
      const { container } = render(<CharacterCount current={80} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');
      expect(element).not.toHaveClass('text-muted-foreground');
      expect(element).not.toHaveClass('text-destructive');
    });

    it('should use warning color at 90%', () => {
      const { container } = render(<CharacterCount current={90} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');
    });

    it('should use warning color at 99% (just below limit)', () => {
      const { container } = render(<CharacterCount current={99} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');
      expect(element).not.toHaveClass('text-destructive');
    });
  });

  describe('Color Coding - Error State', () => {
    it('should use destructive color at 100% (at limit)', () => {
      const { container } = render(<CharacterCount current={100} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-destructive');
      expect(element).not.toHaveClass('text-yellow-600');
      expect(element).not.toHaveClass('text-muted-foreground');
    });

    it('should use destructive color over limit', () => {
      const { container } = render(<CharacterCount current={105} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-destructive');
    });

    it('should use destructive color significantly over limit', () => {
      const { container } = render(<CharacterCount current={150} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-destructive');
    });
  });

  describe('Custom Warning Threshold', () => {
    it('should respect custom warning threshold of 90%', () => {
      const { container } = render(
        <CharacterCount current={85} max={100} warningThreshold={0.9} />
      );
      const element = container.querySelector('p');
      // 85% is below 90% threshold, should be muted
      expect(element).toHaveClass('text-muted-foreground');
    });

    it('should show warning at custom threshold of 90%', () => {
      const { container } = render(
        <CharacterCount current={90} max={100} warningThreshold={0.9} />
      );
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');
    });

    it('should respect custom warning threshold of 50%', () => {
      const { container } = render(
        <CharacterCount current={50} max={100} warningThreshold={0.5} />
      );
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');
    });

    it('should show muted below custom 50% threshold', () => {
      const { container } = render(
        <CharacterCount current={49} max={100} warningThreshold={0.5} />
      );
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');
    });
  });

  describe('Edge Cases', () => {
    it('should handle max of 0 gracefully', () => {
      const { container } = render(<CharacterCount current={0} max={0} />);
      expect(screen.getByText('0 / 0 characters')).toBeInTheDocument();
      const element = container.querySelector('p');
      // When max is 0, percentage is 0, should be muted
      expect(element).toHaveClass('text-muted-foreground');
    });

    it('should handle negative current value', () => {
      render(<CharacterCount current={-5} max={100} />);
      expect(screen.getByText('-5 / 100 characters')).toBeInTheDocument();
    });

    it('should handle very large numbers', () => {
      render(<CharacterCount current={9999} max={10000} />);
      expect(screen.getByText('9999 / 10000 characters')).toBeInTheDocument();
    });

    it('should handle small max values', () => {
      const { container } = render(<CharacterCount current={5} max={10} />);
      expect(screen.getByText('5 / 10 characters')).toBeInTheDocument();
      // 50% is below 80% threshold
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');
    });

    it('should show warning for small max values at threshold', () => {
      const { container } = render(<CharacterCount current={8} max={10} />);
      // 80% should trigger warning
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');
    });
  });

  describe('Accessibility', () => {
    it('should have aria-live="polite" for screen reader updates', () => {
      const { container } = render(<CharacterCount current={50} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveAttribute('aria-live', 'polite');
    });

    it('should have aria-atomic="true" for complete announcements', () => {
      const { container } = render(<CharacterCount current={50} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveAttribute('aria-atomic', 'true');
    });
  });

  describe('Styling', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <CharacterCount current={50} max={100} className="custom-class" />
      );
      const element = container.querySelector('p');
      expect(element).toHaveClass('custom-class');
    });

    it('should maintain base classes with custom className', () => {
      const { container } = render(
        <CharacterCount current={50} max={100} className="custom-class" />
      );
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-sm');
      expect(element).toHaveClass('transition-colors');
      expect(element).toHaveClass('custom-class');
    });

    it('should have transition-colors class for smooth color changes', () => {
      const { container } = render(<CharacterCount current={50} max={100} />);
      const element = container.querySelector('p');
      expect(element).toHaveClass('transition-colors');
      expect(element).toHaveClass('duration-200');
    });
  });

  describe('Real-time Updates', () => {
    it('should update display when current value changes', () => {
      const { rerender } = render(<CharacterCount current={10} max={100} />);
      expect(screen.getByText('10 / 100 characters')).toBeInTheDocument();

      rerender(<CharacterCount current={50} max={100} />);
      expect(screen.getByText('50 / 100 characters')).toBeInTheDocument();
    });

    it('should update color when crossing warning threshold', () => {
      const { container, rerender } = render(<CharacterCount current={79} max={100} />);
      let element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');

      rerender(<CharacterCount current={80} max={100} />);
      element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');
    });

    it('should update color when crossing error threshold', () => {
      const { container, rerender } = render(<CharacterCount current={99} max={100} />);
      let element = container.querySelector('p');
      expect(element).toHaveClass('text-yellow-600');

      rerender(<CharacterCount current={100} max={100} />);
      element = container.querySelector('p');
      expect(element).toHaveClass('text-destructive');
    });

    it('should update color when going back below thresholds', () => {
      const { container, rerender } = render(<CharacterCount current={100} max={100} />);
      let element = container.querySelector('p');
      expect(element).toHaveClass('text-destructive');

      rerender(<CharacterCount current={79} max={100} />);
      element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');
    });
  });

  describe('Integration Scenarios', () => {
    it('should work with typical form input scenario', () => {
      const { container } = render(
        <div>
          <input type="text" maxLength={100} />
          <CharacterCount current={25} max={100} />
        </div>
      );
      expect(screen.getByText('25 / 100 characters')).toBeInTheDocument();
      const element = container.querySelector('p');
      expect(element).toHaveClass('text-muted-foreground');
    });

    it('should work with textarea scenario', () => {
      const { container } = render(
        <div>
          <textarea maxLength={500} />
          <CharacterCount current={450} max={500} showLabel={false} />
        </div>
      );
      expect(screen.getByText('450 / 500')).toBeInTheDocument();
      const element = container.querySelector('p');
      // 90% should show warning
      expect(element).toHaveClass('text-yellow-600');
    });
  });
});
