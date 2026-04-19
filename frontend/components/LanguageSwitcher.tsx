'use client';

/**
 * LanguageSwitcher Component
 *
 * A compact language switcher that can be used in navigation or footer.
 * Provides two variants:
 * - icon: Globe icon with dropdown menu (for navbar)
 * - compact: Text-based toggle (for footer)
 *
 * Features:
 * - Accessible keyboard navigation
 * - ARIA labels for screen readers
 * - Smooth transitions
 * - Minimum 44x44px touch targets
 *
 * Requirements: Bilingual UI System
 */

import { useState, useRef, useEffect } from 'react';
import { Globe } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';
import type { Locale } from '@/types/i18n';

interface LanguageSwitcherProps {
  variant?: 'icon' | 'compact';
  className?: string;
}

const LANGUAGE_OPTIONS: Array<{ value: Locale; label: string; nativeLabel: string }> = [
  { value: 'zh-TW', label: 'Traditional Chinese', nativeLabel: '繁體中文' },
  { value: 'en-US', label: 'English', nativeLabel: 'English' },
];

export function LanguageSwitcher({ variant = 'icon', className = '' }: LanguageSwitcherProps) {
  const { locale, setLocale } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close dropdown on Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  const handleLanguageChange = (newLocale: Locale) => {
    setLocale(newLocale);
    setIsOpen(false);
  };

  if (variant === 'compact') {
    // Compact text-based toggle for footer
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {LANGUAGE_OPTIONS.map((option, index) => (
          <div key={option.value} className="flex items-center">
            <button
              onClick={() => handleLanguageChange(option.value)}
              aria-label={`Switch to ${option.label}`}
              aria-pressed={locale === option.value}
              className={`
                text-sm font-medium transition-colors duration-200
                min-w-[44px] min-h-[44px] px-2
                focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                ${
                  locale === option.value
                    ? 'text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }
              `}
            >
              {option.value === 'zh-TW' ? '繁' : 'EN'}
            </button>
            {index < LANGUAGE_OPTIONS.length - 1 && (
              <span className="text-muted-foreground">/</span>
            )}
          </div>
        ))}
      </div>
    );
  }

  // Icon variant with dropdown for navbar
  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Language selector"
        aria-expanded={isOpen}
        aria-haspopup="true"
        className="
          flex items-center justify-center
          w-10 h-10 rounded-lg
          text-muted-foreground hover:text-foreground
          hover:bg-accent
          transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
        "
      >
        <Globe className="w-5 h-5" />
      </button>

      {isOpen && (
        <div
          role="menu"
          aria-label="Language options"
          className="
            absolute right-0 mt-2 w-48
            bg-background border border-border rounded-lg shadow-lg
            py-1 z-50
            animate-in fade-in slide-in-from-top-2 duration-200
          "
        >
          {LANGUAGE_OPTIONS.map((option) => (
            <button
              key={option.value}
              role="menuitem"
              onClick={() => handleLanguageChange(option.value)}
              aria-label={`Switch to ${option.label}`}
              className={`
                w-full px-4 py-2.5 text-left text-sm
                transition-colors duration-150
                min-h-[44px] flex items-center
                focus:outline-none focus:bg-accent
                ${
                  locale === option.value
                    ? 'bg-accent text-foreground font-medium'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                }
              `}
            >
              <span className="flex-1">{option.nativeLabel}</span>
              {locale === option.value && (
                <span className="text-primary" aria-hidden="true">
                  ✓
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
