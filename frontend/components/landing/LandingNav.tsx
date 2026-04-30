'use client';

/**
 * LandingNav Component
 *
 * Navigation bar for the landing page with logo, navigation links,
 * and login/enter app button based on authentication status.
 *
 * Features:
 * - Responsive hamburger menu for mobile
 * - Smooth scroll to sections
 * - Authentication-aware CTA button
 *
 * Requirements: 1.6, 1.7
 */

import { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import { Logo } from '@/components/Logo';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/contexts/I18nContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

interface LandingNavProps {
  isAuthenticated?: boolean;
}

export function LandingNav({ isAuthenticated = false }: LandingNavProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { t } = useI18n();

  const navLinks = [
    { href: '#features', label: 'Features' },
    { href: '#benefits', label: 'About' },
  ];

  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsMenuOpen(false);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 animate-in slide-in-from-top-4 duration-500">
      <nav className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link
            href="/"
            className="flex-shrink-0 animate-in fade-in slide-in-from-left-4 duration-500"
          >
            <div className="hover:scale-[1.02] transition-transform duration-300">
              <Logo size={32} showText textClassName="hidden sm:inline" />
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-4">
            {navLinks.map((link, index) => (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => scrollToSection(e, link.href)}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-all duration-300 cursor-pointer hover:scale-[1.02] animate-in slide-in-from-top-2 duration-500"
                style={{ animationDelay: `${200 + index * 100}ms` }}
              >
                {link.label}
              </a>
            ))}
            <div className="animate-in zoom-in-50 duration-500 delay-400 hover:scale-[1.02] transition-transform duration-300">
              <LanguageSwitcher variant="icon" />
            </div>
            {isAuthenticated ? (
              <Link
                href="/app/articles"
                className="animate-in slide-in-from-right-4 duration-500 delay-500"
              >
                <Button className="transition-all duration-300 hover:scale-[1.02] hover:shadow-md">
                  {t('buttons.enter-app')}
                </Button>
              </Link>
            ) : (
              <Link
                href="/login"
                className="animate-in slide-in-from-right-4 duration-500 delay-500"
              >
                <Button className="transition-all duration-300 hover:scale-[1.02] hover:shadow-md">
                  {t('buttons.login')}
                </Button>
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden transition-all duration-300 hover:scale-[1.05] animate-in zoom-in-50 duration-500 delay-300"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            <div className="transition-transform duration-300">
              {isMenuOpen ? <X className="h-5 w-5 rotate-90" /> : <Menu className="h-5 w-5" />}
            </div>
          </Button>
        </div>
      </nav>

      {/* Mobile Drawer */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden animate-in fade-in duration-300">
          <div
            className="absolute inset-0 bg-black/50 animate-in fade-in duration-300"
            onClick={() => setIsMenuOpen(false)}
          />
          <nav className="absolute left-0 top-0 bottom-0 w-64 bg-background border-r p-6 space-y-6 animate-in slide-in-from-left-4 duration-300">
            <div className="flex items-center justify-between">
              <div className="hover:scale-[1.02] transition-transform duration-300">
                <Logo size={28} showText />
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsMenuOpen(false)}
                aria-label="Close menu"
                className="transition-all duration-300 hover:scale-[1.05] hover:rotate-90"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <div className="space-y-4">
              {navLinks.map((link, index) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={(e) => scrollToSection(e, link.href)}
                  className="block text-base font-medium hover:text-primary transition-all duration-300 cursor-pointer hover:translate-x-2 animate-in slide-in-from-left-2 duration-500"
                  style={{ animationDelay: `${100 + index * 100}ms` }}
                >
                  {link.label}
                </a>
              ))}
            </div>

            <div className="pt-4 border-t space-y-3 animate-in fade-in duration-500 delay-300">
              <div className="hover:scale-[1.02] transition-transform duration-300">
                <LanguageSwitcher variant="compact" />
              </div>
              {isAuthenticated ? (
                <Link href="/app/articles" className="block">
                  <Button className="w-full transition-all duration-300 hover:scale-[1.02] hover:shadow-md">
                    {t('buttons.enter-app')}
                  </Button>
                </Link>
              ) : (
                <Link href="/login" className="block">
                  <Button className="w-full transition-all duration-300 hover:scale-[1.02] hover:shadow-md">
                    {t('buttons.login')}
                  </Button>
                </Link>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
