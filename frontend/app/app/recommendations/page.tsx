/**
 * Recommendations Page
 *
 * Displays personalized article recommendations based on user ratings
 *
 * Validates: Requirements 3.1-3.10
 */

'use client';

import React, { useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { RefreshCw, Sparkles } from 'lucide-react';
import { RecommendationCard } from '@/features/recommendations/components/RecommendationCard';
import { InsufficientDataMessage } from '@/features/recommendations/components/InsufficientDataMessage';
import { useI18n } from '@/contexts/I18nContext';
import { ArticleListSkeleton } from '@/components/LoadingSkeleton';
import {
  useRecommendations,
  useRefreshRecommendations,
  useDismissRecommendation,
  useTrackRecommendationInteraction,
} from '@/features/recommendations/hooks/useRecommendations';
import { toast } from '@/lib/toast';

/**
 * RecommendationsPage component
 *
 * **Validates: Requirement 3.1**
 * - Provides a dedicated recommendations page at "/recommendations"
 */
export default function RecommendationsPage() {
  const { data, isLoading, error } = useRecommendations();
  const refreshMutation = useRefreshRecommendations();
  const dismissMutation = useDismissRecommendation();
  const trackInteraction = useTrackRecommendationInteraction();
  const { t } = useI18n();

  // Track page view
  useEffect(() => {
    if (data?.recommendations) {
      data.recommendations.forEach((rec) => {
        trackInteraction.mutate({
          recommendationId: rec.id,
          type: 'view',
          timestamp: new Date().toISOString(),
        });
      });
    }
  }, [data?.recommendations]);

  /**
   * Handle refresh recommendations
   *
   * **Validates: Requirement 3.5**
   * - Provides "Refresh Recommendations" button to generate new suggestions
   */
  const handleRefresh = useCallback(() => {
    refreshMutation.mutate(
      {},
      {
        onSuccess: () => {
          toast.success(t('recommendations.updated'));
        },
        onError: (error) => {
          toast.error(t('recommendations.update-failed'));
        },
      }
    );
  }, [refreshMutation, t]);

  /**
   * Handle dismiss recommendation
   *
   * **Validates: Requirement 3.7**
   * - Allows users to dismiss recommendations they're not interested in
   */
  const handleDismiss = useCallback(
    (recommendationId: string) => {
      // Track dismiss interaction
      trackInteraction.mutate({
        recommendationId,
        type: 'dismiss',
        timestamp: new Date().toISOString(),
      });

      dismissMutation.mutate(
        { recommendationId },
        {
          onSuccess: () => {
            toast.success(t('recommendations.dismissed'));
          },
          onError: (error) => {
            toast.error(t('recommendations.operation-failed'));
          },
        }
      );
    },
    [dismissMutation, trackInteraction, t]
  );

  /**
   * Handle recommendation click
   *
   * **Validates: Requirement 3.8**
   * - Tracks recommendation click-through rates for improvement
   */
  const handleClick = useCallback(
    (recommendationId: string) => {
      trackInteraction.mutate({
        recommendationId,
        type: 'click',
        timestamp: new Date().toISOString(),
      });
    },
    [trackInteraction]
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">智慧推薦</h1>
            <p className="text-muted-foreground">基於您的評分歷史的個人化文章推薦</p>
          </div>
        </div>
        <ArticleListSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">智慧推薦</h1>
            <p className="text-muted-foreground">基於您的評分歷史的個人化文章推薦</p>
          </div>
        </div>
        <div className="rounded-lg border bg-destructive/10 p-6 text-center">
          <p className="text-destructive">載入推薦時發生錯誤</p>
          <Button onClick={() => window.location.reload()} className="mt-4">
            {t('buttons.reload-page')}
          </Button>
        </div>
      </div>
    );
  }

  /**
   * **Validates: Requirement 3.6**
   * - Displays message when insufficient rating data exists (less than 3 rated articles)
   */
  if (!data?.hasSufficientData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">智慧推薦</h1>
            <p className="text-muted-foreground">基於您的評分歷史的個人化文章推薦</p>
          </div>
        </div>
        <InsufficientDataMessage
          userRatingCount={data?.userRatingCount || 0}
          minRatingsRequired={data?.minRatingsRequired || 3}
        />
      </div>
    );
  }

  /**
   * **Validates: Requirement 3.9**
   * - Suggests rating more articles when no recommendations are available
   */
  if (!data?.recommendations || data.recommendations.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('recommendations.title')}</h1>
            <p className="text-muted-foreground">{t('recommendations.description')}</p>
          </div>
          <Button onClick={handleRefresh} disabled={refreshMutation.isPending} className="gap-2">
            <RefreshCw className={`h-4 w-4 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
            {t('recommendations.refresh')}
          </Button>
        </div>
        <div className="rounded-lg border bg-card p-6 text-center">
          <Sparkles className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">{t('recommendations.no-recommendations')}</h3>
          <p className="text-muted-foreground mb-4">{t('recommendations.rate-more-articles')}</p>
          <Button asChild>
            <a href="/articles">{t('recommendations.go-to-articles')}</a>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('recommendations.title')}</h1>
          <p className="text-muted-foreground">
            {t('recommendations.description-with-count', { count: data.totalCount })}
          </p>
        </div>
        <Button onClick={handleRefresh} disabled={refreshMutation.isPending} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
          {t('recommendations.refresh-recommendations')}
        </Button>
      </div>

      {/* Recommendations Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {data.recommendations.map((recommendation) => (
          <RecommendationCard
            key={recommendation.id}
            recommendation={recommendation}
            onDismiss={handleDismiss}
            onClick={handleClick}
          />
        ))}
      </div>
    </div>
  );
}
