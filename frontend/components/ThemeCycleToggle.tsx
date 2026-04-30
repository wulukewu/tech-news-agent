'use client';

import * as React from 'react';
import { Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';

interface ThemeCycleToggleProps {
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export function ThemeCycleToggle({ size = 'default', className = '' }: ThemeCycleToggleProps) {
  const { theme, setTheme } = useTheme();
  const { t } = useI18n();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" disabled className={className}>
        <Sun className="h-5 w-5" />
      </Button>
    );
  }

  const cycleTheme = () => {
    const themes = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(theme || 'light');
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycleTheme}
      aria-label={t('theme.toggle')}
      className={`transition-all duration-200 hover:scale-105 ${className}`}
    >
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
    </Button>
  );
}
