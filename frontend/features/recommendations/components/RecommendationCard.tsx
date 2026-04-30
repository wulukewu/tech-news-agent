/**
 * RecommendationCard Component
 *
 * Displays a single article recommendation with title, source, category,
 * AI summary, and recommendation reason
 *
 * Validates: Requirements 3.3, 3.4, 3.7
 */

'use client';

import React, { useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { X, ExternalLink, Star } from 'lucide-react';
import { Recommendation } from '@/types/recommendation';
import { formatDistanceToNow } from 'date-fns';
import { zhTW } from 'date-fns/locale';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onDismiss?: (id: string) => void;
  onClick?: (id: string) => void;
}

/**
 * RecommendationCard component
 *
 * **Validates: Requirements 3.4**
 * - Displays article title, source, category, AI summary, and recommendation reason
 */
export function RecommendationCard({
  recommendation,
  onDismiss,
  onClick,
}: RecommendationCardProps) {
  const { article, reason, confidence } = recommendation;

  const handleDismiss = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onDismiss?.(recommendation.id);
    },
    [recommendation.id, onDismiss]
  );

  const handleClick = useCallback(() => {
    onClick?.(recommendation.id);
  }, [recommendation.id, onClick]);

  const handleOpenArticle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      window.open(article.url, '_blank', 'noopener,noreferrer');
    },
    [article.url]
  );

  const confidenceStars = Math.round(confidence * 5);

  return (
    <Card
      className="group relative hover:shadow-md transition-all duration-300 cursor-pointer hover:scale-[1.02] hover:-translate-y-1"
      onClick={handleClick}
    >
      {/* Dismiss button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-2 right-2 h-8 w-8 rounded-full hover:bg-destructive/10 transition-all duration-300 hover:scale-[1.05] opacity-0 group-hover:opacity-100"
        onClick={handleDismiss}
        aria-label="忽略推薦"
      >
        <X className="h-4 w-4 transition-transform duration-300 hover:rotate-90" />
      </Button>

      <CardHeader className="pb-3">
        <div className="flex items-start gap-2 pr-8">
          <div className="flex-1">
            <CardTitle className="text-lg line-clamp-2 mb-2 group-hover:text-primary transition-colors duration-200">
              {article.title}
            </CardTitle>
            <CardDescription className="flex items-center gap-2 flex-wrap">
              <span className="text-sm">{article.feedName}</span>
              <span className="text-muted-foreground">•</span>
              <Badge
                variant="secondary"
                className="text-xs transition-all duration-300 hover:scale-[1.02]"
              >
                {article.category}
              </Badge>
              {article.publishedAt && (
                <>
                  <span className="text-muted-foreground">•</span>
                  <span className="text-xs">
                    {formatDistanceToNow(new Date(article.publishedAt), {
                      addSuffix: true,
                      locale: zhTW,
                    })}
                  </span>
                </>
              )}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* AI Summary */}
        {article.aiSummary && (
          <div className="text-sm text-muted-foreground line-clamp-3 transition-colors duration-200 group-hover:text-foreground/80">
            {article.aiSummary}
          </div>
        )}

        {/* Recommendation Reason */}
        <div className="bg-primary/5 rounded-lg p-3 border border-primary/10 transition-all duration-200 group-hover:bg-primary/10 group-hover:border-primary/20">
          <div className="flex items-start gap-2">
            <div className="flex items-center gap-1 mt-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`h-3 w-3 transition-all duration-300 hover:scale-125 ${
                    i < confidenceStars ? 'fill-primary text-primary' : 'text-muted-foreground/30'
                  }`}
                  style={{ animationDelay: `${i * 50}ms` }}
                />
              ))}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-primary mb-1">推薦理由</p>
              <p className="text-sm text-muted-foreground">{reason}</p>
            </div>
          </div>
        </div>

        {/* Tinkering Index */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">技術深度</span>
            <div className="flex items-center gap-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`h-3 w-3 transition-all duration-300 hover:scale-125 ${
                    i < article.tinkeringIndex
                      ? 'fill-yellow-500 text-yellow-500'
                      : 'text-muted-foreground/30'
                  }`}
                  style={{ animationDelay: `${i * 50}ms` }}
                />
              ))}
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleOpenArticle}
            className="gap-2 transition-all duration-300 hover:scale-[1.02] hover:shadow-md"
          >
            閱讀文章
            <ExternalLink className="h-3 w-3 transition-transform duration-300 hover:scale-[1.05]" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
