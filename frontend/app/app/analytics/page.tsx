import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '分析儀表板',
  description: '閱讀習慣和偏好趨勢分析',
};

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">分析儀表板</h1>
          <p className="text-muted-foreground">深入了解您的閱讀習慣和偏好趨勢</p>
        </div>
      </div>

      {/* Analytics Dashboard will be implemented in future tasks */}
      <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-semibold mb-2">進階分析儀表板</h3>
          <p className="text-muted-foreground mb-4">詳細的閱讀分析功能即將推出</p>
          <div className="text-sm text-muted-foreground">
            將提供閱讀活動圖表、分類偏好分析、生產力指標等功能
          </div>
        </div>
      </div>
    </div>
  );
}
