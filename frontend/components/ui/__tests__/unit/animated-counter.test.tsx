import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AnimatedCounter } from '../../animated-counter';

describe('AnimatedCounter Component', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('renders initial formatted value correctly', () => {
    render(<AnimatedCounter value={100} />);
    const counter = screen.getByText('100');
    expect(counter).toBeInTheDocument();
  });

  it('renders with prefix and suffix', () => {
    render(<AnimatedCounter value={42} prefix="$" suffix=" USD" />);
    const counter = screen.getByText('$42 USD');
    expect(counter).toBeInTheDocument();
  });

  it('respects decimal places', () => {
    render(<AnimatedCounter value={98.76} decimals={1} />);
    const counter = screen.getByText('98.8');
    expect(counter).toBeInTheDocument();
  });

  it('animates smoothly on value update', () => {
    let mockTime = 1000;

    // Custom robust requestAnimationFrame mock to pass explicit timestamps
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
      setTimeout(() => cb(mockTime), 0);
      return 1;
    });

    const { rerender } = render(<AnimatedCounter value={10} duration={100} />);
    expect(screen.getByText('10')).toBeInTheDocument();

    // Trigger update
    mockTime = 1000; // Animation start time
    rerender(<AnimatedCounter value={20} duration={100} />);

    // Baseline the first frame start time
    act(() => {
      vi.advanceTimersByTime(0);
    });

    // Advance to 50% progress
    act(() => {
      mockTime = 1050; // 50ms elapsed
      vi.advanceTimersByTime(50);
    });

    // Check intermediate value (e.g., 18 or 19 due to ease-out)
    const textAfterPartial = screen.getByText(/^[1-2]\d$/).textContent;
    expect(Number(textAfterPartial)).toBeGreaterThan(10);
    expect(Number(textAfterPartial)).toBeLessThan(20);

    // Complete the animation
    act(() => {
      mockTime = 1100; // 100ms elapsed
      vi.advanceTimersByTime(50);
    });

    expect(screen.getByText('20')).toBeInTheDocument();
  });
});
