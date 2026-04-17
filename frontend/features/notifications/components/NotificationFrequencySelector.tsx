'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { NotificationFrequency } from '@/types/notification';
import { Clock, Zap, Calendar, CalendarDays } from 'lucide-react';

interface NotificationFrequencySelectorProps {
  frequency: NotificationFrequency;
  onFrequencyChange: (frequency: NotificationFrequency) => void;
  disabled?: boolean;
}

const frequencyOptions = [
  {
    value: 'immediate' as NotificationFrequency,
    label: '即時通知',
    description: '新文章發布時立即通知',
    icon: Zap,
  },
  {
    value: 'daily' as NotificationFrequency,
    label: '每日摘要',
    description: '每天一次彙整通知',
    icon: Calendar,
  },
  {
    value: 'weekly' as NotificationFrequency,
    label: '每週摘要',
    description: '每週一次彙整通知',
    icon: CalendarDays,
  },
];

export function NotificationFrequencySelector({
  frequency,
  onFrequencyChange,
  disabled = false,
}: NotificationFrequencySelectorProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          通知頻率
        </CardTitle>
        <CardDescription>選擇您希望接收通知的頻率</CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup
          value={frequency || 'immediate'}
          onValueChange={(value) => onFrequencyChange(value as NotificationFrequency)}
          disabled={disabled}
          className="space-y-3"
        >
          {frequencyOptions.map((option) => {
            const Icon = option.icon;
            return (
              <div
                key={option.value}
                className="flex items-center space-x-3 rounded-lg border p-4 hover:bg-accent/50 transition-colors"
              >
                <RadioGroupItem value={option.value} id={option.value} />
                <Label
                  htmlFor={option.value}
                  className="flex-1 cursor-pointer flex items-start gap-3"
                >
                  <Icon className="h-5 w-5 mt-0.5 text-muted-foreground" />
                  <div className="space-y-1">
                    <p className="font-medium leading-none">{option.label}</p>
                    <p className="text-sm text-muted-foreground">{option.description}</p>
                  </div>
                </Label>
              </div>
            );
          })}
        </RadioGroup>
      </CardContent>
    </Card>
  );
}
