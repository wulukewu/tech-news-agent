import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
    './features/**/*.{ts,tsx}',
    './providers/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      // Custom breakpoints for responsive design (Req 1.1, 1.2)
      screens: {
        xs: '375px', // Mobile
        sm: '640px', // Small devices
        md: '768px', // Tablet
        lg: '1024px', // Desktop
        xl: '1440px', // Wide desktop
        '2xl': '1536px',
      },
      // Semantic color tokens (Req 4.1, 4.2)
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      // Custom border radius values (Req 4.4)
      borderRadius: {
        sm: '2px', // Subtle
        md: '4px', // Inputs, small components
        lg: '6px', // Cards, buttons
        xl: '8px', // Modals, large components
        '2xl': '12px', // Rounded cards
        '3xl': '16px', // Very rounded
      },
      // Custom spacing scale including touch targets (Req 1.7, 2.1)
      spacing: {
        '18': '4.5rem',
        '44': '44px', // Touch target size
        '56': '56px', // Mobile nav item height
        '88': '22rem',
      },
      // Typography scale (Req 4.3)
      fontSize: {
        xs: ['12px', { lineHeight: '1.5' }], // Captions, badges
        sm: ['14px', { lineHeight: '1.5' }], // Labels, helper text
        base: ['16px', { lineHeight: '1.5' }], // Body text
        lg: ['18px', { lineHeight: '1.5' }], // Subheadings
        xl: ['20px', { lineHeight: '1.4' }], // Section titles
        '2xl': ['24px', { lineHeight: '1.3' }], // Page titles
        '3xl': ['30px', { lineHeight: '1.2' }], // Hero titles
        '4xl': ['36px', { lineHeight: '1.2' }], // Large headings
        '5xl': ['48px', { lineHeight: '1.1' }], // Display
      },
      // Shadow system for elevation (Req 4.5)
      boxShadow: {
        sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
        md: '0 4px 6px rgba(0, 0, 0, 0.1)',
        lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
        xl: '0 20px 25px rgba(0, 0, 0, 0.1)',
      },
      // Minimum dimensions for touch targets (Req 2.1, 2.3)
      minHeight: {
        '44': '44px', // Minimum touch target size
        '48': '48px', // Form controls on mobile
        '56': '56px', // Mobile nav items
      },
      minWidth: {
        '44': '44px', // Minimum touch target size
        '48': '48px', // Form controls on mobile
        '56': '56px',
      },
      // Animation timing functions and durations (Req 4.7, 21.1)
      transitionDuration: {
        '150': '150ms', // Micro-interactions
        '200': '200ms', // Standard transitions
        '300': '300ms', // Standard transitions
        '500': '500ms', // Complex animations
      },
      transitionTimingFunction: {
        'ease-out': 'cubic-bezier(0.4, 0, 0.2, 1)', // Enter animations
        'ease-in': 'cubic-bezier(0.4, 0, 1, 1)', // Exit animations
        'ease-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)', // Hover effects
      },
      // Keyframe animations (Req 21.2, 21.3)
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-out': {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        'slide-in-from-left': {
          from: { transform: 'translateX(-100%)' },
          to: { transform: 'translateX(0)' },
        },
        'slide-out-to-left': {
          from: { transform: 'translateX(0)' },
          to: { transform: 'translateX(-100%)' },
        },
        'slide-up': {
          from: { transform: 'translateY(100%)' },
          to: { transform: 'translateY(0)' },
        },
        'scale-up': {
          from: { transform: 'scale(0.95)', opacity: '0' },
          to: { transform: 'scale(1)', opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'fade-out': 'fade-out 0.2s ease-out',
        'slide-in-from-left': 'slide-in-from-left 0.3s ease-out',
        'slide-out-to-left': 'slide-out-to-left 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'scale-up': 'scale-up 0.2s ease-out',
        shimmer: 'shimmer 2s infinite linear',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
    // Add custom utilities
    function ({ addUtilities }: any) {
      const newUtilities = {
        '.touch-target': {
          minHeight: '44px',
          minWidth: '44px',
        },
        '.safe-area-pb': {
          paddingBottom: 'env(safe-area-inset-bottom)',
        },
        '.safe-area-pt': {
          paddingTop: 'env(safe-area-inset-top)',
        },
        '.safe-area-pl': {
          paddingLeft: 'env(safe-area-inset-left)',
        },
        '.safe-area-pr': {
          paddingRight: 'env(safe-area-inset-right)',
        },
      };
      addUtilities(newUtilities);
    },
  ],
};

export default config;
