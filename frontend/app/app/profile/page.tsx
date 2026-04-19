'use client';

import { useState } from 'react';
import { useUser } from '@/contexts/UserContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Settings, BookMarked, Rss, BarChart3 } from 'lucide-react';
import Link from 'next/link';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';

/**
 * Profile Page
 *
 * Displays user information, edit functionality, and account statistics
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
 */
export default function ProfilePage() {
  const { user } = useUser();
  const { t } = useI18n();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
  });

  const handleSave = async () => {
    try {
      // TODO: Implement API call to update user profile
      toast.success(t('success.profile-updated'));
      setIsEditing(false);
    } catch (error) {
      toast.error(t('errors.profile-update-failed'));
    }
  };

  const handleCancel = () => {
    setFormData({
      username: user?.username || '',
      email: user?.email || '',
    });
    setIsEditing(false);
  };

  if (!user) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-4xl">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">{t('pages.profile.title')}</h1>
          <p className="text-muted-foreground">{t('pages.profile.description')}</p>
        </div>

        {/* Profile Information Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{t('pages.profile.profile-information')}</CardTitle>
                <CardDescription>{t('pages.profile.profile-information-desc')}</CardDescription>
              </div>
              {!isEditing && (
                <Button onClick={() => setIsEditing(true)}>{t('buttons.edit-profile')}</Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Avatar */}
            <div className="flex items-center gap-4">
              <Avatar className="h-20 w-20">
                {user.avatar && <AvatarImage src={user.avatar} alt={user.username} />}
                <AvatarFallback className="text-2xl">
                  {user.username?.[0]?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-lg font-semibold">{user.username}</h3>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
            </div>

            {/* Edit Form */}
            {isEditing ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username">{t('pages.profile.username')}</Label>
                  <Input
                    id="username"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    placeholder={t('pages.profile.enter-username')}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">{t('pages.profile.email')}</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder={t('pages.profile.enter-email')}
                  />
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleSave}>{t('buttons.save-changes')}</Button>
                  <Button variant="outline" onClick={handleCancel}>
                    {t('buttons.cancel')}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <Label className="text-muted-foreground">{t('pages.profile.username')}</Label>
                  <p className="text-lg">{user.username}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t('pages.profile.email')}</Label>
                  <p className="text-lg">{user.email}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Account Statistics */}
        <Card>
          <CardHeader>
            <CardTitle>{t('pages.profile.account-statistics')}</CardTitle>
            <CardDescription>{t('pages.profile.account-statistics-desc')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-4 rounded-lg bg-muted/50">
                <div className="p-2 rounded-full bg-primary/10">
                  <BookMarked className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('pages.profile.reading-list')}</p>
                  <p className="text-2xl font-bold">0</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 rounded-lg bg-muted/50">
                <div className="p-2 rounded-full bg-primary/10">
                  <Rss className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t('pages.profile.subscriptions')}
                  </p>
                  <p className="text-2xl font-bold">0</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 rounded-lg bg-muted/50">
                <div className="p-2 rounded-full bg-primary/10">
                  <BarChart3 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t('pages.profile.articles-read')}
                  </p>
                  <p className="text-2xl font-bold">0</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle>{t('pages.profile.quick-links')}</CardTitle>
            <CardDescription>{t('pages.profile.quick-links-desc')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Link href="/dashboard/settings">
                <Button variant="ghost" className="w-full justify-start gap-2">
                  <Settings className="h-4 w-4" />
                  {t('pages.profile.settings')}
                </Button>
              </Link>
              <Link href="/dashboard/analytics">
                <Button variant="ghost" className="w-full justify-start gap-2">
                  <BarChart3 className="h-4 w-4" />
                  {t('pages.profile.analytics')}
                </Button>
              </Link>
              <Link href="/dashboard/reading-list">
                <Button variant="ghost" className="w-full justify-start gap-2">
                  <BookMarked className="h-4 w-4" />
                  {t('pages.profile.reading-list')}
                </Button>
              </Link>
              <Link href="/dashboard/subscriptions">
                <Button variant="ghost" className="w-full justify-start gap-2">
                  <Rss className="h-4 w-4" />
                  {t('pages.profile.subscriptions')}
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
