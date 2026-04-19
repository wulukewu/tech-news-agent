'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { NotificationFrequency } from '@/types/notification';
import { useI18n } from '@/contexts/I18nContext';
import type { TranslationKey } from '@/types/i18n';
import { Clock, Zap, Calendar, CalendarDays, BellOff } from 'lucide-react';

interface NotificationFrequencySelectorProps {
  frequency: NotificationFrequency;
  onFrequencyChange: (frequency: NotificationFrequency) => void;
  disabled?: boolean;
}

interface FrequencyOption {
  value: NotificationFrequency;
  labelKey: TranslationKey;
  descriptionKey: TranslationKey;
  icon: React.ComponentType<{ className?: string }>;
}

const frequencyOptions: FrequencyOption[] = [
  {
    value: 'immediate' as NotificationFrequency,
    labelKey: 'notification-frequency.immediate',
    descriptionKey: 'notification-frequency.immediate-desc',
    icon: Zap,
  },
  {
    value: 'daily' as NotificationFrequency,
    labelKey: 'notification-frequency.daily',
    descriptionKey: 'notification-frequency.daily-desc',
    icon: Calendar,
  },
  {
    value: 'weekly' as NotificationFrequency,
    labelKey: 'notification-frequency.weekly',
    descriptionKey: 'notification-frequency.weekly-desc',
    icon: CalendarDays,
  },
  {
    value: 'disabled' as NotificationFrequency,
    labelKey: 'notification-frequency.disabled',
    descriptionKey: 'notification-frequency.disabled-desc',
    icon: BellOff,
  },
];

export function NotificationFrequencySelector({
  frequency,
  onFrequencyChange,
  disabled = false,
}: NotificationFrequencySelectorProps) {
  const { t } = useI18n();

  // Memoize translated frequency options to prevent re-translation on every render
  // Requirements: 8.6 - Performance optimization with useMemo
  const translatedFrequencyOptions = useMemo(
    () =>
      frequencyOptions.map((option) => ({
        ...option,
        translatedLabel: t(option.labelKey),
        translatedDescription: t(option.descriptionKey),
      })),
    [t]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          {t('notification-frequency.title')}
        </CardTitle>
        <CardDescription>{t('notification-frequency.description')}</CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup
          value={frequency || 'immediate'}
          onValueChange={(value) => onFrequencyChange(value as NotificationFrequency)}
          disabled={disabled}
          className="space-y-3"
        >
          {translatedFrequencyOptions.map((option) => {
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
                    <p className="font-medium leading-none">{option.translatedLabel}</p>
                    <p className="text-sm text-muted-foreground">{option.translatedDescription}</p>
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
