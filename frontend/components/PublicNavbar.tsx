'use client';

import { Button } from '@/components/ui/button';
import { Logo } from '@/components/Logo';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeCycleToggle } from '@/components/ThemeCycleToggle';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';

interface PublicNavbarProps {
  showBackButton?: boolean;
  backHref?: string;
  backText?: string;
}

export function PublicNavbar({
  showBackButton = false,
  backHref = '/',
  backText = 'Back to Home',
}: PublicNavbarProps) {
  const { isAuthenticated, loading } = useAuth();
  const { locale } = useI18n();

  return (
    <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        {/* Left: Logo or Back Button */}
        <div className="flex items-center gap-3">
          {showBackButton ? (
            <Link href={backHref}>
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                {backText}
              </Button>
            </Link>
          ) : (
            <>
              <Logo size={32} />
              <span className="font-bold text-xl">Tech News Agent</span>
            </>
          )}
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-3">
          <LanguageSwitcher variant="icon" />
          <ThemeCycleToggle />

          {!loading && (
            <Button asChild>
              <Link href="/app">
                {isAuthenticated
                  ? locale === 'zh-TW'
                    ? '開啟 App'
                    : 'Open App'
                  : locale === 'zh-TW'
                    ? '立即開始'
                    : 'Get Started'}
              </Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
