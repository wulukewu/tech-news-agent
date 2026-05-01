'use client';

import { lazy, Suspense } from 'react';
import type { TooltipTourProps } from './TooltipTour';

// Lazy load the TooltipTour component
const TooltipTour = lazy(() =>
  import('./TooltipTour').then((mod) => ({ default: mod.TooltipTour }))
);

/**
 * Lazy-loaded TooltipTour with Suspense boundary
 *
 * Requirements: 15.1, 15.4
 */
export function LazyTooltipTour(props: TooltipTourProps) {
  return (
    <Suspense fallback={null}>
      <TooltipTour {...props} />
    </Suspense>
  );
}
