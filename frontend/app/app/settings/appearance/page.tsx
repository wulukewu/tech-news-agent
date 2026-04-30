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
      <div className="animate-in fade-in-50 slide-in-from-top-4 duration-500">
        <h1 className="text-2xl font-bold">{t('pages.appearance.title')}</h1>
        <p className="text-muted-foreground text-sm">{t('pages.appearance.description')}</p>
      </div>

      {/* Theme Selection */}
      <Card className="animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-100 hover:shadow-lg transition-all">
        <CardHeader>
          <div className="flex items-center gap-3">
            <Palette className="h-5 w-5 transition-transform duration-200 hover:scale-110" />
            <div>
              <CardTitle>{t('pages.appearance.theme')}</CardTitle>
              <CardDescription>{t('pages.appearance.theme-description')}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3">
            {themes.map((themeOption, index) => {
              const Icon = themeOption.icon;
              const isSelected = theme === themeOption.id;

              return (
                <div
                  key={themeOption.id}
                  className="relative animate-in slide-in-from-left-2 duration-500"
                  style={{ animationDelay: `${200 + index * 100}ms` }}
                >
                  <Button
                    variant={isSelected ? 'default' : 'outline'}
                    className="w-full justify-start h-auto p-4 transition-all duration-200 hover:scale-[1.02] hover:shadow-md group"
                    onClick={() => setTheme(themeOption.id)}
                  >
                    <div className="flex items-center gap-3 w-full">
                      <Icon className="h-5 w-5 transition-transform duration-200 group-hover:scale-110" />
                      <div className="flex-1 text-left">
                        <div className="font-medium">{themeOption.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {themeOption.description}
                        </div>
                      </div>
                      {isSelected && (
                        <Check className="h-4 w-4 animate-in zoom-in-50 duration-300" />
                      )}
                    </div>
                  </Button>
                </div>
              );
            })}
          </div>

          <div className="pt-4 border-t animate-in fade-in-50 duration-500 delay-500">
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
                  <Moon className="h-4 w-4 text-muted-foreground animate-pulse" />
                ) : (
                  <Sun className="h-4 w-4 text-muted-foreground animate-pulse" />
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Theme Preview */}
      <Card className="animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-200 hover:shadow-lg transition-all">
        <CardHeader>
          <CardTitle>{t('pages.appearance.preview')}</CardTitle>
          <CardDescription>{t('pages.appearance.preview-description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Sample UI Elements */}
            <div className="p-4 border rounded-lg bg-card transition-all duration-300 hover:shadow-md hover:scale-[1.01]">
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
                  <Button
                    size="sm"
                    variant="default"
                    className="transition-all duration-200 hover:scale-105 hover:shadow-md"
                  >
                    {t('pages.appearance.primary-button')}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="transition-all duration-200 hover:scale-105 hover:shadow-sm"
                  >
                    {t('pages.appearance.secondary-button')}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="transition-all duration-200 hover:scale-105"
                  >
                    {t('pages.appearance.text-button')}
                  </Button>
                </div>
              </div>
            </div>

            <div className="text-xs text-muted-foreground animate-in fade-in-50 duration-500 delay-600">
              {t('pages.appearance.theme-applies-immediately')}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Future Features */}
      <Card className="animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-300 hover:shadow-lg transition-all">
        <CardHeader>
          <CardTitle>{t('pages.appearance.coming-soon')}</CardTitle>
          <CardDescription>{t('pages.appearance.future-features')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 text-sm text-muted-foreground">
            {[
              t('pages.appearance.custom-colors'),
              t('pages.appearance.font-size'),
              t('pages.appearance.layout-mode'),
              t('pages.appearance.high-contrast'),
            ].map((feature, index) => (
              <div
                key={feature}
                className="animate-in slide-in-from-left-2 duration-500"
                style={{ animationDelay: `${400 + index * 100}ms` }}
              >
                • {feature}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
