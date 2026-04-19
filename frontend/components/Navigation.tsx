'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Rss,
  BookMarked,
  LogOut,
  Menu,
  X,
  Settings,
  BarChart3,
  Heart,
  Monitor,
} from 'lucide-react';
import { useAuth } from '@/lib/hooks/useAuth';
import { useUser } from '@/contexts/UserContext';
import { useI18n } from '@/contexts/I18nContext';
import type { TranslationKey } from '@/types/i18n';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/ThemeToggle';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { Logo } from '@/components/Logo';
import { UserMenu } from '@/components/UserMenu';
import { cn } from '@/lib/utils';
import { toast } from '@/lib/toast';

interface NavItem {
  href: string;
  labelKey: TranslationKey;
  icon: React.ComponentType<{ className?: string }>;
}

// Main navigation items (3 core features - Req 4.1)
const mainNavItems: NavItem[] = [
  { href: '/app/articles', labelKey: 'nav.articles', icon: Home },
  { href: '/app/reading-list', labelKey: 'nav.reading-list', icon: BookMarked },
  { href: '/app/subscriptions', labelKey: 'nav.subscriptions', icon: Rss },
];

// Secondary items moved to user menu (Req 4.2)
const secondaryNavItems: NavItem[] = [
  { href: '/app/recommendations', labelKey: 'nav.recommendations', icon: Heart },
  { href: '/app/analytics', labelKey: 'nav.analytics', icon: BarChart3 },
  { href: '/app/settings', labelKey: 'nav.settings', icon: Settings },
  { href: '/app/system-status', labelKey: 'nav.system-status', icon: Monitor },
];

export function Navigation() {
  const { logout } = useAuth();
  const { user } = useUser();
  const { t } = useI18n();
  const pathname = usePathname();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Memoize translated navigation items to prevent re-translation on every render
  // Requirements: 8.6 - Performance optimization with useMemo
  const translatedMainNavItems = React.useMemo(
    () =>
      mainNavItems.map((item) => ({
        ...item,
        translatedLabel: t(item.labelKey),
      })),
    [t]
  );

  const translatedSecondaryNavItems = React.useMemo(
    () =>
      secondaryNavItems.map((item) => ({
        ...item,
        translatedLabel: t(item.labelKey),
      })),
    [t]
  );

  // Prevent body scrolling when drawer is open (Req 3.3, 23.5)
  useEffect(() => {
    if (isDrawerOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    // Cleanup on unmount
    return () => {
      document.body.style.overflow = '';
    };
  }, [isDrawerOpen]);

  const handleLogout = async () => {
    try {
      await logout();
      toast.success(t('success.logout'));
    } catch (error) {
      toast.error(t('errors.logout-failed'));
    }
  };

  const closeDrawer = () => {
    setIsDrawerOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="container mx-auto px-4" aria-label="Main navigation">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-4 lg:gap-6">
            <Link href="/" className="hover:opacity-80 transition-opacity flex-shrink-0">
              <Logo size={28} showText={true} textClassName="hidden sm:inline text-xl" />
            </Link>

            {/* Desktop navigation - only show main items */}
            <div className="hidden md:flex gap-1.5 lg:gap-2">
              {translatedMainNavItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-1.5 px-2.5 lg:px-3 py-2 rounded-md transition-colors cursor-pointer',
                      'hover:bg-accent hover:text-accent-foreground',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                      'min-h-[44px] min-w-[44px]', // Touch-friendly targets (Req 9.2)
                      isActive
                        ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-foreground'
                        : 'text-foreground'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    <span className="text-sm font-medium whitespace-nowrap">
                      {item.translatedLabel}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <LanguageSwitcher variant="icon" />
            <ThemeToggle variant="dropdown" />

            {/* User menu for desktop (Req 4.1, 4.2, 4.3, 4.4) */}
            {user && <UserMenu />}

            {/* Hamburger menu button - visible below 768px (Req 23.1) */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden touch-target cursor-pointer"
              onClick={() => setIsDrawerOpen(!isDrawerOpen)}
              aria-label="Toggle navigation menu"
              aria-expanded={isDrawerOpen}
            >
              {isDrawerOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </nav>

      {/* Mobile drawer navigation (Req 23.2, 23.3, 23.4) */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop overlay (Req 23.3, 23.4) */}
          <div
            className="absolute inset-0 bg-black/50 animate-fade-in"
            onClick={closeDrawer}
            aria-hidden="true"
          />

          {/* Drawer panel - slides in from left (Req 23.2) */}
          <nav
            className="absolute left-0 top-0 bottom-0 w-64 bg-card border-r shadow-xl animate-slide-in-from-left"
            aria-label="Mobile navigation"
          >
            {/* User profile section at top (Req 23.7) */}
            {user && (
              <div className="flex items-center gap-3 p-4 border-b">
                <Avatar className="h-10 w-10">
                  {user.avatar && <AvatarImage src={user.avatar} alt={user.username || 'User'} />}
                  <AvatarFallback>{user.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{user.username}</p>
                </div>
                {/* Close button in drawer header */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="touch-target cursor-pointer"
                  onClick={closeDrawer}
                  aria-label="Close navigation menu"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            )}

            {/* Navigation items with full-width touch targets (Req 3.7, 23.6) */}
            <div className="py-4 space-y-1 overflow-y-auto max-h-[calc(100vh-200px)]">
              {[...translatedMainNavItems, ...translatedSecondaryNavItems].map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 px-4 py-3 min-h-[56px] w-full cursor-pointer transition-colors',
                      'hover:bg-accent hover:text-accent-foreground',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                      isActive && 'bg-primary text-primary-foreground relative',
                      isActive &&
                        'before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-primary-foreground'
                    )}
                    onClick={closeDrawer}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                    <span className="text-sm font-medium">{item.translatedLabel}</span>
                  </Link>
                );
              })}
            </div>

            {/* Bottom section with language switcher, theme toggle and logout */}
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-card space-y-3">
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between px-2">
                  <span className="text-sm font-medium">{t('nav.language')}</span>
                  <LanguageSwitcher variant="compact" />
                </div>
                <div className="flex items-center justify-between px-2">
                  <span className="text-sm font-medium">{t('nav.theme')}</span>
                  <ThemeToggle variant="dropdown" />
                </div>
              </div>
              {user && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    handleLogout();
                    closeDrawer();
                  }}
                  className="w-full justify-start touch-target cursor-pointer"
                >
                  <LogOut className="h-4 w-4 mr-2" aria-hidden="true" />
                  {t('nav.logout')}
                </Button>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
