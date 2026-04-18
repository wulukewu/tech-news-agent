'use client';

/**
 * FeaturesSection Component
 *
 * Showcases 3-4 key features of the product with icons and descriptions.
 * Uses a responsive grid layout.
 *
 * Features:
 * - Icon-based feature cards
 * - Responsive grid (1 col mobile, 2 col tablet, 3 col desktop)
 * - Hover effects
 *
 * Requirements: 1.3
 */

import { Rss, BookMarked, Sparkles, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const features = [
  {
    icon: Rss,
    title: 'Smart Subscribe',
    description:
      'Subscribe to multiple tech news sources and aggregate them in one place. Never miss important updates from your favorite tech blogs.',
  },
  {
    icon: BookMarked,
    title: 'Reading List',
    description:
      'Save articles for later, track your reading progress, and organize your content with status tracking and ratings.',
  },
  {
    icon: Sparkles,
    title: 'AI Recommendations',
    description:
      'Get personalized article recommendations powered by AI. Discover content that matches your interests and reading patterns.',
  },
  {
    icon: TrendingUp,
    title: 'Technical Depth Indicator',
    description:
      'See the "tinkering index" for each article - know at a glance whether content is beginner-friendly or deep technical.',
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-20 md:py-32 bg-muted/50">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-6xl">
          {/* Section Header */}
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight">
              Key Features
            </h2>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
              Everything you need to stay on top of tech news
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card
                  key={index}
                  className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer border-2 hover:border-primary/50"
                >
                  <CardHeader>
                    <div className="mb-4 inline-flex p-3 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                      <Icon className="h-6 w-6" />
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
