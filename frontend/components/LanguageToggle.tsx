'use client';

import * as React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';

interface LanguageToggleProps {
  className?: string;
}

export function LanguageToggle({ className = '' }: LanguageToggleProps) {
  const { locale, setLocale } = useI18n();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" disabled className={className}>
        <span className="text-sm font-bold">文</span>
      </Button>
    );
  }

  const toggle = () => setLocale(locale === 'zh-TW' ? 'en-US' : 'zh-TW');

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label={locale === 'zh-TW' ? 'Switch to English' : '切換為繁體中文'}
      className={`transition-all duration-300 hover:scale-[1.02] ${className}`}
    >
      <span
        className={`absolute text-sm font-bold transition-all duration-300 ${
          locale === 'zh-TW' ? 'scale-100 opacity-100' : 'scale-0 opacity-0'
        }`}
      >
        文
      </span>
      <span
        className={`absolute text-sm font-bold transition-all duration-300 ${
          locale === 'en-US' ? 'scale-100 opacity-100' : 'scale-0 opacity-0'
        }`}
      >
        A
      </span>
    </Button>
  );
}
