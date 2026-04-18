'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings } from 'lucide-react';

export default function PreferencesPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Settings className="h-5 w-5" />
            <div>
              <CardTitle>偏好設定</CardTitle>
              <CardDescription>管理一般偏好設定</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-lg font-medium text-muted-foreground">即將推出</p>
            <p className="text-sm text-muted-foreground mt-2">
              預設排序方式、每頁顯示數量和其他偏好設定功能正在開發中
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
