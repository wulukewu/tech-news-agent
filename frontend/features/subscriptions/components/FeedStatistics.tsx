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
import { useI18n } from '@/contexts/I18nContext';

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
          className={`w-3 h-3 transition-all duration-300 hover:scale-[1.05] ${
            i < Math.floor(rating)
              ? 'fill-yellow-400 text-yellow-400 animate-pulse'
              : i < rating
                ? 'fill-yellow-200 text-yellow-400'
                : 'text-gray-300 dark:text-gray-600'
          }`}
        />
      ))}
      <span className="ml-1 text-xs text-muted-foreground transition-colors duration-200 hover:text-foreground">
        ({rating.toFixed(1)})
      </span>
    </div>
  );
}

export function FeedStatistics({
  totalArticles,
  articlesThisWeek,
  averageTinkeringIndex,
  className = '',
}: FeedStatisticsProps) {
  const { t } = useI18n();

  const stats = [
    {
      icon: FileText,
      label: t('statistics.total-articles'),
      value: totalArticles.toLocaleString(),
      color: 'text-blue-600 dark:text-blue-400',
      content: null,
    },
    {
      icon: TrendingUp,
      label: t('statistics.articles-this-week'),
      value: articlesThisWeek.toLocaleString(),
      color: 'text-green-600 dark:text-green-400',
      content: null,
    },
    {
      icon: Star,
      label: t('statistics.average-tinkering-index'),
      value: '',
      color: 'text-yellow-600 dark:text-yellow-400',
      content: <StarRating rating={averageTinkeringIndex} />,
    },
  ];

  return (
    <div className={`grid grid-cols-3 gap-3 ${className}`}>
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card
            key={stat.label}
            className="border-muted animate-in slide-in-from-bottom-4 duration-500 hover:shadow-md transition-all hover:border-primary/20"
            style={{ animationDelay: `${index * 150}ms` }}
          >
            <CardContent className="p-3">
              <div
                className="flex items-center gap-2 animate-in slide-in-from-left-2 duration-300"
                style={{ animationDelay: `${index * 150 + 200}ms` }}
              >
                <Icon
                  className={`w-4 h-4 ${stat.color} transition-transform duration-300 hover:scale-[1.05] animate-pulse`}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-muted-foreground truncate transition-colors duration-200 hover:text-foreground">
                    {stat.label}
                  </div>
                  {stat.content ? (
                    <div
                      className="mt-1 animate-in fade-in duration-300"
                      style={{ animationDelay: `${index * 150 + 300}ms` }}
                    >
                      {stat.content}
                    </div>
                  ) : (
                    <div
                      className="text-lg font-semibold transition-all duration-300 hover:scale-[1.05] hover:text-primary animate-in zoom-in-50 duration-300"
                      style={{ animationDelay: `${index * 150 + 300}ms` }}
                    >
                      {stat.value}
                    </div>
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
