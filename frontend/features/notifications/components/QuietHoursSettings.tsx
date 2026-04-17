'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Moon } from 'lucide-react';

interface QuietHoursSettingsProps {
  quietHours?: {
    enabled: boolean;
    start: string;
    end: string;
  };
  onQuietHoursChange: (quietHours: { enabled: boolean; start: string; end: string }) => void;
  disabled?: boolean;
}

export function QuietHoursSettings({
  quietHours,
  onQuietHoursChange,
  disabled = false,
}: QuietHoursSettingsProps) {
  // Provide default values if quietHours is undefined
  const safeQuietHours = quietHours || {
    enabled: false,
    start: '22:00',
    end: '08:00',
  };

  const handleToggle = (enabled: boolean) => {
    onQuietHoursChange({ ...safeQuietHours, enabled });
  };

  const handleStartChange = (start: string) => {
    onQuietHoursChange({ ...safeQuietHours, start });
  };

  const handleEndChange = (end: string) => {
    onQuietHoursChange({ ...safeQuietHours, end });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Moon className="h-5 w-5" />
          勿擾時段
        </CardTitle>
        <CardDescription>設定您不希望接收通知的時段</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="quiet-hours-enabled">啟用勿擾時段</Label>
            <p className="text-sm text-muted-foreground">在指定時段內暫停通知</p>
          </div>
          <Switch
            id="quiet-hours-enabled"
            checked={safeQuietHours.enabled}
            onCheckedChange={handleToggle}
            disabled={disabled}
          />
        </div>

        {safeQuietHours.enabled && (
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="space-y-2">
              <Label htmlFor="quiet-hours-start">開始時間</Label>
              <Input
                id="quiet-hours-start"
                type="time"
                value={safeQuietHours.start}
                onChange={(e) => handleStartChange(e.target.value)}
                disabled={disabled}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="quiet-hours-end">結束時間</Label>
              <Input
                id="quiet-hours-end"
                type="time"
                value={safeQuietHours.end}
                onChange={(e) => handleEndChange(e.target.value)}
                disabled={disabled}
              />
            </div>
          </div>
        )}

        {safeQuietHours.enabled && (
          <p className="text-sm text-muted-foreground">
            通知將在 {safeQuietHours.start} 至 {safeQuietHours.end} 期間暫停
          </p>
        )}
      </CardContent>
    </Card>
  );
}
