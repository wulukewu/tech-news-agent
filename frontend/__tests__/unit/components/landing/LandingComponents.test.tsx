/**
 * Landing Components Tests
 *
 * Basic rendering tests for landing page components.
 */

import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { LandingNav } from '@/components/landing/LandingNav';
import { HeroSection } from '@/components/landing/HeroSection';
import { FeaturesSection } from '@/components/landing/FeaturesSection';
import { BenefitsSection } from '@/components/landing/BenefitsSection';
import { CTASection } from '@/components/landing/CTASection';
import { Footer } from '@/components/landing/Footer';

// Mock Next.js Link component
vi.mock('next/link', () => {
  return {
    default: ({ children, href }: { children: React.ReactNode; href: string }) => {
      return <a href={href}>{children}</a>;
    },
  };
});

describe('Landing Page Components', () => {
  describe('LandingNav', () => {
    it('renders navigation with login button for unauthenticated users', () => {
      render(<LandingNav isAuthenticated={false} />);
      expect(screen.getByText('Login')).toBeInTheDocument();
      expect(screen.getByText('Features')).toBeInTheDocument();
      expect(screen.getByText('About')).toBeInTheDocument();
    });

    it('renders navigation with Enter App button for authenticated users', () => {
      render(<LandingNav isAuthenticated={true} />);
      expect(screen.getByText('Enter App')).toBeInTheDocument();
    });
  });

  describe('HeroSection', () => {
    it('renders hero section with product name and tagline', () => {
      render(<HeroSection />);
      expect(screen.getByText('Tech News Agent')).toBeInTheDocument();
      expect(screen.getByText('Your Personalized Tech News Platform')).toBeInTheDocument();
      expect(screen.getByText('Get Started')).toBeInTheDocument();
      expect(screen.getByText('Learn More')).toBeInTheDocument();
    });
  });

  describe('FeaturesSection', () => {
    it('renders all feature cards', () => {
      render(<FeaturesSection />);
      expect(screen.getByText('Key Features')).toBeInTheDocument();
      expect(screen.getByText('Smart Subscribe')).toBeInTheDocument();
      expect(screen.getByText('Reading List')).toBeInTheDocument();
      expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
      expect(screen.getByText('Technical Depth Indicator')).toBeInTheDocument();
    });
  });

  describe('BenefitsSection', () => {
    it('renders benefits section with headline', () => {
      render(<BenefitsSection />);
      expect(screen.getByText('Why Choose Tech News Agent?')).toBeInTheDocument();
      expect(screen.getByText('Save Time')).toBeInTheDocument();
      expect(screen.getByText('Stay Focused')).toBeInTheDocument();
      expect(screen.getByText('Quality Content')).toBeInTheDocument();
      expect(screen.getByText('Never Miss Out')).toBeInTheDocument();
    });
  });

  describe('CTASection', () => {
    it('renders call-to-action section', () => {
      render(<CTASection />);
      expect(screen.getByText('Ready to Get Started?')).toBeInTheDocument();
      expect(screen.getByText('Login with Discord')).toBeInTheDocument();
    });
  });

  describe('Footer', () => {
    it('renders footer with links and copyright', () => {
      render(<Footer />);
      expect(screen.getByText(/© \d{4} Tech News Agent/)).toBeInTheDocument();
      expect(screen.getByText('Product')).toBeInTheDocument();
      expect(screen.getByText('Resources')).toBeInTheDocument();
      expect(screen.getByText('Legal')).toBeInTheDocument();
    });
  });
});
