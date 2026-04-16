/**
 * AI Analysis hooks
 *
 * Custom React hooks for managing AI analysis state,
 * API calls, and user interactions.
 */

import React, { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { queryKeys } from '@/lib/api/queries';
import { cacheStrategies } from '@/lib/cache';
import {
  generateAnalysis,
  getCachedAnalysis,
  copyAnalysisToClipboard,
  formatAnalysisForSharing,
} from '../services';
import type { AnalysisResult, AnalysisProgress } from '../types';

/**
 * Hook for managing AI analysis data and operations
 *
 * @param articleId - The article ID to analyze
 * @returns Analysis query, mutation, and utility functions
 */
export function useAnalysis(articleId: string) {
  const queryClient = useQueryClient();

  // Query for cached analysis
  const analysisQuery = useQuery({
    queryKey: queryKeys.articles.analysis(articleId),
    queryFn: () => getCachedAnalysis(articleId),
    ...cacheStrategies.aiAnalysis,
    enabled: !!articleId,
  });

  // Mutation for generating new analysis
  const generateMutation = useMutation({
    mutationFn: () => generateAnalysis(articleId),
    onSuccess: (data) => {
      // Update cache with new analysis
      queryClient.setQueryData(queryKeys.articles.analysis(articleId), data);
      toast.success('分析完成！');
    },
    onError: (error: Error) => {
      toast.error(`分析失敗：${error.message}`);
    },
  });

  return {
    // Data
    analysis: analysisQuery.data,
    isLoading: analysisQuery.isLoading,
    isGenerating: generateMutation.isPending,
    error: analysisQuery.error || generateMutation.error,

    // Actions
    generateAnalysis: generateMutation.mutate,
    refetch: analysisQuery.refetch,
  };
}

/**
 * Hook for managing analysis modal state and interactions
 *
 * @param articleId - The article ID
 * @param articleTitle - The article title
 * @returns Modal state and interaction handlers
 */
export function useAnalysisModal(articleId: string, articleTitle: string) {
  const [isOpen, setIsOpen] = useState(false);
  const [progress, setProgress] = useState<AnalysisProgress>({
    progress: 0,
    status: '準備分析...',
    isComplete: false,
    hasError: false,
  });

  const { analysis, isLoading, isGenerating, generateAnalysis } = useAnalysis(articleId);

  // Open modal and start analysis if needed
  const openModal = useCallback(() => {
    setIsOpen(true);

    // If no cached analysis exists, generate new one
    if (!analysis && !isLoading) {
      setProgress({
        progress: 10,
        status: '正在生成深度分析...',
        isComplete: false,
        hasError: false,
      });

      generateAnalysis();
    }
  }, [analysis, isLoading, generateAnalysis]);

  // Close modal and reset state
  const closeModal = useCallback(() => {
    setIsOpen(false);
    setProgress({
      progress: 0,
      status: '準備分析...',
      isComplete: false,
      hasError: false,
    });
  }, []);

  // Copy analysis to clipboard
  const copyAnalysis = useCallback(async () => {
    if (!analysis) return;

    const formattedText = formatAnalysisForSharing(analysis, articleTitle);
    const success = await copyAnalysisToClipboard(formattedText);

    if (success) {
      toast.success('分析內容已複製到剪貼簿');
    } else {
      toast.error('複製失敗，請手動選取文字');
    }
  }, [analysis, articleTitle]);

  // Generate shareable link
  const shareAnalysis = useCallback(() => {
    if (!analysis) return;

    const shareUrl = `${window.location.origin}/articles/${articleId}/analysis`;

    if (navigator.share) {
      // Use native sharing if available
      navigator
        .share({
          title: `AI 分析：${articleTitle}`,
          text: '查看這篇文章的 AI 深度分析',
          url: shareUrl,
        })
        .catch(() => {
          // Fallback to copying URL
          copyAnalysisToClipboard(shareUrl);
          toast.success('分享連結已複製到剪貼簿');
        });
    } else {
      // Fallback to copying URL
      copyAnalysisToClipboard(shareUrl);
      toast.success('分享連結已複製到剪貼簿');
    }
  }, [analysis, articleId, articleTitle]);

  // Update progress based on generation state
  React.useEffect(() => {
    if (isGenerating) {
      // Simulate progress during generation
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev.progress >= 90) {
            return prev; // Stop at 90% until complete
          }
          return {
            ...prev,
            progress: Math.min(prev.progress + 10, 90),
            status:
              prev.progress < 30
                ? '分析文章內容...'
                : prev.progress < 60
                  ? '提取技術概念...'
                  : '生成建議步驟...',
          };
        });
      }, 2000);

      return () => clearInterval(interval);
    } else if (analysis) {
      setProgress({
        progress: 100,
        status: '分析完成',
        isComplete: true,
        hasError: false,
      });
    }
  }, [isGenerating, analysis]);

  return {
    // State
    isOpen,
    analysis,
    progress,
    isLoading: isLoading || isGenerating,

    // Actions
    openModal,
    closeModal,
    copyAnalysis,
    shareAnalysis,
  };
}

/**
 * Hook for tracking analysis interactions
 *
 * @param articleId - The article ID
 * @returns Interaction tracking functions
 */
export function useAnalysisTracking(articleId: string) {
  const trackAnalysisView = useCallback(() => {
    // Track when user views analysis
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'analysis_view', {
        article_id: articleId,
        timestamp: Date.now(),
      });
    }
  }, [articleId]);

  const trackAnalysisCopy = useCallback(() => {
    // Track when user copies analysis
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'analysis_copy', {
        article_id: articleId,
        timestamp: Date.now(),
      });
    }
  }, [articleId]);

  const trackAnalysisShare = useCallback(() => {
    // Track when user shares analysis
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'analysis_share', {
        article_id: articleId,
        timestamp: Date.now(),
      });
    }
  }, [articleId]);

  return {
    trackAnalysisView,
    trackAnalysisCopy,
    trackAnalysisShare,
  };
}
