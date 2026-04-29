'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useI18n } from '@/contexts/I18nContext';

export default function SystemStatusSettingsPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.system-status')}</h1>
        <p className="text-muted-foreground text-sm">查看系統健康狀態和服務狀況</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>系統監控</CardTitle>
          <CardDescription>系統狀態和服務健康檢查</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">系統狀態功能開發中...</p>
        </CardContent>
      </Card>
    </div>
  );
}
