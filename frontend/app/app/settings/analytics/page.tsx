'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useI18n } from '@/contexts/I18nContext';

export default function AnalyticsSettingsPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.analytics')}</h1>
        <p className="text-muted-foreground text-sm">查看您的閱讀統計和活動分析</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>分析設定</CardTitle>
          <CardDescription>管理您的數據收集和分析偏好</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">分析功能開發中...</p>
        </CardContent>
      </Card>
    </div>
  );
}
