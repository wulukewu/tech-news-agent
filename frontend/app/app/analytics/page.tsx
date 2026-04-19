'use client';

import { useI18n } from '@/contexts/I18nContext';

export default function AnalyticsPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('analytics.title')}</h1>
          <p className="text-muted-foreground">{t('analytics.description')}</p>
        </div>
      </div>

      {/* Analytics Dashboard will be implemented in future tasks */}
      <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-semibold mb-2">{t('analytics.advanced-dashboard')}</h3>
          <p className="text-muted-foreground mb-4">{t('analytics.coming-soon')}</p>
          <div className="text-sm text-muted-foreground">{t('analytics.features-preview')}</div>
        </div>
      </div>
    </div>
  );
}
