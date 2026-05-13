'use client';

import { Card, CardContent } from '@/components/ui/card';
import { useI18n } from '@/contexts/I18nContext';
import type { Feed } from '@/types/feed';

export function HealthStatsGrid({ feeds, subscribed }: { feeds: Feed[]; subscribed?: boolean }) {
  const { t } = useI18n();
  const filtered = subscribed ? feeds.filter((f) => f.is_subscribed) : feeds;
  const stats = [
    { key: 'healthy', label: t('ui.health-healthy'), dot: 'bg-green-500' },
    { key: 'warning', label: t('ui.health-stale'), dot: 'bg-yellow-500' },
    { key: 'error', label: t('ui.health-error'), dot: 'bg-red-500' },
    { key: 'unknown', label: t('ui.health-unknown'), dot: 'bg-muted-foreground' },
  ] as const;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {stats.map(({ key, label, dot }) => (
        <Card key={key}>
          <CardContent className="p-3">
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dot}`} />
              <div className="min-w-0">
                <div className="text-xs text-muted-foreground truncate">{label}</div>
                <div className="text-lg font-semibold tabular-nums">
                  {
                    filtered.filter((f) =>
                      key === 'unknown'
                        ? f.health_status === 'unknown' || !f.health_status
                        : f.health_status === key
                    ).length
                  }
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
