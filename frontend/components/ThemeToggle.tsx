'use client';

import * as React from 'react';
import { Moon, Sun, Monitor, Palette } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';

interface ThemeToggleProps {
  variant?: 'button' | 'dropdown' | 'icon';
  size?: 'sm' | 'default' | 'lg';
  showLabel?: boolean;
}

export function ThemeToggle({
  variant = 'button',
  size = 'default',
  showLabel = false,
}: ThemeToggleProps) {
  const { theme, setTheme, systemTheme } = useTheme();
  const { t } = useI18n();
  const [mounted, setMounted] = React.useState(false);

  // useEffect only runs on the client, so now we can safely show the UI
  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" disabled>
        <Sun className="h-5 w-5" />
      </Button>
    );
  }

  const currentTheme = theme === 'system' ? systemTheme : theme;

  // Get theme icon
  const getThemeIcon = (themeName: string) => {
    switch (themeName) {
      case 'dark':
        return <Moon className="h-4 w-4" />;
      case 'light':
        return <Sun className="h-4 w-4" />;
      case 'system':
        return <Monitor className="h-4 w-4" />;
      default:
        return <Palette className="h-4 w-4" />;
    }
  };

  // Get theme label
  const getThemeLabel = (themeName: string) => {
    switch (themeName) {
      case 'dark':
        return t('theme.dark');
      case 'light':
        return t('theme.light');
      case 'system':
        return t('theme.system');
      default:
        return themeName;
    }
  };

  if (variant === 'dropdown') {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            aria-label={t('theme.toggle')}
            className="transition-all duration-300 hover:scale-[1.02]"
          >
            {currentTheme === 'dark' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuLabel>{t('theme.select')}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {['light', 'dark', 'system'].map((themeName) => (
            <DropdownMenuItem
              key={themeName}
              onClick={() => setTheme(themeName)}
              className={theme === themeName ? 'bg-accent' : ''}
            >
              <div className="flex items-center gap-2">
                {getThemeIcon(themeName)}
                <span>{getThemeLabel(themeName)}</span>
                {theme === themeName && <div className="ml-auto h-2 w-2 bg-primary rounded-full" />}
              </div>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  if (variant === 'icon') {
    const cycleTheme = () => {
      const themes = ['light', 'dark', 'system'];
      const currentIndex = themes.indexOf(theme || 'light');
      const nextIndex = (currentIndex + 1) % themes.length;
      setTheme(themes[nextIndex]);
    };

    const getIconForTheme = () => {
      return (
        <>
          <Sun
            className={`h-5 w-5 transition-all duration-300 ${
              theme === 'light' ? 'rotate-0 scale-100' : 'rotate-90 scale-0'
            }`}
          />
          <Moon
            className={`absolute h-5 w-5 transition-all duration-300 ${
              theme === 'dark' ? 'rotate-0 scale-100' : '-rotate-90 scale-0'
            }`}
          />
          <Monitor
            className={`absolute h-5 w-5 transition-all duration-300 ${
              theme === 'system' ? 'scale-100' : 'scale-0'
            }`}
          />
        </>
      );
    };

    return (
      <Button
        variant="ghost"
        size="icon"
        onClick={cycleTheme}
        aria-label={t('theme.toggle')}
        className="transition-all duration-300 hover:scale-[1.02]"
      >
        {getIconForTheme()}
      </Button>
    );
  }

  if (showLabel) {
    const targetMode = currentTheme === 'dark' ? t('theme.light') : t('theme.dark');
    return (
      <Button
        variant="ghost"
        onClick={() => setTheme(currentTheme === 'dark' ? 'light' : 'dark')}
        aria-label={t('theme.switch-to', { mode: targetMode })}
        className="transition-all duration-300 hover:scale-[1.02] gap-2"
        size={size}
      >
        <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
        <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        <span className="text-sm">{getThemeLabel(currentTheme || 'light')}</span>
      </Button>
    );
  }

  const targetMode = currentTheme === 'dark' ? t('theme.light') : t('theme.dark');
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(currentTheme === 'dark' ? 'light' : 'dark')}
      aria-label={t('theme.switch-to', { mode: targetMode })}
      className="transition-all duration-300 hover:scale-[1.02]"
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
