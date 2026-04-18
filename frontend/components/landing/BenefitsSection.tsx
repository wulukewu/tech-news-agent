'use client';

/**
 * BenefitsSection Component
 *
 * Explains why users should choose Tech News Agent.
 * Highlights unique value propositions and benefits.
 *
 * Features:
 * - Benefit list with checkmarks
 * - Visual hierarchy
 * - Compelling copy
 *
 * Requirements: 1.4
 */

import { CheckCircle2, Zap, Target, Shield, Clock } from 'lucide-react';

const benefits = [
  {
    icon: Zap,
    title: 'Save Time',
    description:
      'Stop visiting dozens of websites. Get all your tech news in one centralized dashboard.',
  },
  {
    icon: Target,
    title: 'Stay Focused',
    description: 'AI-powered recommendations help you discover relevant content without the noise.',
  },
  {
    icon: Shield,
    title: 'Quality Content',
    description:
      'Technical depth indicators help you find the right level of content for your needs.',
  },
  {
    icon: Clock,
    title: 'Never Miss Out',
    description:
      'Automatic updates from your subscribed feeds ensure you stay current with the latest tech trends.',
  },
];

export function BenefitsSection() {
  return (
    <section id="benefits" className="py-20 md:py-32 bg-background">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Headline and Description */}
            <div className="space-y-6">
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight">
                Why Choose Tech News Agent?
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Built for developers, tech enthusiasts, and anyone who wants to stay informed about
                the rapidly evolving tech landscape.
              </p>

              <div className="space-y-4 pt-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-6 w-6 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Aggregate multiple tech news sources</p>
                    <p className="text-sm text-muted-foreground">
                      Connect to RSS feeds, blogs, and news sites
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-6 w-6 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">AI-driven personalized recommendations</p>
                    <p className="text-sm text-muted-foreground">
                      Smart algorithms learn your preferences over time
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-6 w-6 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Technical depth indicator</p>
                    <p className="text-sm text-muted-foreground">
                      Know the complexity level before you dive in
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-6 w-6 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium">Organized reading list</p>
                    <p className="text-sm text-muted-foreground">
                      Track what you&apos;ve read and what&apos;s next
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Benefits Cards */}
            <div className="grid sm:grid-cols-2 gap-6">
              {benefits.map((benefit, index) => {
                const Icon = benefit.icon;
                return (
                  <div
                    key={index}
                    className="p-6 rounded-lg border bg-card hover:shadow-md transition-shadow"
                  >
                    <div className="mb-4 inline-flex p-2 rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-semibold mb-2">{benefit.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {benefit.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
