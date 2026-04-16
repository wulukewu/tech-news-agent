/**
 * System Health Card Component
 *
 * Displays system health metrics including database connection,
 * API response times, and error rates.
 *
 * Requirements: 5.4
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Database, Activity, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import type { SystemHealth } from '../types';
import { formatDistanceToNow } from 'date-fns';
import { zhTW } from 'date-fns/locale';

interface SystemHealthCardProps {
  health: SystemHealth;
}

/**
 * Format response time with appropriate unit and color
 */
function formatResponseTime(ms: number): { value: string; color: string } {
  if (ms < 100) {
    return { value: `${ms}ms`, color: 'text-green-600 dark:text-green-400' };
  } else if (ms < 500) {
    return { value: `${ms}ms`, color: 'text-yellow-600 dark:text-yellow-400' };
  } else {
    return { value: `${ms}ms`, color: 'text-red-600 dark:text-red-400' };
  }
}

/**
 * Format error rate with appropriate color
 */
function formatErrorRate(rate: number): { value: string; color: string } {
  if (rate < 1) {
    return { value: rate.toFixed(2), color: 'text-green-600 dark:text-green-400' };
  } else if (rate < 5) {
    return { value: rate.toFixed(2), color: 'text-yellow-600 dark:text-yellow-400' };
  } else {
    return { value: rate.toFixed(2), color: 'text-red-600 dark:text-red-400' };
  }
}

export function SystemHealthCard({ health }: SystemHealthCardProps) {
  const dbResponseTime = formatResponseTime(health.database.responseTime);
  const apiAvgResponseTime = formatResponseTime(health.api.averageResponseTime);
  const apiP95ResponseTime = formatResponseTime(health.api.p95ResponseTime);
  const apiP99ResponseTime = formatResponseTime(health.api.p99ResponseTime);
  const errorRate = formatErrorRate(health.errors.rate);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2">
          <Activity className="h-5 w-5" />
          系統健康度
        </CardTitle>
        <CardDescription>資料庫連線、API 回應時間、錯誤率等指標</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Database Connection */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">資料庫連線</span>
              </div>
              {health.database.connected ? (
                <Badge variant="default" className="bg-green-500 hover:bg-green-600">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  已連線
                </Badge>
              ) : (
                <Badge variant="destructive">
                  <XCircle className="h-3 w-3 mr-1" />
                  未連線
                </Badge>
              )}
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">回應時間</span>
              <span className={`font-mono font-medium ${dbResponseTime.color}`}>
                {dbResponseTime.value}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">最後檢查</span>
              <span className="text-muted-foreground">
                {formatDistanceToNow(health.database.lastChecked, {
                  addSuffix: true,
                  locale: zhTW,
                })}
              </span>
            </div>
          </div>

          <div className="border-t" />

          {/* API Response Times */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">API 回應時間</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">平均</div>
                <div className={`text-lg font-mono font-semibold ${apiAvgResponseTime.color}`}>
                  {apiAvgResponseTime.value}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">P95</div>
                <div className={`text-lg font-mono font-semibold ${apiP95ResponseTime.color}`}>
                  {apiP95ResponseTime.value}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">P99</div>
                <div className={`text-lg font-mono font-semibold ${apiP99ResponseTime.color}`}>
                  {apiP99ResponseTime.value}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm pt-2">
              <span className="text-muted-foreground">最後檢查</span>
              <span className="text-muted-foreground">
                {formatDistanceToNow(health.api.lastChecked, {
                  addSuffix: true,
                  locale: zhTW,
                })}
              </span>
            </div>
          </div>

          <div className="border-t" />

          {/* Error Rates */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">錯誤率</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">每分鐘錯誤數</div>
                <div className={`text-lg font-mono font-semibold ${errorRate.color}`}>
                  {errorRate.value}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">24 小時總錯誤</div>
                <div className="text-lg font-mono font-semibold">{health.errors.total24h}</div>
              </div>
            </div>
            {health.errors.lastError && (
              <div className="flex items-center justify-between text-sm pt-2">
                <span className="text-muted-foreground">最後錯誤</span>
                <span className="text-muted-foreground">
                  {formatDistanceToNow(health.errors.lastError, {
                    addSuffix: true,
                    locale: zhTW,
                  })}
                </span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
