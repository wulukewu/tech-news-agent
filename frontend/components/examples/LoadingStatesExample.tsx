/**
 * Loading States Example
 *
 * Demonstrates all the loading state components implemented for task 15
 * This file serves as both documentation and testing for the loading components
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ArticleGridSkeleton,
  FeedListSkeleton,
  ReadingListSkeleton,
  NavigationSkeleton,
} from '@/components/LoadingSkeleton';
import {
  InfiniteScrollSpinner,
  InitialPageSkeleton,
  ComponentLoadingOverlay,
  CardLoadingOverlay,
} from '@/components/ui/loading-indicators';
import {
  LoadingAnnouncement,
  ArticleLoadingAnnouncer,
  SearchLoadingAnnouncer,
} from '@/components/ui/loading-announcements';
import {
  FadeInContent,
  SlideUpContent,
  ScaleInContent,
  ContentTransition,
} from '@/components/ui/content-transitions';

export function LoadingStatesExample() {
  const [isLoading, setIsLoading] = useState(false);
  const [showSkeletons, setShowSkeletons] = useState(true);
  const [transitionType, setTransitionType] = useState<'fade' | 'slide-up' | 'scale'>('fade');

  const simulateLoading = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 2000);
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Loading States Demo</h1>
        <p className="text-muted-foreground">
          Demonstration of all loading state components with shimmer animations and smooth
          transitions
        </p>

        <div className="flex gap-4 justify-center">
          <Button onClick={() => setShowSkeletons(!showSkeletons)}>
            {showSkeletons ? 'Hide' : 'Show'} Skeletons
          </Button>
          <Button onClick={simulateLoading} disabled={isLoading}>
            {isLoading ? 'Loading...' : 'Test Loading'}
          </Button>
        </div>
      </div>

      {/* Skeleton Components Section */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Skeleton Components</h2>

        {showSkeletons && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Navigation Skeleton</CardTitle>
              </CardHeader>
              <CardContent>
                <NavigationSkeleton />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Article Grid Skeleton</CardTitle>
              </CardHeader>
              <CardContent>
                <ArticleGridSkeleton count={3} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Feed List Skeleton</CardTitle>
              </CardHeader>
              <CardContent>
                <FeedListSkeleton count={3} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Reading List Skeleton</CardTitle>
              </CardHeader>
              <CardContent>
                <ReadingListSkeleton count={2} />
              </CardContent>
            </Card>
          </>
        )}
      </section>

      {/* Loading Indicators Section */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Loading Indicators</h2>

        <Card>
          <CardHeader>
            <CardTitle>Infinite Scroll Spinner</CardTitle>
          </CardHeader>
          <CardContent>
            <InfiniteScrollSpinner text="Loading more articles..." />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Card Loading Overlay</CardTitle>
          </CardHeader>
          <CardContent>
            <CardLoadingOverlay isLoading={isLoading}>
              <div className="p-8 bg-muted rounded-lg">
                <p>This content has a loading overlay when isLoading is true</p>
              </div>
            </CardLoadingOverlay>
          </CardContent>
        </Card>
      </section>

      {/* Content Transitions Section */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Content Transitions</h2>

        <div className="flex gap-2 mb-4">
          <Button
            variant={transitionType === 'fade' ? 'default' : 'outline'}
            onClick={() => setTransitionType('fade')}
          >
            Fade
          </Button>
          <Button
            variant={transitionType === 'slide-up' ? 'default' : 'outline'}
            onClick={() => setTransitionType('slide-up')}
          >
            Slide Up
          </Button>
          <Button
            variant={transitionType === 'scale' ? 'default' : 'outline'}
            onClick={() => setTransitionType('scale')}
          >
            Scale
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Content Transition Demo</CardTitle>
          </CardHeader>
          <CardContent>
            <ContentTransition
              type={transitionType}
              isLoading={isLoading}
              fallback={
                <div className="p-8 bg-muted rounded-lg animate-pulse">Loading content...</div>
              }
            >
              <div className="p-8 bg-primary/10 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Content Loaded!</h3>
                <p>This content fades in smoothly when loading completes.</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Transition type: {transitionType}
                </p>
              </div>
            </ContentTransition>
          </CardContent>
        </Card>
      </section>

      {/* Accessibility Features */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Accessibility Features</h2>

        <Card>
          <CardHeader>
            <CardTitle>Screen Reader Announcements</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4">
              These components announce loading states to screen readers (check with screen reader
              enabled):
            </p>

            <LoadingAnnouncement
              isLoading={isLoading}
              loadingMessage="Loading example content"
              completedMessage="Example content loaded successfully"
            />

            <ArticleLoadingAnnouncer isLoading={isLoading} count={5} />

            <SearchLoadingAnnouncer isLoading={isLoading} query="example search" resultCount={10} />
          </CardContent>
        </Card>
      </section>

      {/* Initial Page Skeleton Demo */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold">Initial Page Skeleton</h2>

        <Card>
          <CardHeader>
            <CardTitle>Dashboard Page Skeleton</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden">
              <InitialPageSkeleton type="dashboard" showNavigation={false} />
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
