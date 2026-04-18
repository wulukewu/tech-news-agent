'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Palette } from 'lucide-react';

export default function AppearancePage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Palette className="h-5 w-5" />
            <div>
              <CardTitle>外觀設定</CardTitle>
              <CardDescription>自訂主題、語言和顯示偏好</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Palette className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-lg font-medium text-muted-foreground">即將推出</p>
            <p className="text-sm text-muted-foreground mt-2">
              深色模式、語言選擇和其他外觀設定功能正在開發中
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
