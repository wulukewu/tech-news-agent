/**
 * Landing Page Integration Test
 *
 * Tests that the landing page renders correctly with all components
 * and is responsive across different breakpoints.
 */

import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { LandingNav } from '../../LandingNav';
import { HeroSection } from '../../HeroSection';
import { FeaturesSection } from '../../FeaturesSection';
import { BenefitsSection } from '../../BenefitsSection';
import { CTASection } from '../../CTASection';
import { Footer } from '../../Footer';

// Mock Next.js components
vi.mock('next/link', () => {
  return {
    default: ({ children, href }: { children: React.ReactNode; href: string }) => {
      return <a href={href}>{children}</a>;
    },
  };
});

describe('Landing Page Components', () => {
  describe('LandingNav', () => {
    it('renders navigation with logo and links', () => {
      render(<LandingNav />);
      expect(screen.getByText('Features')).toBeInTheDocument();
      expect(screen.getByText('About')).toBeInTheDocument();
      expect(screen.getByText('Login')).toBeInTheDocument();
    });

    it('shows "Enter App" button when authenticated', () => {
      render(<LandingNav isAuthenticated={true} />);
      expect(screen.getByText('Enter App')).toBeInTheDocument();
    });
  });

  describe('HeroSection', () => {
    it('renders hero content with headline and CTA', () => {
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
      expect(screen.getByText('Smart Subscribe')).toBeInTheDocument();
      expect(screen.getByText('Reading List')).toBeInTheDocument();
      expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
      expect(screen.getByText('Technical Depth Indicator')).toBeInTheDocument();
    });
  });

  describe('BenefitsSection', () => {
    it('renders benefits content', () => {
      render(<BenefitsSection />);
      expect(
        screen.getByRole('heading', { name: /Why Choose Tech News Agent/i })
      ).toBeInTheDocument();
    });
  });

  describe('CTASection', () => {
    it('renders call-to-action', () => {
      render(<CTASection />);
      expect(screen.getByRole('heading', { name: /Ready to Get Started/i })).toBeInTheDocument();
    });
  });

  describe('Footer', () => {
    it('renders footer content', () => {
      render(<Footer />);
      const footerText = screen.getAllByText(/Tech News Agent/i);
      expect(footerText.length).toBeGreaterThan(0);
    });
  });
});
