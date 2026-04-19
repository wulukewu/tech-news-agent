'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Rss, BookMarked, Menu, X, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/UserContext';
import { useI18n } from '@/contexts/I18nContext';
import type { TranslationKey } from '@/types/i18n';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Logo } from '@/components/Logo';

export interface NavigationItem {
  href: string;
  label?: string; // Deprecated: use labelKey instead
  labelKey?: TranslationKey; // Translation key for the label
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  disabled?: boolean;
  shortcut?: string;
}

interface SidebarProps {
  navigation?: NavigationItem[];
  collapsed?: boolean;
  onToggle?: () => void;
  className?: string;
}

const defaultNavigation: NavigationItem[] = [
  { href: '/app/articles', labelKey: 'nav.articles', icon: Home, shortcut: 'D' },
  { href: '/app/reading-list', labelKey: 'nav.reading-list', icon: BookMarked, shortcut: 'R' },
  { href: '/app/subscriptions', labelKey: 'nav.subscriptions', icon: Rss, shortcut: 'S' },
  { href: '/app/settings', labelKey: 'nav.settings', icon: Bell, shortcut: 'N' },
];

/**
 * Sidebar - Responsive sidebar navigation component
 * Desktop: Fixed sidebar with 64px collapsed / 256px expanded width
 * Mobile: Slide-out drawer navigation
 * Requirements: 3.1, 3.4, 3.5, 3.6, 17.1
 */
export function Sidebar({
  navigation = defaultNavigation,
  collapsed = false,
  onToggle: _onToggle,
  className,
}: SidebarProps) {
  const pathname = usePathname();
  const { user } = useUser();
  const { t } = useI18n();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Memoize translated navigation items to prevent re-translation on every render
  // Requirements: 8.6 - Performance optimization with useMemo
  const translatedNavigation = React.useMemo(
    () =>
      navigation.map((item) => ({
        ...item,
        translatedLabel: item.labelKey ? t(item.labelKey) : item.label || '',
      })),
    [navigation, t]
  );

  const toggleMobileMenu = () => setMobileMenuOpen(!mobileMenuOpen);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle shortcuts when not in input fields
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      // Handle Cmd/Ctrl + key combinations
      if (event.metaKey || event.ctrlKey) {
        const shortcut = event.key.toLowerCase();
        const item = translatedNavigation.find((nav) => nav.shortcut?.toLowerCase() === shortcut);

        if (item && !item.disabled) {
          event.preventDefault();
          window.location.href = item.href;
        }
      }

      // Handle escape to close mobile menu
      if (event.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [translatedNavigation, mobileMenuOpen]);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  return (
    <>
      {/* Desktop Sidebar - Req 3.1, 3.4, 3.5, 3.6 */}
      <div className={cn('hidden lg:flex lg:flex-col lg:h-full', className)}>
        {/* Logo section at top - Req 3.1 */}
        <div
          className={cn(
            'flex items-center border-b transition-all duration-300',
            collapsed ? 'justify-center p-3' : 'justify-between p-4'
          )}
        >
          <Link href="/" className="hover:opacity-80 transition-opacity">
            <Logo
              size={collapsed ? 24 : 28}
              showText={!collapsed}
              textClassName="text-base font-bold"
            />
          </Link>
        </div>

        {/* Navigation items - Req 3.1, 3.4 */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto" aria-label="Sidebar navigation">
          {translatedNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            const label = item.translatedLabel;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-md transition-all duration-200 cursor-pointer group relative',
                  'hover:bg-accent hover:text-accent-foreground',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  // Active state with left border highlight - Req 3.4
                  isActive &&
                    'bg-accent/50 text-accent-foreground before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-primary before:rounded-r',
                  item.disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
                  collapsed && 'justify-center px-2'
                )}
                aria-current={isActive ? 'page' : undefined}
                aria-disabled={item.disabled}
                title={collapsed ? `${label} (Cmd+${item.shortcut})` : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {!collapsed && (
                  <>
                    <span className="truncate flex-1">{label}</span>
                    <div className="flex items-center gap-2">
                      {item.badge && (
                        <span className="bg-muted text-muted-foreground text-xs px-2 py-0.5 rounded-full min-w-[20px] text-center">
                          {item.badge}
                        </span>
                      )}
                      {item.shortcut && (
                        <kbd className="hidden group-hover:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                          <span className="text-xs">⌘</span>
                          {item.shortcut}
                        </kbd>
                      )}
                    </div>
                  </>
                )}

                {/* Tooltip for collapsed state */}
                {collapsed && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-sm rounded-md shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 whitespace-nowrap">
                    {label}
                    {item.shortcut && (
                      <span className="ml-2 text-xs text-muted-foreground">⌘{item.shortcut}</span>
                    )}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User profile section at bottom - Req 3.5, 3.6, 17.1 */}
        <div
          className={cn(
            'border-t p-3 transition-all duration-300',
            collapsed ? 'flex flex-col items-center gap-2' : 'space-y-3'
          )}
        >
          {user && (
            <div
              className={cn('flex items-center gap-3', collapsed ? 'flex-col' : 'flex-row min-w-0')}
            >
              <Avatar className={cn('flex-shrink-0', collapsed ? 'h-8 w-8' : 'h-10 w-10')}>
                {user.avatar && <AvatarImage src={user.avatar} alt={user.username || 'User'} />}
                <AvatarFallback>{user.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
              </Avatar>
              {!collapsed && (
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground truncate">{user.username}</p>
                  <p className="text-xs text-muted-foreground truncate">
                    ID: {user.id.slice(0, 8)}...
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Theme toggle in profile section - Req 3.6, 17.1 */}
          <div className={cn('flex', collapsed ? 'justify-center' : 'justify-start')}>
            <ThemeToggle variant="button" />
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="lg:hidden">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleMobileMenu}
          className="fixed top-4 left-4 z-[60] lg:hidden bg-background/80 backdrop-blur border shadow-sm"
          aria-label="Toggle mobile menu"
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>

        {/* Mobile menu overlay */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={toggleMobileMenu}
            aria-hidden="true"
          />
        )}

        {/* Mobile menu */}
        <div
          className={cn(
            'fixed inset-y-0 left-0 z-50 w-72 bg-background border-r transform transition-transform duration-300 ease-in-out lg:hidden shadow-xl',
            mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex flex-col h-full pt-16">
            {/* Mobile header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                {user && (
                  <>
                    <Avatar className="h-8 w-8">
                      {user.avatar && (
                        <AvatarImage src={user.avatar} alt={user.username || 'User'} />
                      )}
                      <AvatarFallback>{user.username?.[0]?.toUpperCase() || 'U'}</AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground truncate">
                        {user.username}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        ID: {user.id.slice(0, 8)}...
                      </p>
                    </div>
                  </>
                )}
              </div>
              <div className="flex items-center gap-1">
                <ThemeToggle variant="button" />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleMobileMenu}
                  className="h-8 w-8"
                  aria-label="Close mobile menu"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Mobile navigation */}
            <nav className="flex-1 p-4 space-y-1 overflow-y-auto" aria-label="Mobile navigation">
              {translatedNavigation.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                const label = item.translatedLabel;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={toggleMobileMenu}
                    className={cn(
                      'flex items-center gap-3 px-3 py-3 text-sm font-medium rounded-lg transition-colors cursor-pointer',
                      'hover:bg-accent hover:text-accent-foreground',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                      isActive && 'bg-primary text-primary-foreground hover:bg-primary/90',
                      item.disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                    aria-disabled={item.disabled}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                    <span className="truncate flex-1">{label}</span>
                    {item.badge && (
                      <span className="bg-muted text-muted-foreground text-xs px-2 py-0.5 rounded-full">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Mobile bottom navigation */}
        <div className="fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur border-t lg:hidden safe-area-pb">
          <nav className="flex justify-around py-2" aria-label="Bottom navigation">
            {translatedNavigation.slice(0, 5).map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              const label = item.translatedLabel;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex flex-col items-center gap-1 px-2 py-2 text-xs font-medium rounded-lg transition-colors cursor-pointer relative min-h-[44px] min-w-[44px] justify-center',
                    'hover:bg-accent hover:text-accent-foreground',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                    isActive && 'text-primary bg-primary/10',
                    item.disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                  aria-disabled={item.disabled}
                  aria-label={label}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                  <span className="truncate max-w-[60px] leading-tight">{label}</span>
                  {item.badge && (
                    <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded-full min-w-[18px] h-[18px] flex items-center justify-center">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </>
  );
}
