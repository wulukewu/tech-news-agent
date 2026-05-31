'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Zap, Brain, MessageSquare, FileText, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { PublicNavbar } from '@/components/PublicNavbar';
import { Footer } from '@/components/landing/Footer';
import { useI18n } from '@/contexts/I18nContext';
import { fetchPublicRecommendedArticles } from '@/lib/api/articles';
import { ArticleCard } from '@/components/ArticleCard';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from '@/lib/toast';
import type { Article } from '@/types/article';

export default function ModernLandingPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadArticles = useCallback(async (isSilent = false) => {
    if (!isSilent) setIsLoading(true);
    else setIsRefreshing(true);

    try {
      // Fetch 3 recommended articles
      const data = await fetchPublicRecommendedArticles(3);
      if (data && data.length > 0) {
        setArticles(data);
      }
    } catch (err) {
      console.error('Error fetching landing articles:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadArticles();

    // 30 seconds auto-refresh interval
    const interval = setInterval(() => {
      loadArticles(true);
    }, 30000);

    return () => clearInterval(interval);
  }, [loadArticles]);

  const handleActionRedirect = useCallback(
    (toastMessageKey: string) => {
      toast.info(t(toastMessageKey as any));
      router.push('/login');
    },
    [router, t]
  );

  const scrollToFeatures = () => {
    const featuresSection = document.getElementById('features-section');
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      <PublicNavbar />

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 lg:py-24">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Left: Content */}
          <div className="space-y-6 lg:pt-6">
            <div className="space-y-4">
              <Badge variant="secondary" className="w-fit">
                <Zap className="w-3 h-3 mr-1" />
                {t('pages.landing.hero.badge')}
              </Badge>
              <h1 className="text-4xl lg:text-6xl font-bold tracking-tight">
                {t('pages.landing.hero.title')}
                <span className="text-primary block">
                  {t('pages.landing.hero.title-highlight')}
                </span>
              </h1>
              <p className="text-xl text-muted-foreground leading-relaxed">
                {t('pages.landing.hero.description')}
              </p>
            </div>

            {/* Key Features */}
            <div className="flex flex-wrap gap-3">
              <Badge variant="secondary" className="flex items-center gap-2">
                <FileText className="w-3 h-3" />
                {t('pages.landing.features.multi-source')}
              </Badge>
              <Badge variant="secondary" className="flex items-center gap-2">
                <Brain className="w-3 h-3" />
                {t('pages.landing.features.ai-powered')}
              </Badge>
              <Badge variant="secondary" className="flex items-center gap-2">
                <MessageSquare className="w-3 h-3" />
                {t('pages.landing.features.discord')}
              </Badge>
              <Badge variant="secondary" className="flex items-center gap-2">
                <Zap className="w-3 h-3" />
                {t('pages.landing.features.smart-reminders')}
              </Badge>
            </div>

            {/* CTA */}
            <div className="flex gap-4">
              <Button size="lg" asChild>
                <Link href="/app">
                  {t('pages.landing.hero.cta-primary')} <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" onClick={scrollToFeatures}>
                {t('pages.landing.hero.cta-secondary')}
              </Button>
            </div>
          </div>

          {/* Right: Live Demo */}
          <div className="space-y-6" id="demo-section">
            <div className="flex items-center justify-between mb-4 border-b pb-2">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
                {t('pages.landing.features.demo-title')}
                <Badge
                  variant="outline"
                  className="text-[10px] uppercase font-bold text-emerald-600 dark:text-emerald-400 border-emerald-500/20 bg-emerald-500/5 px-1.5 py-0"
                >
                  {t('pages.landing.features.live-badge')}
                </Badge>
              </h3>
              {isRefreshing && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            </div>

            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="overflow-hidden border border-border/60">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <Skeleton className="h-4 w-16" />
                        <Skeleton className="h-4 w-24" />
                      </div>
                      <Skeleton className="h-6 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                      <div className="space-y-2 pt-2">
                        <Skeleton className="h-12 w-full" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : articles.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground border border-dashed rounded-lg">
                <p>{t('pages.landing.features.no-articles')}</p>
              </div>
            ) : (
              <div className="space-y-4 animate-in fade-in duration-500">
                {articles.map((article) => (
                  <div
                    key={article.id}
                    className="transition-all duration-300 transform hover:-translate-y-0.5"
                  >
                    <ArticleCard article={article} hideActions={true} />
                  </div>
                ))}

                {/* Registration CTA button at the bottom of the feed */}
                <div className="pt-2 text-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    asChild
                    className="text-xs text-muted-foreground hover:text-primary transition-colors duration-200"
                  >
                    <Link href="/login">{t('pages.landing.features.login-to-unlock')}</Link>
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features-section" className="bg-muted/30 py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">
              {t('pages.landing.section.title')}
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              {t('pages.landing.section.description')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Smart Reminders */}
            <Card className="text-center p-8">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-3">
                {t('pages.landing.section.smart-reminders-title')}
              </h3>
              <p className="text-muted-foreground">
                {t('pages.landing.section.smart-reminders-desc')}
              </p>
            </Card>

            {/* AI Analysis */}
            <Card className="text-center p-8">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Brain className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-3">
                {t('pages.landing.section.ai-analysis-title')}
              </h3>
              <p className="text-muted-foreground">{t('pages.landing.section.ai-analysis-desc')}</p>
            </Card>

            {/* Multi-Platform */}
            <Card className="text-center p-8">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-3">
                {t('pages.landing.section.multi-platform-title')}
              </h3>
              <p className="text-muted-foreground">
                {t('pages.landing.section.multi-platform-desc')}
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-2xl mx-auto space-y-8">
            <h2 className="text-3xl lg:text-4xl font-bold">{t('pages.landing.cta.title')}</h2>
            <p className="text-xl text-muted-foreground">{t('pages.landing.cta.description')}</p>
            <div className="flex gap-4 justify-center">
              <Button size="lg" asChild>
                <Link href="/app">
                  {t('pages.landing.cta.button')} <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
