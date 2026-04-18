'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Bell, Palette, User, Settings as SettingsIcon } from 'lucide-react';

interface SettingsLayoutProps {
  children: React.ReactNode;
}

const settingsNav = [
  {
    title: '通知',
    href: '/app/settings/notifications',
    icon: Bell,
  },
  {
    title: '外觀',
    href: '/app/settings/appearance',
    icon: Palette,
  },
  {
    title: '帳戶',
    href: '/app/settings/account',
    icon: User,
  },
  {
    title: '偏好',
    href: '/app/settings/preferences',
    icon: SettingsIcon,
  },
];

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">設定</h1>
        <p className="text-muted-foreground">管理您的帳戶設定和個人偏好</p>
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
                  'flex items-center gap-2 px-1 py-4 border-b-2 font-medium text-sm whitespace-nowrap transition-colors',
                  'hover:text-foreground hover:border-border',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  isActive
                    ? 'border-primary text-foreground'
                    : 'border-transparent text-muted-foreground'
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
