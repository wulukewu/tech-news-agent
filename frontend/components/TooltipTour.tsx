'use client';

import { useEffect, useState, useRef } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

/**
 * Single tooltip step configuration
 */
export interface TooltipStep {
  /** Unique identifier for this step */
  id: string;
  /** CSS selector for the target element */
  target: string;
  /** Title of the tooltip */
  title: string;
  /** Description/content of the tooltip */
  description: string;
  /** Placement relative to target */
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

/**
 * TooltipTour component props
 */
export interface TooltipTourProps {
  /** Array of tooltip steps to display */
  steps: TooltipStep[];
  /** Whether the tour is active */
  isActive: boolean;
  /** Callback when tour is completed */
  onComplete: () => void;
  /** Callback when tour is skipped */
  onSkip: () => void;
  /** Whether to show spotlight effect */
  showSpotlight?: boolean;
}

/**
 * TooltipTour component
 *
 * Displays sequential tooltips to guide users through key features.
 * Includes spotlight effect to highlight target elements.
 *
 * Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
 *
 * @example
 * ```tsx
 * <TooltipTour
 *   steps={[
 *     {
 *       id: 'subscribe-button',
 *       target: '[data-tour="subscribe"]',
 *       title: '訂閱按鈕',
 *       description: '點擊這裡訂閱或取消訂閱來源',
 *       placement: 'bottom'
 *     }
 *   ]}
 *   isActive={true}
 *   onComplete={() => markTourCompleted()}
 *   onSkip={() => markTourSkipped()}
 *   showSpotlight={true}
 * />
 * ```
 */
export function TooltipTour({
  steps,
  isActive,
  onComplete,
  onSkip,
  showSpotlight = true,
}: TooltipTourProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const currentStep = steps[currentStepIndex];
  const isLastStep = currentStepIndex === steps.length - 1;
  const isFirstStep = currentStepIndex === 0;

  useEffect(() => {
    if (!isActive || !currentStep) return;

    const updatePosition = () => {
      const targetElement = document.querySelector(currentStep.target);
      if (!targetElement) return;

      const rect = targetElement.getBoundingClientRect();
      setTargetRect(rect);

      // Calculate tooltip position based on placement
      const placement = currentStep.placement || 'bottom';
      const tooltipWidth = 320;
      const tooltipHeight = 200;
      const gap = 16;

      let top = 0;
      let left = 0;

      switch (placement) {
        case 'top':
          top = rect.top - tooltipHeight - gap;
          left = rect.left + rect.width / 2 - tooltipWidth / 2;
          break;
        case 'bottom':
          top = rect.bottom + gap;
          left = rect.left + rect.width / 2 - tooltipWidth / 2;
          break;
        case 'left':
          top = rect.top + rect.height / 2 - tooltipHeight / 2;
          left = rect.left - tooltipWidth - gap;
          break;
        case 'right':
          top = rect.top + rect.height / 2 - tooltipHeight / 2;
          left = rect.right + gap;
          break;
      }

      // Keep tooltip within viewport
      const padding = 16;
      top = Math.max(
        padding,
        Math.min(top, window.innerHeight - tooltipHeight - padding),
      );
      left = Math.max(
        padding,
        Math.min(left, window.innerWidth - tooltipWidth - padding),
      );

      setTooltipPosition({ top, left });
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition);

    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition);
    };
  }, [currentStep, isActive]);

  const nextStep = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const previousStep = () => {
    if (!isFirstStep) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const skipTour = () => {
    onSkip();
  };

  if (!isActive || !currentStep) return null;

  return (
    <>
      {/* Spotlight overlay */}
      {showSpotlight && targetRect && (
        <div
          className="fixed inset-0 pointer-events-none z-[9998]"
          style={{
            background: `radial-gradient(
              circle at ${targetRect.left + targetRect.width / 2}px ${targetRect.top + targetRect.height / 2}px,
              transparent ${Math.max(targetRect.width, targetRect.height) / 2 + 10}px,
              rgba(0, 0, 0, 0.7) ${Math.max(targetRect.width, targetRect.height) / 2 + 50}px
            )`,
          }}
        />
      )}

      {/* Tooltip card */}
      <div
        ref={tooltipRef}
        className="fixed z-[9999] w-80"
        style={{
          top: `${tooltipPosition.top}px`,
          left: `${tooltipPosition.left}px`,
        }}
      >
        <Card className="shadow-2xl border-2">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-lg">{currentStep.title}</CardTitle>
                <CardDescription className="text-xs mt-1">
                  步驟 {currentStepIndex + 1} / {steps.length}
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={skipTour}
                className="h-6 w-6 p-0"
                aria-label="跳過導覽"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {currentStep.description}
            </p>

            <div className="flex items-center justify-between gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={previousStep}
                disabled={isFirstStep}
              >
                上一步
              </Button>

              <div className="flex gap-1">
                {steps.map((_, index) => (
                  <div
                    key={index}
                    className={`h-1.5 w-1.5 rounded-full transition-colors ${
                      index === currentStepIndex
                        ? 'bg-primary'
                        : 'bg-muted-foreground/30'
                    }`}
                  />
                ))}
              </div>

              <Button size="sm" onClick={nextStep}>
                {isLastStep ? '完成' : '下一步'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
