import { Metadata } from 'next';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bell, Palette, ChevronRight } from 'lucide-react';

export const metadata: Metadata = {
  title: '設定',
  description: '管理您的帳戶設定和偏好',
};

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">設定</h1>
          <p className="text-muted-foreground">管理您的帳戶設定和個人偏好</p>
        </div>
      </div>

      {/* Settings panels */}
      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bell className="h-5 w-5" />
                <div>
                  <CardTitle>通知偏好設定</CardTitle>
                  <CardDescription>管理您的通知偏好和頻率設定</CardDescription>
                </div>
              </div>
              <Link href="/dashboard/settings/notifications">
                <Button variant="ghost" size="sm">
                  設定
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              自訂通知頻率、勿擾時段、技術深度閾值和個別來源通知設定
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Palette className="h-5 w-5" />
              <div>
                <CardTitle>介面設定</CardTitle>
                <CardDescription>自訂主題、語言和顯示偏好</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">深色模式和多語言支援即將推出</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
