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
        className="max-w-4xl max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-300"
        data-testid="analysis-modal"
      >
        <DialogHeader className="animate-in slide-in-from-top-4 duration-500 delay-200">
          <DialogTitle className="text-xl font-bold leading-tight pr-8 animate-in fade-in duration-300 delay-300">
            {articleTitle}
          </DialogTitle>

          {/* Article metadata - Validates Requirements 2.2 */}
          <DialogDescription asChild>
            <div className="flex flex-col gap-2 text-sm text-muted-foreground animate-in slide-in-from-left-4 duration-500 delay-400">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-1 transition-colors duration-200 hover:text-foreground">
                  <ExternalLink className="h-4 w-4 transition-transform duration-200 hover:scale-110" />
                  <span>{articleSource}</span>
                </div>

                {articlePublishedAt && (
                  <div className="flex items-center gap-1 transition-colors duration-200 hover:text-foreground">
                    <Calendar className="h-4 w-4 transition-transform duration-200 hover:scale-110" />
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
            <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-500 delay-500">
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="lg" text={progress.status} data-testid="analysis-loading" />
              </div>

              {/* Progress indicator */}
              <div className="space-y-2 animate-in slide-in-from-left-4 duration-500 delay-600">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{progress.status}</span>
                  <span className="text-muted-foreground">{progress.progress}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-500 ease-out animate-in slide-in-from-left-full"
                    style={{ width: `${progress.progress}%` }}
                  />
                </div>
              </div>

              <p className="text-sm text-muted-foreground text-center animate-in fade-in duration-500 delay-700">
                AI 正在深度分析文章內容，這可能需要最多 30 秒的時間...
              </p>
            </div>
          )}

          {/* Error state - Validates Requirements 2.9 */}
          {progress.hasError && (
            <Alert
              variant="destructive"
              className="animate-in slide-in-from-bottom-4 duration-500 delay-500"
            >
              <AlertCircle className="h-4 w-4 animate-pulse" />
              <AlertDescription>
                {progress.errorMessage || '分析生成失敗，請稍後再試'}
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-2 transition-all duration-200 hover:scale-105"
                  onClick={() => window.location.reload()}
                >
                  重試
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Analysis results - Validates Requirements 2.4 */}
          {analysis && (
            <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500 delay-600">
              {/* Analysis metadata */}
              <div className="flex items-center justify-between animate-in slide-in-from-left-4 duration-500 delay-700">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500 animate-pulse" />
                  <span className="text-sm text-muted-foreground transition-colors duration-200 hover:text-foreground">
                    分析完成於 {analysis.generatedAt.toLocaleString('zh-TW')}
                  </span>
                  <Badge
                    variant="secondary"
                    className="text-xs animate-in zoom-in-50 duration-300 delay-800 transition-all hover:scale-105"
                  >
                    {analysis.model}
                  </Badge>
                </div>

                {/* Action buttons - Validates Requirements 2.7, 2.8 */}
                <div className="flex gap-2 animate-in slide-in-from-right-4 duration-500 delay-900">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyAnalysis}
                    data-testid="copy-analysis"
                    className="transition-all duration-200 hover:scale-105"
                  >
                    <Copy className="h-4 w-4 mr-1 transition-transform duration-200 hover:scale-110" />
                    複製分析
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleShareAnalysis}
                    data-testid="share-analysis"
                    className="transition-all duration-200 hover:scale-105"
                  >
                    <Share2 className="h-4 w-4 mr-1 transition-transform duration-200 hover:scale-110" />
                    分享分析
                  </Button>
                </div>
              </div>

              {/* Core Technical Concepts */}
              <div className="animate-in slide-in-from-left-4 duration-500 delay-1000">
                <AnalysisSection title="核心技術概念" items={analysis.coreConcepts} icon="🔧" />
              </div>

              {/* Application Scenarios */}
              <div className="animate-in slide-in-from-right-4 duration-500 delay-1100">
                <AnalysisSection title="應用場景" items={analysis.applicationScenarios} icon="🚀" />
              </div>

              {/* Potential Risks */}
              <div className="animate-in slide-in-from-left-4 duration-500 delay-1200">
                <AnalysisSection
                  title="潛在風險"
                  items={analysis.potentialRisks}
                  icon="⚠️"
                  variant="warning"
                />
              </div>

              {/* Recommended Steps */}
              <div className="animate-in slide-in-from-right-4 duration-500 delay-1300">
                <AnalysisSection
                  title="建議步驟"
                  items={analysis.recommendedSteps}
                  icon="📋"
                  variant="success"
                />
              </div>
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
    <div
      className={`rounded-lg border p-4 ${borderColor} ${bgColor} hover:shadow-md transition-all duration-200`}
    >
      <h3 className="flex items-center gap-2 font-semibold mb-3 animate-in slide-in-from-left-2 duration-300">
        <span className="text-lg transition-transform duration-200 hover:scale-110">{icon}</span>
        {title}
      </h3>

      {items.length > 0 ? (
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li
              key={index}
              className="flex items-start gap-2 animate-in slide-in-from-left-2 duration-300 transition-colors hover:text-foreground"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <span className="text-muted-foreground mt-1">•</span>
              <span className="text-sm leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground italic animate-in fade-in duration-300">
          此部分暫無內容
        </p>
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
