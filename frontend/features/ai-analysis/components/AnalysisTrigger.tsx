'use client';

/**
 * AnalysisTrigger Component
 *
 * Button component that triggers the AI analysis modal.
 * Can be used in article cards, lists, or other contexts.
 */

import React from 'react';
import { Brain, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { AnalysisModal } from './AnalysisModal';
import { useAnalysisModal } from '../hooks';

interface AnalysisTriggerProps {
  /** Article ID to analyze */
  articleId: string;
  /** Article title for display */
  articleTitle: string;
  /** Article source name */
  articleSource: string;
  /** Article published date */
  articlePublishedAt: string | null;
  /** Button variant */
  variant?: 'default' | 'outline' | 'secondary' | 'ghost';
  /** Button size */
  size?: 'default' | 'sm' | 'lg' | 'icon';
  /** Whether to show full text or just icon */
  showText?: boolean;
  /** Custom button text */
  buttonText?: string;
  /** Additional CSS classes */
  className?: string;
  /** Whether the button is disabled */
  disabled?: boolean;
}

/**
 * AnalysisTrigger - Button that opens analysis modal
 *
 * **Validates: Requirements 2.1**
 * WHEN a user clicks "Deep Dive Analysis" on an article,
 * THE AI_Analysis_Panel SHALL open in a modal dialog
 */
export function AnalysisTrigger({
  articleId,
  articleTitle,
  articleSource,
  articlePublishedAt,
  variant = 'outline',
  size = 'sm',
  showText = true,
  buttonText = 'Deep Dive Analysis',
  className,
  disabled = false,
}: AnalysisTriggerProps) {
  const { isOpen, isLoading, openModal, closeModal } = useAnalysisModal(articleId, articleTitle);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    openModal();
  };

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={handleClick}
        disabled={disabled || isLoading}
        className={`${className} transition-all duration-200 hover:scale-105 animate-in fade-in zoom-in-50 duration-300`}
        data-testid="analysis-button"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Brain className="h-4 w-4 transition-transform duration-200 hover:scale-110" />
        )}

        {showText && (
          <span className="ml-1 transition-all duration-200">
            {isLoading ? '分析中...' : buttonText}
          </span>
        )}
      </Button>

      <AnalysisModal
        articleId={articleId}
        articleTitle={articleTitle}
        articleSource={articleSource}
        articlePublishedAt={articlePublishedAt}
        isOpen={isOpen}
        onClose={closeModal}
      />
    </>
  );
}

/**
 * Compact version for use in tight spaces
 */
export function CompactAnalysisTrigger(props: Omit<AnalysisTriggerProps, 'showText' | 'size'>) {
  return <AnalysisTrigger {...props} showText={false} size="sm" variant="ghost" />;
}

/**
 * Primary version for main call-to-action
 */
export function PrimaryAnalysisTrigger(props: Omit<AnalysisTriggerProps, 'variant'>) {
  return <AnalysisTrigger {...props} variant="default" />;
}

export default AnalysisTrigger;
