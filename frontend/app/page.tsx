'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Zap, Brain, MessageSquare, Star, FileText } from 'lucide-react';
import Link from 'next/link';
import { Logo } from '@/components/Logo';

// Mock data for demo
const mockArticles = [
  {
    id: '1',
    title: 'Next.js 15 Released with Revolutionary App Router Improvements',
    category: 'Frontend',
    tinkering_index: 4.2,
    published_at: '2024-04-29T10:00:00Z',
    ai_summary: 'Major performance improvements and new caching strategies...',
  },
  {
    id: '2',
    title: 'OpenAI Announces GPT-5 with Multimodal Capabilities',
    category: 'AI/ML',
    tinkering_index: 4.8,
    published_at: '2024-04-29T08:30:00Z',
    ai_summary: 'Breakthrough in reasoning and code generation...',
  },
];

export default function ModernLandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      {/* Navigation */}
      <nav className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo size={32} />
            <span className="font-bold text-xl">Tech News Agent</span>
          </div>
          <div className="flex items-center gap-4">
            <Button asChild>
              <Link href="/app">Get Started</Link>
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Content */}
          <div className="space-y-8">
            <div className="space-y-4">
              <Badge variant="secondary" className="w-fit">
                <Zap className="w-3 h-3 mr-1" />
                AI-Powered News Curation
              </Badge>
              <h1 className="text-4xl lg:text-6xl font-bold tracking-tight">
                Your Personal
                <span className="text-primary block">Tech News Hub</span>
              </h1>
              <p className="text-xl text-muted-foreground leading-relaxed">
                Intelligent article discovery, AI-powered summaries, and personalized
                recommendations delivered through web dashboard and Discord DM.
              </p>
            </div>

            {/* Key Features */}
            <div className="flex flex-wrap gap-3">
              <Badge variant="secondary" className="flex items-center gap-2">
                <FileText className="w-3 h-3" />
                Multi-source RSS
              </Badge>
              <Badge variant="secondary" className="flex items-center gap-2">
                <Brain className="w-3 h-3" />
                AI-Powered Analysis
              </Badge>
              <Badge variant="secondary" className="flex items-center gap-2">
                <MessageSquare className="w-3 h-3" />
                Discord Integration
              </Badge>
              <Badge variant="secondary" className="flex items-center gap-2">
                <Zap className="w-3 h-3" />
                Smart Reminders
              </Badge>
            </div>

            {/* CTA */}
            <div className="flex gap-4">
              <Button size="lg" asChild>
                <Link href="/app">
                  Start Free <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
              <Button variant="outline" size="lg">
                View Demo
              </Button>
            </div>
          </div>

          {/* Right: Live Demo */}
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-semibold mb-4">Live Article Feed</h3>
            </div>
            <div className="space-y-4">
              {mockArticles.map((article) => (
                <Card key={article.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Badge variant="outline">{article.category}</Badge>
                        <div className="flex items-center gap-1">
                          {Array.from({ length: Math.floor(article.tinkering_index) }).map(
                            (_, i) => (
                              <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                            )
                          )}
                          <span className="text-sm text-muted-foreground ml-1">
                            {article.tinkering_index}
                          </span>
                        </div>
                      </div>
                      <h4 className="font-semibold leading-tight">{article.title}</h4>
                      <p className="text-sm text-muted-foreground">{article.ai_summary}</p>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{new Date(article.published_at).toLocaleDateString()}</span>
                        <span>AI Generated Summary</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-muted/30 py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">Intelligent News Curation</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Advanced AI algorithms analyze and curate tech news from multiple sources, delivering
              personalized content that matters to you.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Smart Reminders */}
            <Card className="text-center p-8">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Smart Reminders</h3>
              <p className="text-muted-foreground">
                AI-powered recommendations based on your reading history and preferences, delivered
                via Discord DM at optimal times.
              </p>
            </Card>

            {/* AI Analysis */}
            <Card className="text-center p-8">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Brain className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI Analysis</h3>
              <p className="text-muted-foreground">
                Every article gets a technical depth score and AI-generated summary, helping you
                quickly identify valuable content.
              </p>
            </Card>

            {/* Multi-Platform */}
            <Card className="text-center p-8">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Multi-Platform</h3>
              <p className="text-muted-foreground">
                Access your curated news through web dashboard, Discord bot commands, or REST API
                integration.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-2xl mx-auto space-y-8">
            <h2 className="text-3xl lg:text-4xl font-bold">
              Ready to Transform Your Tech News Experience?
            </h2>
            <p className="text-xl text-muted-foreground">
              Join hundreds of developers and tech enthusiasts who rely on AI-powered curation to
              stay ahead of the curve.
            </p>
            <div className="flex gap-4 justify-center">
              <Button size="lg" asChild>
                <Link href="/app">
                  Get Started Free <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-muted/30 py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center gap-3 mb-4 md:mb-0">
              <Logo size={24} />
              <span className="font-semibold">Tech News Agent</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2026 Tech News Agent. Intelligent news curation for developers.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
