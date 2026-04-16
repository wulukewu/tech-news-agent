'use client';

/**
 * AnalysisModal Component
 *
 * Modal dialog for displaying AI-generated article analysis.
 * Supports loading states, error handling, and user interactions.
 *
 * **Validates: Requirements 2.1, 2.2, 2.5, 2.7, 2.8, 2.9, 2.10**
 */

import React from 'react';
import { Calendar, ExternalLink, Copy, Share2, AlertCircle, CheckCircle2 } from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

import { useAnalysisModal, useAnalysisTracking } from '../hooks';
import type { AnalysisModalProps } from '../types';

/**
 * AnalysisModal - Main modal component for AI analysis
 *
 * **Validates: Requirements 2.1**
 * WHEN a user clicks "Deep Dive Analysis" on an article,
 * THE AI_Analysis_Panel SHALL open in a modal dialog
 */
export function AnalysisModal({
  articleId,
  articleTitle,
  articleSource,
  articlePublishedAt,
  isOpen,
  onClose,
}: AnalysisModalProps) {
  const { analysis, progress, isLoading, copyAnalysis, shareAnalysis } = useAnalysisModal(
    articleId,
    articleTitle
  );

  const { trackAnalysisView, trackAnalysisCopy, trackAnalysisShare } =
    useAnalysisTracking(articleId);

  // Track analysis view when modal opens
  React.useEffect(() => {
    if (isOpen && analysis) {
      trackAnalysisView();
    }
  }, [isOpen, analysis, trackAnalysisView]);

  const handleCopyAnalysis = () => {
    copyAnalysis();
    trackAnalysisCopy();
  };

  const handleShareAnalysis = () => {
    shareAnalysis();
    trackAnalysisShare();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className="max-w-4xl max-h-[90vh] overflow-y-auto"
        data-testid="analysis-modal"
      >
        <DialogHeader>
          <DialogTitle className="text-xl font-bold leading-tight pr-8">{articleTitle}</DialogTitle>

          {/* Article metadata - Validates Requirements 2.2 */}
          <DialogDescription asChild>
            <div className="flex flex-col gap-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-1">
                  <ExternalLink className="h-4 w-4" />
                  <span>{articleSource}</span>
                </div>

                {articlePublishedAt && (
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>
                      {new Date(articlePublishedAt).toLocaleDateString('zh-TW', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Loading state - Validates Requirements 2.5 */}
          {isLoading && (
            <div className="space-y-4">
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="lg" text={progress.status} data-testid="analysis-loading" />
              </div>

              {/* Progress indicator */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{progress.status}</span>
                  <span className="text-muted-foreground">{progress.progress}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress.progress}%` }}
                  />
                </div>
              </div>

              <p className="text-sm text-muted-foreground text-center">
                AI 正在深度分析文章內容，這可能需要最多 30 秒的時間...
              </p>
            </div>
          )}

          {/* Error state - Validates Requirements 2.9 */}
          {progress.hasError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {progress.errorMessage || '分析生成失敗，請稍後再試'}
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-2"
                  onClick={() => window.location.reload()}
                >
                  重試
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Analysis results - Validates Requirements 2.4 */}
          {analysis && (
            <div className="space-y-6">
              {/* Analysis metadata */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-muted-foreground">
                    分析完成於 {analysis.generatedAt.toLocaleString('zh-TW')}
                  </span>
                  <Badge variant="secondary" className="text-xs">
                    {analysis.model}
                  </Badge>
                </div>

                {/* Action buttons - Validates Requirements 2.7, 2.8 */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyAnalysis}
                    data-testid="copy-analysis"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    複製分析
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleShareAnalysis}
                    data-testid="share-analysis"
                  >
                    <Share2 className="h-4 w-4 mr-1" />
                    分享分析
                  </Button>
                </div>
              </div>

              {/* Core Technical Concepts */}
              <AnalysisSection title="核心技術概念" items={analysis.coreConcepts} icon="🔧" />

              {/* Application Scenarios */}
              <AnalysisSection title="應用場景" items={analysis.applicationScenarios} icon="🚀" />

              {/* Potential Risks */}
              <AnalysisSection
                title="潛在風險"
                items={analysis.potentialRisks}
                icon="⚠️"
                variant="warning"
              />

              {/* Recommended Steps */}
              <AnalysisSection
                title="建議步驟"
                items={analysis.recommendedSteps}
                icon="📋"
                variant="success"
              />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * AnalysisSection - Reusable section component for analysis results
 */
interface AnalysisSectionProps {
  title: string;
  items: string[];
  icon: string;
  variant?: 'default' | 'warning' | 'success';
}

function AnalysisSection({ title, items, icon, variant = 'default' }: AnalysisSectionProps) {
  const borderColor = {
    default: 'border-border',
    warning: 'border-yellow-200 dark:border-yellow-800',
    success: 'border-green-200 dark:border-green-800',
  }[variant];

  const bgColor = {
    default: 'bg-card',
    warning: 'bg-yellow-50 dark:bg-yellow-950/20',
    success: 'bg-green-50 dark:bg-green-950/20',
  }[variant];

  return (
    <div className={`rounded-lg border p-4 ${borderColor} ${bgColor}`}>
      <h3 className="flex items-center gap-2 font-semibold mb-3">
        <span className="text-lg">{icon}</span>
        {title}
      </h3>

      {items.length > 0 ? (
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li key={index} className="flex items-start gap-2">
              <span className="text-muted-foreground mt-1">•</span>
              <span className="text-sm leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground italic">此部分暫無內容</p>
      )}
    </div>
  );
}

/**
 * AnalysisLoadingSkeleton - Loading skeleton for analysis content
 */
export function AnalysisLoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>

      {/* Sections skeleton */}
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="space-y-3 p-4 border rounded-lg">
          <Skeleton className="h-5 w-1/3" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/5" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default AnalysisModal;
