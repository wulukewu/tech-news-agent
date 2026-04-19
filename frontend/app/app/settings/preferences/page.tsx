'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

export default function PreferencesPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Settings className="h-5 w-5" />
            <div>
              <CardTitle>{t('settings.preferences.title')}</CardTitle>
              <CardDescription>{t('settings.preferences.description')}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-lg font-medium text-muted-foreground">
              {t('analytics.coming-soon')}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {t('settings.preferences.placeholder')}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
