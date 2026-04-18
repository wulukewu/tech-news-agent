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
        <div className="mx-auto max-w-4xl">
          <div className="relative overflow-hidden rounded-2xl border bg-card p-8 md:p-12 lg:p-16 shadow-xl">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-grid-slate-100 [mask-image:radial-gradient(white,transparent_85%)] dark:bg-grid-slate-700/25" />

            <div className="relative text-center space-y-6">
              {/* Icon */}
              <div className="inline-flex p-3 rounded-full bg-primary/10 text-primary mb-4">
                <Sparkles className="h-8 w-8" />
              </div>

              {/* Headline */}
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight">
                Ready to Get Started?
              </h2>

              {/* Description */}
              <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
                Join Tech News Agent today and transform the way you consume tech news. Quick login
                with your Discord account.
              </p>

              {/* CTA Button */}
              <div className="pt-6">
                <Link href="/login">
                  <Button
                    size="lg"
                    className="text-lg px-10 py-7 h-auto group shadow-lg hover:shadow-xl transition-all"
                  >
                    Login with Discord
                    <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
              </div>

              {/* Subtext */}
              <p className="text-sm text-muted-foreground pt-4">
                No credit card required • Free to use • Sign up in seconds
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
