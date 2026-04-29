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
      description: '明亮的外觀，適合白天使用',
      icon: Sun,
    },
    {
      id: 'dark',
      name: t('theme.dark'),
      description: '深色的外觀，適合夜間使用',
      icon: Moon,
    },
    {
      id: 'system',
      name: t('theme.system'),
      description: '跟隨系統設定自動切換',
      icon: Monitor,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">外觀</h1>
        <p className="text-muted-foreground text-sm">自訂應用程式的外觀和主題</p>
      </div>

      {/* Theme Selection */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Palette className="h-5 w-5" />
            <div>
              <CardTitle>主題</CardTitle>
              <CardDescription>選擇您偏好的外觀主題</CardDescription>
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
                <Label className="text-sm font-medium">目前主題</Label>
                <p className="text-sm text-muted-foreground">
                  {theme === 'system'
                    ? `系統 (${currentTheme === 'dark' ? '深色' : '明亮'})`
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
          <CardTitle>預覽</CardTitle>
          <CardDescription>查看目前主題的外觀</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Sample UI Elements */}
            <div className="p-4 border rounded-lg bg-card">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">範例文章標題</h3>
                  <div className="text-xs text-muted-foreground">2 小時前</div>
                </div>
                <p className="text-sm text-muted-foreground">
                  這是一個範例文章的摘要內容，用來展示目前主題的文字顏色和對比度。
                </p>
                <div className="flex gap-2">
                  <Button size="sm" variant="default">
                    主要按鈕
                  </Button>
                  <Button size="sm" variant="outline">
                    次要按鈕
                  </Button>
                  <Button size="sm" variant="ghost">
                    文字按鈕
                  </Button>
                </div>
              </div>
            </div>

            <div className="text-xs text-muted-foreground">主題變更會立即套用到整個應用程式</div>
          </div>
        </CardContent>
      </Card>

      {/* Future Features */}
      <Card>
        <CardHeader>
          <CardTitle>即將推出</CardTitle>
          <CardDescription>未來的外觀自訂功能</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 text-sm text-muted-foreground">
            <div>• 自訂主色調</div>
            <div>• 字體大小調整</div>
            <div>• 緊湊/寬鬆佈局模式</div>
            <div>• 高對比度模式</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
