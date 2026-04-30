'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { User } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

export default function AccountPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-lg transition-all">
        <CardHeader>
          <div className="flex items-center gap-3 animate-in slide-in-from-left-4 duration-500 delay-200">
            <div className="p-2 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-300 hover:scale-110 transition-transform">
              <User className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="animate-in fade-in duration-500 delay-400">
                {t('settings.account.title')}
              </CardTitle>
              <CardDescription className="animate-in fade-in duration-500 delay-500">
                {t('settings.account.description')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-600">
            <div className="relative inline-block animate-in zoom-in-50 duration-500 delay-700">
              <User className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50 animate-pulse" />
              <div className="absolute inset-0 h-12 w-12 mx-auto text-muted-foreground/20 animate-ping">
                <User className="h-12 w-12" />
              </div>
            </div>
            <p className="text-lg font-medium text-muted-foreground animate-in slide-in-from-bottom-2 duration-500 delay-800">
              {t('settings.account.placeholder')}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
