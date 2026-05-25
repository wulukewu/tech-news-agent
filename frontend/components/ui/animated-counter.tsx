'use client';

import { useEffect, useRef, useState } from 'react';

export interface AnimatedCounterProps {
  value: number;
  duration?: number; // duration in ms, default is 800ms
  decimals?: number; // decimal places, default is 0
  prefix?: string;
  suffix?: string;
  className?: string;
}

const easeOutCubic = (t: number): number => 1 - Math.pow(1 - t, 3);

export function AnimatedCounter({
  value,
  duration = 800,
  decimals = 0,
  prefix = '',
  suffix = '',
  className = '',
}: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(value);
  const startValueRef = useRef(value);
  const targetValueRef = useRef(value);
  const startTimeRef = useRef<number | null>(null);

  // Sync target value changes and animate smoothly
  useEffect(() => {
    startValueRef.current = displayValue;
    targetValueRef.current = value;
    startTimeRef.current = null; // Reset animation timeline

    let animationFrameId: number;

    const animate = (timestamp: number) => {
      if (startTimeRef.current === null) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutCubic(progress);

      const currentValue =
        startValueRef.current + (targetValueRef.current - startValueRef.current) * easedProgress;

      setDisplayValue(currentValue);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        setDisplayValue(targetValueRef.current);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [value, duration]);

  const formatted = displayValue.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  return (
    <span className={`tabular-nums ${className}`} aria-live="polite">
      {prefix}
      {formatted}
      {suffix}
    </span>
  );
}
