'use client';

import { lazy, Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy load the OnboardingModal component
const OnboardingModal = lazy(() =>
  import('./OnboardingModal').then((mod) => ({ default: mod.OnboardingModal }))
);

/**
 * Loading skeleton for OnboardingModal
 */
function OnboardingModalSkeleton() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-2xl p-6 bg-card rounded-lg shadow-lg">
        <Skeleton className="h-8 w-3/4 mb-4" />
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-5/6 mb-6" />
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-24" />
        </div>
      </div>
    </div>
  );
}

/**
 * Lazy-loaded OnboardingModal with Suspense boundary
 *
 * Requirements: 15.1, 15.4
 */
export function LazyOnboardingModal(props: any) {
  return (
    <Suspense fallback={<OnboardingModalSkeleton />}>
      <OnboardingModal {...props} />
    </Suspense>
  );
}
