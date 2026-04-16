/**
 * InsufficientDataMessage Component
 *
 * Displays a message when user doesn't have enough ratings for recommendations
 *
 * Validates: Requirements 3.6, 3.9
 */

'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Star, TrendingUp } from 'lucide-react';
import Link from 'next/link';

interface InsufficientDataMessageProps {
  userRatingCount: number;
  minRatingsRequired: number;
}

/**
 * InsufficientDataMessage component
 *
 * **Validates: Requirement 3.6**
 * - Displays message when insufficient rating data exists (less than 3 rated articles)
 *
 * **Validates: Requirement 3.9**
 * - Suggests rating more articles when no recommendations are available
 */
export function InsufficientDataMessage({
  userRatingCount,
  minRatingsRequired,
}: InsufficientDataMessageProps) {
  const ratingsNeeded = minRatingsRequired - userRatingCount;

  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <div className="rounded-full bg-primary/10 p-4 mb-4">
          <TrendingUp className="h-8 w-8 text-primary" />
        </div>

        <h3 className="text-xl font-semibold mb-2">開始建立您的推薦系統</h3>

        <p className="text-muted-foreground mb-6 max-w-md">
          {userRatingCount === 0 ? (
            <>
              為了提供精準的個人化推薦，我們需要了解您的閱讀偏好。 請至少評分{' '}
              <span className="font-semibold text-foreground">{minRatingsRequired}</span> 篇文章。
            </>
          ) : (
            <>
              您已評分 <span className="font-semibold text-foreground">{userRatingCount}</span>{' '}
              篇文章， 還需要 <span className="font-semibold text-foreground">{ratingsNeeded}</span>{' '}
              篇評分 即可獲得個人化推薦。
            </>
          )}
        </p>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button asChild size="lg" className="gap-2">
            <Link href="/articles">
              <Star className="h-4 w-4" />
              開始評分文章
            </Link>
          </Button>

          {userRatingCount > 0 && (
            <Button asChild variant="outline" size="lg">
              <Link href="/reading-list">查看已評分文章</Link>
            </Button>
          )}
        </div>

        <div className="mt-8 p-4 bg-muted/50 rounded-lg max-w-md">
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">💡 提示：</span>
            評分 4 星以上的文章將用於生成推薦。評分越多，推薦越精準！
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
