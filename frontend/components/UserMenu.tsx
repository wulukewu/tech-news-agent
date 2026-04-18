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
import { BarChart3, Settings, Bell, Monitor, User, LogOut } from 'lucide-react';
import Link from 'next/link';
import { toast } from '@/lib/toast';

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

  if (!user) return null;

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-full"
        aria-label="User menu"
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
            <span>Profile</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem asChild>
          <Link href="/app/analytics" className="cursor-pointer">
            <BarChart3 className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>Analytics</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem asChild>
          <Link href="/app/settings" className="cursor-pointer">
            <Settings className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>Settings</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem asChild>
          <Link href="/app/settings/notifications" className="cursor-pointer">
            <Bell className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>Notifications</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem asChild>
          <Link href="/app/system-status" className="cursor-pointer">
            <Monitor className="mr-2 h-4 w-4" aria-hidden="true" />
            <span>System Status</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-destructive focus:text-destructive"
        >
          <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
          <span>Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
