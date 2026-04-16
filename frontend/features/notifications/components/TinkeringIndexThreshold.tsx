'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Star } from 'lucide-react';

interface TinkeringIndexThresholdProps {
  threshold: number;
  onThresholdChange: (threshold: number) => void;
  disabled?: boolean;
}

const thresholdLabels = [
  { value: 1, label: '所有文章', description: '接收所有新文章通知' },
  { value: 2, label: '基礎技術', description: '包含基礎技術內容' },
  { value: 3, label: '中等深度', description: '需要一定技術背景' },
  { value: 4, label: '進階技術', description: '深入的技術討論' },
  { value: 5, label: '專家級', description: '僅限最深入的技術文章' },
];

export function TinkeringIndexThreshold({
  threshold,
  onThresholdChange,
  disabled = false,
}: TinkeringIndexThresholdProps) {
  const currentLabel = thresholdLabels.find((l) => l.value === threshold) || thresholdLabels[2];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Star className="h-5 w-5" />
          技術深度閾值
        </CardTitle>
        <CardDescription>設定接收通知的最低技術深度要求</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>最低技術深度指數</Label>
            <div className="flex items-center gap-1">
              {Array.from({ length: threshold }).map((_, i) => (
                <Star
                  key={i}
                  className="h-4 w-4 fill-yellow-400 text-yellow-400"
                  data-testid={`star-filled-${i}`}
                />
              ))}
              {Array.from({ length: 5 - threshold }).map((_, i) => (
                <Star
                  key={i + threshold}
                  className="h-4 w-4 text-muted-foreground"
                  data-testid={`star-empty-${i + threshold}`}
                />
              ))}
            </div>
          </div>

          <Slider
            value={[threshold]}
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
          <p className="text-sm font-medium">技術深度說明</p>
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
