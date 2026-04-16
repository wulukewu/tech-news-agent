/**
 * Fetch Statistics Card Component
 *
 * Displays recent fetch statistics including articles processed,
 * success rate, and processing time.
 *
 * Requirements: 5.5
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { FileText, TrendingUp, Clock, CheckCircle2, XCircle } from 'lucide-react';
import type { FetchStatistics } from '../types';

interface FetchStatisticsCardProps {
  statistics: FetchStatistics;
}

/**
 * Format processing time with appropriate unit
 */
function formatProcessingTime(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  } else {
    return `${(ms / 60000).toFixed(1)}m`;
  }
}

/**
 * Get success rate color based on percentage
 */
function getSuccessRateColor(rate: number): string {
  if (rate >= 95) {
    return 'text-green-600 dark:text-green-400';
  } else if (rate >= 80) {
    return 'text-yellow-600 dark:text-yellow-400';
  } else {
    return 'text-red-600 dark:text-red-400';
  }
}

export function FetchStatisticsCard({ statistics }: FetchStatisticsCardProps) {
  const successRateColor = getSuccessRateColor(statistics.successRate);
  const processingTime = formatProcessingTime(statistics.averageProcessingTime);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          抓取統計
        </CardTitle>
        <CardDescription>最近 24 小時的文章抓取統計資料</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Articles Processed */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">處理文章數</span>
              </div>
              <span className="text-2xl font-bold">{statistics.totalArticles24h}</span>
            </div>
            <p className="text-xs text-muted-foreground">過去 24 小時內成功處理的文章總數</p>
          </div>

          <div className="border-t" />

          {/* Success Rate */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">成功率</span>
              </div>
              <span className={`text-2xl font-bold ${successRateColor}`}>
                {statistics.successRate.toFixed(1)}%
              </span>
            </div>
            <Progress value={statistics.successRate} className="h-2" />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-green-500" />
                <span>成功: {statistics.totalFetches24h - statistics.failedFetches24h} 次</span>
              </div>
              <div className="flex items-center gap-1">
                <XCircle className="h-3 w-3 text-red-500" />
                <span>失敗: {statistics.failedFetches24h} 次</span>
              </div>
            </div>
          </div>

          <div className="border-t" />

          {/* Processing Time */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">平均處理時間</span>
              </div>
              <span className="text-2xl font-bold font-mono">{processingTime}</span>
            </div>
            <p className="text-xs text-muted-foreground">每次抓取操作的平均處理時間</p>
          </div>

          <div className="border-t" />

          {/* Total Fetches */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">總抓取次數</span>
              <span className="text-lg font-semibold">{statistics.totalFetches24h}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">失敗次數</span>
              <span className="text-lg font-semibold text-red-600 dark:text-red-400">
                {statistics.failedFetches24h}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
