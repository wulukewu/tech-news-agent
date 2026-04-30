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
            <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-1000">
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight">
                Why Choose Tech News Agent?
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed animate-in fade-in slide-in-from-left-4 duration-1000 delay-200">
                Built for developers, tech enthusiasts, and anyone who wants to stay informed about
                the rapidly evolving tech landscape.
              </p>

              <div className="space-y-4 pt-4">
                {[
                  {
                    title: 'Aggregate multiple tech news sources',
                    desc: 'Connect to RSS feeds, blogs, and news sites',
                  },
                  {
                    title: 'AI-driven personalized recommendations',
                    desc: 'Smart algorithms learn your preferences over time',
                  },
                  {
                    title: 'Technical depth indicator',
                    desc: 'Know the complexity level before you dive in',
                  },
                  {
                    title: 'Organized reading list',
                    desc: "Track what you've read and what's next",
                  },
                ].map((item, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 animate-in fade-in slide-in-from-left-2 duration-500"
                    style={{ animationDelay: `${400 + index * 150}ms` }}
                  >
                    <CheckCircle2
                      className="h-6 w-6 text-primary flex-shrink-0 mt-0.5 animate-in zoom-in-50 duration-300"
                      style={{ animationDelay: `${500 + index * 150}ms` }}
                    />
                    <div>
                      <p className="font-medium">{item.title}</p>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Benefits Cards */}
            <div className="grid sm:grid-cols-2 gap-6">
              {benefits.map((benefit, index) => {
                const Icon = benefit.icon;
                return (
                  <div
                    key={index}
                    className="p-6 rounded-lg border bg-card hover:shadow-lg transition-all duration-300 hover:-translate-y-1 hover:scale-105 group animate-in fade-in slide-in-from-right-4 duration-1000"
                    style={{ animationDelay: `${600 + index * 200}ms` }}
                  >
                    <div className="mb-4 inline-flex p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300 group-hover:scale-110 group-hover:rotate-3">
                      <Icon className="h-5 w-5 transition-transform duration-300 group-hover:scale-110" />
                    </div>
                    <h3 className="font-semibold mb-2 transition-colors duration-300 group-hover:text-primary">
                      {benefit.title}
                    </h3>
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
