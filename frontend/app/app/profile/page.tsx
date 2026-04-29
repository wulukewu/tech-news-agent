'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@/contexts/UserContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { BookMarked, Rss, BarChart3, ExternalLink } from 'lucide-react';
import Link from 'next/link';
import { apiClient } from '@/lib/api/client';
import { useI18n } from '@/contexts/I18nContext';
import { Skeleton } from '@/components/ui/skeleton';

interface UserStats {
  reading_list_count: number;
  subscriptions_count: number;
  articles_read_count: number;
}

export default function ProfilePage() {
  const { user } = useUser();
  const { t } = useI18n();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiClient
      .get<UserStats>('/api/auth/me/stats')
      .then((res) => setStats(res.data))
      .catch(() =>
        setStats({ reading_list_count: 0, subscriptions_count: 0, articles_read_count: 0 })
      )
      .finally(() => setStatsLoading(false));
  }, [user]);

  if (!user) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-3xl space-y-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-32 rounded-lg" />
        <Skeleton className="h-32 rounded-lg" />
      </div>
    );
  }

  const displayName = user.username || user.discordId;

  return (
    <div className="container mx-auto py-8 px-4 max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('pages.profile.title')}</h1>
        <p className="text-muted-foreground text-sm">{t('pages.profile.description')}</p>
      </div>

      {/* Profile Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              {user.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
              <AvatarFallback className="text-xl">{displayName?.[0]?.toUpperCase()}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold truncate">{displayName}</h2>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="secondary" className="text-xs">
                  Discord
                </Badge>
                <span className="text-xs text-muted-foreground truncate">{user.discordId}</span>
              </div>
            </div>
            <Button variant="outline" size="sm" asChild>
              <a href="https://discord.com/channels/@me" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                Discord
              </a>
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-4">{t('pages.profile.discord-managed')}</p>
        </CardContent>
      </Card>

      {/* Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t('pages.profile.account-statistics')}</CardTitle>
          <CardDescription className="text-sm">
            {t('pages.profile.account-statistics-desc')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {[
              {
                icon: BookMarked,
                label: t('pages.profile.reading-list'),
                value: stats?.reading_list_count,
                href: '/app/reading-list',
              },
              {
                icon: Rss,
                label: t('pages.profile.subscriptions'),
                value: stats?.subscriptions_count,
                href: '/app/subscriptions',
              },
              {
                icon: BarChart3,
                label: t('pages.profile.articles-read'),
                value: stats?.articles_read_count,
                href: '/app/reading-list',
              },
            ].map(({ icon: Icon, label, value, href }) => (
              <Link key={label} href={href}>
                <div className="flex flex-col items-center gap-2 p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors cursor-pointer text-center">
                  <div className="p-2 rounded-full bg-primary/10">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                  <p className="text-xs text-muted-foreground">{label}</p>
                  {statsLoading ? (
                    <Skeleton className="h-7 w-8" />
                  ) : (
                    <p className="text-2xl font-bold">{value ?? 0}</p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t('pages.profile.quick-links')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {[
            { href: '/app/subscriptions', icon: Rss, label: t('pages.profile.subscriptions') },
            { href: '/app/reading-list', icon: BookMarked, label: t('pages.profile.reading-list') },
            {
              href: '/app/settings/preferences',
              icon: BarChart3,
              label: t('pages.profile.settings'),
            },
          ].map(({ href, icon: Icon, label }) => (
            <Link key={href} href={href}>
              <Button variant="ghost" className="w-full justify-start gap-2">
                <Icon className="h-4 w-4" />
                {label}
              </Button>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
