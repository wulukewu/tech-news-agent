'use client';

/**
 * CTASection Component
 *
 * Call-to-action section encouraging users to sign up/login.
 * Features prominent login button and compelling copy.
 *
 * Features:
 * - Eye-catching design
 * - Clear call-to-action
 * - Discord OAuth branding
 *
 * Requirements: 1.5
 */

import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CTASection() {
  return (
    <section className="py-20 md:py-32 bg-gradient-to-br from-primary/10 via-primary/5 to-background">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-4xl animate-in fade-in slide-in-from-bottom-4 duration-1000">
          <div className="relative overflow-hidden rounded-2xl border bg-card p-8 md:p-12 lg:p-16 shadow-xl hover:shadow-2xl transition-all duration-500 group">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-grid-slate-100 [mask-image:radial-gradient(white,transparent_85%)] dark:bg-grid-slate-700/25 animate-in fade-in duration-2000" />

            <div className="relative text-center space-y-6">
              {/* Icon */}
              <div className="inline-flex p-3 rounded-full bg-primary/10 text-primary mb-4 animate-in zoom-in-50 duration-500 delay-300 group-hover:scale-[1.05] group-hover:rotate-12 transition-transform duration-300">
                <Sparkles className="h-8 w-8 animate-pulse" />
              </div>

              {/* Headline */}
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-200">
                Ready to Get Started?
              </h2>

              {/* Description */}
              <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-400">
                Join Tech News Agent today and transform the way you consume tech news. Quick login
                with your Discord account.
              </p>

              {/* CTA Button */}
              <div className="pt-6 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-600">
                <Link href="/login">
                  <Button
                    size="lg"
                    className="text-lg px-10 py-7 h-auto group shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.05] animate-pulse hover:animate-none"
                  >
                    Login with Discord
                    <ArrowRight className="ml-2 h-5 w-5 transition-transform duration-300 group-hover:translate-x-2 group-hover:scale-125" />
                  </Button>
                </Link>
              </div>

              {/* Subtext */}
              <p className="text-sm text-muted-foreground pt-4 animate-in fade-in duration-1000 delay-800">
                <span className="inline-block animate-bounce delay-100">💳</span> No credit card
                required •<span className="inline-block animate-bounce delay-300">🆓</span> Free to
                use •<span className="inline-block animate-bounce delay-500">⚡</span> Sign up in
                seconds
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
