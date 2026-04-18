'use client';

/**
 * Landing Page
 *
 * The main landing page for new visitors.
 * Features complete landing page with navigation, hero, features,
 * benefits, CTA, and footer sections.
 *
 * Features:
 * - Professional landing page design
 * - Responsive layout
 * - Authentication-aware navigation
 * - Smooth scrolling between sections
 *
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
 */

import { useAuth } from '@/contexts/AuthContext';
import {
  LandingNav,
  HeroSection,
  FeaturesSection,
  BenefitsSection,
  CTASection,
  Footer,
} from '@/components/landing';

export default function LandingPage() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <LandingNav isAuthenticated={isAuthenticated} />
      <HeroSection />
      <FeaturesSection />
      <BenefitsSection />
      <CTASection />
      <Footer />
    </div>
  );
}
