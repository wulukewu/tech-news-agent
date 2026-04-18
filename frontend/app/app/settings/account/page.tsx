'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { User } from 'lucide-react';

export default function AccountPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <User className="h-5 w-5" />
            <div>
              <CardTitle>帳戶設定</CardTitle>
              <CardDescription>管理個人資料和安全性設定</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <User className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-lg font-medium text-muted-foreground">即將推出</p>
            <p className="text-sm text-muted-foreground mt-2">
              個人資料編輯、密碼變更和帳戶安全功能正在開發中
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
