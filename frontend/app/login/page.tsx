'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { AuthGuard } from '@/components/AuthGuard';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Logo } from '@/components/Logo';
import { PublicNavbar } from '@/components/PublicNavbar';
import { useI18n } from '@/contexts/I18nContext';

function DiscordIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginPageFallback />}>
      <AuthGuard fallback={<LoginPageFallback />}>
        <LoginPageInner />
      </AuthGuard>
    </Suspense>
  );
}

function LoginPageFallback() {
  const { t } = useI18n();

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">{t('buttons.loading')}</p>
      </div>
    </div>
  );
}

function LoginPageInner() {
  const { isAuthenticated, loading, login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get('redirect') || '/app/articles';
  const { t } = useI18n();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push(redirect);
    }
  }, [isAuthenticated, loading, redirect, router]);

  const handleLogin = () => {
    login(redirect);
  };

  if (loading) {
    return <LoginPageFallback />;
  }

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]" />

      {/* Header */}
      <PublicNavbar showBackButton={true} backHref="/" backText={t('pages.login.back-to-home')} />

      {/* Main content */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-4 min-h-[calc(100vh-80px)]">
        <div className="w-full max-w-md">
          <Card className="shadow-2xl border-border/50 bg-background/80 backdrop-blur-sm">
            <CardContent className="p-8">
              {/* Logo */}
              <div className="text-center mb-8">
                <div className="flex justify-center mb-6">
                  <div className="relative">
                    <div className="absolute inset-0 blur-2xl bg-primary/20 rounded-full" />
                    <Logo size={80} />
                  </div>
                </div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Welcome Back</h1>
                <p className="text-muted-foreground">
                  Sign in to access your personalized tech news feed
                </p>
              </div>

              {/* Login Button */}
              <Button
                onClick={handleLogin}
                className="w-full h-12 text-base font-semibold bg-[#5865F2] hover:bg-[#4752C4] text-white transition-all duration-200 shadow-lg hover:shadow-xl"
                size="lg"
              >
                <DiscordIcon className="mr-3 h-5 w-5" />
                Continue with Discord
              </Button>

              {/* Features */}
              <div className="mt-8 pt-6 border-t border-border/50">
                <p className="text-sm text-muted-foreground text-center mb-4">What you'll get:</p>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                    <span>AI-powered article recommendations</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                    <span>Smart reminders via Discord DM</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                    <span>Personalized reading lists</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
