'use client';

import React from 'react';
import Link from 'next/link';
import { Search, Bell, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useUser } from '@/contexts/UserContext';
import { useAuth } from '@/contexts/AuthContext';

interface HeaderProps {
  className?: string;
  showSearch?: boolean;
  showNotifications?: boolean;
  showUserMenu?: boolean;
  onSearch?: (query: string) => void;
  searchPlaceholder?: string;
}

/**
 * Header - Application header component
 * Provides navigation, search, notifications, and user menu
 */
export function Header({
  className,
  showSearch = true,
  showNotifications = true,
  showUserMenu = true,
  onSearch,
  searchPlaceholder = '搜尋文章...',
}: HeaderProps) {
  const { user } = useUser();
  const { logout } = useAuth();
  const [searchQuery, setSearchQuery] = React.useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch && searchQuery.trim()) {
      onSearch(searchQuery.trim());
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  return (
    <header className={cn('flex items-center justify-between px-4 py-3 lg:px-6', className)}>
      {/* Logo and brand */}
      <div className="flex items-center gap-4">
        <Link
          href="/"
          className="flex items-center gap-2 font-bold text-lg hover:opacity-80 transition-opacity"
        >
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground text-sm font-bold">TN</span>
          </div>
          <span className="hidden sm:inline">Tech News</span>
        </Link>
      </div>

      {/* Search bar */}
      {showSearch && (
        <div className="flex-1 max-w-md mx-4">
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={handleSearchChange}
              className="pl-10 pr-4"
              aria-label="搜尋"
            />
          </form>
        </div>
      )}

      {/* Right side actions */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <ThemeToggle variant="button" />

        {/* Notifications */}
        {showNotifications && (
          <Button variant="ghost" size="icon" className="relative" aria-label="通知">
            <Bell className="h-5 w-5" />
            {/* Notification badge */}
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
          </Button>
        )}

        {/* User menu */}
        {showUserMenu && user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-9 w-9 rounded-full"
                aria-label="使用者選單"
              >
                <Avatar className="h-9 w-9">
                  {user.avatar && <AvatarImage src={user.avatar} alt={user.username || 'User'} />}
                  <AvatarFallback>
                    <User className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user.username}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user.discordId || `ID: ${user.id.slice(0, 8)}...`}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/settings/profile">個人資料</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings/notifications">通知設定</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings">設定</Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-red-600 focus:text-red-600">
                登出
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Login button for non-authenticated users */}
        {showUserMenu && !user && (
          <Button asChild variant="default" size="sm">
            <Link href="/">登入</Link>
          </Button>
        )}
      </div>
    </header>
  );
}
