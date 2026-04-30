import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

/**
 * Enhanced Skeleton with Shimmer Animation
 * Provides shimmer effect using gradient animation for better perceived performance
 * Requirements: 12.2, 12.6
 */
function ShimmerSkeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-md bg-muted',
        'bg-gradient-to-r from-muted via-muted-foreground/10 to-muted',
        'bg-[length:200%_100%] animate-shimmer',
        className
      )}
      {...props}
    />
  );
}

/**
 * Article Card Skeleton - Mobile Layout
 * Matches the vertical layout structure of ArticleCard component
 * Requirements: 12.1, 12.6
 */
export function ArticleCardSkeletonMobile() {
  return (
    <article>
      <Card className="overflow-hidden animate-in fade-in-50 duration-700">
        <CardContent className="p-0">
          <div className="flex flex-col gap-3">
            <ShimmerSkeleton className="w-full aspect-video rounded-t-lg" />
            <div className="px-4 pb-4 flex flex-col gap-3">
              <div className="space-y-2">
                <ShimmerSkeleton className="h-6 w-full" />
                <ShimmerSkeleton className="h-6 w-3/4" />
              </div>
              <div className="flex items-center gap-2">
                <ShimmerSkeleton className="h-4 w-20" />
                <ShimmerSkeleton className="h-5 w-16 rounded-full" />
                <ShimmerSkeleton className="h-4 w-24" />
              </div>
              <div className="flex items-center gap-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <ShimmerSkeleton key={i} className="h-5 w-5 rounded-sm" />
                ))}
              </div>
              <div className="space-y-2">
                <ShimmerSkeleton className="h-4 w-full" />
                <ShimmerSkeleton className="h-4 w-2/3" />
              </div>
              <div className="flex gap-2">
                <ShimmerSkeleton className="h-11 flex-1 rounded-md" />
                <ShimmerSkeleton className="h-11 flex-1 rounded-md" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </article>
  );
}

/**
 * Article Card Skeleton - Desktop Layout
 * Matches the horizontal layout structure of ArticleCard component
 * Requirements: 12.1, 12.6
 */
export function ArticleCardSkeletonDesktop() {
  return (
    <article>
      <Card className="overflow-hidden">
        <CardContent className="p-0">
          <div className="flex gap-4">
            {/* Image skeleton - left side (200x150) */}
            <ShimmerSkeleton className="w-48 h-32 flex-shrink-0 rounded-l-lg" />

            {/* Content skeleton - right side */}
            <div className="flex flex-1 flex-col gap-2 py-4 pr-4">
              {/* Title and share button row */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 space-y-2">
                  <ShimmerSkeleton className="h-6 w-full" />
                  <ShimmerSkeleton className="h-6 w-4/5" />
                  <ShimmerSkeleton className="h-6 w-2/3" />
                </div>
                <ShimmerSkeleton className="h-11 w-11 rounded-md flex-shrink-0" />
              </div>

              {/* Metadata row skeleton */}
              <div className="flex items-center gap-3">
                <ShimmerSkeleton className="h-4 w-20" />
                <ShimmerSkeleton className="h-5 w-16 rounded-full" />
                <ShimmerSkeleton className="h-4 w-24" />
              </div>

              {/* Tinkering index stars skeleton */}
              <div className="flex items-center gap-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <ShimmerSkeleton key={i} className="h-5 w-5 rounded-sm" />
                ))}
              </div>

              {/* Summary skeleton */}
              <div className="space-y-2 flex-1">
                <ShimmerSkeleton className="h-4 w-full" />
                <ShimmerSkeleton className="h-4 w-3/4" />
              </div>

              {/* Action buttons skeleton */}
              <div className="flex gap-2">
                <ShimmerSkeleton className="h-9 w-24 rounded-md" />
                <ShimmerSkeleton className="h-9 w-28 rounded-md" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </article>
  );
}

/**
 * Article Grid Skeleton
 * Responsive grid that matches the dashboard layout
 * Requirements: 12.1, 12.3
 */
export function ArticleGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="md:hidden">
          <ArticleCardSkeletonMobile />
        </div>
      ))}
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="hidden md:block">
          <ArticleCardSkeletonDesktop />
        </div>
      ))}
    </div>
  );
}

/**
 * Feed List Skeleton
 * Matches the subscription page feed list structure
 * Requirements: 12.1, 12.6
 */
export function FeedListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 flex-1">
                {/* Health indicator */}
                <ShimmerSkeleton className="h-4 w-4 rounded-full" />

                {/* Feed info */}
                <div className="flex-1 space-y-2">
                  <ShimmerSkeleton className="h-5 w-48" />
                  <div className="flex items-center gap-2">
                    <ShimmerSkeleton className="h-4 w-16" />
                    <ShimmerSkeleton className="h-4 w-20" />
                  </div>
                </div>
              </div>

              {/* Toggle switch */}
              <ShimmerSkeleton className="h-6 w-11 rounded-full" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/**
 * Navigation Skeleton
 * Matches the navigation component structure
 * Requirements: 12.1, 12.6
 */
export function NavigationSkeleton() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
      <nav className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            {/* Logo skeleton */}
            <ShimmerSkeleton className="h-8 w-32" />

            {/* Desktop navigation items */}
            <div className="hidden md:flex gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <ShimmerSkeleton key={i} className="h-9 w-24 rounded-md" />
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* User avatar and name */}
            <div className="hidden md:flex items-center gap-2">
              <ShimmerSkeleton className="h-8 w-8 rounded-full" />
              <ShimmerSkeleton className="h-4 w-20" />
            </div>

            {/* Theme toggle */}
            <ShimmerSkeleton className="h-9 w-9 rounded-md" />

            {/* Logout button */}
            <ShimmerSkeleton className="h-9 w-20 rounded-md hidden md:block" />

            {/* Mobile menu button */}
            <ShimmerSkeleton className="h-9 w-9 rounded-md md:hidden" />
          </div>
        </div>
      </nav>
    </header>
  );
}

/**
 * Reading List Item Skeleton
 * Matches the reading list item structure
 * Requirements: 12.1, 12.6
 */
export function ReadingListItemSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Article info */}
          <div className="flex-1 space-y-3">
            {/* Title */}
            <div className="space-y-2">
              <ShimmerSkeleton className="h-6 w-full" />
              <ShimmerSkeleton className="h-6 w-3/4" />
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-2">
              <ShimmerSkeleton className="h-4 w-20" />
              <ShimmerSkeleton className="h-5 w-16 rounded-full" />
              <ShimmerSkeleton className="h-4 w-24" />
            </div>

            {/* Summary */}
            <div className="space-y-2">
              <ShimmerSkeleton className="h-4 w-full" />
              <ShimmerSkeleton className="h-4 w-2/3" />
            </div>
          </div>

          {/* Status and rating controls */}
          <div className="flex flex-col gap-3 md:w-48">
            {/* Status dropdown */}
            <ShimmerSkeleton className="h-9 w-full rounded-md" />

            {/* Rating stars */}
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <ShimmerSkeleton key={i} className="h-5 w-5 rounded-sm" />
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Reading List Skeleton
 * Complete reading list page skeleton
 * Requirements: 12.1, 12.3
 */
export function ReadingListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-6">
      {/* Status filter tabs skeleton */}
      <div className="flex gap-2 border-b">
        {Array.from({ length: 4 }).map((_, i) => (
          <ShimmerSkeleton key={i} className="h-10 w-20 rounded-t-md" />
        ))}
      </div>

      {/* Reading list items */}
      <div className="space-y-4">
        {Array.from({ length: count }).map((_, i) => (
          <ReadingListItemSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

export function LoadingScreen() {
  const { t } = useI18n();
  return (
    <div className="flex min-h-screen items-center justify-center animate-in fade-in-50 duration-500">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <div className="absolute inset-0 h-12 w-12 animate-ping rounded-full border-2 border-primary/20" />
        </div>
        <div className="text-center space-y-2 animate-in slide-in-from-bottom-2 duration-500 delay-300">
          <p className="text-lg font-medium">{t('ui.loading')}</p>
          <p className="text-sm text-muted-foreground animate-pulse">{t('ui.loading-preparing')}</p>
        </div>
      </div>
    </div>
  );
}

// Legacy components for backward compatibility
export function FeedGridSkeleton() {
  return <ArticleGridSkeleton count={6} />;
}

export function ArticleListSkeleton() {
  return <ReadingListSkeleton count={5} />;
}
