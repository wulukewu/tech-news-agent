/**
 * FeedStatistics Component
 *
 * Displays feed statistics including total articles, articles this week, and average tinkering index
 *
 * Validates: Requirements 4.6, 8.6, 25.5
 * - THE Feed_Management_Dashboard SHALL display feed statistics
 *   (total articles, articles this week, average tinkering index)
 * - Show total articles, articles this week, average tinkering index
 * - Use star visualization for average tinkering index
 */

import { FileText, TrendingUp, Star } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export interface FeedStatisticsProps {
  totalArticles: number;
  articlesThisWeek: number;
  averageTinkeringIndex: number;
  className?: string;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`w-3 h-3 ${
            i < Math.floor(rating)
              ? 'fill-yellow-400 text-yellow-400'
              : i < rating
                ? 'fill-yellow-200 text-yellow-400'
                : 'text-gray-300 dark:text-gray-600'
          }`}
        />
      ))}
      <span className="ml-1 text-xs text-muted-foreground">({rating.toFixed(1)})</span>
    </div>
  );
}

export function FeedStatistics({
  totalArticles,
  articlesThisWeek,
  averageTinkeringIndex,
  className = '',
}: FeedStatisticsProps) {
  const stats = [
    {
      icon: FileText,
      label: '總文章數',
      value: totalArticles.toLocaleString(),
      color: 'text-blue-600 dark:text-blue-400',
      content: null,
    },
    {
      icon: TrendingUp,
      label: '本週新增',
      value: articlesThisWeek.toLocaleString(),
      color: 'text-green-600 dark:text-green-400',
      content: null,
    },
    {
      icon: Star,
      label: '平均技術深度',
      value: '',
      color: 'text-yellow-600 dark:text-yellow-400',
      content: <StarRating rating={averageTinkeringIndex} />,
    },
  ];

  return (
    <div className={`grid grid-cols-3 gap-3 ${className}`}>
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label} className="border-muted">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <Icon className={`w-4 h-4 ${stat.color}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-muted-foreground truncate">{stat.label}</div>
                  {stat.content ? (
                    <div className="mt-1">{stat.content}</div>
                  ) : (
                    <div className="text-lg font-semibold">{stat.value}</div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
