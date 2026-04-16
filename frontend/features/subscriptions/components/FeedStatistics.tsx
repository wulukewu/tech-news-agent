/**
 * FeedStatistics Component
 *
 * Displays feed statistics including total articles, articles this week, and average tinkering index
 *
 * Validates: Requirements 4.6
 * - THE Feed_Management_Dashboard SHALL display feed statistics
 *   (total articles, articles this week, average tinkering index)
 */

import { FileText, TrendingUp, Star } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export interface FeedStatisticsProps {
  totalArticles: number;
  articlesThisWeek: number;
  averageTinkeringIndex: number;
  className?: string;
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
    },
    {
      icon: TrendingUp,
      label: '本週新增',
      value: articlesThisWeek.toLocaleString(),
      color: 'text-green-600 dark:text-green-400',
    },
    {
      icon: Star,
      label: '平均技術深度',
      value: averageTinkeringIndex.toFixed(1),
      color: 'text-yellow-600 dark:text-yellow-400',
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
                  <div className="text-lg font-semibold">{stat.value}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
