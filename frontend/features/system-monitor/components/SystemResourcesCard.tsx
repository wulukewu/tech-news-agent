/**
 * System Resources Card Component
 *
 * Displays system resource usage including CPU, memory, and disk.
 *
 * Requirements: 5.8
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Cpu, HardDrive, MemoryStick } from 'lucide-react';
import type { SystemResources } from '../types';
import { useI18n } from '@/contexts/I18nContext';

interface SystemResourcesCardProps {
  resources?: SystemResources;
}

/**
 * Format bytes to human-readable format
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * Get color class based on usage percentage
 */
function getUsageColor(percentage: number): string {
  if (percentage < 70) return 'text-green-600 dark:text-green-400';
  if (percentage < 85) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-red-600 dark:text-red-400';
}

/**
 * Get progress bar color based on usage percentage
 */
function getProgressColor(percentage: number): string {
  if (percentage < 70) return 'bg-green-600';
  if (percentage < 85) return 'bg-yellow-600';
  return 'bg-red-600';
}

export function SystemResourcesCard({ resources }: SystemResourcesCardProps) {
  const { t } = useI18n();

  if (!resources) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            {t('system.resource-usage')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{t('system.resource-unavailable')}</p>
        </CardContent>
      </Card>
    );
  }

  const { cpu, memory, disk } = resources;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cpu className="h-5 w-5" />
          {t('system.resource-usage')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* CPU Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">{t('system.cpu-usage')}</span>
            </div>
            <span className={`text-sm font-semibold ${getUsageColor(cpu.usage)}`}>
              {cpu.usage.toFixed(1)}%
            </span>
          </div>
          <Progress
            value={cpu.usage}
            className="h-2"
            indicatorClassName={getProgressColor(cpu.usage)}
          />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{t('system.cores', { count: cpu.cores })}</span>
            <span>
              {t('system.load-average', {
                values: cpu.loadAverage.map((load) => load.toFixed(2)).join(', '),
              })}
            </span>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MemoryStick className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">{t('system.memory-usage')}</span>
            </div>
            <span className={`text-sm font-semibold ${getUsageColor(memory.usagePercentage)}`}>
              {memory.usagePercentage.toFixed(1)}%
            </span>
          </div>
          <Progress
            value={memory.usagePercentage}
            className="h-2"
            indicatorClassName={getProgressColor(memory.usagePercentage)}
          />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{t('system.used', { amount: formatBytes(memory.used) })}</span>
            <span>{t('system.total', { amount: formatBytes(memory.total) })}</span>
          </div>
        </div>

        {/* Disk Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">{t('system.disk-usage')}</span>
            </div>
            <span className={`text-sm font-semibold ${getUsageColor(disk.usagePercentage)}`}>
              {disk.usagePercentage.toFixed(1)}%
            </span>
          </div>
          <Progress
            value={disk.usagePercentage}
            className="h-2"
            indicatorClassName={getProgressColor(disk.usagePercentage)}
          />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{t('system.used', { amount: formatBytes(disk.used) })}</span>
            <span>{t('system.total', { amount: formatBytes(disk.total) })}</span>
          </div>
        </div>

        {/* Last Updated */}
        <div className="pt-2 border-t">
          <p className="text-xs text-muted-foreground">
            {t('system.last-updated', {
              time: new Date(resources.lastUpdated).toLocaleString('zh-TW'),
            })}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
