'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Palette, Sun, Moon, Monitor, Check } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useI18n } from '@/contexts/I18nContext';
import { useEffect, useState } from 'react';

export default function AppearancePage() {
  const { t } = useI18n();
  const { theme, setTheme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="pt-6">
            <div className="h-32 bg-muted animate-pulse rounded" />
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentTheme = theme === 'system' ? systemTheme : theme;

  const themes = [
    {
      id: 'light',
      name: t('theme.light'),
      description: t('pages.appearance.light-theme'),
      icon: Sun,
    },
    {
      id: 'dark',
      name: t('theme.dark'),
      description: t('pages.appearance.dark-theme'),
      icon: Moon,
    },
    {
      id: 'system',
      name: t('theme.system'),
      description: t('pages.appearance.system-theme'),
      icon: Monitor,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('pages.appearance.title')}</h1>
        <p className="text-muted-foreground text-sm">{t('pages.appearance.description')}</p>
      </div>

      {/* Theme Selection */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Palette className="h-5 w-5" />
            <div>
              <CardTitle>{t('pages.appearance.theme')}</CardTitle>
              <CardDescription>{t('pages.appearance.theme-description')}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3">
            {themes.map((themeOption) => {
              const Icon = themeOption.icon;
              const isSelected = theme === themeOption.id;

              return (
                <div key={themeOption.id} className="relative">
                  <Button
                    variant={isSelected ? 'default' : 'outline'}
                    className="w-full justify-start h-auto p-4"
                    onClick={() => setTheme(themeOption.id)}
                  >
                    <div className="flex items-center gap-3 w-full">
                      <Icon className="h-5 w-5" />
                      <div className="flex-1 text-left">
                        <div className="font-medium">{themeOption.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {themeOption.description}
                        </div>
                      </div>
                      {isSelected && <Check className="h-4 w-4" />}
                    </div>
                  </Button>
                </div>
              );
            })}
          </div>

          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm font-medium">{t('pages.appearance.current-theme')}</Label>
                <p className="text-sm text-muted-foreground">
                  {theme === 'system'
                    ? t('pages.appearance.system-with-mode', {
                        mode:
                          currentTheme === 'dark'
                            ? t('pages.appearance.dark-mode')
                            : t('pages.appearance.light-mode'),
                      })
                    : themes.find((t) => t.id === theme)?.name}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {currentTheme === 'dark' ? (
                  <Moon className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Sun className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Theme Preview */}
      <Card>
        <CardHeader>
          <CardTitle>{t('pages.appearance.preview')}</CardTitle>
          <CardDescription>{t('pages.appearance.preview-description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Sample UI Elements */}
            <div className="p-4 border rounded-lg bg-card">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{t('pages.appearance.sample-title')}</h3>
                  <div className="text-xs text-muted-foreground">
                    {t('pages.appearance.sample-time')}
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  {t('pages.appearance.sample-content')}
                </p>
                <div className="flex gap-2">
                  <Button size="sm" variant="default">
                    {t('pages.appearance.primary-button')}
                  </Button>
                  <Button size="sm" variant="outline">
                    {t('pages.appearance.secondary-button')}
                  </Button>
                  <Button size="sm" variant="ghost">
                    {t('pages.appearance.text-button')}
                  </Button>
                </div>
              </div>
            </div>

            <div className="text-xs text-muted-foreground">
              {t('pages.appearance.theme-applies-immediately')}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Future Features */}
      <Card>
        <CardHeader>
          <CardTitle>{t('pages.appearance.coming-soon')}</CardTitle>
          <CardDescription>{t('pages.appearance.future-features')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 text-sm text-muted-foreground">
            <div>• {t('pages.appearance.custom-colors')}</div>
            <div>• {t('pages.appearance.font-size')}</div>
            <div>• {t('pages.appearance.layout-mode')}</div>
            <div>• {t('pages.appearance.high-contrast')}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
