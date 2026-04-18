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
    description: '管理通知偏好和頻率',
  },
  {
    title: '外觀',
    href: '/app/settings/appearance',
    icon: Palette,
    description: '主題和顯示設定',
  },
  {
    title: '帳戶',
    href: '/app/settings/account',
    icon: User,
    description: '個人資料和安全性',
  },
  {
    title: '偏好設定',
    href: '/app/settings/preferences',
    icon: SettingsIcon,
    description: '一般偏好設定',
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

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <aside className="lg:w-64 flex-shrink-0">
          <nav className="space-y-1">
            {settingsNav.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-start gap-3 px-4 py-3 rounded-lg transition-colors',
                    'hover:bg-accent hover:text-accent-foreground',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    isActive && 'bg-accent text-accent-foreground font-medium'
                  )}
                >
                  <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium">{item.title}</div>
                    <div className="text-sm text-muted-foreground">{item.description}</div>
                  </div>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
