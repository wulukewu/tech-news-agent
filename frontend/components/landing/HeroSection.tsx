'use client';

/**
 * HeroSection Component
 *
 * Hero section for the landing page with product name, tagline,
 * and call-to-action buttons.
 *
 * Features:
 * - Large product logo
 * - Compelling headline and tagline
 * - Primary and secondary CTA buttons
 * - Responsive layout
 *
 * Requirements: 1.2, 1.5
 */

import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';
import { Logo } from '@/components/Logo';
import { Button } from '@/components/ui/button';

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-background via-background to-muted py-20 md:py-32">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]" />

      <div className="container relative mx-auto px-4">
        <div className="mx-auto max-w-4xl text-center space-y-8">
          {/* Logo */}
          <div className="flex justify-center mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <div className="relative">
              <div className="absolute inset-0 blur-3xl bg-primary/20 rounded-full" />
              <Logo size={96} />
            </div>
          </div>

          {/* Headline */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-100">
            Tech News Agent
          </h1>

          {/* Tagline */}
          <p className="text-xl md:text-2xl lg:text-3xl text-muted-foreground font-medium animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-200">
            Your Personalized Tech News Platform
          </p>

          {/* Description */}
          <p className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-300">
            Aggregate multiple tech news sources, get AI-driven personalized recommendations, and
            track technical depth with our intelligent news agent.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500">
            <Link href="/login">
              <Button size="lg" className="text-base px-8 py-6 h-auto group">
                Get Started
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <a href="#features">
              <Button
                size="lg"
                variant="outline"
                className="text-base px-8 py-6 h-auto group"
                onClick={(e) => {
                  e.preventDefault();
                  document.querySelector('#features')?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                <Sparkles className="mr-2 h-5 w-5" />
                Learn More
              </Button>
            </a>
          </div>

          {/* Trust indicator */}
          <p className="text-sm text-muted-foreground pt-8 animate-in fade-in duration-1000 delay-700">
            Powered by AI • Free to use • No credit card required
          </p>
        </div>
      </div>
    </section>
  );
}
