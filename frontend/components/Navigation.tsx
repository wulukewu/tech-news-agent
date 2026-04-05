'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Rss, BookMarked, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '@/lib/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/ThemeToggle';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

export function Navigation() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/subscriptions', label: 'Subscriptions', icon: Rss },
    { href: '/reading-list', label: 'Reading List', icon: BookMarked },
  ];

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  return (
    <header className="border-b bg-background">
      <nav className="container mx-auto px-4" aria-label="Main navigation">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/dashboard" className="text-xl font-bold">
              Tech News Agent
            </Link>

            <div className="hidden md:flex gap-4">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 rounded-md transition-colors cursor-pointer',
                      pathname === item.href
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted',
                    )}
                    aria-current={pathname === item.href ? 'page' : undefined}
                  >
                    <Icon className="h-4 w-4" aria-hidden="true" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <div className="hidden md:flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  {user.avatar && (
                    <AvatarImage
                      src={user.avatar}
                      alt={user.username || 'User'}
                    />
                  )}
                  <AvatarFallback>
                    {user.username?.[0]?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm">{user.username}</span>
              </div>
            )}

            <ThemeToggle />

            {user && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="hidden md:flex"
              >
                <LogOut className="h-4 w-4 mr-2" aria-hidden="true" />
                Logout
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle menu"
              aria-expanded={isMenuOpen}
            >
              {isMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 space-y-2 border-t">
            {user && (
              <div className="flex items-center gap-2 px-3 py-2 mb-2">
                <Avatar className="h-8 w-8">
                  {user.avatar && (
                    <AvatarImage
                      src={user.avatar}
                      alt={user.username || 'User'}
                    />
                  )}
                  <AvatarFallback>
                    {user.username?.[0]?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium">{user.username}</span>
              </div>
            )}
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer',
                    pathname === item.href
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted',
                  )}
                  onClick={() => setIsMenuOpen(false)}
                  aria-current={pathname === item.href ? 'page' : undefined}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
            {user && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  handleLogout();
                  setIsMenuOpen(false);
                }}
                className="w-full justify-start"
              >
                <LogOut className="h-4 w-4 mr-2" aria-hidden="true" />
                Logout
              </Button>
            )}
          </div>
        )}
      </nav>
    </header>
  );
}
