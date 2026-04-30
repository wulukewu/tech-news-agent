'use client';

/**
 * Footer Component
 *
 * Footer section with links, copyright, and social media.
 * Provides navigation and legal information.
 *
 * Features:
 * - Multi-column layout (responsive)
 * - Social media links
 * - Copyright notice
 * - Quick links
 *
 * Requirements: 1.6
 */

import { Github, Twitter, Mail } from 'lucide-react';
import { Logo } from '@/components/Logo';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

const footerLinks = {
  product: [
    { label: 'Features', href: '#features' },
    { label: 'About', href: '#benefits' },
    { label: 'Login', href: '/login' },
  ],
  resources: [
    { label: 'Documentation', href: '#' },
    { label: 'API', href: '#' },
    { label: 'Support', href: '#' },
  ],
  legal: [
    { label: 'Privacy Policy', href: '#' },
    { label: 'Terms of Service', href: '#' },
    { label: 'Cookie Policy', href: '#' },
  ],
};

const socialLinks = [
  { icon: Github, href: 'https://github.com', label: 'GitHub' },
  { icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
  { icon: Mail, href: 'mailto:contact@technewsagent.com', label: 'Email' },
];

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t bg-muted/50">
      <div className="container mx-auto px-4 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-12">
          {/* Brand Column */}
          <div className="lg:col-span-2 space-y-4 animate-in fade-in slide-in-from-left-4 duration-1000">
            <div className="hover:scale-105 transition-transform duration-300">
              <Logo size={32} showText />
            </div>
            <p className="text-sm text-muted-foreground max-w-xs leading-relaxed animate-in fade-in slide-in-from-left-4 duration-1000 delay-200">
              Your personalized tech news platform. Aggregate, discover, and read tech content from
              multiple sources in one place.
            </p>

            {/* Social Links */}
            <div className="flex gap-3 pt-2">
              {socialLinks.map((social, index) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.label}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center h-9 w-9 rounded-md border bg-background hover:bg-accent hover:text-accent-foreground transition-all duration-300 hover:scale-110 hover:shadow-md animate-in zoom-in-50 duration-500"
                    style={{ animationDelay: `${400 + index * 100}ms` }}
                    aria-label={social.label}
                  >
                    <Icon className="h-4 w-4 transition-transform duration-300 hover:scale-110" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Product Links */}
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300">
            <h3 className="font-semibold mb-4">Product</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link, index) => (
                <li
                  key={link.label}
                  className="animate-in slide-in-from-bottom-2 duration-500"
                  style={{ animationDelay: `${500 + index * 100}ms` }}
                >
                  <a
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-all duration-300 cursor-pointer hover:translate-x-1"
                    onClick={(e) => {
                      if (link.href.startsWith('#')) {
                        e.preventDefault();
                        const element = document.querySelector(link.href);
                        if (element) {
                          element.scrollIntoView({ behavior: 'smooth' });
                        }
                      }
                    }}
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-400">
            <h3 className="font-semibold mb-4">Resources</h3>
            <ul className="space-y-3">
              {footerLinks.resources.map((link, index) => (
                <li
                  key={link.label}
                  className="animate-in slide-in-from-bottom-2 duration-500"
                  style={{ animationDelay: `${600 + index * 100}ms` }}
                >
                  <a
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-all duration-300 hover:translate-x-1"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500">
            <h3 className="font-semibold mb-4">Legal</h3>
            <ul className="space-y-3">
              {footerLinks.legal.map((link, index) => (
                <li
                  key={link.label}
                  className="animate-in slide-in-from-bottom-2 duration-500"
                  style={{ animationDelay: `${700 + index * 100}ms` }}
                >
                  <a
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-all duration-300 hover:translate-x-1"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">
              © {currentYear} Tech News Agent. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <div className="hover:scale-105 transition-transform duration-300">
                <LanguageSwitcher variant="compact" />
              </div>
              <p className="text-sm text-muted-foreground hidden sm:block">
                Built with Next.js, TypeScript, and Tailwind CSS
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
