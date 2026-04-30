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
      <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 animate-in slide-in-from-left-4 duration-500 delay-200">
            <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-300 hover:scale-[1.05] transition-transform">
              <Cpu className="h-5 w-5 animate-pulse" />
            </div>
            {t('system.resource-usage')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground animate-in fade-in duration-500 delay-400">
            {t('system.resource-unavailable')}
          </p>
        </CardContent>
      </Card>
    );
  }

  const { cpu, memory, disk } = resources;

  return (
    <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-md transition-all">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 animate-in slide-in-from-left-4 duration-500 delay-200">
          <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-300 hover:scale-[1.05] transition-transform">
            <Cpu className="h-5 w-5 animate-pulse" />
          </div>
          {t('system.resource-usage')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* CPU Usage */}
        <div className="space-y-2 animate-in slide-in-from-left-4 duration-500 delay-400">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
              <span className="text-sm font-medium">{t('system.cpu-usage')}</span>
            </div>
            <span
              className={`text-sm font-semibold ${getUsageColor(cpu.usage)} transition-all duration-300 hover:scale-[1.05]`}
            >
              {cpu.usage.toFixed(1)}%
            </span>
          </div>
          <div className="animate-in slide-in-from-left-full duration-1000 delay-500">
            <Progress
              value={cpu.usage}
              className="h-2"
              indicatorClassName={getProgressColor(cpu.usage)}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground animate-in fade-in duration-300 delay-600">
            <span className="transition-colors duration-200 hover:text-foreground">
              {t('system.cores', { count: cpu.cores })}
            </span>
            <span className="transition-colors duration-200 hover:text-foreground">
              {t('system.load-average', {
                values: cpu.loadAverage.map((load) => load.toFixed(2)).join(', '),
              })}
            </span>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="space-y-2 animate-in slide-in-from-right-4 duration-500 delay-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MemoryStick className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
              <span className="text-sm font-medium">{t('system.memory-usage')}</span>
            </div>
            <span
              className={`text-sm font-semibold ${getUsageColor(memory.usagePercentage)} transition-all duration-300 hover:scale-[1.05]`}
            >
              {memory.usagePercentage.toFixed(1)}%
            </span>
          </div>
          <div className="animate-in slide-in-from-left-full duration-1000 delay-800">
            <Progress
              value={memory.usagePercentage}
              className="h-2"
              indicatorClassName={getProgressColor(memory.usagePercentage)}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground animate-in fade-in duration-300 delay-900">
            <span className="transition-colors duration-200 hover:text-foreground">
              {t('system.used', { amount: formatBytes(memory.used) })}
            </span>
            <span className="transition-colors duration-200 hover:text-foreground">
              {t('system.total', { amount: formatBytes(memory.total) })}
            </span>
          </div>
        </div>

        {/* Disk Usage */}
        <div className="space-y-2 animate-in slide-in-from-left-4 duration-500 delay-1000">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-muted-foreground transition-transform duration-300 hover:scale-[1.05]" />
              <span className="text-sm font-medium">{t('system.disk-usage')}</span>
            </div>
            <span
              className={`text-sm font-semibold ${getUsageColor(disk.usagePercentage)} transition-all duration-300 hover:scale-[1.05]`}
            >
              {disk.usagePercentage.toFixed(1)}%
            </span>
          </div>
          <div className="animate-in slide-in-from-left-full duration-1000 delay-1100">
            <Progress
              value={disk.usagePercentage}
              className="h-2"
              indicatorClassName={getProgressColor(disk.usagePercentage)}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground animate-in fade-in duration-300 delay-1200">
            <span className="transition-colors duration-200 hover:text-foreground">
              {t('system.used', { amount: formatBytes(disk.used) })}
            </span>
            <span className="transition-colors duration-200 hover:text-foreground">
              {t('system.total', { amount: formatBytes(disk.total) })}
            </span>
          </div>
        </div>

        {/* Last Updated */}
        <div className="pt-2 border-t animate-in fade-in duration-500 delay-1300">
          <p className="text-xs text-muted-foreground transition-colors duration-200 hover:text-foreground">
            {t('system.last-updated', {
              time: new Date(resources.lastUpdated).toLocaleString('zh-TW'),
            })}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
