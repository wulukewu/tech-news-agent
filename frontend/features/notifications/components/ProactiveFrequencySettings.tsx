'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Sparkles } from 'lucide-react';
import { toast } from '@/lib/toast';
import {
  getProactiveFrequency,
  updateProactiveFrequency,
  ProactiveFrequency,
} from '@/lib/api/notifications';

const FREQUENCY_LABELS: Record<ProactiveFrequency, string> = {
  daily: '每天',
  every_two_days: '每兩天',
  weekly: '每週',
};

export function ProactiveFrequencySettings() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['proactiveFrequency'],
    queryFn: getProactiveFrequency,
  });

  const mutation = useMutation({
    mutationFn: updateProactiveFrequency,
    onSuccess: (updated) => {
      queryClient.setQueryData(['proactiveFrequency'], updated);
      toast.success('已更新個人化推薦頻率');
    },
    onError: () => toast.error('更新失敗，請稍後再試'),
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-muted-foreground" />
          <div>
            <CardTitle>個人化推薦頻率</CardTitle>
            <CardDescription>
              每次系統抓完新文章後，AI 會主動推薦最相關的文章給你。設定收到推薦 DM 的頻率。
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Select
          value={data?.frequency ?? 'daily'}
          onValueChange={(v) => mutation.mutate(v as ProactiveFrequency)}
          disabled={isLoading || mutation.isPending}
        >
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(FREQUENCY_LABELS) as ProactiveFrequency[]).map((freq) => (
              <SelectItem key={freq} value={freq}>
                {FREQUENCY_LABELS[freq]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardContent>
    </Card>
  );
}
