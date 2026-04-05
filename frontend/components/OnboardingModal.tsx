'use client';

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
import { toast } from 'sonner';

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

export function OnboardingModal({
  isOpen,
  onClose,
  onComplete,
}: OnboardingModalProps) {
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
      const topFeeds = data.feeds
        .slice(0, 5)
        .map((feed: RecommendedFeed) => feed.id);

      setState((prev) => ({
        ...prev,
        recommendedFeeds: data.feeds,
        groupedFeeds: data.grouped_by_category,
        selectedFeeds: topFeeds,
      }));
    } catch (error) {
      console.error('Error fetching recommended feeds:', error);
      toast.error('無法載入推薦來源');
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
      toast.error('請至少選擇一個訂閱來源');
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
      toast.error('訂閱失敗，請稍後再試');
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        {state.currentStep === 'welcome' && (
          <>
            <DialogHeader>
              <div className="flex items-center justify-center mb-4">
                <Sparkles className="h-12 w-12 text-primary" />
              </div>
              <DialogTitle className="text-2xl text-center">
                歡迎使用技術新聞訂閱工具！
              </DialogTitle>
              <DialogDescription className="text-center text-base mt-4">
                這個平台幫助你：
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 my-6">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <p className="text-sm">訂閱優質的技術 RSS 來源</p>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <p className="text-sm">每週自動抓取和分析文章</p>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <p className="text-sm">透過 AI 評分找到最值得閱讀的內容</p>
              </div>
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                variant="outline"
                onClick={handleSkip}
                className="w-full sm:w-auto"
              >
                稍後再說
              </Button>
              <Button onClick={handleStart} className="w-full sm:w-auto">
                開始使用
              </Button>
            </DialogFooter>
          </>
        )}

        {state.currentStep === 'recommendations' && (
          <>
            <DialogHeader>
              <DialogTitle>選擇你感興趣的來源</DialogTitle>
              <DialogDescription>
                我們已為你預選了一些熱門來源，你可以調整選擇
              </DialogDescription>
            </DialogHeader>
            <div className="max-h-[400px] overflow-y-auto space-y-4 my-4">
              {Object.entries(state.groupedFeeds).map(([category, feeds]) => (
                <div key={category} className="space-y-2">
                  <h3 className="font-semibold text-sm text-muted-foreground">
                    {category}
                  </h3>
                  <div className="space-y-2">
                    {feeds.map((feed) => (
                      <div
                        key={feed.id}
                        className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-accent transition-colors cursor-pointer"
                        onClick={() => handleFeedSelection(feed.id)}
                      >
                        <Checkbox
                          id={feed.id}
                          checked={state.selectedFeeds.includes(feed.id)}
                          onCheckedChange={() => handleFeedSelection(feed.id)}
                          className="mt-1"
                        />
                        <div className="flex-1 space-y-1">
                          <Label
                            htmlFor={feed.id}
                            className="text-sm font-medium leading-none cursor-pointer"
                          >
                            {feed.name}
                          </Label>
                          {feed.description && (
                            <p className="text-xs text-muted-foreground">
                              {feed.description}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                variant="outline"
                onClick={handleSkip}
                className="w-full sm:w-auto"
              >
                稍後再說
              </Button>
              <Button
                onClick={handleComplete}
                disabled={state.isLoading || state.selectedFeeds.length === 0}
                className="w-full sm:w-auto"
              >
                {state.isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    訂閱中...
                  </>
                ) : (
                  `確認訂閱 (${state.selectedFeeds.length})`
                )}
              </Button>
            </DialogFooter>
          </>
        )}

        {state.currentStep === 'complete' && (
          <>
            <DialogHeader>
              <div className="flex items-center justify-center mb-4">
                <CheckCircle2 className="h-16 w-16 text-green-500" />
              </div>
              <DialogTitle className="text-2xl text-center">
                設定完成！
              </DialogTitle>
              <DialogDescription className="text-center text-base mt-4">
                已成功訂閱 {state.selectedFeeds.length} 個來源
                <br />
                系統將開始為你抓取文章
              </DialogDescription>
            </DialogHeader>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
