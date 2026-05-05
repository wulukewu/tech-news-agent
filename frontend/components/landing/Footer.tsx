'use client';

import { Logo } from '@/components/Logo';
import { LanguageToggle } from '@/components/LanguageToggle';

const legalLinks = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
];

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t bg-background py-8">
      <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Logo size={24} />
            <span className="font-semibold text-sm">Tech News Agent</span>
          </div>
          <span className="text-sm text-muted-foreground">© {currentYear}</span>
        </div>

        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          {legalLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="hover:text-foreground transition-colors"
            >
              {link.label}
            </a>
          ))}
          <LanguageToggle />
        </div>
      </div>
    </footer>
  );
}
