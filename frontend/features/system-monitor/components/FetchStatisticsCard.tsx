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
    <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-md transition-all">
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2 animate-in slide-in-from-left-4 duration-500 delay-200">
          <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-300 hover:scale-[1.05] transition-transform">
            <TrendingUp className="h-5 w-5 animate-pulse" />
          </div>
          抓取統計
        </CardTitle>
        <CardDescription className="animate-in fade-in duration-500 delay-400">
          最近 24 小時的文章抓取統計資料
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Articles Processed */}
          <div className="space-y-2 animate-in slide-in-from-left-4 duration-500 delay-500">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
                <span className="text-sm font-medium">處理文章數</span>
              </div>
              <span className="text-2xl font-bold transition-all duration-300 hover:scale-[1.05] hover:text-primary">
                {statistics.totalArticles24h}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">過去 24 小時內成功處理的文章總數</p>
          </div>

          <div className="border-t animate-in fade-in duration-300 delay-700" />

          {/* Success Rate */}
          <div className="space-y-3 animate-in slide-in-from-right-4 duration-500 delay-600">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
                <span className="text-sm font-medium">成功率</span>
              </div>
              <span
                className={`text-2xl font-bold transition-all duration-300 hover:scale-[1.05] ${successRateColor}`}
              >
                {statistics.successRate.toFixed(1)}%
              </span>
            </div>
            <div className="animate-in slide-in-from-left-full duration-1000 delay-800">
              <Progress value={statistics.successRate} className="h-2" />
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-1 animate-in slide-in-from-left-2 duration-300 delay-900">
                <CheckCircle2 className="h-3 w-3 text-green-500 animate-pulse" />
                <span>成功: {statistics.totalFetches24h - statistics.failedFetches24h} 次</span>
              </div>
              <div className="flex items-center gap-1 animate-in slide-in-from-right-2 duration-300 delay-1000">
                <XCircle className="h-3 w-3 text-red-500 animate-pulse" />
                <span>失敗: {statistics.failedFetches24h} 次</span>
              </div>
            </div>
          </div>

          <div className="border-t animate-in fade-in duration-300 delay-1100" />

          {/* Processing Time */}
          <div className="space-y-2 animate-in slide-in-from-left-4 duration-500 delay-1000">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
                <span className="text-sm font-medium">平均處理時間</span>
              </div>
              <span className="text-2xl font-bold font-mono transition-all duration-300 hover:scale-[1.05] hover:text-primary">
                {processingTime}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">每次抓取操作的平均處理時間</p>
          </div>

          <div className="border-t animate-in fade-in duration-300 delay-1300" />

          {/* Total Fetches */}
          <div className="space-y-2 animate-in slide-in-from-right-4 duration-500 delay-1200">
            <div className="flex items-center justify-between animate-in slide-in-from-left-2 duration-300 delay-1400">
              <span className="text-sm text-muted-foreground">總抓取次數</span>
              <span className="text-lg font-semibold transition-all duration-300 hover:scale-[1.05]">
                {statistics.totalFetches24h}
              </span>
            </div>
            <div className="flex items-center justify-between animate-in slide-in-from-right-2 duration-300 delay-1500">
              <span className="text-sm text-muted-foreground">失敗次數</span>
              <span className="text-lg font-semibold text-red-600 dark:text-red-400 transition-all duration-300 hover:scale-[1.05]">
                {statistics.failedFetches24h}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
