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
      <div className="border-b">
        <nav className="flex space-x-8 overflow-x-auto" aria-label="Settings tabs">
          {settingsNav.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (pathname === '/app/settings' && item.href === '/app/settings/notifications');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 px-1 py-3 border-b-2 text-sm whitespace-nowrap transition-colors duration-150',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  isActive
                    ? 'border-primary text-foreground font-medium'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.title}
              </Link>
            );
          })}
        </nav>
      </div>
      <main>{children}</main>
    </div>
  );
}
