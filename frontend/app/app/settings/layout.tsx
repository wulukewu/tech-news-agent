'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Bell, Brain, User, Palette, BarChart3, Monitor, Sparkles } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

interface SettingsLayoutProps {
  children: React.ReactNode;
}

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  const pathname = usePathname();
  const { t } = useI18n();

  const settingsNav = [
    { title: t('nav.notifications'), href: '/app/settings/notifications', icon: Bell },
    { title: t('nav.preferences'), href: '/app/settings/preferences', icon: Brain },
    { title: t('nav.reminders'), href: '/app/settings/reminders', icon: Sparkles },
    { title: t('nav.account'), href: '/app/settings/account', icon: User },
    { title: t('nav.appearance'), href: '/app/settings/appearance', icon: Palette },
    { title: t('nav.analytics'), href: '/app/settings/analytics', icon: BarChart3 },
    { title: t('nav.system-status'), href: '/app/settings/system-status', icon: Monitor },
  ];

  return (
    <div className="space-y-6">
      <div className="border-b animate-in fade-in-50 slide-in-from-top-2 duration-500">
        <nav className="flex space-x-8 overflow-x-auto" aria-label="Settings tabs">
          {settingsNav.map((item, index) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (pathname === '/app/settings' && item.href === '/app/settings/notifications');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 px-1 py-3 border-b-2 text-sm whitespace-nowrap',
                  'transition-all duration-300 hover:scale-[1.02]',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'animate-in slide-in-from-top-2 fade-in-50',
                  isActive
                    ? 'border-primary text-foreground font-medium'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                )}
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <Icon
                  className={cn(
                    'h-4 w-4 transition-transform duration-200',
                    isActive ? 'scale-110' : 'hover:scale-[1.05]'
                  )}
                />
                {item.title}
              </Link>
            );
          })}
        </nav>
      </div>
      <main className="animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-300">
        {children}
      </main>
    </div>
  );
}
