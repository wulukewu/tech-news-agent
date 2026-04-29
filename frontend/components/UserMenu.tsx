'use client';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useUser } from '@/contexts/UserContext';
import { useAuth } from '@/lib/hooks/useAuth';
import { Settings, User, LogOut } from 'lucide-react';
import Link from 'next/link';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';

/**
 * UserMenu Component
 *
 * Dropdown menu displaying user profile and navigation to secondary features.
 * Requirements: 4.2, 4.3, 4.4
 *
 * Features:
 * - Display user avatar, name, email (Req 4.2)
 * - Menu items: Analytics, Settings, Notifications, System Status, Profile, Logout (Req 4.3)
 * - Accessible with keyboard navigation (Req 4.4)
 */
export function UserMenu() {
  const { user } = useUser();
  const { logout } = useAuth();
  const { t } = useI18n();

  if (!user) return null;

  const handleLogout = async () => {
    try {
      await logout();
      toast.success(t('success.logout'));
    } catch (error) {
      toast.error(t('errors.logout-failed'));
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-full"
        aria-label={t('ui.user-menu')}
      >
        <Avatar className="h-8 w-8 cursor-pointer hover:opacity-80 transition-opacity">
          {user.avatar && <AvatarImage src={user.avatar} alt={user.username || 'User'} />}
          <AvatarFallback className="text-xs">
            {user.username?.[0]?.toUpperCase() || 'U'}
          </AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        {/* User info section (Req 4.2) */}
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.username}</p>
            {user.email && (
              <p className="text-xs text-muted-foreground leading-none">{user.email}</p>
            )}
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {/* Secondary navigation items (Req 4.3) */}
        <DropdownMenuItem asChild>
          <Link href="/app/profile" className="cursor-pointer">
            <User className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>{t('ui.profile')}</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem asChild>
          <Link href="/app/settings" className="cursor-pointer">
            <Settings className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>{t('nav.settings')}</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-destructive focus:text-destructive"
        >
          <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
          <span>{t('nav.logout')}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
