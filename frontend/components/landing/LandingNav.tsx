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

interface LandingNavProps {
  isAuthenticated?: boolean;
}

export function LandingNav({ isAuthenticated = false }: LandingNavProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

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
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex-shrink-0">
            <Logo size={32} showText textClassName="hidden sm:inline" />
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => scrollToSection(e, link.href)}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                {link.label}
              </a>
            ))}
            {isAuthenticated ? (
              <Link href="/dashboard/articles">
                <Button>Enter App</Button>
              </Link>
            ) : (
              <Link href="/login">
                <Button>Login</Button>
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </nav>

      {/* Mobile Drawer */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setIsMenuOpen(false)} />
          <nav className="absolute left-0 top-0 bottom-0 w-64 bg-background border-r p-6 space-y-6">
            <div className="flex items-center justify-between">
              <Logo size={28} showText />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsMenuOpen(false)}
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <div className="space-y-4">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={(e) => scrollToSection(e, link.href)}
                  className="block text-base font-medium hover:text-primary transition-colors cursor-pointer"
                >
                  {link.label}
                </a>
              ))}
            </div>

            <div className="pt-4 border-t">
              {isAuthenticated ? (
                <Link href="/dashboard/articles" className="block">
                  <Button className="w-full">Enter App</Button>
                </Link>
              ) : (
                <Link href="/login" className="block">
                  <Button className="w-full">Login</Button>
                </Link>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
