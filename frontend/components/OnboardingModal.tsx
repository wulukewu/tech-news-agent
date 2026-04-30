'use client';
import { logger } from '@/lib/utils/logger';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Loader2, CheckCircle2, Sparkles } from 'lucide-react';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';

/**
 * OnboardingModal Component
 *
 * Displays a multi-step onboarding flow for new users:
 * 1. Welcome - Platform introduction
 * 2. Recommendations - Feed selection
 * 3. Complete - Success message
 *
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.6
 */

// TypeScript interfaces
export interface RecommendedFeed {
  id: string;
  name: string;
  url: string;
  category: string;
  description: string | null;
  is_recommended: boolean;
  recommendation_priority: number;
  is_subscribed: boolean;
}

export interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

interface OnboardingModalState {
  currentStep: 'welcome' | 'recommendations' | 'complete';
  selectedFeeds: string[];
  isLoading: boolean;
  recommendedFeeds: RecommendedFeed[];
  groupedFeeds: Record<string, RecommendedFeed[]>;
}

export function OnboardingModal({ isOpen, onClose, onComplete }: OnboardingModalProps) {
  const { t } = useI18n();
  const [state, setState] = useState<OnboardingModalState>({
    currentStep: 'welcome',
    selectedFeeds: [],
    isLoading: false,
    recommendedFeeds: [],
    groupedFeeds: {},
  });

  // Fetch recommended feeds when modal opens
  useEffect(() => {
    if (isOpen && state.currentStep === 'welcome') {
      fetchRecommendedFeeds();
    }
  }, [isOpen]);

  const fetchRecommendedFeeds = async () => {
    try {
      const response = await fetch('/api/feeds/recommended', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch recommended feeds');
      }

      const data = await response.json();

      // Pre-select 3-5 popular feeds (highest priority)
      const topFeeds = data.feeds.slice(0, 5).map((feed: RecommendedFeed) => feed.id);

      setState((prev) => ({
        ...prev,
        recommendedFeeds: data.feeds,
        groupedFeeds: data.grouped_by_category,
        selectedFeeds: topFeeds,
      }));
    } catch (error) {
      console.error('Error fetching recommended feeds:', error);
      toast.error(t('errors.onboarding-load-failed'));
    }
  };

  const handleStart = () => {
    setState((prev) => ({ ...prev, currentStep: 'recommendations' }));

    // Log analytics event
    fetch('/api/analytics/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        event_type: 'onboarding_started',
        event_data: { source: 'web' },
      }),
    }).catch(console.error);
  };

  const handleSkip = async () => {
    try {
      await fetch('/api/onboarding/skip', {
        method: 'POST',
        credentials: 'include',
      });

      // Log analytics event
      fetch('/api/analytics/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'onboarding_skipped',
          event_data: { step: state.currentStep },
        }),
      }).catch(console.error);

      onClose();
    } catch (error) {
      console.error('Error skipping onboarding:', error);
      onClose();
    }
  };

  const handleFeedSelection = (feedId: string) => {
    setState((prev) => ({
      ...prev,
      selectedFeeds: prev.selectedFeeds.includes(feedId)
        ? prev.selectedFeeds.filter((id) => id !== feedId)
        : [...prev.selectedFeeds, feedId],
    }));
  };

  const handleComplete = async () => {
    if (state.selectedFeeds.length === 0) {
      toast.error(t('errors.onboarding-select-required'));
      return;
    }

    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      // Subscribe to selected feeds
      const subscribeResponse = await fetch('/api/subscriptions/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ feed_ids: state.selectedFeeds }),
      });

      if (!subscribeResponse.ok) {
        throw new Error('Failed to subscribe to feeds');
      }

      const subscribeData = await subscribeResponse.json();

      // Mark onboarding as completed
      await fetch('/api/onboarding/complete', {
        method: 'POST',
        credentials: 'include',
      });

      // Log analytics event
      fetch('/api/analytics/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          event_type: 'onboarding_finished',
          event_data: {
            feeds_selected: state.selectedFeeds.length,
            feeds_subscribed: subscribeData.subscribed_count,
          },
        }),
      }).catch(console.error);

      setState((prev) => ({
        ...prev,
        currentStep: 'complete',
        isLoading: false,
      }));

      // Auto-close after showing success
      setTimeout(() => {
        onComplete();
        onClose();
      }, 2000);
    } catch (error) {
      console.error('Error completing onboarding:', error);
      toast.error(t('errors.onboarding-subscribe-failed'));
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] animate-in fade-in zoom-in-95 duration-500">
        {state.currentStep === 'welcome' && (
          <>
            <DialogHeader>
              <div className="flex items-center justify-center mb-4 animate-in zoom-in-50 duration-1000 delay-200">
                <div className="relative">
                  <Sparkles className="h-12 w-12 text-primary animate-pulse" />
                  <div className="absolute inset-0 h-12 w-12 text-primary/20 animate-ping">
                    <Sparkles className="h-12 w-12" />
                  </div>
                </div>
              </div>
              <DialogTitle className="text-2xl text-center animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-400">
                {t('onboarding.welcome-title')}
              </DialogTitle>
              <DialogDescription className="text-center text-base mt-4 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-600">
                {t('onboarding.welcome-description')}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 my-6">
              {[
                t('onboarding.feature-1'),
                t('onboarding.feature-2'),
                t('onboarding.feature-3'),
              ].map((feature, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 animate-in slide-in-from-left-4 duration-500"
                  style={{ animationDelay: `${800 + index * 200}ms` }}
                >
                  <CheckCircle2
                    className="h-5 w-5 text-primary mt-0.5 flex-shrink-0 animate-in zoom-in-50 duration-300"
                    style={{ animationDelay: `${900 + index * 200}ms` }}
                  />
                  <p className="text-sm">{feature}</p>
                </div>
              ))}
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-1400">
              <Button
                variant="outline"
                onClick={handleSkip}
                className="w-full sm:w-auto transition-all duration-300 hover:scale-[1.02]"
              >
                {t('onboarding.skip')}
              </Button>
              <Button
                onClick={handleStart}
                className="w-full sm:w-auto transition-all duration-300 hover:scale-[1.02] hover:shadow-md"
              >
                {t('onboarding.get-started')}
              </Button>
            </DialogFooter>
          </>
        )}

        {state.currentStep === 'recommendations' && (
          <>
            <DialogHeader className="animate-in fade-in slide-in-from-top-4 duration-500">
              <DialogTitle>{t('onboarding.select-sources')}</DialogTitle>
              <DialogDescription>{t('onboarding.select-sources-description')}</DialogDescription>
            </DialogHeader>
            <div className="max-h-[400px] overflow-y-auto space-y-4 my-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-200">
              {Object.entries(state.groupedFeeds).map(([category, feeds], categoryIndex) => (
                <div
                  key={category}
                  className="space-y-2 animate-in slide-in-from-left-4 duration-500"
                  style={{ animationDelay: `${300 + categoryIndex * 100}ms` }}
                >
                  <h3 className="font-semibold text-sm text-muted-foreground">{category}</h3>
                  <div className="space-y-2">
                    {feeds.map((feed, feedIndex) => (
                      <div
                        key={feed.id}
                        className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-accent transition-all duration-300 cursor-pointer hover:scale-[1.02] hover:shadow-sm animate-in slide-in-from-right-2 duration-300"
                        style={{
                          animationDelay: `${400 + categoryIndex * 100 + feedIndex * 50}ms`,
                        }}
                        onClick={() => handleFeedSelection(feed.id)}
                      >
                        <Checkbox
                          id={feed.id}
                          checked={state.selectedFeeds.includes(feed.id)}
                          onCheckedChange={() => handleFeedSelection(feed.id)}
                          className="mt-1 transition-transform duration-300 hover:scale-[1.05]"
                        />
                        <div className="flex-1 space-y-1">
                          <Label
                            htmlFor={feed.id}
                            className="text-sm font-medium leading-none cursor-pointer transition-colors duration-200 hover:text-primary"
                          >
                            {feed.name}
                          </Label>
                          {feed.description && (
                            <p className="text-xs text-muted-foreground">{feed.description}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-600">
              <Button
                variant="outline"
                onClick={handleSkip}
                className="w-full sm:w-auto transition-all duration-300 hover:scale-[1.02]"
              >
                {t('onboarding.skip')}
              </Button>
              <Button
                onClick={handleComplete}
                disabled={state.isLoading || state.selectedFeeds.length === 0}
                className="w-full sm:w-auto transition-all duration-300 hover:scale-[1.02] hover:shadow-md disabled:hover:scale-100"
              >
                {state.isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t('onboarding.subscribing')}
                  </>
                ) : (
                  t('onboarding.confirm-subscribe', { count: state.selectedFeeds.length })
                )}
              </Button>
            </DialogFooter>
          </>
        )}

        {state.currentStep === 'complete' && (
          <>
            <DialogHeader>
              <div className="flex items-center justify-center mb-4 animate-in zoom-in-50 duration-1000">
                <div className="relative">
                  <CheckCircle2 className="h-16 w-16 text-green-500 animate-pulse" />
                  <div className="absolute inset-0 h-16 w-16 text-green-500/20 animate-ping">
                    <CheckCircle2 className="h-16 w-16" />
                  </div>
                </div>
              </div>
              <DialogTitle className="text-2xl text-center animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300">
                {t('onboarding.setup-complete')}
              </DialogTitle>
              <DialogDescription className="text-center text-base mt-4 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500">
                {t('onboarding.subscribed-sources', { count: state.selectedFeeds.length })}
                <br />
                {t('onboarding.system-will-fetch')}
              </DialogDescription>
            </DialogHeader>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
