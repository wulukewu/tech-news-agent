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
      <div className="animate-in fade-in-50 slide-in-from-top-4 duration-500">
        <h1 className="text-2xl font-bold">{t('pages.profile.title')}</h1>
        <p className="text-muted-foreground text-sm">{t('pages.profile.description')}</p>
      </div>

      {/* Profile Card */}
      <Card className="animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-100 hover:shadow-lg transition-all">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16 transition-all duration-300 hover:scale-110 hover:shadow-lg">
              {user.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
              <AvatarFallback className="text-xl transition-colors duration-200 hover:bg-primary hover:text-primary-foreground">
                {displayName?.[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold truncate">{displayName}</h2>
              <div className="flex items-center gap-2 mt-1">
                <Badge
                  variant="secondary"
                  className="text-xs transition-all duration-200 hover:scale-105"
                >
                  Discord
                </Badge>
                <span className="text-xs text-muted-foreground truncate">{user.discordId}</span>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              asChild
              className="transition-all duration-200 hover:scale-105 hover:shadow-md"
            >
              <a href="https://discord.com/channels/@me" target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3.5 w-3.5 mr-1.5 transition-transform duration-200 hover:scale-110" />
                Discord
              </a>
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-4">{t('pages.profile.discord-managed')}</p>
        </CardContent>
      </Card>

      {/* Stats */}
      <Card className="animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-200 hover:shadow-lg transition-all">
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
            ].map(({ icon: Icon, label, value, href }, index) => (
              <Link key={label} href={href}>
                <div
                  className="group flex flex-col items-center gap-2 p-4 rounded-lg bg-muted/50 hover:bg-muted transition-all duration-300 cursor-pointer text-center hover:scale-105 hover:shadow-md animate-in zoom-in-50"
                  style={{ animationDelay: `${300 + index * 100}ms` }}
                >
                  <div className="p-2 rounded-full bg-primary/10 transition-all duration-200 group-hover:bg-primary/20 group-hover:scale-110">
                    <Icon className="h-4 w-4 text-primary transition-transform duration-200 group-hover:scale-110" />
                  </div>
                  <p className="text-xs text-muted-foreground">{label}</p>
                  {statsLoading ? (
                    <Skeleton className="h-7 w-8" />
                  ) : (
                    <p className="text-2xl font-bold transition-transform duration-200 group-hover:scale-110">
                      {value ?? 0}
                    </p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card className="animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-300 hover:shadow-lg transition-all">
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
          ].map(({ href, icon: Icon, label }, index) => (
            <Link key={href} href={href}>
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 transition-all duration-200 hover:scale-[1.02] hover:shadow-sm animate-in slide-in-from-left-2"
                style={{ animationDelay: `${400 + index * 100}ms` }}
              >
                <Icon className="h-4 w-4 transition-transform duration-200 hover:scale-110" />
                {label}
              </Button>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
