/**
 * System Status Page
 *
 * Displays system monitoring dashboard with scheduler status,
 * system health metrics, feed status information, and resource usage.
 *
 * Features real-time updates through polling and permission verification.
 *
 * Requirements: 5.1, 5.2, 5.3, 5.7, 5.8, 5.10
 */

'use client';

import { useState } from 'react';
import { Metadata } from 'next';
import {
  SchedulerStatusWidget,
  ManualFetchDialog,
  SystemHealthCard,
  FetchStatisticsCard,
  FeedStatusCard,
  SystemResourcesCard,
  PermissionGuard,
} from '@/features/system-monitor/components';
import {
  useSystemStatus,
  useTriggerManualFetch,
} from '@/features/system-monitor/hooks/useSystemStatus';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * System Status Page Component
 *
 * Main page for system monitoring, displaying:
 * - Scheduler status and execution information
 * - Manual fetch trigger with confirmation
 * - System health metrics (database, API, errors)
 * - Fetch statistics (articles processed, success rate)
 * - Feed status information with health indicators
 * - System resource usage (CPU, memory, disk) if available
 *
 * Features:
 * - Real-time updates via polling (every 30 seconds)
 * - Permission verification (authenticated users only)
 * - Manual refresh capability
 *
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.10
 */
function SystemStatusPageContent() {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Fetch complete system status with auto-refresh every 30 seconds (Requirement 5.7)
  const {
    data: systemStatus,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useSystemStatus({
    refetchInterval: 30000, // 30 seconds for real-time updates
  });

  // Manual fetch mutation
  const triggerMutation = useTriggerManualFetch();

  const handleTriggerClick = () => {
    setShowConfirmDialog(true);
  };

  const handleConfirmTrigger = () => {
    triggerMutation.mutate();
  };

  const handleManualRefresh = () => {
    refetch();
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">系統狀態</h1>
            <p className="text-muted-foreground">
              監控系統健康度和排程器執行狀況
              {dataUpdatedAt && (
                <span className="ml-2 text-xs">
                  (最後更新: {new Date(dataUpdatedAt).toLocaleTimeString('zh-TW')})
                </span>
              )}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={handleManualRefresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            手動重新整理
          </Button>
        </div>

        {/* Main Content */}
        <div className="grid gap-6">
          {/* Scheduler Status Widget */}
          {isLoading ? (
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              </CardContent>
            </Card>
          ) : error ? (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-5 w-5" />
                  <p>無法載入系統狀態</p>
                </div>
              </CardContent>
            </Card>
          ) : systemStatus ? (
            <>
              {/* Scheduler Status */}
              <SchedulerStatusWidget
                status={systemStatus.scheduler}
                isTriggering={triggerMutation.isPending}
                onTrigger={handleTriggerClick}
              />

              {/* System Health Metrics */}
              <SystemHealthCard health={systemStatus.health} />

              {/* System Resources (Requirement 5.8) */}
              <SystemResourcesCard resources={systemStatus.resources} />

              {/* Fetch Statistics */}
              <FetchStatisticsCard statistics={systemStatus.statistics} />

              {/* Feed Status */}
              <FeedStatusCard feeds={systemStatus.feeds} />
            </>
          ) : null}
        </div>

        {/* Real-time Update Indicator */}
        <div className="flex items-center justify-center">
          <p className="text-xs text-muted-foreground">
            <RefreshCw className="inline h-3 w-3 mr-1" />
            自動更新每 30 秒執行一次
          </p>
        </div>
      </div>

      {/* Manual Fetch Confirmation Dialog */}
      <ManualFetchDialog
        open={showConfirmDialog}
        onOpenChange={setShowConfirmDialog}
        onConfirm={handleConfirmTrigger}
        isLoading={triggerMutation.isPending}
      />
    </div>
  );
}

/**
 * System Status Page with Permission Guard
 *
 * Wraps the page content with permission verification.
 *
 * Requirements: 5.10
 */
export default function SystemStatusPage() {
  return (
    <PermissionGuard>
      <SystemStatusPageContent />
    </PermissionGuard>
  );
}
