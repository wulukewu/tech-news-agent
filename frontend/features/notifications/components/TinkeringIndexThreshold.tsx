'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Star } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

interface TinkeringIndexThresholdProps {
  threshold: number;
  onThresholdChange: (threshold: number) => void;
  disabled?: boolean;
}

export function TinkeringIndexThreshold({
  threshold,
  onThresholdChange,
  disabled = false,
}: TinkeringIndexThresholdProps) {
  const { t } = useI18n();

  const thresholdLabels = [
    {
      value: 1,
      label: t('settings.notifications.threshold-all'),
      description: t('settings.notifications.threshold-all-desc'),
    },
    {
      value: 2,
      label: t('settings.notifications.threshold-basic'),
      description: t('settings.notifications.threshold-basic-desc'),
    },
    {
      value: 3,
      label: t('settings.notifications.threshold-intermediate'),
      description: t('settings.notifications.threshold-intermediate-desc'),
    },
    {
      value: 4,
      label: t('settings.notifications.threshold-advanced'),
      description: t('settings.notifications.threshold-advanced-desc'),
    },
    {
      value: 5,
      label: t('settings.notifications.threshold-expert'),
      description: t('settings.notifications.threshold-expert-desc'),
    },
  ];

  // Provide default value if threshold is undefined
  const safeThreshold = threshold || 3;
  const currentLabel = thresholdLabels.find((l) => l.value === safeThreshold) || thresholdLabels[2];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Star className="h-5 w-5" />
          {t('settings.notifications.threshold-title')}
        </CardTitle>
        <CardDescription>{t('settings.notifications.threshold-desc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>{t('settings.notifications.min-threshold')}</Label>
            <div className="flex items-center gap-1">
              {Array.from({ length: safeThreshold }).map((_, i) => (
                <Star
                  key={i}
                  className="h-4 w-4 fill-yellow-400 text-yellow-400"
                  data-testid={`star-filled-${i}`}
                />
              ))}
              {Array.from({ length: 5 - safeThreshold }).map((_, i) => (
                <Star
                  key={i + safeThreshold}
                  className="h-4 w-4 text-muted-foreground"
                  data-testid={`star-empty-${i + safeThreshold}`}
                />
              ))}
            </div>
          </div>

          <Slider
            value={[safeThreshold]}
            onValueChange={([value]) => onThresholdChange(value)}
            min={1}
            max={5}
            step={1}
            disabled={disabled}
            className="w-full"
          />

          <div className="rounded-lg bg-muted p-4">
            <p className="font-medium">{currentLabel.label}</p>
            <p className="text-sm text-muted-foreground mt-1">{currentLabel.description}</p>
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium">{t('settings.notifications.threshold-explanation')}</p>
          <div className="space-y-1 text-sm text-muted-foreground">
            {thresholdLabels.map((label) => (
              <div key={label.value} className="flex items-center gap-2">
                <div className="flex items-center gap-0.5">
                  {Array.from({ length: label.value }).map((_, i) => (
                    <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <span>- {label.description}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
