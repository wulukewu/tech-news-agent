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
import { zhTW, enUS } from 'date-fns/locale';
import { useI18n } from '@/contexts/I18nContext';

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
  const { t, locale } = useI18n();
  const dateLocale = locale === 'zh-TW' ? zhTW : enUS;

  const dbResponseTime = formatResponseTime(health.database.responseTime);
  const apiAvgResponseTime = formatResponseTime(health.api.averageResponseTime);
  const apiP95ResponseTime = formatResponseTime(health.api.p95ResponseTime);
  const apiP99ResponseTime = formatResponseTime(health.api.p99ResponseTime);
  const errorRate = formatErrorRate(health.errors.rate);

  return (
    <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-md transition-all">
      <CardHeader>
        <CardTitle className="text-xl flex items-center gap-2 animate-in slide-in-from-left-4 duration-500 delay-200">
          <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-300 hover:scale-[1.05] transition-transform">
            <Activity className="h-5 w-5 animate-pulse" />
          </div>
          {t('system.system-health')}
        </CardTitle>
        <CardDescription className="animate-in fade-in duration-500 delay-400">
          {t('system.system-health-desc')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Database Connection */}
          <div className="space-y-2 animate-in slide-in-from-left-4 duration-500 delay-500">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
                <span className="text-sm font-medium">{t('system.database-connection')}</span>
              </div>
              {health.database.connected ? (
                <Badge
                  variant="default"
                  className="bg-green-500 hover:bg-green-600 transition-all duration-300 hover:scale-[1.02] animate-pulse"
                >
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  {t('ui.connected')}
                </Badge>
              ) : (
                <Badge
                  variant="destructive"
                  className="transition-all duration-300 hover:scale-[1.02] animate-pulse"
                >
                  <XCircle className="h-3 w-3 mr-1" />
                  {t('ui.disconnected')}
                </Badge>
              )}
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{t('system.response-time')}</span>
              <span
                className={`font-mono font-medium transition-colors duration-200 hover:scale-[1.02] ${dbResponseTime.color}`}
              >
                {dbResponseTime.value}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{t('system.last-checked')}</span>
              <span className="text-muted-foreground">
                {formatDistanceToNow(health.database.lastChecked, {
                  addSuffix: true,
                  locale: dateLocale,
                })}
              </span>
            </div>
          </div>

          <div className="border-t animate-in fade-in duration-300 delay-700" />

          {/* API Response Times */}
          <div className="space-y-2 animate-in slide-in-from-right-4 duration-500 delay-600">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
              <span className="text-sm font-medium">{t('system.api-response-time')}</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: t('system.average'), value: apiAvgResponseTime },
                { label: 'P95', value: apiP95ResponseTime },
                { label: 'P99', value: apiP99ResponseTime },
              ].map((metric, index) => (
                <div
                  key={index}
                  className="space-y-1 animate-in zoom-in-50 duration-300"
                  style={{ animationDelay: `${800 + index * 100}ms` }}
                >
                  <div className="text-xs text-muted-foreground">{metric.label}</div>
                  <div
                    className={`text-lg font-mono font-semibold transition-all duration-300 hover:scale-[1.05] ${metric.value.color}`}
                  >
                    {metric.value.value}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between text-sm pt-2">
              <span className="text-muted-foreground">{t('system.last-checked')}</span>
              <span className="text-muted-foreground">
                {formatDistanceToNow(health.api.lastChecked, {
                  addSuffix: true,
                  locale: dateLocale,
                })}
              </span>
            </div>
          </div>

          <div className="border-t animate-in fade-in duration-300 delay-1000" />

          {/* Error Rates */}
          <div className="space-y-2 animate-in slide-in-from-left-4 duration-500 delay-900">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
              <span className="text-sm font-medium">{t('system.error-rate')}</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1 animate-in zoom-in-50 duration-300 delay-1100">
                <div className="text-xs text-muted-foreground">{t('system.errors-per-minute')}</div>
                <div
                  className={`text-lg font-mono font-semibold transition-all duration-300 hover:scale-[1.05] ${errorRate.color}`}
                >
                  {errorRate.value}
                </div>
              </div>
              <div className="space-y-1 animate-in zoom-in-50 duration-300 delay-1200">
                <div className="text-xs text-muted-foreground">{t('system.total-errors-24h')}</div>
                <div className="text-lg font-mono font-semibold transition-all duration-300 hover:scale-[1.05]">
                  {health.errors.total24h}
                </div>
              </div>
            </div>
            {health.errors.lastError && (
              <div className="flex items-center justify-between text-sm pt-2 animate-in fade-in duration-500 delay-1300">
                <span className="text-muted-foreground">{t('system.last-error')}</span>
                <span className="text-muted-foreground">
                  {formatDistanceToNow(health.errors.lastError, {
                    addSuffix: true,
                    locale: dateLocale,
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
