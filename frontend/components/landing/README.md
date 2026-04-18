# Landing Page Components

This directory contains all components for the landing page (`/`).

## Components

### LandingNav

Navigation bar for the landing page with responsive hamburger menu.

**Features:**

- Logo and navigation links (Features, About)
- Authentication-aware CTA button (Login/Enter App)
- Mobile drawer menu
- Smooth scroll to sections

**Props:**

- `isAuthenticated?: boolean` - Whether user is authenticated

### HeroSection

Hero section with product name, tagline, and CTA buttons.

**Features:**

- Large product logo with glow effect
- Compelling headline and tagline
- Primary and secondary CTA buttons
- Responsive layout with animations

### FeaturesSection

Showcases 4 key features with icons and descriptions.

**Features:**

- Icon-based feature cards
- Responsive grid (1 col mobile, 2 col tablet, 4 col desktop)
- Hover effects with card lift
- Uses Lucide icons

**Key Features Displayed:**

1. Smart Subscribe - RSS feed aggregation
2. Reading List - Save and organize articles
3. AI Recommendations - Personalized content
4. Technical Depth Indicator - Tinkering index

### BenefitsSection

Explains why users should choose Tech News Agent.

**Features:**

- Two-column layout (text + benefit cards)
- Checkmark list of main benefits
- 4 benefit cards with icons
- Responsive grid layout

### CTASection

Call-to-action section encouraging users to sign up.

**Features:**

- Eye-catching gradient background
- Prominent login button
- Trust indicators
- Decorative background pattern

### Footer

Footer with links, copyright, and social media.

**Features:**

- Multi-column layout (5 columns on desktop)
- Product, Resources, and Legal link sections
- Social media icons (GitHub, Twitter, Email)
- Copyright notice
- Responsive layout

## Usage

```tsx
import {
  LandingNav,
  HeroSection,
  FeaturesSection,
  BenefitsSection,
  CTASection,
  Footer,
} from '@/components/landing';

export default function LandingPage() {
  const { isAuthenticated } = useAuth();

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
```

## Design Principles

- **Responsive**: All components work on mobile (375px), tablet (768px), and desktop (1024px+)
- **Accessible**: Proper ARIA labels, semantic HTML, keyboard navigation
- **Professional**: Clean design with shadcn/ui components and Tailwind CSS
- **Performant**: Optimized animations, no layout shifts
- **Consistent**: Uses project's design system (colors, typography, spacing)

## Requirements Satisfied

- **1.2**: Landing page displays product name, tagline, and hero section
- **1.3**: Features section showcases key capabilities
- **1.4**: Benefits section explains value proposition
- **1.5**: CTA section with login button
- **1.6**: Navigation bar with links
- **1.7**: Authentication-aware navigation (Enter App for logged-in users)
- **1.8**: Responsive across all breakpoints

## Testing

Tests are located in `frontend/__tests__/unit/components/landing/LandingComponents.test.tsx`.

Run tests:

```bash
npm test -- __tests__/unit/components/landing/LandingComponents.test.tsx
```

All components have basic rendering tests to ensure they display correctly.
