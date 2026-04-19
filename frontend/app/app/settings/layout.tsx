'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Bell, Palette, User, Settings as SettingsIcon } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

interface SettingsLayoutProps {
  children: React.ReactNode;
}

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  const pathname = usePathname();
  const { t } = useI18n();

  const settingsNav = [
    {
      title: t('nav.notifications'),
      href: '/app/settings/notifications',
      icon: Bell,
    },
    {
      title: t('nav.appearance'),
      href: '/app/settings/appearance',
      icon: Palette,
    },
    {
      title: t('nav.account'),
      href: '/app/settings/account',
      icon: User,
    },
    {
      title: t('nav.preferences'),
      href: '/app/settings/preferences',
      icon: SettingsIcon,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('settings.title')}</h1>
        <p className="text-muted-foreground">{t('settings.description')}</p>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b">
        <nav className="flex space-x-8 overflow-x-auto" aria-label="Settings tabs">
          {settingsNav.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 px-1 py-4 border-b-2 font-medium text-sm whitespace-nowrap transition-all duration-200',
                  'hover:text-foreground hover:border-border',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  isActive
                    ? 'border-primary text-primary font-semibold shadow-sm'
                    : 'border-transparent text-muted-foreground hover:text-foreground/80'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.title}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <main>{children}</main>
    </div>
  );
}
