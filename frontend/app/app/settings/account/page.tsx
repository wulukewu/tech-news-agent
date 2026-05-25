'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { User } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

export default function AccountPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <Card className="animate-in fade-in slide-in-from-bottom-2 duration-300 hover-spring active-tap border-muted">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary transition-transform duration-200 group-hover:scale-[1.1]">
              <User className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>{t('settings.account.title')}</CardTitle>
              <CardDescription>{t('settings.account.description')}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <div className="relative inline-block">
              <User className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50 animate-pulse" />
              <div className="absolute inset-0 h-12 w-12 mx-auto text-muted-foreground/20 animate-ping">
                <User className="h-12 w-12" />
              </div>
            </div>
            <p className="text-lg font-medium text-muted-foreground">
              {t('settings.account.placeholder')}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
